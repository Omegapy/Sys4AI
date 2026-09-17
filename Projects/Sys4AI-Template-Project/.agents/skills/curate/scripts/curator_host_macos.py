"""Inactive assets and explicitly selected trusted-host lifecycle operations.

No import, distribution, status or relocation check installs a service or hook.
The trusted host executes reviewed plans through its independent service grant.
"""
import hashlib
from contextlib import contextmanager
from contextlib import ExitStack
import fcntl
import os
from pathlib import Path
import plistlib
import re
import secrets
import stat
import subprocess
import unicodedata
from curator_policy import PolicyError, canonical, decode, digest, exact, require, sha


def assets(selection):
    exact(selection, ('project_id','root','root_identity','python','script','selection_path','log_directory','cadence_seconds'))
    require(all(Path(selection[k]).is_absolute() for k in ('root','python','script','selection_path','log_directory')),
            'host_paths','Select exact absolute checkout, runtime, script, configuration and host log paths.')
    require(type(selection['cadence_seconds']) is int and 1<=selection['cadence_seconds']<=86400,'host_cadence','Select a finite host cadence.')
    label='com.sys4ai.curator.'+digest([selection['project_id'],selection['root'],selection['root_identity']])[:24]
    content=plistlib.dumps({'Label':label,'ProgramArguments':[selection['python'],selection['script'],'tick','--selection',selection['selection_path']],
        'WorkingDirectory':selection['root'],'StartInterval':selection['cadence_seconds'],'RunAtLoad':False,
        'StandardOutPath':str(Path(selection['log_directory'])/(label+'.stdout.log')),
        'StandardErrorPath':str(Path(selection['log_directory'])/(label+'.stderr.log'))},sort_keys=True)
    return {'label':label,'bytes':content,'sha256':hashlib.sha256(content).hexdigest(),'installed':False,'hook':False}


def lifecycle(action, selection, *, asset_sha256, prior=None, source_available=True, observed_identity=None,
              service_permission=False, operation_id=None):
    require(action in ('install','uninstall','relocate'),'host_action','Select a fixed host lifecycle action.')
    sha(asset_sha256);require(type(operation_id) is str and operation_id,'host_operation','An exact host operation identity is required.')
    if not source_available:return {'state':'unavailable','preserve_pending':True,'actions':[],'deletion':False}
    require(observed_identity==selection['root_identity'],'host_identity','Checkout moved or was replaced; revalidate identity explicitly.')
    require(service_permission is True,'service_permission','Host lifecycle needs its distinct selected service grant.')
    expected=assets(selection)
    require(asset_sha256==expected['sha256'],'host_asset_changed','Reviewed host asset bytes differ.')
    if action in ('uninstall','relocate'):
        require(prior is not None and prior['asset_sha256']==asset_sha256 and prior['label']==expected['label'],
                'host_owner','Existing installation is not this exact owned operation.')
    return {'state':'reviewed_plan','operation_id':operation_id,'action':action,'label':expected['label'],
            'asset_sha256':asset_sha256,'root_identity':selection['root_identity'],'requires_trusted_host_execution':True,
            'preserve_unknown_assets':True,'hook_actions':[]}


def status(*, selected, pending, volume_available, identity_current, loaded, process_current, probe_current, owner_current):
    if not volume_available:return {'state':'unavailable','pending':pending,'reason':'volume_unavailable','delete':False}
    if not identity_current or not owner_current:return {'state':'blocked','pending':pending,'reason':'identity_or_owner_changed','delete':False}
    if not selected:return {'state':'pending' if pending else 'idle','pending':pending,'delete':False}
    if not loaded or not process_current or not probe_current:return {'state':'unavailable','pending':pending,'reason':'fresh_runtime_check_required','delete':False}
    return {'state':'ready' if pending else 'idle','pending':pending,'runtime_observed':True,'delete':False}


