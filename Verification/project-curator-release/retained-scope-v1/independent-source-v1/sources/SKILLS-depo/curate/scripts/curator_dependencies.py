"""Bounded dependency evidence; source retrieval and installation are independent."""
import json
import re
from curator_policy import digest, exact, moment, require, sha

KINDS=('package','backend','model','tool','action','skill')


def cached_primary_observation(raw, *, expected_sha256):
    """Read the exact host-selected observation; no fresh network claim is made."""
    import hashlib
    sha(expected_sha256)
    require(type(raw) is bytes and len(raw)<=250000 and hashlib.sha256(raw).hexdigest()==expected_sha256,
            'dependency_observation','Cached primary observation differs from its selected bytes.')
    observed=json.loads(raw)
    require(observed['kind']=='ReadOnlyPrimaryDependencyObservation' and observed['source']['status']==200 and observed['canonical_identity_matches'] is True,
            'dependency_observation','Selected observation did not establish an exact successful package identity.')
    source=observed['source'];distribution=observed['source_distribution'];version=distribution['version']
    name=observed['installed_distribution']['name'];url='https://pypi.org/pypi/'+name+'/'+version+'/json'
    normalize=lambda value:re.sub(r'[-_.]+','-',value).casefold()
    require(source['requested_url']==source['final_url']==url and normalize(name)==normalize(distribution['name']),
            'dependency_identity','Cached observation differs from its exact official version endpoint.')
    times=observed['release_upload_times'];require(type(times) is list and bool(times) and len(times)<=500,'dependency_observation','Release upload provenance is missing.')
    for value in [observed['observed_at'],*times]:moment(value)
    sha(observed['response_sha256'])
    return {'source':url,'source_sha256':observed['response_sha256'],'name':distribution['name'],'version':version,
            'retrieved_at':observed['observed_at'],'published_at':min(times,key=moment),'kind':'release','security_claim':False}


def inventory(records):
    require(type(records) is list and len(records)<=500,'dependency_limit','Select a bounded declared inventory.')
    seen=set()
    for row in records:
        exact(row,('kind','name','version','source','source_sha256','owner'))
        require(row['kind'] in KINDS and all(type(row[k]) is str and row[k] for k in ('name','version','source','owner')),
                'inventory_gap','Dependency identity, version or owner is unknown.')
        sha(row['source_sha256']);key=(row['kind'],row['name'])
        require(key not in seen,'inventory_conflict','Conflicting dependency declarations require their current updater.');seen.add(key)
    return records


def pypi_version_response(raw, *, url, expected_name, expected_version, retrieved_at, published_at):
    require(type(raw) is bytes and len(raw)<=2000000,'dependency_response','Primary response exceeds its bound.')
    moment(retrieved_at);moment(published_at)
    require(url=='https://pypi.org/pypi/'+expected_name+'/'+expected_version+'/json','primary_source','Select the exact official version endpoint.')
    data=json.loads(raw);info=data['info'];normalize=lambda value:re.sub(r'[-_.]+','-',value).casefold()
    require(normalize(info['name'])==normalize(expected_name) and info['version']==expected_version,'dependency_identity','Primary response names another package/version.')
    import hashlib
    return {'source':url,'source_sha256':hashlib.sha256(raw).hexdigest(),'name':info['name'],'version':info['version'],
            'retrieved_at':retrieved_at,'published_at':published_at,'kind':'release','security_claim':False}


def assess(record, evidence, *, now, due_at, fresh_until, network_selected=False, updater_owner=None, retained_pin=False):
    inventory([record]);moment(now);moment(due_at);moment(fresh_until)
    base={'state':'idle','model_calls':0,'network_calls':0,'installation':False,'repository_change_required':False}
    if moment(now)<moment(due_at):return base
    if updater_owner and updater_owner!=record['owner']:return {**base,'state':'held','reason':'competing_updater'}
    if evidence is None or moment(now)>moment(fresh_until):return {**base,'state':'pending','reason':'selected_source_required' if network_selected else 'source_permission_or_cache_required'}
    exact(evidence,('source','source_sha256','name','version','retrieved_at','published_at','kind','security_claim'))
    sha(evidence['source_sha256']);moment(evidence['retrieved_at']);moment(evidence['published_at'])
    normalize=lambda value:re.sub(r'[-_.]+','-',value).casefold()
    require(normalize(evidence['name'])==normalize(record['name']) and evidence['kind'] in ('release','security') and moment(evidence['published_at'])<=moment(evidence['retrieved_at'])<=moment(now)<=moment(fresh_until), 'dependency_evidence','Dependency evidence is not attributable or its observation window is invalid.')
    if evidence['kind']=='security':require(evidence['security_claim'] is True,'security_evidence','Security findings require explicit supporting advisory evidence.')
    return {**base,'state':'finding','disposition':'security' if evidence['kind']=='security' else 'retained_compatible_pin' if retained_pin else 'upgrade_candidate' if evidence['version']!=record['version'] else 'current_pin',
            'dependency':record,'evidence':evidence}


def candidate(change, permissions, *, checks, current_environment_sha256):
    exact(change,('declaration','package_source','runtime_install','service_start','major','backend','schema','storage','environment_sha256'))
    require(all(type(change[key]) is bool for key in change if key!='environment_sha256'),'dependency_selection','Every requested dependency effect must be an explicit boolean.')
    required={key for key in ('declaration','package_source','runtime_install','service_start') if change[key]}
    require(required<=set(permissions),'dependency_permission','Declaration, source, installation and startup permissions are separate.')
    require(change['environment_sha256']==current_environment_sha256,'environment_changed','The selected candidate environment changed.')
    protected=any(change[key] for key in ('major','backend','schema','storage'))
    return {'state':'protected_review' if protected else 'verified_candidate' if checks and all(x['passed'] for x in checks) else 'held',
            'live_environment_changed':False,'installation_performed':False,'checks':checks}
