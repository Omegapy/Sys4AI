"""Root diagnostic: observe a bounded enum without changing the failing assertion."""
import ast,contextlib,hashlib,inspect,io,json,os,pathlib,stat,subprocess,sys,tempfile,time,unittest
ROOT=pathlib.Path('/Volumes/P-SSD/AngryOwl/Sys4AI')
STAGE=pathlib.Path('/private/tmp/explorer-security-host-4xl8qvlu/captured-stage')
OUT=pathlib.Path(tempfile.mkdtemp(prefix='explorer-security05-enum-',dir='/private/tmp'))
hash=lambda b:hashlib.sha256(b).hexdigest()
helper=ast.parse(pathlib.Path('/private/tmp/run-explorer-qualification-security-host.py').read_bytes());fn=next(n for n in helper.body if isinstance(n,ast.FunctionDef) and n.name=='read_exact');exec(compile(ast.Module(body=[fn],type_ignores=[]),'root-read-exact','exec'))
manifest_raw=read_exact(STAGE/'inputs.json');assert hash(manifest_raw)=='cc675b1cda566e31d74c93574370128ab4a0dd3909f23538bc39654f3ee1da59'
manifest=json.loads(manifest_raw)
def verify():
 for row in manifest['files']:
  raw=read_exact(STAGE/row['path']);assert hash(raw)==row['sha256'] and len(raw)==row['bytes']
verify();driver=STAGE/'host-security-runner.py';raw=read_exact(driver)
allowed_codes={'source_unavailable','resource_limit','snapshot_changed','source_forbidden','source_locator_invalid','source_observation_changed','identity_unavailable','deadline_exceeded','presentation_invalid','invalid_request','canonical_invalid','configuration_needed'}
allowed_variants={'symlink','oversized','binary','missing'}
observations=[];original_run=unittest.TextTestRunner.run;original_popen=subprocess.Popen;spawned=[]
def tracked(*args,**kwargs):
 p=original_popen(*args,**kwargs);spawned.append(p);return p
subprocess.Popen=tracked
expected='test_explorer_security.SecurityTests.test_at26_source_replacement_never_follows_or_repairs'
def observe_run(runner,suite):
 def walk(node):
  if isinstance(node,unittest.TestSuite):
   for child in node:yield from walk(child)
  else:yield node
 cases=list(walk(suite));assert len(cases)==1 and cases[0].id()==expected
 case=cases[0];original_denied=case.denied
 def denied(result,codes=None):
  variant=inspect.currentframe().f_back.f_locals.get('variant');assert variant in allowed_variants
  value=json.loads(result[2]);code=value.get('error',{}).get('code')
  observations.append({'variant':variant,'http_status':result[0] if type(result[0]) is int else None,'observed_error_code':code if code in allowed_codes else 'unrecognized','recognized_enum':code in allowed_codes})
  return original_denied(result,codes)
 case.denied=denied
 return original_run(runner,suite)
unittest.TextTestRunner.run=observe_run
sys.argv=[str(driver),'--case',expected];stdout=io.StringIO();stderr=io.StringIO();exit_code=None;error_type=None
namespace={'__name__':'__main__','__file__':str(driver),'__package__':None}
started=time.monotonic();print(json.dumps({'status':'running','output_directory':str(OUT),'root_pid':os.getpid()}),flush=True)
try:
 with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
  try:exec(compile(raw,str(driver),'exec',dont_inherit=True),namespace)
  except SystemExit as error:exit_code=error.code
  except BaseException as error:error_type=type(error).__name__
finally:
 unittest.TextTestRunner.run=original_run;subprocess.Popen=original_popen
 for p in reversed(spawned):
  if p.poll() is None:
   p.terminate()
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
verify();safe_result=json.loads(stdout.getvalue());assert safe_result['tests_run']==1 and safe_result['failures']==1 and safe_result['errors']==0
assert exit_code==1 and error_type is None
assert all(p.poll() is not None for p in spawned)
report={'schema_version':1,'actor':'/root','purpose':'Observe the exact failing variant and allowlisted error enum while retaining original security-05 test assertions and production bytes. This is diagnostic evidence, not a passing test or a changed acceptance rule.','source_stage':str(STAGE),'manifest_sha256':hash(manifest_raw),'driver_sha256':hash(raw),'diagnostic_script_sha256':hash(pathlib.Path(__file__).read_bytes()),'method':'Only unittest.TextTestRunner.run wraps the one test instance denied() method to record a safe enum and variant, then calls the original denied() assertion unchanged. Real Service/Reader and fixture code execute unchanged.','observations':observations,'original_assertion_exit':exit_code,'original_safe_result':safe_result,'elapsed_seconds':time.monotonic()-started,'inputs_unchanged':True,'observed_owned_processes':[{'pid':p.pid,'exit_code':p.returncode} for p in spawned],'owned_processes_reaped':True,'stderr_bytes':len(stderr.getvalue().encode()),'raw_stderr_retained':False}
(OUT/'diagnostic.py').write_bytes(pathlib.Path(__file__).read_bytes());receipt=OUT/'result.json';receipt.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'diagnostic_completed_original_test_failed','result':str(receipt),'sha256':hash(receipt.read_bytes()),'observations':observations,'elapsed_seconds':report['elapsed_seconds'],'owned_processes_reaped':True}),flush=True)
