"""Read-only root counterfactual probes; existing confined workers and limits."""
from pathlib import Path
import json,time,collections
from concurrent.futures import ThreadPoolExecutor
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'.agents/skills/ontology/scripts'))
from ontology_standards import _prepare,infer,validate
from ontology_core import canonical_bytes,sha256
from ontology_limits import limits
OUT=Path(__file__).resolve().parent
cfg,payload,p=_prepare(ROOT)
empty=canonical_bytes({'@context':p.config['context']['path'],'@graph':[]})
overrides={name:empty for name in ('ONTOLOGY/modules/project/curator.jsonld','ONTOLOGY/bindings/curator.jsonld')}
summary={'current_context':payload['context']['snapshot_sha256'],'record_count':len(p.records),'curator_record_count':sum(r['@id'].startswith(p.namespace+'curator-') for r in p.records),'kind_counts':dict(collections.Counter(r['kind'] for r in p.records)),'limits':limits(cfg['limits']),'probes':[]}
def probe(operation):
 start=time.monotonic();value=(infer if operation=='infer' else validate)(ROOT,overrides=overrides)
 raw=canonical_bytes(value);(OUT/('without-curator-'+operation+'.json')).write_bytes(raw)
 row={'probe':'without-curator-'+operation,'status':value['status'],'complete':value['complete'],'elapsed_seconds':time.monotonic()-start,'response_bytes':len(raw),'worker':value.get('worker'),'scope':'counterfactual graph override only; all remaining records and constraints retained; not a current-root health result'}
 if operation=='infer':row.update(proofs=len(value.get('proofs',[])),provenance_quads=len(value.get('provenance',[])),inferred=len(value.get('inferred',[])))
 return row
with ThreadPoolExecutor(max_workers=2) as executor:summary['probes']=list(executor.map(probe,['infer','validate']))
(OUT/'counterfactual-summary.json').write_bytes(canonical_bytes(summary));print(json.dumps(summary,indent=2))
