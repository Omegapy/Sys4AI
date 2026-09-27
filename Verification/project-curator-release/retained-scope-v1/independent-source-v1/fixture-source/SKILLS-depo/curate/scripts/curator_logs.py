"""Summary-first, registered log access; projections never replace raw evidence."""
import base64
from collections import Counter, deque
from contextlib import contextmanager
import copy
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import stat

from curator_confinement import canonical_root, parent_descriptor, read_native_header
from curator_policy import PolicyError, canonical, digest, exact, require

DEFAULTS={'scan_bytes':8388608,'scan_lines':20000,'record_bytes':131072,'response_bytes':16000,'matches':12,'excerpt_bytes':768}
MAXIMA={'scan_bytes':64000000,'scan_lines':100000,'record_bytes':262144,'response_bytes':32000,'matches':50,'excerpt_bytes':4000}
MINIMA={'scan_bytes':1024,'scan_lines':1,'record_bytes':256,'response_bytes':4096,'matches':1,'excerpt_bytes':64}
PRIVATE=('reasoning','token','compaction','world_state','account','configuration')
BULK_KEYS={'contents','reads','instructions','reasoning','config','configuration','tokenUsage','usage','threads','turns','world_state','account'}


def _text(value,limit):
    if type(value) is not str:return None
    return value.encode('utf-8',errors='replace')[:limit].decode('utf-8',errors='ignore')


def _json(raw):
    def pairs(values):
        result={}
        for key,value in values:
            if key in result:raise ValueError('Duplicate key')
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs)


def _identity(info):
    return {'device':info.st_dev,'inode':info.st_ino,'uid':info.st_uid,'mode':stat.S_IMODE(info.st_mode),
        'links':info.st_nlink,'size':info.st_size,'mtime_ns':info.st_mtime_ns}


@contextmanager
def _opened(entry):
    with parent_descriptor(entry['root'],entry['path']) as (parent,name):
        try:fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
        except OSError as exc:raise PolicyError('log_unavailable','Registered log is unavailable or aliased.') from exc
        with os.fdopen(fd,'rb') as stream:
            info=os.fstat(stream.fileno());require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'log_type','Registered log must be a regular single-link file.')
            before=_identity(info);header=read_native_header(stream,entry['actor']) if entry['format']=='native-jsonl' else {}
            current={**before,**header};old=entry.get('identity')
            if old is not None:
                fixed=lambda item:{key:value for key,value in item.items() if key not in ('size','mtime_ns')}
                require(fixed(old)==fixed(current) and current['size']>=old['size'] and current['mtime_ns']>=old['mtime_ns'],
                        'log_identity_changed','Registered log inode/header changed or shrank.')
            yield stream,current
            require(_identity(os.fstat(stream.fileno()))==before and _identity(os.stat(name,dir_fd=parent,follow_symlinks=False))==before,
                    'log_changed','Log changed during this bounded read; request a fresh summary.')


def register_log(root,path,*,actor=None,format='native-jsonl',readers=()):
    """Trusted host/bootstrap selection only. Native requests never call registration."""
    require(format in ('native-jsonl','text'),'log_format','Unsupported registered log format.')
    require(format!='native-jsonl' or type(actor) is str and actor,'log_actor','Native logs require an exact source actor.')
    entry={'root':str(canonical_root(root)),'path':path,'actor':actor,'format':format,
        'readers':copy.deepcopy(list(readers)),'registration_id':secrets.token_hex(16)}
    with _opened(entry) as (_,identity):entry['identity']=identity
    return entry


def _outcome(value,limit,projection,depth=0):
    """Allowlisted tool-result fields, including native content-block lists."""
    if depth>8:return [],False,False,False
    parts=[];failed=False;succeeded=False;mentioned=False
    if type(value) is list:
        for item in value:
            p,f,s,m=_outcome(item,limit,projection,depth+1);parts+=p;failed|=f;succeeded|=s;mentioned|=m
    elif type(value) is dict:
        for key in ('state','status','exit_code'):
            item=value.get(key)
            if type(item) in (str,int,bool):
                parts.append(key+'='+str(item));failed|=(key=='exit_code' and item!=0
                    or str(item).casefold() in ('failed','error','blocked','denied','partial','unavailable'))
                succeeded|=(key=='exit_code' and item==0 or str(item).casefold() in ('complete','completed','success','succeeded','passed'))
        if type(value.get('code')) in (str,int):
            parts.append('code='+str(value['code']));failed|=not succeeded and value['code'] not in (0,'0','','ok','OK')
        failed|=('error' in value and value['error'] not in (None,{},[],''))
        if not BULK_KEYS.intersection(value):
            for key in ('output','content','error','diagnostic','message','text'):
                if key in value:
                    p,f,s,m=_outcome(value[key],limit,projection,depth+1);parts+=p;failed|=f;succeeded|=s;mentioned|=m
    elif type(value) is str:
        stripped=value.strip()
        if stripped.startswith(('{','[')):
            try:return _outcome(_json(stripped),limit,projection,depth+1)
            except (ValueError,RecursionError):return [],False,False,False
        lower=value.casefold();positions=[lower.find(word) for word in ('error','failed','exception','denied','blocked','unsafe_') if word in lower]
        mentioned=bool(positions)
        if mentioned or projection=='tool_output':parts.append(value[:limit])
    return parts,failed,succeeded,mentioned


