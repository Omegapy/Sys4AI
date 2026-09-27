"""Pure bounded views and explicitly authorized derived Markdown rebuild."""
from collaboration_store import encoded, rebuild, require


def render(board, **filters):
    result=board.query(**filters)
    lines=['# Task discussion','',f"Task: {board.c.task['task_id']}; execution: {board.c.o['execution_id']}; generation: {board.c.o['generation']}.",'',f"Visible matched: {result['total']}; shown: {result['returned']}; remaining: {result['remaining']}.",'']
    for item in result['items']:
        m=item['message']; lines += [f"## {m['message_id']} ({m['type']})",'',m['title'],'',m['body'],'',f"Source: {item['source']['path']} sha256 {item['source']['sha256']}",f"Thread: {m['thread_id']}; reply: {m['reply_to']}; supersedes: {m['supersedes']}.",f"Communication states: {', '.join(x['state'] for x in item['handling']) or 'available'}; these do not establish comprehension or Task acceptance.",'']
    content='\n'.join(lines).encode()
    while len(content)>board.c.policy['bounds']['output_bytes'] and result['items']:
        result['items'].pop()
        # The JSON query already reports coverage. For a larger Markdown representation
        # expose only IDs/references rather than silently clipping body text.
        lines=['# Task discussion','',f"Visible matched: {result['total']}; detailed coverage omitted for Markdown bound.",'']+[x['message']['message_id']+' '+x['source']['sha256'] for x in result['items']]
        content='\n'.join(lines).encode()
    require(len(content)<=board.c.policy['bounds']['output_bytes'],'COLLAB_SIZE')
    return content


def rebuild_view(board, **filters):
    raw=board.c.namespace+'/views/TASK-BILLBOARD.md'; board.c.writable(raw)
    content=render(board,**filters); rebuild(board.c.root,raw,content,board.c.policy['bounds']['output_bytes'])
    return {'path':raw,'derived':True,'bytes':len(content)}
