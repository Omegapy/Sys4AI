from pathlib import Path
import json,os,sys,unittest,time
root=Path('/Volumes/P-SSD/AngryOwl/Sys4AI');out=root/'Verification/guard-capacity-20260913';candidate=Path(json.loads((out/'candidate-location.json').read_text())['root'])
os.environ.update(PYTHONDONTWRITEBYTECODE='1',SYS4AI_GUARD_INSTALLED_ROOT=str(candidate),SYS4AI_TEST_DEPOT_ROOT=str(root),SYS4AI_STANDARDS_PYTHON=str(root/'.venv-ontology-standards/bin/python'),SYS4AI_GUARD_EVIDENCE=str(out/'installed-dispatch-evidence.json'),SYS4AI_GUARD_BOUNDARY_EVIDENCE=str(out/'installed-boundary-evidence.json'))
sys.path.insert(0,str(root/'SKILLS-depo/ontology/tests'))
import guard_support
original=guard_support.helper_path
def selected_fixture(relative):
    if str(relative)=='SKILLS-depo/init-new-project/tests/test_initializer.py':
        return root/'.agents/skills/init-new-project/tests/test_initializer.py'
    return original(relative)
guard_support.helper_path=selected_fixture
# Only fixture selection changes: the installed root initializer is v9, so use
# its own unchanged v9 fixture policy rather than the independent v11 source.
# Every actual adapter, validator, assertion and negative control stays intact.
start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromNames(['test_guarded_dispatch','test_guard_recovery']);result=unittest.TextTestRunner(verbosity=2).run(suite)
report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'seconds':time.monotonic()-start,'successful':result.wasSuccessful(),'candidate_root':str(candidate),'fixture_selection':'Exact installed v9 initializer fixture; unchanged matrix assertions and actual backend; root adapters preserved.'};(out/'installed-dispatch-run.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));sys.exit(0 if result.wasSuccessful() else 1)
