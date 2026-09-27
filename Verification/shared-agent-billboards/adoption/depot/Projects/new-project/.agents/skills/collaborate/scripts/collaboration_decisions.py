"""Bounded communication evidence and current owner objections, never Task writes."""
from pathlib import Path
from collaboration_store import CollaborationError, digest, encoded, exact, identifier, publish, reference, require


def decision_current(board, kind, decision_id):
    c=board.c
    require(c.manager or c.a['function']=='senior', 'COLLAB_OWNER')
    if kind=='synthesis':
        record=c.o['syntheses'].get(decision_id); require(record is not None,'COLLAB_DECISION')
        c.call('synthesis_current',decision_id,c.task,c.root,c.folder)
        require(c.manager or record['assignment_id']==c.assignment,'COLLAB_OWNER')
    elif kind=='acceptance':
        require(c.manager and decision_id in c.o['acceptances'],'COLLAB_DECISION')
        c.call('acceptance_current',decision_id,c.task,c.root,c.folder)
    elif kind=='review':
        require(c.manager and decision_id in c.o['reviews'],'COLLAB_DECISION')
        record=c.o['reviews'][decision_id]
        cand=c.call('candidate_current',record['candidate_id'],c.task,c.root,c.folder)
        st=c.o['subtasks'][c.o['assignments'][record['assignment_id']]['subtask_id']]
        require(record['baseline']==st['digest'] and record['round']==st['round'],'COLLAB_DECISION')
        c.call('evidence_current',record['findings'],c.folder)
        # Current assigned mapping remains enforced by canonical review validation.
        slot=next(x for x in st['baseline']['slots'] if x['slot']==c.o['assignments'][record['assignment_id']]['slot'])
        require(slot['solver_slot']==c.o['assignments'][cand['assignment_id']]['slot'],'COLLAB_DECISION')
    elif kind=='verification':
        require(c.manager and decision_id in c.o['subtasks'],'COLLAB_DECISION')
        c.call('verified_current',decision_id,c.task,c.root,c.folder)
    else:
        raise CollaborationError('COLLAB_DECISION')
    return {'kind':kind,'id':decision_id}


def assess(board, subtask, assessments):
    board.c.current(); board.c.eligibility(subtask)
    require(board.c.manager or board.c.a['function']=='senior','COLLAB_OWNER')
    require(isinstance(assessments,list) and len(assessments)<=200,'COLLAB_BOUND')
    material=[x for x in board.messages() if x['message']['subtask']==subtask and x['message']['material']]
    accepted={}
    for a in assessments:
        exact(a,('message_id','target','disposition','owner','decision_kind','decision_id','evidence','reason'))
        require(a['owner']==board.c.assignment and a['disposition'] in ('addressed','rejected','obsolete','deferred'),'COLLAB_OWNER')
        matches=[x for x in material if x['message']['message_id']==a['message_id'] and (a['target'] in x['message']['targets'] or a['target'] is None and not x['message']['targets'])]
        require(len(matches)==1 and isinstance(a['reason'],str) and 0<len(a['reason'])<=2000,'COLLAB_TARGET')
        require(isinstance(a['evidence'],list) and 0<len(a['evidence'])<=200,'COLLAB_REFS')
        for ref in a['evidence']:
            require(board.c.scope(ref['path']),'COLLAB_SCOPE'); reference(board.c.root,ref)
        decision_current(board,a['decision_kind'],a['decision_id'])
        key=(a['message_id'],None,None) if a['target'] is None else (a['message_id'],a['target']['path'],a['target']['sha256'])
        require(key not in accepted,'COLLAB_DUPLICATE'); accepted[key]=a
    pending=[]
    for item in material:
        for target in item['message']['targets'] or [None]:
            key=(item['message']['message_id'],None,None) if target is None else (item['message']['message_id'],target['path'],target['sha256'])
            if key not in accepted or accepted[key]['disposition']=='deferred':
                pending.append({'message_id':item['message']['message_id'],'source':item['source'],'target':target,'owner':board.c.assignment,'effect':'current criteria require attributed owner assessment'})
    return {'subtask':subtask,'eligible':not pending,'pending':pending,'assessments':assessments,'communication_closure_is_resolution':False}


def snapshot(board, operation_id, selected_ids, assessments=None):
    identifier(operation_id); board.c.current()
    require(board.c.manager or board.c.a['function']=='senior','COLLAB_OWNER')
    require(isinstance(selected_ids,list) and len(selected_ids)<=200 and len(set(selected_ids))==len(selected_ids),'COLLAB_BOUND')
    all_items=board.messages(); selected=[board.find(mid) for mid in selected_ids]
    selection=[{'message_id':x['message']['message_id'],'source':x['source'],'targets':x['message']['targets']} for x in selected]
    payload={**board.c.binding(),'operation_id':operation_id,'selected':selection,'included':len(selection),'omitted_visible':len(all_items)-len(selection),'assessments':assessments or [],'conversation_copied':False}
    require(sum(1+len(x['targets']) for x in selection)<=200 and len(encoded(payload))<=250000,'COLLAB_BOUND')
    if assessments:
        for sid in {x['message']['subtask'] for x in selected}:
            relevant=[a for a in assessments if a['message_id'] in {x['message']['message_id'] for x in selected if x['message']['subtask']==sid}]
            assess(board,sid,relevant)
    raw=board.c.namespace+'/snapshots/'+operation_id+'.json'; board.c.writable(raw)
    return publish(board.c.root,raw,payload,250000)
