"""Consume one existing completion review; no second reflection or memory store."""
from curator_policy import digest, exact, require, sha


def disposition(review, *, capture, explicit_save=False, consumed=(), active_work=()):
    exact(review, ('completion_id','objective','artifact','source_sha256','mode','durable','supported','cause_established','already_repaired','remaining_obligations'))
    require(type(capture) is bool and type(explicit_save) is bool, 'capture_selection', 'Capture and explicit-save authority are independent.')
    sha(review['source_sha256']);require(review['mode'] in ('review','automatic','explicit'), 'review_mode', 'Use the existing completion-review mode.')
    identity=digest({k:review[k] for k in ('completion_id','objective','artifact','source_sha256')})
    result={'completion_identity':identity,'state':'proposed','route':'contextual_recall','persist':False,'benefit':'unobserved','new_review':False,'task_activation':False}
    if identity in consumed:return {**result,'state':'unchanged','route':None}
    if not review['supported'] or not review['durable']:return {**result,'state':'held' if not review['supported'] else 'idle','route':None}
    result['persist']=review['mode']!='review' and (capture or explicit_save)
    matching=[w for w in active_work if all(w.get(k)==review[k] for k in ('objective','artifact','source_sha256'))
              and w.get('state') not in ('completed','cancelled','close-old-task')]
    if matching:return {**result,'route':'current_owner','owners':[w['owner'] for w in matching]}
    if review['already_repaired']:return {**result,'route':'remaining_obligations' if review['remaining_obligations'] else 'contextual_recall','obligations':review['remaining_obligations']}
    return {**result,'route':'targeted_improvement' if review['cause_established'] else 'bounded_investigation'}