def _project(value,turn,limit,projection):
    if type(value) is not dict:return {'kind':'malformed_record'},turn
    event=value.get('type');payload=value.get('payload',value)
    if type(payload) is not dict:return {'kind':'omitted','event':_text(event,100)},turn
    kind=payload.get('type',event);kind=kind if type(kind) is str else 'unknown'
    if event=='turn_context' or kind=='task_started':
        turn=_text(payload.get('turn_id',payload.get('id')),150) or turn
    refs={'event':_text(kind,100),'event_id':_text(payload.get('id'),150),'call_id':_text(payload.get('call_id'),150),'turn_id':turn,
        'event_ordinal':value.get('ordinal') if type(value.get('ordinal')) is int else None,'timestamp':_text(value.get('timestamp'),80)}
    if any(word in kind.casefold() for word in PRIVATE) or event in ('session_meta','turn_context'):
        return {'kind':'omitted',**refs},turn
    if kind in ('custom_tool_call_output','function_call_output','functionCallOutput'):
        parts,failed,succeeded,mentioned=_outcome(payload.get('output'),limit,projection)
        if succeeded and not failed and projection=='events':parts=[part for part in parts if part.startswith(('state=','status=','code=','exit_code='))]
        return {'kind':'tool_outcome','status':'failed' if failed else 'succeeded' if succeeded else 'error_mention' if mentioned else 'observed',
            'outcome_basis':'structured_result' if failed or succeeded else 'literal_mention' if mentioned else 'unclassified_output',
            'excerpt':_text('; '.join(parts),limit),'tool':_text(payload.get('name'),100),**refs},turn
    if kind in ('custom_tool_call','function_call'):
        return {'kind':'tool_call','tool':_text(payload.get('name'),100),'status':'called',**refs},turn
    if kind=='message':
        if payload.get('role')!='assistant' or payload.get('phase') not in ('final','final_answer'):
            return {'kind':'omitted',**refs},turn
        content=payload.get('content',[])
        text=' '.join(item.get('text','') for item in content if type(item) is dict and item.get('type') in ('output_text','text') and type(item.get('text')) is str) if type(content) is list else ''
        return {'kind':'assistant_final','excerpt':_text(text,limit),**refs},turn
    if kind in ('error','warning','task_complete','task_started','turn_aborted'):
        parts,failed,_,mentioned=_outcome(payload,limit,projection)
        return {'kind':'activity','status':'failed' if failed or kind in ('error','turn_aborted') else kind,
            'excerpt':_text('; '.join(parts),limit),**refs},turn
    return {'kind':'omitted',**refs},turn