class MacOSExecutor:
    """Fixed trusted-host effects. Construction and imports perform no effects.

    Only HostOwner supplies paths/labels. This executor is never exposed as a
    native candidate tool. Tests substitute launchctl and use an isolated home.
    """
    def __init__(self, *, home=None, uid=None):
        self.home=Path.home() if home is None else Path(home)
        self.uid=os.getuid() if uid is None else uid
        require(self.home.is_absolute() and type(self.uid) is int and self.uid>=0,'host_identity','Select the actual trusted host home and uid.')

    @contextmanager
    def _parent(self, path):
        path=Path(path);require(path.is_absolute() and '..' not in path.parts,'host_paths','Expected an exact absolute host path.')
        fold=lambda name:unicodedata.normalize('NFC',name).casefold()
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
        try:
            for part in path.parts[1:-1]:
                matches=[name for name in os.listdir(fd) if fold(name)==fold(part)]
                if not matches:raise FileNotFoundError(str(path))
                require(matches==[part],'host_alias','Host directory spelling or normalization differs.')
                child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=child
            matches=[name for name in os.listdir(fd) if fold(name)==fold(path.name)]
            require(not matches or matches==[path.name],'host_alias','Host file spelling or normalization differs.')
            yield fd,path.name
        finally:os.close(fd)

    def identity(self, root):
        root=Path(root)
        with self._parent(root) as (parent,name):
            fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
            try:info=os.fstat(fd);return [info.st_dev,info.st_ino]
            finally:os.close(fd)

    def read(self, path):
        path=Path(path)
        try:
            with self._parent(path) as (parent,name):
                fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                with os.fdopen(fd,'rb') as source:
                    before=os.fstat(source.fileno())
                    require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=250000,
                            'host_file','Expected one bounded regular owned file.')
                    raw=source.read(250001);after=os.fstat(source.fileno());current=os.stat(name,dir_fd=parent,follow_symlinks=False)
                    stamp=lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
                    require(len(raw)<=250000 and stamp(before)==stamp(after)==stamp(current),'host_file_changed','Owned host file changed during read.')
                    return raw
        except FileNotFoundError:return None

    def mkdir(self, path, *, anchor=None):
        # Never recreate a detached checkout or missing host home. Only children
        # of an already present explicit anchor may be created.
        path=Path(path);anchor=self.home if anchor is None else Path(anchor)
        require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(anchor),
                'host_paths','Expected an owned directory below the existing selected root.')
        with self._parent(anchor) as (parent,name):fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
        try:
            for name in path.relative_to(anchor).parts:
                try:os.mkdir(name,0o700,dir_fd=fd)
                except FileExistsError:pass
                child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                os.close(fd);fd=child
        finally:os.close(fd)

    def replace(self, path, expected, data, *, anchor=None):
        require(type(data) is bytes and len(data)<=250000,'host_file','Host write exceeds its fixed bound.')
        path=Path(path);self.mkdir(path.parent,anchor=anchor)
        with self._parent(path) as (parent,name):
            raw=self.read(path)
            require(_hash(raw)==expected,'host_file_changed','Exact host predecessor changed; preserve it.')
            temporary='.'+name+'.'+secrets.token_hex(8)
            fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            try:
                with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
                require(_hash(self.read(path))==expected,'host_file_changed','Host predecessor changed before replacement.')
                os.replace(temporary,name,src_dir_fd=parent,dst_dir_fd=parent);os.fsync(parent)
            finally:
                try:os.unlink(temporary,dir_fd=parent)
                except FileNotFoundError:pass

    def remove(self, path, expected):
        path=Path(path)
        with self._parent(path) as (parent,name):
            require(_hash(self.read(path))==expected,'host_file_changed','Exact owned asset changed; preserve it.')
            os.unlink(name,dir_fd=parent);os.fsync(parent)

    @contextmanager
    def locked(self, root):
        directory=Path(root)/'control_records/curator/operations';self.mkdir(directory,anchor=root)
        with self._parent(directory/'.host.lock') as (parent,name):
            fd=os.open(name,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=parent)
            try:
                info=os.fstat(fd);require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'host_lock','Expected one exact host-owner lock.')
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:raise PolicyError('host_busy','Another host operation owns this checkout; preserve its work.')
                yield
            finally:os.close(fd)

    def launchctl(self, action, label, asset_path):
        require(action in ('status','load','unload') and re.fullmatch(r'com\.sys4ai\.curator\.[a-f0-9]{24}',label),
                'host_command','Only the fixed Curator lifecycle verbs and label are allowed.')
        expected=self.home/'Library/LaunchAgents'/(label+'.plist')
        require(Path(asset_path)==expected,'host_paths','The owned label fixes its LaunchAgents path.')
        domain='gui/'+str(self.uid);target=domain+'/'+label
        args={'status':['print',target],'load':['bootstrap',domain,str(expected)],'unload':['bootout',target]}[action]
        result=subprocess.run(['/bin/launchctl',*args],stdin=subprocess.DEVNULL,capture_output=True,timeout=15,check=False)
        require(len(result.stdout)+len(result.stderr)<=250000,'host_output','Host command output exceeds its bounded observation.')
        output=(result.stdout+result.stderr).decode('utf-8','replace')
        if action=='status':
            if result.returncode:
                require('Could not find service' in output or 'Could not find specified service' in output,
                        'host_unavailable','The selected launchd domain could not be observed.')
                return {'loaded':False,'path':None,'pid':None,'process_current':False}
            path=re.search(r'^\s*path = (.+)$',output,re.M);pid=re.search(r'^\s*pid = (\d+)$',output,re.M)
            require(path is not None,'host_observation','Loaded job has no exact observed asset path.')
            process=False;number=int(pid[1]) if pid else None
            if number is not None:
                try:os.kill(number,0);process=True
                except ProcessLookupError:pass
            return {'loaded':True,'path':path[1].strip(),'pid':number,'process_current':process}
        require(result.returncode==0,'host_effect_uncertain','Host effect failed or is uncertain; retry its exact journal.')
        return {'returncode':0}


