"""Run only the four assigned reader suites and bind their live input bytes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent
FILES=['SKILLS-depo/ontology/scripts/ontology_explorer_read.py','SKILLS-depo/ontology/scripts/ontology_explorer_source.py']+['SKILLS-depo/ontology/tests/test_explorer_'+x+'.py' for x in ('read','search','sources','processes')]+['SKILLS-depo/ontology/scripts/ontology_explorer_snapshot.py','SKILLS-depo/ontology/references/explorer-contract.md','ONTOLOGY-depo/schema/explorer-v1.json','SKILLS-depo/ontology/tests/explorer_support.py']
def refs():return [{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'bytes':(ROOT/p).stat().st_size} for p in FILES]
run=sys.argv[1];before=refs();started=time.monotonic()
command=[sys.executable,'-B','-m','unittest','-v','test_explorer_read','test_explorer_search','test_explorer_sources','test_explorer_processes']
with (OUT/(run+'.stdout')).open('w') as stdout,(OUT/(run+'.stderr')).open('w') as stderr:
 result=subprocess.run(command,cwd=ROOT/'SKILLS-depo/ontology/tests',stdout=stdout,stderr=stderr,timeout=180)
after=refs();report={'command':command,'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-started,'inputs':before,'inputs_unchanged':before==after,'scope':'Four assigned reader suites. No production HTTP, supervisor, browser, accessibility, human or release acceptance.'}
(OUT/(run+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('inputs','command')}));sys.exit(result.returncode or (0 if before==after else 2))
