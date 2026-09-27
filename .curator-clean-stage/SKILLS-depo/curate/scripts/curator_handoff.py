"""Exact conversational selection and preservation of interrupted original work."""
from copy import deepcopy
from curator_policy import digest, exact, moment, require


def select(utterance, offers, *, now, current_sources, current_authority):
    require(type(utterance) is str and len(utterance)<=4000,'selection_text','Expected bounded user text.')
    text=utterance.strip().casefold().rstrip('.!')
    clear=text in ('do it','yes, do it','go ahead','proceed','fix it','continue with that')
    if not clear:return {'state':'read_only' if '?' in utterance else 'selection_required','selected':None,'task_activation':False}
    if len(offers)!=1:return {'state':'selection_required','selected':None,'task_activation':False}
    offer=offers[0];exact(offer,('item_id','operation_id','source_sha256','authority_sha256','expires_at','original_work'))
    if moment(now)>moment(offer['expires_at']) or current_sources.get(offer['item_id'])!=offer['source_sha256'] or offer['authority_sha256']!=current_authority:
        return {'state':'stale_offer','selected':None,'task_activation':False}
    return {'state':'selected','selected':deepcopy(offer),'route':'existing_task_intake','task_activation':False,
            'authority':'Exact selection only; current owner and action grants still apply.'}


def retain_original(original, selection):
    exact(original, ('objective','constraints','task_id','execution_id','source_refs','assumptions','authority_sha256'))
    require(selection['state']=='selected','handoff_selection','An exact user selection is required.')
    require(original == selection['selected']['original_work'], 'handoff_original',
            'Retain the complete original objective, Task, execution, sources, constraints and authority selected in this offer.')
    return {'original':deepcopy(original),'original_sha256':digest(original),'maintenance':deepcopy(selection['selected']),
            'competing_execution':False}


def continue_original(handoff, *, maintenance_outcome, current_original, integrity_current, scope_current, authority_current):
    require(maintenance_outcome in ('completed','blocked','failed'),'handoff_outcome','Observe the actual maintenance result.')
    require(handoff['original'] == handoff['maintenance']['original_work'] and digest(handoff['original']) == handoff['original_sha256'],
            'handoff_original', 'Original work differs from the retained selected offer.')
    unchanged=digest(current_original)==handoff['original_sha256']
    ready=maintenance_outcome=='completed' and unchanged and integrity_current and scope_current and authority_current
    return {'state':'continuation_ready' if ready else 'held','original':deepcopy(handoff['original']),
            'recheck_required':not ready,'task_activation':False,'competing_execution':False,
            'reasons':[] if ready else ['maintenance_or_original_prerequisite_changed']}
