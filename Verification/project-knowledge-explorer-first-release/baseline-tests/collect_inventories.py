"""Bounded current source inventories; does not modify product state."""
import ast
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from collect_baseline import ROOT, OUT, LOGS, now, digest, metadata, write
sys.path.insert(0, str(ROOT / '.agents/skills/ontology/scripts'))
from ontology_core import load_project

def ref(path, locator=None):
    result = {'path': path, 'sha256': digest((ROOT/path).read_bytes())}
    if locator:
        result['locator'] = locator
    return result

def parts(name, rows, limit=200000):
    chunks, current = [], []
    for row in rows:
        if current and len(json.dumps(current+[row],indent=2).encode()) > limit:
            path=LOGS / f'{name}-{len(chunks)+1:02d}.json';write(path,current);chunks.append(ref(str(path.relative_to(ROOT))));current=[]
        current.append(row)
    if current:
        path=LOGS / f'{name}-{len(chunks)+1:02d}.json';write(path,current);chunks.append(ref(str(path.relative_to(ROOT))))
    return chunks

def source_lines(path, needle):
    lines=(ROOT/path).read_text().splitlines()
    match=next(i for i,line in enumerate(lines,1) if needle in line)
    return ref(path,f'line:{match}')

def callers():
    scopes=['SKILLS-depo','.agents','tools','depot','ONTOLOGY-depo','reference-assets/ONTOLOGY-depo',
            'SPECS-depo','Projects/Sys4AI-Template-Project','README.md','SPECS.md','ontology-advanced.yaml']
    argv=['rg','-l','-i','--hidden','--glob','!**/__pycache__/**','--glob','!**/*.pyc',
          '--glob','!**/node_modules/**','--glob','!**/.git/**',
          'workbench|ontology_workbench|trusted_authority|TrustedAuthority|assess_service',*scopes]
    proc=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
    if proc.returncode not in (0,1):raise RuntimeError(proc.stderr)
    entries=[]
    for path in sorted(proc.stdout.splitlines()):
        text=(ROOT/path).read_text()
        lines=text.splitlines()
        matches=[{'line': i,'terms': sorted(set(re.findall(r'(?i)workbench|ontology_workbench|trusted_authority|TrustedAuthority|assess_service',line)))}
                 for i,line in enumerate(lines,1) if re.search(r'(?i)workbench|trusted_authority|assess_service',line)]
        categories=[]
        if '/tests/' in path or path.startswith('tests/'):categories.append('test')
        if '/workbench/' in path or path.endswith('ontology_workbench.py'):categories.append('runtime')
        if path.endswith('ontology_advanced_cli.py'):categories.extend(['launcher','runtime'])
        if path.endswith(('ontology_health.py','ontology_authority.py','ontology_guards.py','ontology_guard_setup.py','ontology_proposals.py','ontology_profiles.py','ontology_proposal_validation.py','ontology_integration.py','ontology_publication.py')):categories.append('shared helper')
        if '/init-new-project/' in path or path.startswith('depot/') or path.startswith('Projects/Sys4AI-Template-Project/'):categories.append('distribution')
        if path.endswith('.md'):categories.append('docs')
        if not categories:categories.append('runtime')
        legacy='/assets/static-capability-v11.json' in path
        if legacy:categories=['historical','distribution']
        imports=[]
        if path.endswith('.py'):
            tree=ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module in ['ontology_workbench','ontology_authority']:
                    imports.append({'line':node.lineno,'module':node.module,'names':[n.name for n in node.names]})
        entries.append({**ref(path),'categories':sorted(set(categories)), 'matches':matches,'direct_imports':imports,
                        'scope':'Template copy' if path.startswith('Projects/') else 'installed root' if path.startswith('.agents/') else 'reusable source' if path.startswith(('SKILLS-depo/','ONTOLOGY-depo/','SPECS-depo/')) else 'root contract',
                        'retirement_rule':'Preserve previous initializer edition bytes and requirements.' if legacy else 'Review each current caller before cutover; category alone grants no deletion authority.'})
    historical=subprocess.run(['git','grep','-l','-i','workbench','HEAD','--','Verification'],cwd=ROOT,capture_output=True,text=True)
    historical_paths=sorted(p.removeprefix('HEAD:') for p in historical.stdout.splitlines())
    for path in historical_paths:
        entries.append({'path':path,'categories':['historical'],'scope':'committed Verification evidence; filename inventory only',
                        'retirement_rule':'Preserve immutable historical evidence; not an active runtime caller.'})
    mapping=json.loads((ROOT/'depot/template-update.json').read_text())
    report={'schema_version':1,'captured_at':now(),'scan':{'argv':argv,'returncode':proc.returncode,'roots':scopes,
            'excluded':['Git internals','Python caches','node_modules','independent product projects','Task candidate contents','private runtime/session files'],
            'historical_argv':['git','grep','-l','-i','workbench','HEAD','--','Verification'],'historical_returncode':historical.returncode},
            'categories':dict(Counter(c for e in entries for c in e['categories'])),'caller_count':len(entries),
            'entries':entries,
            'shared_helper_findings':[
                {'fact':'ontology_health imports assess_service from ontology_workbench; CLI and test fixtures import Workbench and trusted_authority. Preserve health and authority behavior when retiring human frontend.', 'sources':[source_lines('SKILLS-depo/ontology/scripts/ontology_health.py','from ontology_workbench'),source_lines('SKILLS-depo/ontology/scripts/ontology_advanced_cli.py','from ontology_workbench')]},
                {'fact':'TrustedAuthority delegates native observation, Director/manager validation, active manager checks and grants to ontology_authority. Publication, proposals, guards, profiles and integration use ontology_authority independently.', 'sources':[source_lines('SKILLS-depo/ontology/scripts/ontology_workbench.py','class TrustedAuthority'),source_lines('SKILLS-depo/ontology/scripts/ontology_publication.py','from ontology_authority')]},
            ],
            'initializer':{'current_setup_contract':'governance-starter-v12','advanced_module_contract':'governance-starter-v9',
                'sources':[source_lines('SKILLS-depo/init-new-project/scripts/init_new_project.py','SETUP_CONTRACT ='),source_lines('SKILLS-depo/init-new-project/scripts/init_ontology_advanced.py','RESOURCES =')],
                'required_old_frontend_assets':['workbench/index.html','workbench/app.js','workbench/editor.js','workbench/review.js','workbench/advanced.js','workbench/styles.css'],
                'current_manifest':'SKILLS-depo/init-new-project/assets/static-capability-v1.json','retained_previous_manifest':'SKILLS-depo/init-new-project/assets/static-capability-v11.json',
                'qualification':'Current root installed initializer manifest and source manifest have distinct current bytes. Preserve each until separately scoped reviewed adoption; previous v1-v11 edition requirements must retain semantics.'},
            'template_distribution':{'template':mapping['template'],'mapping':ref('depot/template-update.json'),
                'updater':ref('tools/template_update.py'),'exclusion_source':source_lines('tools/template_update.py','EXCLUDED ='),
                'excluded_output_names':['dist','build','node_modules','.sys4ai','models','logs'],
                'implication':'New production assets cannot rely on excluded dist/build output shipping automatically. Explicit current asset manifest and neutral Template package validation are later release work.'}}
    write(OUT/'caller-inventory.json',report)
    print('callers',len(entries),'historical',len(historical_paths),flush=True)

