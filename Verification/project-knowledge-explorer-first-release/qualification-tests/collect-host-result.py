"""Copy exact root-produced public evidence and verify stage/result correspondence."""
from pathlib import Path
import json,hashlib,stat,os,sys
ROOT=Path(__file__).resolve().parents[3];Q=Path(__file__).resolve().parent
source=Path(sys.argv[1]);expected=sys.argv[2];label=sys.argv[3];expected_status=sys.argv[4] if len(sys.argv)==5 else 'passed';assert expected_status in ('passed','failed')
assert source.is_absolute() and str(source).startswith('/private/tmp/explorer-') and label.replace('-','').isalnum()
def read(p):
    assert not p.is_symlink();fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno());assert stat.S_ISREG(a.st_mode) and a.st_nlink==1;b=f.read();z=os.fstat(f.fileno())
    assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns);return b
def sha(b):return hashlib.sha256(b).hexdigest()
raw=read(source/'receipt.json');assert sha(raw)==expected;receipt=json.loads(raw)
assert receipt['actor']=='/root' and receipt['status']==expected_status and receipt['result_status']==expected_status and receipt['exit_code']==(0 if expected_status=='passed' else 1)
assert not receipt['timed_out'] and not receipt['output_limit'] and not receipt['post_verification_errors'] and not receipt['host_error'] and receipt['observed_descendants_exited'] and receipt['stderr_bytes']==0 and not receipt['emergency_signals']
stdout=read(source/'stdout.json');assert sha(stdout)==receipt['stdout_sha256'] and len(stdout)==receipt['stdout_bytes'];result=json.loads(stdout);assert result['status']==expected_status
assert sha(read(source/'host-wrapper.py'))==receipt['host_wrapper_sha256'];assert sha(read(source/'reviewed-job.json'))==receipt['job']['sha256']==sha(read(Path(receipt['job']['path'])))
for key in ('original_stage','execution_stage'):
    stage=Path(receipt[key]);manifest=read(stage/'inputs.json');assert sha(manifest)==receipt['manifest_sha256'];rows=json.loads(manifest)['files'];assert len(rows)==receipt['admitted_files']
    for row in rows:
        b=read(stage/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256'],row['path']
    assert {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}=={'inputs.json'}|{r['path'] for r in rows}
    assert not any(p.is_symlink() for p in stage.rglob('*'))
dest=Q/('actual-'+label);dest.mkdir();refs=[]
for name in ('receipt.json','stdout.json','host-wrapper.py','reviewed-job.json','admission.json'):
    b=read(source/name);p=dest/name;p.write_bytes(b);refs.append({'path':str(p.relative_to(ROOT)),'sha256':sha(b),'bytes':len(b)})
record={'status':'verified_actual_'+expected_status,'actual_executor':'/root','worker_action':'Verified and copied exact public host evidence; did not execute listener/browser job.','original_directory':str(source),'references':refs,'complete_original_and_captured_stage_verified':True,'receipt_sha256':expected}
p=dest/'attribution.json';p.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}))
