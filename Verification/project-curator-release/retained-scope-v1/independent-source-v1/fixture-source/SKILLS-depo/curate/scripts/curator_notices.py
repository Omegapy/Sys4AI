"""Quiet, local notice classification. No message transport or external default."""
from curator_policy import digest, exact, require
from curator_workspace import overlaps


def notice(item, *, affected_paths, previous_sha256=None, digest_selected=False):
    exact(item, ('id','paths','state','impact','action','meaningful','routine_success'))
    require(item['state'] in ('information','warning','blocker','idle','complete'), 'notice_state','Unknown notice level.')
    if not overlaps(item['paths'],affected_paths) or item['state']=='idle' or item['routine_success'] or not item['meaningful'] or digest(item)==previous_sha256:
        return None
    require(all(type(item[k]) is str and item[k].strip() for k in ('id','impact','action')),'notice_text','A relevant notice needs exact item, impact and action.')
    return {'id':item['id'],'level':item['state'],'impact':item['impact'],'action':item['action'],
            'sha256':digest(item),'delivery':'selected_digest' if digest_selected else 'local','external_destination':None}
