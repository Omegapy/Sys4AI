"""Prepare requests and reconcile immutable receipts; never invoke native tools."""
from collaboration_read import Board
from collaboration_task import Context
from collaboration_store import encoded, require


def pending(board, recipient):
    c=board.c
    require(recipient in c.policy['participants'] and recipient in c.o['assignments'], 'COLLAB_AUDIENCE')
    other=Context(c.root,c.task_path,recipient,c.o['assignments'][recipient]['native_id'],c.o['execution_id'],c.o['generation'],c.policy_ref)
    target=Board(other)
    visible=target.messages(); delivered={x['receipt']['message_id'] for x in target.receipts(visible) if x['receipt']['state']=='notified' and x['receipt']['recipient']==recipient}
    # A sender can prepare only its own contributions; manager uses current scope.
    permitted={x['message']['message_id'] for x in board.messages()}
    requests=[]
    for item in visible:
        m=item['message']
        if m['message_id'] not in permitted or m['message_id'] in delivered or recipient not in m['recipients']: continue
        if not c.manager and m['assignment']!=c.assignment: continue
        request={'message_id':m['message_id'],'source':item['source'],'recipient':recipient,'native_id':other.actor,'summary':m['title'][:300],'urgency':m['urgency'],'transport':'collaboration.send_message','wake':False}
        trial={'requests':requests+[request],'remaining':len(visible)}
        if len(requests)>=c.policy['bounds']['page_items'] or len(encoded(trial))>c.policy['bounds']['output_bytes']: break
        requests.append(request)
    eligible=[x for x in visible if x['message']['message_id'] in permitted and x['message']['message_id'] not in delivered and recipient in x['message']['recipients'] and (c.manager or x['message']['assignment']==c.assignment)]
    return {'requests':requests,'remaining':len(eligible)-len(requests),'persistence_is_delivery':False,'wake':False}