def processes():
    p=load_project(ROOT)
    source_index={json.dumps({k:s[k] for k in ('path','sha256','locator')},sort_keys=True):i for i,s in enumerate(p.sources)}
    records=[{'id':r['@id'],'kind':r['kind'],'types':r.get('@type',[]),'label':r.get('label'),
              'definition':r.get('definition'),'location':p.locations[r['@id']],
              'source_indices':[source_index[json.dumps(s,sort_keys=True)] for s in r.get('sources',[])]} for r in p.records]
    selected=[r for r in p.records if r['kind']=='instance' and (r['@id'].endswith(':curator-process') or ':curator-function-' in r['@id'])]
    process_rows=[]
    field_predicates={'inputs':'curator-predicate-consumes','outputs':'curator-predicate-produces','roles':'curator-predicate-coordinatesOwner',
                      'applicability':'curator-predicate-triggeredBy','prerequisites':'curator-predicate-requiresPrerequisite','scope':'curator-predicate-maintains'}
    for record in selected:
        edges=[r for r in p.relations if r['subject']==record['@id'] or r['object']==record['@id']]
        fields={'purpose':{'status':'supported','text':record['definition'],'source':{'path':p.locations[record['@id']].split('#')[0],
                                                                          'locator':p.locations[record['@id']]},'sources':record['sources']}}
        for field,suffix in field_predicates.items():
            matches=[e for e in edges if e['subject']==record['@id'] and e['predicate'].endswith(':'+suffix)]
            fields[field]={'status':'supported' if matches else 'absent_in_selected_record_relations',
                           'relations':[{'id':e['@id'],'subject':e['subject'],'predicate':e['predicate'],'object':e['object'],
                                         'object_label':p.by_id[e['object']]['label'],'location':p.locations[e['@id']], 'sources':e['sources']} for e in matches]}
        fields['related_skills_and_documents']={'status':'supported','record_sources':record['sources'],
            'relation_ids':[e['@id'] for e in edges],
            'qualification':'Source paths are supporting documents; relation labels/types retain canonical meaning and do not imply execution sequence.'}
        fields['ordered_steps']={'status':'absent_in_canonical_structured_fields','inspected_keys':sorted(record),
            'canonical_sequence_predicates':[], 'source_prose_status':'partial_order_constraints_recorded_separately; no full process sequence asserted',
            'required_fallback':'An ordered description has not been recorded. These are the documented relationships.'}
        fields['branches']={'status':'absent_in_canonical_structured_fields','source_prose_status':'Conditional owner/session rules exist; no source-supported global branch graph asserted.'}
        process_rows.append({'id':record['@id'],'label':record['label'],'canonical_kind':record['kind'],'types':record['@type'],
                             'selection_basis':'Explicit curator-process identity or declared curator-function prefix; not an inferred Process type.', 'fields':fields})
    examined=['CURATOR.md','curator.yaml','curator-session.yaml','.agents/skills/curate/ACTIONS.md',
              '.agents/skills/curate/SKILL.md','.agents/skills/curate/references/commands.md',
              '.agents/skills/curate/references/session-maintenance.md']
    ordering=[
        {'claim':'Manager reservation precedes actual launch, role acknowledgement and activation; only then sole Task writer ownership applies.', 'source':source_lines('CURATOR.md','After actual launch')},
        {'claim':'New ordinary Curator intake validates selection before reservation source/context inclusion, actual receipt, reads and confirmed activation.', 'source':source_lines('.agents/skills/curate/ACTIONS.md','First validate')},
        {'claim':'Session-start gathers observations and retains pending signals; current-owner evaluation and selected dispatch remain separate.', 'source':source_lines('.agents/skills/curate/references/session-maintenance.md','This command gathers current')},
        {'claim':'Delivery consumption follows a completed outcome and attributable canonical owner receipt; dispatch alone does not consume it.', 'source':source_lines('.agents/skills/curate/references/session-maintenance.md','The application retains')},
        {'claim':'Log access starts with a summary, then bounded query/excerpts when needed; this ordering is local to log access.', 'source':source_lines('.agents/skills/curate/SKILL.md','For log access, start with a summary.')},
    ]
    file_counts=[]
    for module in p.modules:
        for name in module['files']:
            file=module['path']+'/'+name
            if file.endswith('.jsonld'):
                d=json.loads((ROOT/file).read_text())
                if '@graph' in d:file_counts.append({'path':file,'scope':'locked imported module','records':len(d['@graph'])})
    for name in p.config['project_files']+p.config['binding_files']:
        file_counts.append({'path':name,'scope':'binding file' if name in p.config['binding_files'] else 'project file',
                            'records':len(json.loads((ROOT/name).read_text())['@graph'])})
    report={'schema_version':1,'captured_at':now(),'project_id':p.project_id,'loader':ref('.agents/skills/ontology/scripts/ontology_core.py'),
            'scope_reconciliation':{'seven_local_files_inventory':347,'complete_loaded_inventory':len(p.records),'complete_loaded_non_binding_records':347,'binding_records':sum(r['kind']=='binding' for r in p.records),
                'explanation':'The seven selected local files contain 347 records INCLUDING 65 bindings: project.jsonld 90 + curator.jsonld 192 + five binding files 65. The full loader adds 65 imported-core records for 412 total. The full loaded non-binding count is also 347 (412 minus 65 bindings), a distinct coincidental count. Neither inventory proves process ordering.','files':file_counts},
            'counts':{'kind':dict(Counter(r['kind'] for r in p.records)),'type':dict(Counter(t for r in p.records for t in r.get('@type',[]))),
                      'predicate_usage':dict(Counter(r['predicate'] for r in p.relations)), 'records_missing_definition':[r['@id'] for r in p.records if not r.get('definition')],
                      'source_freshness':dict(Counter(s['status'] for s in p.sources))},
            'record_inventory_chunks':parts('record-inventory',records),'sources':p.sources,
            'process_candidates':process_rows,'process_source_coverage':{'fully_inspected_documents':[ref(f) for f in examined],
                 'unexamined_linked_source_bodies':sorted({s['path'] for r in selected for s in r['sources']}-set(examined)),
                 'qualification':'Canonical functions/relationships and the listed full documents were inspected. Linked scripts and other skill bodies not listed as fully inspected are unexamined for textual step order. No absence claim extends to them.'},
            'supported_partial_ordering':ordering,'global_ordering_conclusion':'No structured global sequence is present in the selected canonical records. Examined prose provides the cited local precedence constraints, not one total ordering of all Curator actions. Unexamined sources remain explicit.',
            'canonical_mutation':False}
    write(OUT/'process-content-inventory.json',report)
    print('process candidates',len(selected),'records',len(p.records),flush=True)

if __name__=='__main__':
    callers()
    processes()
