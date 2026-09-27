"""Typed admission and complete-team bookkeeping, separate from runtime claims."""
from collections import deque
from dataclasses import dataclass, field
from curator_policy import PolicyError, digest, exact, require

TEAMS = {
    'generic': ('worker',),
    'complex': ('solver_a', 'solver_b', 'senior', 'implementer'),
    'extra-complex': ('solver_a', 'solver_b', 'reviewer_a', 'reviewer_b', 'senior', 'implementer'),
}


@dataclass
class Actor:
    reservation: str
    parent: str
    function: str
    input_sha256: str
    profile_sha256: str
    native_id: str | None = None
    state: str = 'reserved'
    role_reads: dict | None = None
    effective: dict | None = None


class RuntimeCoordinator:
    """Reservations survive uncertainty. This class creates no native actors."""
    def __init__(self, adapter, model, effort, capacity):
        require(type(capacity) is int and capacity > 0, 'capacity', 'Observed positive capacity is required.')
        self.adapter = adapter; self.model = model; self.effort = effort
        self.capacity = capacity; self.actors = {}; self.pending = deque(); self.closed = False

    def reserve_team(self, category, parent, input_sha256, profiles, *, implementation=True):
        require(category in TEAMS and not self.closed, 'category', 'Unknown category or stopped admission.')
        team = tuple(k for k in TEAMS[category] if implementation or k != 'implementer')
        require(set(profiles) == set(team), 'team_profiles', 'Every required logical actor needs its own profile.')
        for function in team:
            key = parent + ':' + function
            require(key not in self.actors, 'reservation_duplicate', 'Existing reservation cannot be replaced.')
            self.actors[key] = Actor(key, parent, function, input_sha256, profiles[function])
            self.pending.append(key)
        return team

    def capacity_ready(self):
        # Readiness, an idle turn, or interruption does not prove the native
        # session released its capacity. Retain every bound session slot.
        active = sum(a.native_id is not None or a.state in ('reserved-launch', 'launch_uncertain') for a in self.actors.values())
        return not self.closed and active < self.capacity and bool(self.pending)

    def next_reservation(self):
        require(self.capacity_ready(), 'capacity', 'Queue retained; no available native slot.')
        key = self.pending.popleft(); self.actors[key].state = 'reserved-launch'; return self.actors[key]

    def record_launch(self, reservation, observation):
        actor = self.actors[reservation]
        require(actor.state in ('reserved-launch', 'launch_uncertain') and actor.native_id is None, 'launch_duplicate', 'Reservation already bound.')
        native_id = self.adapter.validate_launch(observation, actor.parent)
        require(native_id != actor.parent and all(a.native_id != native_id for a in self.actors.values()), 'native_duplicate', 'Native child is not distinct.')
        actor.native_id = native_id; actor.state = 'bootstrap'; return actor

    def ready(self, reservation, role_reads, effective, expected_roles):
        actor = self.actors[reservation]
        require(actor.state == 'bootstrap' and actor.native_id, 'bootstrap', 'Native bootstrap required.')
        require(role_reads == expected_roles, 'role_reads', 'Exact role acknowledgement differs.')
        require(effective.get('model') == self.model and effective.get('reasoningEffort') == self.effort
                and effective.get('profile_sha256') == actor.profile_sha256 and effective.get('observed') is True,
                'effective_settings', 'Actual effective settings/profile are not established.')
        require(effective.get('independent_input_sha256') == actor.input_sha256 and effective.get('channels_isolated') is True,
                'input_isolation', 'Whole-problem input/channel independence is unproven.')
        actor.role_reads = role_reads; actor.effective = effective; actor.state = 'ready'

    def release_work(self, reservation, text):
        actor = self.actors[reservation]
        require(not self.closed and actor.state == 'ready', 'work_held', 'Actor has not passed readiness.')
        result = self.adapter.followup(actor.native_id, text); actor.state = 'working'; return result

    def uncertain(self, reservation):
        actor = self.actors[reservation]
        require(actor.state == 'reserved-launch', 'reservation', 'No launch in progress.')
        actor.state = 'launch_uncertain'

    def stop(self):
        self.closed = True; results = {}
        for key, actor in self.actors.items():
            if actor.native_id and actor.state in ('working', 'bootstrap', 'ready'):
                actor.state = 'stop_requested'
                try:
                    observed = self.adapter.observe(actor.native_id)
                    native_state = observed['thread']['status']['type']
                    if native_state == 'active':
                        results[key] = {'state':'interrupt_requested', 'result':self.adapter.interrupt(actor.native_id)}
                    else:
                        actor.state = 'idle_unreconciled' if native_state == 'idle' else 'stop_uncertain'
                        results[key] = {'state':actor.state, 'observation':observed}
                except (PolicyError, OSError, KeyError) as exc:
                    actor.state = 'stop_uncertain'
                    results[key] = {'state':'stop_uncertain', 'code':getattr(exc,'code','observation_unavailable')}
        return results

    def reconcile(self, reservation, observation):
        actor = self.actors[reservation]
        state = self.adapter.validate_status(observation, actor.native_id)
        if state in ('interrupted', 'failed'):
            actor.state = 'stopped' if state == 'interrupted' else 'failed'
        elif state == 'idle':
            actor.state = 'idle'
        # Idle is not revocation or permission to replace the actor.
        return actor.state
