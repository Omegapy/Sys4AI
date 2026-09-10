"""Reopen canonical evidence and retain bounded actual browser/API observations."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
base=Path(__file__).resolve().parents[2];root=base/'Verification/ontology-second-release/fixtures/generation-native'
sys.path[:0]=[str(root/'.agents/skills/ontology/scripts'),str(base/'SKILLS-depo/ontology/tests')]
from ontology_core import canonical_bytes,sha256
from ontology_proposals import open_proposal
from ontology_standards import infer,query
from ontology_workbench import Workbench,trusted_authority
from test_workbench_security import Client
out=base/'Verification/ontology-second-release/browser-evidence';out.mkdir(exist_ok=True)
def save(name,value):
 p=out/name;p.write_bytes(canonical_bytes(value));return {'path':str(p.relative_to(base)),'sha256':sha256(p)}
pid='ONTPROP-7644b491e5044aa2be747e647cb3fd6d';current=open_proposal(root,pid);event=next(e for e in current['events'] if e['decision']=='published');receipt=event['details']['receipt'];candidate=current['revision']['candidate'];path=root/candidate['changes'][0]['path'];before=sha256(path)
assert current['head']['state']=='published' and before==candidate['changes'][0]['sha256'];guard=receipt['ontology_guard'];assert guard['semantic_status']=='conformant' and guard['lock_rechecked'] and receipt['status']=='complete'
refs=[save('published-proposal.json',current)]
result=infer(root);assert result['status']=='ok' and result['trusted'];refs.append(save('inference.json',result))
answer=query(root,'ASK WHERE { <urn:sys4ai:ontology:project:example:browser-release-bundle> a <urn:sys4ai:ontology:core:Artifact> }',graphs=['inferred']);assert answer['answer'] is True and answer['complete'];refs.append(save('inferred-query.json',answer))
reader=Workbench(root).start()
try:
 client=Client(reader).connect();code,rejected=client.post('publish',{'id':pid,'revision':2,'review_sha256':current['head']['review_sha256']});assert code==403 and rejected['error']['code']=='publication_unavailable'
 probes={'unauthorized_publish':{'http_status':code,'response':rejected}}
 for name,headers in [('origin',{'Origin':'https://hostile.example'}),('host',{'Host':'hostile.example'}),('csrf',{'X-Ontology-CSRF':'forged'})]:
  code,r=client.post('state',{},**headers);assert code==403;probes[name]={'http_status':code,'response':r}
 code,r=client.post('state',{'actor_id':'/root'});assert code==403;probes['forged_actor']={'http_status':code,'response':r}
 code,r=client.post('source',{'reference':{'path':'../../unselected-sentinel','locator':'line:1'}});assert code!=200;probes['escaping_source']={'http_status':code,'response':r}
 assert sha256(path)==before;probes['canonical_sha256_before']=before;probes['canonical_sha256_after']=sha256(path);refs.append(save('real-service-negative-probes.json',probes))
finally:reader.close()
# A harmless executable-looking label is saved only as an unpublished candidate.
# The following receipt normalizes the host's just-observed actual native roster entry.
now=datetime.now(timezone.utc).isoformat();native={'tool':'collaboration.list_agents','result':{'agents':[{'agent_name':'/root','agent_status':'running'}]}};cfg=json.loads((root/'ontology.yaml').read_text());authority=trusted_authority(root,actor_id='/root',actor_kind='director',native_receipt=native,observed_at=now,scope=cfg['project_files']+cfg['binding_files']);service=Workbench(root,authority).start()
try:
 client=Client(service).connect();form={'id':'urn:sys4ai:ontology:project:example:browser-text-safety','kind':'concept','label':'<img src=x onerror="document.title=\'UNSAFE-LABEL-EXECUTED\'">','definition':'An unpublished label-safety probe for this disposable browser acceptance project.','types':['urn:sys4ai:ontology:core:OntologyConcept'],'aliases':[],'sources':[{'path':'docs/release-evidence.md','locator':'section:Release evidence bundles'}],'reason':'Verify source-provided text is rendered as text; do not publish this probe.'}
 code,saved=client.post('draft',{'form':form,'expected_target_sha256':before});save('unsafe-label-probe-response.json',{'http_status':code,'response':saved});assert code==200,saved;refs.append(save('unsafe-label-draft.json',saved));assert sha256(path)==before
 unsafe=saved['head']['proposal_id']
finally:service.close()
observations=[
 {'case':'session-isolation','status':'passed','evidence':'CUA author tabs4/5 on port52431 remained usable after a browsing-only tab6 connected on port52432. The prior shared-cookie failure was fixed and independently regressed.'},
 {'case':'keyboard-alias-search','status':'passed','evidence':'Filled verification bundle and pressed Enter; exactly one result, Release evidence bundle.'},
 {'case':'concept-and-relation','status':'passed','evidence':'Inspector showed the generated sourced definition and ReleaseEvidenceBundle subtypeOf Artifact, plus equivalent list and graph controls.'},
 {'case':'invalid-draft','status':'passed','evidence':'Browser form saved r1 with an empty definition; real validation showed missing_metadata and SHACL violation; no canonical publication occurred.'},
 {'case':'revision-and-conflict','status':'passed','evidence':'Tab4 saved corrected r2. Tab5 stale save was rejected and retained its exact pending definition text.'},
 {'case':'reject-and-reload','status':'passed','evidence':'Rejected r2 exposed no Publish control. Reload retained the same identity and rejected state. Explicit reopen and revalidation preceded review.'},
 {'case':'review-publish-reopen','status':'passed','evidence':'Inspected exact before/after diff, accepted exact review, clicked Publish reviewed change; UI reported Published and reopened the canonical result. Receipt has current actor and conformant under-lock semantic guard.'},
 {'case':'proof-and-query','status':'passed','evidence':'Expanded cax-sco proof with both sourced premises; selected inferred graph, ran actual SPARQL ASK, observed answer true and complete true.'},
 {'case':'browsing-only','status':'passed','evidence':'Tab6 displayed Browsing session, Create a draft disabled, no Accept/Publish/Revise controls. Separate actual HTTP publication attempt returned403 publication_unavailable with unchanged canonical hash.'},
 {'case':'visual-and-responsive','status':'passed','evidence':'Actual screenshots inspected review columns and non-graph concept view. Narrow tab6 measured clientWidth500, scrollWidth500, innerWidth520. The browser minimum prevented claiming a390-pixel run. Viewport override reset.'},
 {'case':'source-text-execution','status':'pending-browser-inspection','proposal_id':unsafe}]
report={'schema_version':1,'status':'partial','project_root':str(root),'observation_tool':'mcp__cua_repl.js','browser':'Codex in-app browser','published_proposal':pid,'published_operation':candidate['operation_id'],'published_sha256':before,'guard':{k:guard[k] for k in ('action_id','semantic_status','lock_rechecked','authorization','request_sha256')},'observations':observations,'evidence':refs,'unsafe_probe_proposal':unsafe,'native_generation':{'proposal_id':'ONTPROP-16ca267865ae4434aaeda32d064bbed2','evidence':'Verification/ontology-second-release/generation-acceptance.json'},'limits':['Browser screenshots were inspected through CUA; its content-export command is unsupported. No screenshot file is claimed.','HTTP and synthetic fixture tests are labeled separately from actual native/browser evidence.']}
(base/'Verification/ontology-second-release/browser-acceptance.json').write_bytes(canonical_bytes(report));print(json.dumps({'status':report['status'],'unsafe_probe_proposal':unsafe,'published_guard':guard['semantic_status']}))