class LogService:
    """A trusted registry and signed source/reader-scoped continuation cursors."""
    def __init__(self,entries=None,*,cursor_key=None):
        self.entries=copy.deepcopy(entries or {});self.key=cursor_key or secrets.token_bytes(32)
        require(type(self.entries) is dict and len(self.entries)<=50,'log_registry','A registry holds at most 50 explicitly registered logs.')
        require(type(self.key) is bytes and len(self.key)==32,'log_registry','Cursor key must be private trusted state.')
        for handle,entry in self.entries.items():
            require(type(handle) is str and 0<len(handle.encode('utf-8'))<=100 and not any(ord(c)<32 for c in handle),'log_registry','Invalid registered handle.')
            exact(entry,('root','path','actor','format','readers','registration_id','identity'))
            require(entry['format'] in ('native-jsonl','text') and type(entry['readers']) is list and len(entry['readers'])<=50
                    and all(type(reader) is dict for reader in entry['readers']) and type(entry['identity']) is dict
                    and all(type(entry[key]) is str and 0<len(entry[key].encode('utf-8'))<=4096 for key in ('root','path','registration_id'))
                    and (entry['actor'] is None and entry['format']=='text' or type(entry['actor']) is str and 0<len(entry['actor'].encode('utf-8'))<=150)
                    and len(canonical(entry))<=32768,'log_registry','Invalid or oversized registered log selection.')

    def _select(self,handle,reader):
        require(type(handle) is str and handle in self.entries,'log_unknown','Unknown registered log handle.')
        entry=self.entries[handle]
        if reader is not None:require(reader in entry['readers'],'log_forbidden','Log is not released to this exact current reader incarnation.')
        return entry

    def discover(self,reader=None):
        result={'state':'available','logs':[{'handle':handle,'format':entry['format']}
            for handle,entry in sorted(self.entries.items()) if reader is None or reader in entry['readers']]}
        require(len(canonical(result))+1<=DEFAULTS['response_bytes'],'log_registry','Discovery exceeds the fixed response bound.')
        return result

    def _seal(self,value):
        raw=canonical(value);return base64.urlsafe_b64encode(raw).decode().rstrip('=')+'.'+hmac.new(self.key,raw,hashlib.sha256).hexdigest()

    def _unseal(self,value):
        require(type(value) is str and len(value)<=4096,'log_cursor','Invalid continuation cursor.')
        try:
            token,signature=value.split('.');raw=base64.b64decode(token+'='*(-len(token)%4),altchars=b'-_',validate=True)
            require(hmac.compare_digest(hmac.new(self.key,raw,hashlib.sha256).hexdigest(),signature),'log_cursor','Cursor is not issued by this log registry.')
            result=_json(raw)
        except (ValueError,UnicodeError) as exc:raise PolicyError('log_cursor','Malformed continuation cursor.') from exc
        return result

    def summary(self,handle,*,reader=None,options=None):return self._read(handle,reader,options or {},True)
    def query(self,handle,query,*,reader=None):return self._read(handle,reader,query,False)

    def _read(self,handle,reader,query,summary):
        entry=self._select(handle,reader);require(type(query) is dict,'log_query','Expected bounded query options.')
        allowed=set(DEFAULTS)|{'cursor'}|(set() if summary else {'mode','literal','start_line','lines','projection'})
        require(set(query)<=set(allowed),'log_query','Unknown log query field; paths and actor selection are not accepted.')
        limits={**DEFAULTS,**{key:query[key] for key in DEFAULTS if key in query}}
        require(all(type(value) is int and MINIMA[key]<=value<=MAXIMA[key] for key,value in limits.items()),'log_limit','Log query limits are outside their fixed bounds.')
        mode='summary' if summary else query.get('mode','search');projection='events' if summary else query.get('projection','events')
        require(mode in ('summary','search','excerpt') and projection in ('events','tool_output'),'log_query','Unsupported log mode or projection.')
        literal=query.get('literal','');start_line=query.get('start_line',1);lines=query.get('lines',10)
        require(type(start_line) is int and start_line>=1 and type(lines) is int and 1<=lines<=100,'log_query','Invalid excerpt line range.')
        require(mode!='search' or type(literal) is str and 0<len(literal.encode())<=200,'log_query','Search requires a nonempty literal of at most 200 UTF-8 bytes.')
        signature=digest({'mode':mode,'projection':projection,'literal':literal,'start_line':start_line,'lines':lines})
        found=[];resume_states=[];significant=deque(maxlen=limits['matches']);recent=deque(maxlen=6);counts=Counter();turn=None
        with _opened(entry) as (stream,identity):
            version=digest({'registration':entry['registration_id'],'identity':identity});reader_id=digest(reader)
            offset=0;line=1;skipping=False;origin=0
            if query.get('cursor') is not None:
                cursor=self._unseal(query['cursor']);exact(cursor,('handle','source_version','reader','query','offset','line','turn','skipping','origin'))
                require(cursor['handle']==handle and cursor['source_version']==version and cursor['reader']==reader_id and cursor['query']==signature,
                        'log_cursor_stale','Log/reader/query changed; obtain a fresh summary or query.')
                offset=cursor['offset'];line=cursor['line'];turn=cursor['turn'];skipping=cursor['skipping'];origin=cursor['origin']
            stream.seek(offset);begin=offset;first_line=line;scanned=0;records=0;partial=False;stop_reason=None
            while offset<identity['size'] and scanned<limits['scan_bytes'] and records<limits['scan_lines']:
                remain=min(limits['scan_bytes']-scanned,identity['size']-offset);at=offset;turn_before=turn
                pending_state={'offset':at,'line':line,'turn':turn_before,'skipping':skipping,'origin':origin if skipping else at}
                raw=stream.readline(min(limits['record_bytes']+1,remain));offset+=len(raw);scanned+=len(raw)
                if not raw:break
                complete=raw.endswith(b'\n')
                if not skipping and not complete and len(raw)<=limits['record_bytes'] and offset<identity['size']:
                    require(at!=begin,'log_scan_bound','The next record needs a larger scan_bytes window; it was not discarded.')
                    offset=at;stop_reason='scan_boundary_record_pending';break
                if skipping or len(raw)>limits['record_bytes']:
                    if not skipping:origin=at;counts['oversized_or_scan_split']+=1
                    skipping=not complete
                    if complete:line+=1;records+=1
                    if not complete:continue
                    item={'kind':'oversized_record','line':line-1,'byte_start':origin,'byte_end':offset,'record_sha256':None,'hash_scope':'not_hashed_oversized_record'}
                elif not complete:
                    counts['partial_last_record']+=1;partial=True;stop_reason='partial_last_record';break
                else:
                    try:
                        text=raw.decode('utf-8',errors='strict')
                        if entry['format']=='native-jsonl':item,turn=_project(_json(text),turn,limits['record_bytes'],projection)
                        else:
                            parts,failed,_,mentioned=_outcome(text,limits['record_bytes'],projection)
                            item={'kind':'text','status':'failed' if failed else 'error_mention' if mentioned else 'observed','excerpt':_text('; '.join(parts),limits['record_bytes'])}
                    except (ValueError,UnicodeError,RecursionError):item={'kind':'malformed_record'}
                    item.update(line=line,byte_start=at,byte_end=offset,record_sha256=hashlib.sha256(raw).hexdigest(),hash_scope='complete_original_jsonl_record' if entry['format']=='native-jsonl' else 'complete_original_text_line')
                    line+=1;records+=1
                counts[item['kind']]+=1
                selected=(not summary and (mode=='excerpt' and start_line<=item['line']<start_line+lines
                    or mode=='search' and literal in canonical(item).decode()))
                excerpt=item.get('excerpt')
                if type(excerpt) is str:
                    center=max(0,excerpt.find(literal)-64) if mode=='search' and literal in excerpt else 0
                    if mode!='search' and item.get('status')=='error_mention':
                        positions=[excerpt.casefold().find(word) for word in ('error','failed','exception','denied','blocked','unsafe_') if word in excerpt.casefold()]
                        if positions:center=max(0,min(positions)-64)
                    clipped=_text(excerpt[center:],limits['excerpt_bytes']);item['excerpt_truncated']=clipped!=excerpt;item['excerpt']=clipped
                if item.get('status') in ('failed','error_mention'):significant.append(item)
                if item['kind']!='omitted':recent.append(item)
                if not summary:
                    if selected and item['kind']!='omitted':
                        found.append(item);resume_states.append(pending_state)
                    if len(found)>=limits['matches']:stop_reason='matches';break
                    if mode=='excerpt' and line>=start_line+lines:stop_reason='excerpt_end';break
            remaining=offset<identity['size'];cursor=None
            if remaining and stop_reason!='excerpt_end':cursor=self._seal({'handle':handle,'source_version':version,'reader':reader_id,'query':signature,
                'offset':offset,'line':line,'turn':turn,'skipping':skipping,'origin':origin})
            source={'handle':handle,'source_actor':entry['actor'],'registration_id':entry['registration_id'],'source_version':version,
                'identity':identity,'integrity_scope':'inode/header and observed stat version; not whole-log content integrity'}
            result={'state':'summary' if summary else 'query','query_handle':handle,'source':source,'projection':projection,'limits':limits,
                'coverage':{'byte_start':begin,'byte_end':offset,'source_bytes':identity['size'],'scanned_bytes':scanned,'first_line':first_line,
                    'next_line':line,'complete_records':records,'complete_source':begin==0 and not remaining and not partial,
                    'scanned_to_eof':not remaining and not partial,
                    'partial_last_record':partial,'skipping_oversized_record':skipping,'stop_reason':stop_reason or ('scan_bound' if remaining else 'eof'),
                    'response_truncated':False},'cursor':cursor,'counts':dict(counts)}
            if summary:result.update(significant=list(significant),recent=list(recent))
            else:result['matches']=found
            while len(canonical(result))+1>limits['response_bytes']:
                key=next((key for key in ('recent','significant','matches') if result.get(key)),None)
                require(key is not None,'log_response_bound','Log response metadata exceeds the selected response bound.')
                result[key].pop();result['coverage']['response_truncated']=True
                if key=='matches':
                    state=resume_states[len(result['matches'])]
                    result['cursor']=self._seal({'handle':handle,'source_version':version,'reader':reader_id,'query':signature,**state})
                    result['coverage'].update(next_line=state['line'],resume_byte=state['offset'],complete_source=False,stop_reason='response_bound')
                    require(result['matches'],'log_response_bound','The next matching record cannot fit this response_bytes limit; it was not discarded.')
        entry['identity']=identity
        return result
