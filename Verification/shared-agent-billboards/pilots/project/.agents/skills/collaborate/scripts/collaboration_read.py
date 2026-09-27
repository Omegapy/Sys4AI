"""All context-producing routes use this pre-exposure board filter."""
from __future__ import annotations
import json
import re
from pathlib import Path
from collaboration_store import CollaborationError, digest, encoded, exact, identifier, private_check, publish, read_bytes, records, reference, require
from collaboration_task import Context

TYPES = ('note','question','finding','challenge','blocker','help-request','change-notice','proposal')
POST_FIELDS = ('operation_id','thread_id','reply_to','supersedes','subtask','type','title','body','phase','visibility','recipients','requested_response','urgency','targets','evidence','limitations','material')
BIND_FIELDS = ('version','project','task','execution','generation','assignment','native_id','policy_sha256')
MESSAGE_FIELDS = BIND_FIELDS + POST_FIELDS + ('message_id',)
RECEIPT_FIELDS = BIND_FIELDS + ('operation_id','message_id','message_sha256','recipient','state','evidence','native_receipt')
STATES = ('delivery-attempt','notified','failed','uncertain','acknowledged','handled','answered','deferred')


class Board:
    def __init__(self, context):
        self.c = context; self.limit = context.policy['bounds']['record_bytes']

    def phase(self, sid):
        self.c.current()
        rule = self.c.policy['subtasks'][sid]
        if rule['independent_first_pass'] and rule['phase'] in ('independent','peer-exchange'):
            try:
                self.c.candidates(sid)
                return 'peer-exchange'
            except CollaborationError:
                return 'independent'
        return rule['phase']

    def _shape(self, p, aid):
        exact(p, MESSAGE_FIELDS)
        require(type(p['version']) is int and p['version'] == 1, 'COLLAB_VERSION')
        require(p['project'] == str(self.c.root) and p['task'] == self.c.task['task_id'], 'COLLAB_BINDING')
        require(type(p['generation']) is int and isinstance(p['execution'],str), 'COLLAB_BINDING')
        require(p['assignment'] == aid and p['native_id'] == self.c.o['assignments'][aid]['native_id'], 'COLLAB_IDENTITY')
        identifier(p['operation_id']); identifier(p['thread_id'])
        require(p['message_id'] == aid + '.' + p['operation_id'], 'COLLAB_ID')
        require(p['subtask'] in self.c.policy['subtasks'] and p['type'] in TYPES, 'COLLAB_MESSAGE')
        require(p['visibility'] in ('operational','findings','verdict') and p['urgency'] in ('routine','blocker'), 'COLLAB_MESSAGE')
        require(p['phase'] in ('independent','peer-exchange','review','component','integration'), 'COLLAB_PHASE')
        rule = self.c.policy['subtasks'][p['subtask']]
        require(type(p['recipients']) is list and bool(p['recipients']) and len(p['recipients']) <= 200 and len(set(p['recipients'])) == len(p['recipients']) and set(p['recipients']) <= set(rule['audience']), 'COLLAB_AUDIENCE')
        require(type(p['material']) is bool, 'COLLAB_MESSAGE')
        for key in ('title','body','requested_response'):
            require(isinstance(p[key], str) and bool(p[key].strip()) and len(p[key]) <= (20000 if key == 'body' else 2000), 'COLLAB_TEXT')
        for key in ('targets','evidence'):
            require(type(p[key]) is list and len(p[key]) <= 200, 'COLLAB_REFS')
            for ref in p[key]:
                exact(ref, ('path','sha256'))
                require(isinstance(ref['path'], str) and isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'COLLAB_REFS')
        require(type(p['limitations']) is list and len(p['limitations']) <= 200 and all(isinstance(x,str) and len(x) <= 2000 for x in p['limitations']), 'COLLAB_REFS')
        if p['material'] and p['type'] in ('finding','challenge','blocker','change-notice'):
            require(bool(p['targets']), 'COLLAB_TARGET')
        for key in ('reply_to','supersedes'):
            require(p[key] is None or isinstance(p[key],str) and len(p[key]) <= 200, 'COLLAB_REFERENCE')
        if p['type'] in ('finding','challenge','proposal'):
            require(p['visibility'] != 'operational','COLLAB_VISIBILITY')
        if self.c.o['assignments'][aid]['function']=='reviewer' and p['type'] in ('finding','challenge','proposal'):
            require(p['visibility']=='verdict','COLLAB_VISIBILITY')
        if p['visibility']=='operational' and (rule['independent_first_pass'] or rule['reviewer_first_pass']):
            require(p['type'] in ('note','question','blocker','help-request','change-notice') and p['title'] in ('Source unavailable','Tool unavailable','Clarification requested') and p['body']=='Operational notice; ask the current manager for the permitted clarification.' and p['requested_response']=='Manager: assess the exact frozen source or tool issue at the next active checkpoint.', 'COLLAB_OPERATIONAL')
            require(re.fullmatch(r'notice[0-9]{1,8}',p['operation_id']) and p['thread_id']=='operations' and p['reply_to'] is None and p['supersedes'] is None and p['limitations']==[] and not p['material'],'COLLAB_OPERATIONAL')
            inputs=self.c.o['subtasks'][p['subtask']]['baseline']['inputs']
            require(all(r in inputs for r in p['targets']+p['evidence']),'COLLAB_OPERATIONAL')
        private_check(p)

    def _visible(self, p):
        c = self.c; aid = p['assignment']
        if (p['execution'],p['generation'],p['policy_sha256']) != (c.o['execution_id'],c.o['generation'],c.policy_ref['sha256']):
            return False
        if c.assignment != aid and c.assignment not in p['recipients'] and not (c.manager and p['material']):
            return False
        if not all(c.scope(r['path']) for r in p['targets'] + p['evidence']):
            return False
        if aid == c.assignment or c.manager:
            return True
        sid = p['subtask']; rule = c.policy['subtasks'][sid]
        if p['visibility'] == 'operational':
            return True
        if c.a['function'] == 'reviewer' and rule['reviewer_first_pass']:
            try:
                if not c.first_review(c.assignment):
                    return False
            except CollaborationError:
                return False
        if rule['independent_first_pass']:
            try:
                c.candidates(sid)
            except CollaborationError:
                return False
        return True

    def messages(self):
        self.c.current()
        out = []
        for aid, entry in self.c.policy['participants'].items():
            ns = entry['namespace']
            if aid not in self.c.o['assignments'] or not self.c.scope(ns):
                continue  # Never open an unauthorized directory, including counts/errors.
            try: self.c.call('producer', aid)
            except CollaborationError: continue
            for p, ref in records(self.c.root, ns + '/messages', self.limit):
                self._shape(p, aid)
                if self._visible(p):
                    out.append({'message':p,'source':ref})
        return sorted(out, key=lambda x: x['message']['message_id'])

    def find(self, mid):
        found = [item for item in self.messages() if item['message']['message_id'] == mid]
        require(len(found) == 1, 'COLLAB_REFERENCE')
        return found[0]

    def post(self, supplied):
        exact(supplied, POST_FIELDS)
        self.c.current()
        c = self.c; p = {**c.binding(), **supplied, 'message_id':c.assignment + '.' + supplied['operation_id']}
        self._shape(p,c.assignment)
        require(c.manager or p['subtask'] == c.a['subtask_id'], 'COLLAB_SCOPE')
        require(p['phase'] == self.phase(p['subtask']), 'COLLAB_PHASE')
        for ref in p['targets'] + p['evidence']:
            require(c.scope(ref['path']), 'COLLAB_SCOPE'); reference(c.root, ref)
        for key in ('reply_to','supersedes'):
            if p[key] is not None:
                old = self.find(p[key])['message']
                require(old['thread_id'] == p['thread_id'], 'COLLAB_REFERENCE')
                if key == 'supersedes':
                    require(old['assignment'] == c.assignment, 'COLLAB_REFERENCE')
        raw = c.namespace + '/messages/' + p['operation_id'] + '.json'; c.writable(raw)
        return {'message_id':p['message_id'],'source':publish(c.root,raw,p,self.limit)}

    def receipts(self, visible):
        allowed = {x['message']['message_id']:x for x in visible}; out = []
        for aid, entry in self.c.policy['participants'].items():
            if aid not in self.c.o['assignments'] or not self.c.scope(entry['namespace']):
                continue
            for p, ref in records(self.c.root, entry['namespace']+'/receipts', self.limit):
                exact(p, RECEIPT_FIELDS)
                require(type(p['version']) is int and p['version']==1 and p['project']==str(self.c.root) and p['task']==self.c.task['task_id'] and type(p['generation']) is int, 'COLLAB_BINDING')
                require(p['assignment'] == aid and p['native_id'] == self.c.o['assignments'][aid]['native_id'], 'COLLAB_IDENTITY')
                if (p['execution'],p['generation'],p['policy_sha256']) != (self.c.o['execution_id'],self.c.o['generation'],self.c.policy_ref['sha256']):
                    continue
                item = allowed.get(p['message_id'])
                if item is None or p['message_sha256'] != item['source']['sha256']:
                    continue
                m = item['message']; require(p['state'] in STATES, 'COLLAB_RECEIPT')
                require(p['recipient'] in m['recipients'], 'COLLAB_RECEIPT')
                if p['state'] in ('acknowledged','handled','answered','deferred'):
                    require(aid == p['recipient'], 'COLLAB_IDENTITY')
                else:
                    require(aid == m['assignment'] or aid == self.c.o['manager_id'], 'COLLAB_IDENTITY')
                private_check(p)
                rule=self.c.policy['subtasks'][m['subtask']]
                sealed=False
                if self.c.assignment != aid and not self.c.manager:
                    try:
                        if rule['independent_first_pass']: self.c.candidates(m['subtask'])
                        if self.c.a['function']=='reviewer' and rule['reviewer_first_pass']:
                            sealed=not self.c.first_review(self.c.assignment)
                    except CollaborationError: sealed=True
                if sealed:
                    # Receipt prose/tool results can contain conclusions too. Expose fixed
                    # state evidence only while the recipient's first-pass gate is closed.
                    p={**p,'operation_id':'sealed_'+digest(encoded(ref)),'evidence':'Communication state only; additional evidence remains sealed.','native_receipt':None}
                    ref={'sha256':ref['sha256'],'sealed':True}
                out.append({'receipt':p,'source':ref})
        return out

    def receipt(self, operation_id, mid, state, recipient=None, evidence='', native_receipt=None):
        identifier(operation_id); require(state in STATES and isinstance(evidence,str) and len(evidence) <= 2000, 'COLLAB_RECEIPT')
        item = self.find(mid); m = item['message']; recipient = recipient or self.c.assignment
        require(recipient in m['recipients'], 'COLLAB_AUDIENCE')
        if state in ('acknowledged','handled','answered','deferred'):
            require(recipient == self.c.assignment, 'COLLAB_IDENTITY')
        else:
            require(self.c.assignment == m['assignment'] or self.c.manager, 'COLLAB_IDENTITY')
        if state == 'notified':
            exact(native_receipt, ('tool','native_id','result'))
            require(native_receipt['tool'] == 'collaboration.send_message' and native_receipt['native_id'] == self.c.o['assignments'][recipient]['native_id'] and native_receipt['result'] is not None, 'COLLAB_NATIVE_RECEIPT')
        elif native_receipt is not None:
            exact(native_receipt, ('tool','native_id','result'))
            require(native_receipt['tool'] == 'collaboration.send_message' and native_receipt['native_id'] == self.c.o['assignments'][recipient]['native_id'], 'COLLAB_NATIVE_RECEIPT')
        p = {**self.c.binding(),'operation_id':operation_id,'message_id':mid,'message_sha256':item['source']['sha256'],'recipient':recipient,'state':state,'evidence':evidence,'native_receipt':native_receipt}
        raw = self.c.namespace + '/receipts/' + operation_id + '.json'; self.c.writable(raw)
        return publish(self.c.root,raw,p,self.limit)

    def query(self, *, subtask=None, thread=None, participant=None, type=None, artifact=None, phase=None, search=None, unread=False, offset=0, items=None):
        require(type is None or type in TYPES, 'COLLAB_FILTER')
        require(isinstance(offset,int) and offset >= 0 and (search is None or isinstance(search,str) and len(search) <= 200), 'COLLAB_FILTER')
        visible = self.messages(); receipts = self.receipts(visible)
        handled = {r['receipt']['message_id'] for r in receipts if r['receipt']['recipient'] == self.c.assignment and r['receipt']['state'] in ('acknowledged','handled','answered','deferred')}
        acknowledged = {r['receipt']['message_id'] for r in receipts if r['receipt']['recipient'] == self.c.assignment and r['receipt']['state'] == 'acknowledged'}
        matches=[]
        for item in visible:
            m=item['message']
            if any(value is not None and m[field] != value for field,value in [('subtask',subtask),('thread_id',thread),('assignment',participant),('type',type),('phase',phase)]): continue
            if artifact is not None and not any(r['path']==artifact for r in m['targets']+m['evidence']): continue
            if search is not None and search.casefold() not in (m['title']+'\n'+m['body']).casefold(): continue
            if unread and m['message_id'] in handled: continue
            states=[r['receipt'] for r in receipts if r['receipt']['message_id']==m['message_id']]
            matches.append({**item,'handling':states,'reported_reading':m['message_id'] in acknowledged})
        maximum=self.c.policy['bounds']['page_items']; requested=maximum if items is None else items
        require(isinstance(requested,int) and 1 <= requested <= maximum, 'COLLAB_BOUND')
        result={'version':1,'items':[],'total':len(matches),'returned':0,'remaining':len(matches)-min(offset,len(matches)),'offset':offset,'checkpoint':digest(encoded([x['source'] for x in matches])),'limits':self.c.policy['bounds']}
        for item in matches[offset:offset+requested]:
            trial={**result,'items':result['items']+[item],'returned':result['returned']+1,'remaining':len(matches)-offset-result['returned']-1}
            if len(encoded(trial)) > self.c.policy['bounds']['output_bytes']: break
            result=trial
        if result['returned']==0 and matches[offset:]: result['next_item_exceeds_output']=True
        return result

    def linked(self, mid, ref):
        item=self.find(mid); require(ref in item['message']['targets']+item['message']['evidence'], 'COLLAB_REFERENCE')
        require(self.c.scope(ref['path']), 'COLLAB_SCOPE')
        data=reference(self.c.root,ref, self.c.policy['bounds']['output_bytes'])
        try: text=data.decode('utf-8')
        except UnicodeError as exc: raise CollaborationError('COLLAB_TEXT') from exc
        private_check(text)
        result={'source':ref,'content':text}
        require(len(encoded(result))<=self.c.policy['bounds']['output_bytes'], 'COLLAB_SIZE')
        return result