def _hash(raw):
    return None if raw is None else hashlib.sha256(raw).hexdigest()


class HostOwner:
    """Executable host-only service owner, with exact resumable local receipts.

    The caller is the trusted host controller. Its selected service_permission
    assertion is an authority boundary, not a cryptographic authentication token.
    No native candidate tool is added and no session is created here.
    """
    def __init__(self, executor=None):self.executor=executor or MacOSExecutor()

    def _path(self, selected):return self.executor.home/'Library/LaunchAgents'/(assets(selected)['label']+'.plist')

    def _journal(self, root, operation_id):
        require(type(operation_id) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,96}',operation_id),
                'host_operation','Select a bounded exact operation identity.')
        return Path(root)/'control_records/curator/operations'/('host-'+operation_id+'.json')

    def _check(self, selected, reviewed):
        expected=assets(selected)
        exact(reviewed,('asset_sha256','script_sha256','selection_sha256'))
        for value in reviewed.values():sha(value)
        require(reviewed['asset_sha256']==expected['sha256'],'host_asset_changed','Reviewed asset bytes differ.')
        require(self.executor.identity(selected['root'])==selected['root_identity'],'host_identity','Selected checkout identity changed.')
        for key,field in [('script','script_sha256'),('selection_path','selection_sha256')]:
            require(_hash(self.executor.read(selected[key]))==reviewed[field],'host_source_changed','Selected host source or scheduling selection changed.')
        return expected

    def _loaded(self, selected):
        asset=assets(selected);path=self._path(selected)
        value=self.executor.launchctl('status',asset['label'],path)
        exact(value,('loaded','path','pid','process_current'))
        require(type(value['loaded']) is bool and type(value['process_current']) is bool,
                'host_observation','Expected a fresh fixed host observation.')
        require(not value['loaded'] or value['path']==str(path),'host_owner','Loaded label belongs to another asset path.')
        return value

    def _prior(self, prior, *, moved_to=None):
        moved='relocated_receipt_sha256' in prior
        exact(prior,('root','operation_id','relocated_receipt_sha256') if moved else ('root','operation_id'))
        if moved:
            sha(prior['relocated_receipt_sha256'])
            require(moved_to is not None and moved_to['root']!=prior['root'],'host_relocation','A physical move needs its exact selected new root.')
            try:self.executor.identity(prior['root'])
            except FileNotFoundError:pass
            else:raise PolicyError('host_relocation','The original root is present; do not guess a physical move or remove its state.')
        location=moved_to['root'] if moved else prior['root']
        raw=self.executor.read(self._journal(location,prior['operation_id']))
        require(raw is not None,'host_owner','An exact durable prior installation receipt is required.')
        if moved:require(_hash(raw)==prior['relocated_receipt_sha256'],'host_owner','The relocated historical installation receipt changed.')
        record=decode(raw)
        require(record.get('schema_version')==1 and record.get('state')=='completed'
                and record.get('action') in ('install','relocate') and record['selection']['root']==prior['root'],
                'host_owner','The selected prior operation is not a completed installation here.')
        if moved:
            # Only an explicitly selected rename of this same physical checkout
            # can locate its old receipt here. The receipt binds historical old
            # sources; the separately reviewed new selection is checked current.
            require(record['selection']['root_identity']==moved_to['root_identity']==self.executor.identity(moved_to['root']),
                    'host_identity','The relocated receipt does not belong to this same physical checkout.')
            require(assets(record['selection'])['sha256']==record['reviewed']['asset_sha256'],
                    'host_owner','Historical source/asset binding differs from its exact installed selection.')
        else:self._check(record['selection'],record['reviewed'])
        return record

    def inspect(self, selection, reviewed, *, prior=None, pending=False, probe=None):
        """Fresh host status; optional probe must be an actual trusted runtime check."""
        try:self._check(selection,reviewed)
        except FileNotFoundError:return status(selected=True,pending=pending,volume_available=False,identity_current=False,loaded=False,process_current=False,probe_current=False,owner_current=False)
        owned=False
        if prior is not None:
            receipt=self._prior(prior);owned=receipt['selection']==selection and receipt['reviewed']==reviewed
        raw=self.executor.read(self._path(selection));current=_hash(raw)==reviewed['asset_sha256']
        if raw is not None and not current:return status(selected=True,pending=pending,volume_available=True,identity_current=True,loaded=False,process_current=False,probe_current=False,owner_current=False)
        observed=self._loaded(selection)
        probed=probe(selection,reviewed,observed) if probe is not None and owned and current and observed['process_current'] else False
        require(type(probed) is bool,'host_probe','The trusted runtime probe must return its current result.')
        return {**status(selected=owned,pending=pending,volume_available=True,identity_current=True,
            loaded=observed['loaded'],process_current=observed['process_current'],probe_current=probed,owner_current=owned or raw is None),
            'host':observed,'standalone_bridge_available':False}

    def execute(self, action, selection, reviewed, *, operation_id, service_permission=False, prior=None, fault=None):
        require(service_permission is True,'service_permission','The trusted host must select its independent service permission.')
        try:
            self._check(selection,reviewed)
            old=self._prior(prior,moved_to=selection if action=='relocate' else None) if prior is not None else None
            moved=prior is not None and 'relocated_receipt_sha256' in prior
            roots=sorted({selection['root'],*([old['selection']['root']] if old is not None and not moved else [])})
            with ExitStack() as stack:
                for root in roots:stack.enter_context(self.executor.locked(root))
                return self._execute(action,selection,reviewed,operation_id=operation_id,
                                     service_permission=service_permission,prior=prior,fault=fault)
        except FileNotFoundError:
            return {'state':'unavailable','preserve_pending':True,'deletion':False,'operation_id':operation_id}

    def _execute(self, action, selection, reviewed, *, operation_id, service_permission=False, prior=None, fault=None):
        """Install/uninstall/relocate only fixed reviewed assets on the trusted host.

        For relocation, selection is the new checkout and prior identifies the
        old completed installation. Both volumes must remain available.
        """
        require(action in ('install','uninstall','relocate'),'host_action','Select a fixed lifecycle action.')
        require(service_permission is True,'service_permission','The trusted host must select its independent service permission.')
        require((action=='install')==(prior is None),'host_owner','Removal or relocation requires its exact prior installation.')
        try:
            asset=self._check(selection,reviewed)
            old=self._prior(prior,moved_to=selection if action=='relocate' else None) if prior is not None else None
        except FileNotFoundError:
            return {'state':'unavailable','preserve_pending':True,'deletion':False,'operation_id':operation_id}
        if action=='uninstall':require(old['selection']==selection and old['reviewed']==reviewed,'host_owner','Uninstall differs from its exact installed asset.')
        if action=='relocate':require(assets(old['selection'])['label']!=asset['label'],'host_relocation','Relocation must select a different checkout identity.')
        path=self._journal(selection['root'],operation_id);raw=self.executor.read(path)
        intent={'schema_version':1,'operation_id':operation_id,'action':action,'selection':selection,'reviewed':reviewed,
                'prior':prior,'prior_sha256':digest(old) if old is not None else None}
        selections=[selection] if action!='relocate' else [selection,old['selection']]
        reviews=[reviewed] if action!='relocate' else [reviewed,old['reviewed']]
        moved=prior is not None and 'relocated_receipt_sha256' in prior
        def check(index):
            if moved and index==1:
                require(digest(self._prior(prior,moved_to=selection))==intent['prior_sha256'],
                        'host_owner','Moved historical receipt changed during the selected operation.')
            else:self._check(selections[index],reviews[index])
        if raw is None:
            steps=[]
            for index,current in enumerate(selections):
                installing=action=='install' or action=='relocate' and index==0
                observed=self._loaded(current);present=_hash(self.executor.read(self._path(current)))
                require(present==(None if installing else reviews[index]['asset_sha256']),
                        'host_owner','Unknown or changed host assets are preserved, including identical unowned assets.')
                require(not installing or not observed['loaded'],'host_owner','An existing loaded label is not adopted implicitly.')
                steps.extend(([{'kind':'asset','index':index,'before':None,'after':reviews[index]['asset_sha256']},
                               {'kind':'service','index':index,'before':False,'after':True}] if installing else
                              [{'kind':'service','index':index,'before':observed['loaded'],'after':False},
                               {'kind':'asset','index':index,'before':reviews[index]['asset_sha256'],'after':None}]))
            record={**intent,'state':'pending','steps':[{**step,'state':'pending'} for step in steps]}
            self.executor.replace(path,None,canonical(record),anchor=selection['root']);raw=canonical(record)
        else:
            record=decode(raw)
            require(all(record.get(k)==v for k,v in intent.items()),'host_operation_changed','Retry only the same reviewed host operation.')
            require(record.get('state') in ('pending','completed') and type(record.get('steps')) is list and len(record['steps']) in (2,4),
                    'host_journal','Unknown host lifecycle journal.')
        def save():
            nonlocal raw
            value=canonical(record);self.executor.replace(path,_hash(raw),value,anchor=selection['root']);raw=value
        def observation(step):
            current=selections[step['index']]
            return _hash(self.executor.read(self._path(current))) if step['kind']=='asset' else self._loaded(current)['loaded']
        for number,step in enumerate(record['steps']):
            for index in range(len(selections)):check(index)
            for earlier in record['steps'][:number]:
                require(observation(earlier)==earlier['after'],'host_state_changed','A completed effect changed; preserve its current state.')
            present=observation(step)
            if step['state']=='completed':
                require(present==step['after'],'host_state_changed','Completed host effect changed; exact replay is held.');continue
            require(step['state'] in ('pending','started'),'host_journal','Unknown host step state.')
            require(present==step['before'] or step['state']=='started' and present==step['after'],
                    'host_state_changed','Unreviewed host state differs from this exact partial operation.')
            if step['state']=='pending':step['state']='started';save()
            if present!=step['after']:
                if fault:fault('before_effect_'+str(number))
                current=selections[step['index']];target=self._path(current)
                check(step['index'])
                # Reopen exact asset identity before any launchctl effect too.
                if step['kind']=='service':
                    require(_hash(self.executor.read(target))==reviews[step['index']]['asset_sha256'],
                            'host_asset_changed','The exact service asset changed before host execution.')
                    self.executor.launchctl('load' if step['after'] else 'unload',assets(current)['label'],target)
                elif step['after'] is None:self.executor.remove(target,step['before'])
                else:self.executor.replace(target,step['before'],assets(current)['bytes'])
                if fault:fault('after_effect_'+str(number))
            require(observation(step)==step['after'],'host_effect_uncertain','Host effect is not yet observed; retain its pending journal.')
            step['state']='completed';save()
        if record['state']!='completed':record['state']='completed';save()
        return {'state':'completed','action':action,'operation_id':operation_id,'receipt':{'root':selection['root'],'operation_id':operation_id},
                'asset_sha256':reviewed['asset_sha256'],'standalone_ready':False}
