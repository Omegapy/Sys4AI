"""Create a bounded pending handoff, without invoking any knowledge owner."""
from collaboration_store import encoded, identifier, private_check, publish, reference, require


def proposal(board, operation_id, owner_kind, thread_id, selected_ids, evidence, suggested_change, validation, limitations):
    identifier(operation_id); identifier(thread_id); board.c.current()
    require(owner_kind in ('memory','ontology','curator'),'COLLAB_OWNER')
    require(isinstance(selected_ids,list) and 0<len(selected_ids)<=200 and len(set(selected_ids))==len(selected_ids),'COLLAB_BOUND')
    selected=[board.find(mid) for mid in selected_ids]
    require(all(x['message']['thread_id']==thread_id for x in selected),'COLLAB_REFERENCE')
    require(isinstance(evidence,list) and 0<len(evidence)<=200,'COLLAB_REFS')
    for ref in evidence:
        require(board.c.scope(ref['path']),'COLLAB_SCOPE');reference(board.c.root,ref)
    for value in (suggested_change,validation):
        require(isinstance(value,str) and 0<len(value)<=2000,'COLLAB_TEXT')
    require(isinstance(limitations,list) and len(limitations)<=200 and all(isinstance(x,str) and len(x)<=2000 for x in limitations),'COLLAB_TEXT')
    payload={**board.c.binding(),'operation_id':operation_id,'owner_kind':owner_kind,'thread_id':thread_id,'sources':[{'message_id':x['message']['message_id'],'source':x['source'],'targets':x['message']['targets']} for x in selected],'evidence':evidence,'suggested_change':suggested_change,'validation':validation,'limitations':limitations,'status':'pending_owner','published':False,'owner_invoked':False,'frozen_initial_context_eligible':False}
    require(len(evidence)+sum(1+len(x['message']['targets']) for x in selected)<=200 and len(encoded(payload))<=250000,'COLLAB_BOUND');private_check(payload)
    raw=board.c.namespace+'/proposals/'+operation_id+'.json';board.c.writable(raw)
    return publish(board.c.root,raw,payload,250000)
