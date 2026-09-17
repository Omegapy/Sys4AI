"""Read current Task pause/recovery state through its existing public owner."""
from pathlib import Path
from curator_policy import exact,require


class RecoveryController:
    """No separate pause ledger; the selected canonical Task remains the owner."""
    def __init__(self, task_owner, task_folder):
        require(callable(getattr(task_owner,'validate_task_folder',None)),
                'task_owner_unavailable','Select the existing Task validation owner.')
        self.owner=task_owner;self.folder=Path(task_folder)

    def _state(self):
        state,errors,_=self.owner.validate_task_folder(self.folder)
        require(state is not None and not errors,'task_owner_unavailable','Current canonical Task is unavailable or invalid.')
        return state

    def read(self):
        state=self._state();orch=state.get('orchestration') or {}
        stage=orch.get('stage','unassigned')
        return {'task_id':state['task_id'],'revision':state['revision'],'status':state['status'],
                'stage':stage,'writer':orch.get('writer'),
                'paused':state['status']=='paused' or stage in ('stopping','stopped','blocked'),
                'stopping_confirmed':stage=='stopped',
                'execution_id':orch.get('execution_id'),'generation':orch.get('generation')}

    def binding(self, selected, *, actor, allow_inactive=False):
        exact(selected,('task_id','revision','execution_id','generation'))
        current=self.read()
        require(all(current[key]==value for key,value in selected.items()) and current['writer']==actor,
                'task_changed','Operation must retain the current canonical Task and writer.')
        require(allow_inactive or (current['stage']=='active' and current['status']=='open'),
                'execution_paused','The current Task owner has not opened execution.')
        return dict(selected)

    def gate(self, action, tool, request, *, owner_command=None):
        current=self.read()
        if action=='pause' and tool=='task.event':
            require(request['payload'].get('event',{}).get('kind') in ('stop.request','stop.finish'),
                    'pause_selection','Pause uses the selected Task stopping operation.')
        if action=='resume' and tool=='task.event':
            require(request['payload'].get('event',{}).get('kind')=='execution.resume',
                    'resume_selection','Resume uses the existing Task execution resume operation.')
        if action in ('pause','resume') and tool=='task.response':
            expected='paused' if action=='pause' else 'open'
            require(request['payload'].get('status_after')==expected or (action=='pause' and owner_command=='pause' and 'status_after' not in request['payload']),
                    'pause_selection','Select the matching Task lifecycle response.')
        if current['paused']:
            require(action in ('pause','resume','retry','review'),'execution_paused',
                    'Current Task pause retains pending work and holds new operations.')
        return current
