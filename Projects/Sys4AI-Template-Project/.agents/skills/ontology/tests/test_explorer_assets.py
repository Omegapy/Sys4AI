"""Pure package tests; production-build tests opt in via EXPLORER_BUILD_FIXTURE.

No live product or canonical project files are modified. Build fixture contents
and dependencies are prepared explicitly by the release worker, not installed by
the test suite. Every mutation uses its own disposable directory.
"""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ontology_explorer_assets as a

SCHEMA = "a" * 64
ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture(root, bodies=None):
    root.mkdir(parents=True, exist_ok=True)
    bodies = bodies or {"index.html": b'<html><head><link rel="stylesheet" href="./chunks/main.css"><script type="module" src="./chunks/main.js"></script></head><body>Reader</body></html>',
                        "chunks/main.js": b'export const start=()=>import("./lazy.js");',
                        "chunks/lazy.js": b'export const x=1;', "chunks/main.css": b'body { color: black; }'}
    members = []
    for name, data in bodies.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        members.append({"path": name, "sha256": digest(data), "bytes": len(data), "mime": a.MIMES[Path(name).suffix]})
    manifest = {"schema_version": 1, "api_version": 1, "build_id": "0" * 64, "entry": "index.html", "assets": members,
                "source_digest": "b" * 64, "lock_sha256": "c" * 64, "notices_sha256": "d" * 64,
                "toolchain": {"node": "25.9.0", "npm": "11.12.1"}, "build_command": "npm run build && npm run package:runtime"}
    manifest["build_id"] = a.build_id(manifest, SCHEMA)
    write_manifest(root, manifest)
    return manifest


def write_manifest(root, manifest):
    (root / "manifest.json").write_bytes(a.canonical_bytes(manifest))


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="explorer-assets-", dir="/private/tmp")
        self.root = Path(self.temp.name) / "assets"
        self.manifest = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def reject(self, reason=None):
        with self.assertRaises(a.AssetError) as failure:
            a.load_assets(self.root, schema_sha256=SCHEMA)
        if reason:
            self.assertEqual(failure.exception.reason, reason)

    def test_valid_closed_package_and_only_exact_http_aliases(self):
        package = a.load_assets(self.root, schema_sha256=SCHEMA)
        self.assertEqual(package.read('/'), package.read('/index.html'))
        self.assertEqual(package.read('/chunks/lazy.js'), (b'export const x=1;', 'text/javascript'))
        for name in ['/manifest.json', '/package.json', '/node_modules/x.js', '/chunks/%6cazy.js', '/chunks/../index.html', '/index.html?x=1', '//index.html', '/chunks\\lazy.js', '/index.html#x', 'http://127.0.0.1/']:
            with self.subTest(path=name), self.assertRaises(a.AssetError) as failure:
                package.read(name)
            self.assertEqual(failure.exception.code, 'resource_forbidden')
        with self.assertRaises(TypeError):
            package.members['new.js'] = {}

    def test_nested_entry_uses_its_actual_directory(self):
        bodies={'pages/start.html':b'<script type="module" src="../chunks/main.js"></script>', 'chunks/main.js':b'export const x=1;'}
        members=[]
        for name,data in bodies.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            members.append({'path':name,'sha256':digest(data),'bytes':len(data),'mime':a.MIMES[p.suffix]})
        m=copy.deepcopy(self.manifest);m.update(entry='pages/start.html',assets=members);write_manifest(self.root,m)
        package=a.load_assets(self.root)
        self.assertEqual(package.read('/')[0],bodies['pages/start.html'])
        self.assertEqual(package.manifest['entry'],'pages/start.html')
        self.assertEqual(a.asset_path('chunks/.local.js'),'chunks/.local.js')

    def test_canonical_serialization_matches_existing_core(self):
        from ontology_core import canonical_bytes
        values = [{"z": "日本語 😀", "a": [1, None, False]}, {"domain": "sys4ai-explorer-build-v1", "source_digest": "f" * 64}]
        for value in values:
            self.assertEqual(a.canonical_bytes(value), canonical_bytes(value))

    def test_closed_shape_numeric_tokens_and_metadata(self):
        for mutation in [lambda m: m.update(unknown=True), lambda m: m.update(schema_version=True), lambda m: m.update(api_version=1.0), lambda m: m['assets'][0].update(bytes=True), lambda m: m['assets'][0].update(bytes=1.0), lambda m: m['toolchain'].update(extra='x'), lambda m: m['toolchain'].update(npm='11.12'), lambda m: m.update(entry='chunks/main.js'), lambda m: m.update(build_id='A'*64), lambda m: m['assets'][0].update(sha256='x'*64), lambda m: m['assets'][0].update(mime='text/javascript')]:
            with self.subTest(mutation=mutation):
                m = copy.deepcopy(self.manifest); mutation(m); write_manifest(self.root, m); self.reject()
        write_manifest(self.root, self.manifest)
        self.reject_metadata()

    def reject_metadata(self):
        with self.assertRaises(a.AssetError):
            a.load_assets(self.root, schema_sha256='e'*64)
        with self.assertRaises(a.AssetError):
            a.load_assets(self.root, lock_path=self.root/'index.html')

    def test_duplicate_json_and_depth_and_utf8(self):
        raw = a.canonical_bytes(self.manifest)
        cases = [raw.replace(b'"schema_version": 1', b'"schema_version": 1,"schema_version": 1'), b'['*17+b'0'+b']'*17, b'\xff', raw.replace(b'"schema_version": 1', b'"schema_version": NaN')]
        for raw in cases:
            (self.root/'manifest.json').write_bytes(raw); self.reject()

    def test_paths_aliases_and_forbidden_inventory(self):
        for path in ['../x.js', './x.js', '/x.js', 'chunks//x.js', 'x%2e.js', 'x\\y.js', 'é.js', '.git/x.js', 'node_modules/x.js', 'fixtures/x.js', 'src/x.js', 'Tasks/x.js', 'x.js.map', 'manifest.json', 'x'*238+'.js']:
            with self.subTest(path=path):
                m = copy.deepcopy(self.manifest); m['assets'][1]['path'] = path; write_manifest(self.root, m); self.reject()
        m = copy.deepcopy(self.manifest); m['assets'].append(dict(m['assets'][1], path='chunks/MAIN.js')); write_manifest(self.root, m); self.reject('duplicate_asset_path')

    def test_preallocation_limits(self):
        for mutation in [lambda m: m['assets'][0].update(bytes=a.MAX_FILE_BYTES+1), lambda m: m.update(assets=m['assets']*17), lambda m: [x.update(bytes=a.MAX_FILE_BYTES) for x in m['assets']]]:
            m=copy.deepcopy(self.manifest); mutation(m); write_manifest(self.root,m);self.reject()
        (self.root/'manifest.json').write_bytes(b' '* (a.MAX_MANIFEST_BYTES+1));self.reject('asset_size_limit')

    def test_missing_empty_hash_and_same_mtime_tamper(self):
        target=self.root/'chunks/main.js'; before=target.stat(); raw=target.read_bytes()
        target.write_bytes(b'x'*len(raw));os.utime(target,ns=(before.st_atime_ns,before.st_mtime_ns));self.reject('asset_hash_mismatch')
        target.write_bytes(b'');self.reject('asset_size_limit')
        target.unlink();self.reject('asset_unavailable')

    def test_symlink_and_hardlink_and_parent_symlink(self):
        target=self.root/'chunks/main.js';outside=self.root.parent/'outside.js';outside.write_bytes(target.read_bytes());target.unlink();target.symlink_to(outside);self.reject()
        target.unlink();os.link(outside,target);self.reject('unsafe_asset_file')
        target.unlink();target.write_bytes(outside.read_bytes())
        original=self.root/'chunks';renamed=self.root/'renamed';original.rename(renamed);original.symlink_to(renamed,target_is_directory=True);self.reject()

    def test_fifo_and_oversized_regular_file_fail_before_read(self):
        target=self.root/'chunks/main.js';target.unlink();os.mkfifo(target)
        self.reject('unsafe_asset_file')
        target.unlink()
        with target.open('wb') as output:output.truncate(a.MAX_FILE_BYTES+1)
        self.reject('asset_size_limit')

    def test_manifest_and_root_links(self):
        manifest=self.root/'manifest.json'; outside=self.root.parent/'manifest.json';manifest.rename(outside);manifest.symlink_to(outside);self.reject()
        manifest.unlink();shutil.copyfile(outside,manifest)
        alias=self.root.parent/'alias';alias.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(a.AssetError):a.load_assets(alias)

    def test_read_rechecks_pinned_bytes_and_manifest(self):
        package=a.load_assets(self.root);target=self.root/'chunks/lazy.js';target.write_bytes(b'export const x=2;')
        with self.assertRaises(a.AssetError):package.read('/chunks/lazy.js')
        target.write_bytes(b'export const x=1;');m=copy.deepcopy(self.manifest);m['source_digest']='e'*64;write_manifest(self.root,m)
        with self.assertRaises(a.AssetError):package.read('/')

    def test_import_closure_positive_forms(self):
        for js in ['import "./lazy.js";', 'import {x} from "./lazy.js";', 'export {x} from "./lazy.js";', 'export * from "./lazy.js";', 'export * as x from "./lazy.js";', 'export {x};\nimport("./lazy.js")', 'const r=/import("remote")/; import("./lazy.js");', 'const s="import(\\"remote\\")"; import("./lazy.js")', 'const s=`plain import("remote") ${import("./lazy.js")}`']:
            with self.subTest(js=js):
                bodies={m['path']:(self.root/m['path']).read_bytes() for m in self.manifest['assets']};bodies['chunks/main.js']=js.encode();fixture(self.root,bodies);a.load_assets(self.root)

    def test_import_closure_remote_computed_missing_escaped(self):
        for js in ['import "https://example.test/x.js";', 'import("//example.test/x.js")', 'import("./missing.js")', 'import("./lazy.js?x")', 'import("./%6cazy.js")', 'import("../../outside.js")', 'import(foo)', 'import(`./${foo}.js`)', 'const x=`nested ${`deep ${import("https://bad/x.js")}`}`', 'import("./"+foo)', 'export {x}\nimport("https://example.test/x.js")', 'const x=`${import("https://example.test/x.js")}`', r'import(".\x2flazy.js")']:
            with self.subTest(js=js):
                bodies={m['path']:(self.root/m['path']).read_bytes() for m in self.manifest['assets']};bodies['chunks/main.js']=js.encode();fixture(self.root,bodies);self.reject()

    def test_html_css_and_unreachable_rejection(self):
        cases=[('index.html',b'<video poster="https://bad/x"></video>'),('index.html',b'<body background="https://bad/x"></body>'),('chunks/main.css',b'body{background:image-set("https://bad/x" 1x)}'),('index.html',b'<script>alert(1)</script>'),('index.html',b'<base href="https://bad"><script type="module" src="./chunks/main.js"></script>'),('index.html',b'<div onclick="bad()">x</div>'),('chunks/main.css',b'body{background:url(https://bad/x.css)}'),('chunks/main.css',b'@import "https://bad/x.css";'),('chunks/main.css',b'@im\\port "x.css";'),('chunks/main.js',b'export const x=1;'),('chunks/main.js',b'//# sourceMappingURL=a.map\nimport("./lazy.js")')]
        for path,data in cases:
            with self.subTest(path=path,data=data):
                fixture(self.root);bodies={m['path']:(self.root/m['path']).read_bytes() for m in self.manifest['assets']};bodies[path]=data;fixture(self.root,bodies);self.reject()

    def test_repeated_imports_keep_bounded_closure(self):
        bodies={m['path']:(self.root/m['path']).read_bytes() for m in self.manifest['assets']}
        bodies['chunks/main.js']=b'import("./lazy.js");'*10000
        manifest=fixture(self.root,bodies)
        graph=a.validate_closure(manifest,bodies)
        self.assertEqual(graph['chunks/main.js'],['chunks/lazy.js'])
        a.load_assets(self.root)

    def test_runtime_has_no_mutator_or_optional_import(self):
        import ast
        tree=ast.parse((ROOT/'scripts/ontology_explorer_assets.py').read_text())
        imports={node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node,ast.ImportFrom) and node.module}|{name.name.split('.')[0] for node in ast.walk(tree) if isinstance(node,ast.Import) for name in node.names}
        self.assertTrue(imports<=sys.stdlib_module_names|{'__future__'})
        forbidden={'write','unlink','replace','mkdir','makedirs','remove','rename','rmdir'}
        self.assertFalse([n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute) and n.attr in forbidden])


@unittest.skipUnless(os.environ.get('EXPLORER_BUILD_FIXTURE'), 'explicit reviewed disposable build fixture required')
class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(os.environ['EXPLORER_BUILD_FIXTURE'])
        self.temp=tempfile.TemporaryDirectory(prefix='explorer-publisher-test-',dir='/private/tmp')
        self.root=Path(self.temp.name)/'ontology/explorer'
        shutil.copytree(self.base.parent, self.root.parent, symlinks=True)
        if (self.root/'assets').exists(): shutil.rmtree(self.root/'assets')
        self.env={**os.environ,'EXPLORER_SCHEMA':str(self.base.parent/'schema.json'),'EXPLORER_PYTHON':sys.executable,'PYTHONDONTWRITEBYTECODE':'1'}

    def tearDown(self):self.temp.cleanup()

    def run_node(self,script):
        return subprocess.run(['node','--input-type=module','-e',script],cwd=self.root,env=self.env,text=True,capture_output=True,timeout=40)

    def publish(self,ok=True):
        result=self.run_node("import {publishRuntime} from './scripts/package-runtime.mjs';console.log(JSON.stringify(publishRuntime(process.cwd())));")
        self.assertEqual(result.returncode==0,ok,result.stdout+result.stderr)
        return result

    def test_publisher_valid_and_unowned_preservation(self):
        self.publish();marker=self.root/'assets/unrelated.txt';marker.write_text('preserve');before=marker.read_bytes();self.publish();self.assertEqual(marker.read_bytes(),before)

    def test_source_drift_and_output_tamper_fail_before_publication(self):
        self.publish();old=(self.root/'assets/manifest.json').read_bytes();source=self.root/'src/main.ts';source.write_text(source.read_text()+'\n// changed\n');self.publish(False);self.assertEqual((self.root/'assets/manifest.json').read_bytes(),old)

    def test_unowned_collision_and_unsafe_destination(self):
        (self.root/'assets').mkdir();(self.root/'assets/index.html').write_text('owned by somebody else');self.publish(False);self.assertEqual((self.root/'assets/index.html').read_text(),'owned by somebody else')
        shutil.rmtree(self.root/'assets');outside=self.root/'outside';outside.mkdir();(self.root/'assets').symlink_to(outside,target_is_directory=True);self.publish(False);self.assertEqual(list(outside.iterdir()),[])

    def test_bad_dist_and_prior_owned_tamper_preserved(self):
        self.publish();old=(self.root/'assets/manifest.json').read_bytes();(self.root/'assets/index.html').write_text('customized');self.publish(False);self.assertEqual((self.root/'assets/index.html').read_text(),'customized');self.assertEqual((self.root/'assets/manifest.json').read_bytes(),old)

    def test_tampered_dist_rejected_before_output(self):
        file=next((self.root/'dist/chunks').glob('*.js'))
        file.write_bytes(file.read_bytes()+b'\n// unbuilt output')
        self.publish(False);self.assertFalse((self.root/'assets').exists())

    def test_manifest_last_failure_is_not_a_valid_package(self):
        wrapper=self.root.parent/'python-fail-manifest'
        wrapper.write_text('#!'+sys.executable+'\nimport os,sys\n_original_replace=os.replace\ndef replace(src,dst,*args,**kwargs):\n if dst=="manifest.json": raise OSError("injected manifest commit failure")\n return _original_replace(src,dst,*args,**kwargs)\nos.replace=replace\nexec(sys.argv[sys.argv.index("-c")+1])\n')
        wrapper.chmod(0o700);self.env['EXPLORER_PYTHON']=str(wrapper)
        failed=self.publish(False)
        self.assertIn('injected manifest commit failure',failed.stderr)
        self.assertFalse((self.root/'assets/manifest.json').exists())
        self.assertTrue((self.root/'assets/index.html').is_file())
        with self.assertRaises(a.AssetError):a.load_assets(self.root/'assets')
        self.assertFalse(list((self.root/'assets').rglob('.explorer-publish-*')))

    def test_helper_change_before_execution_is_rejected(self):
        wrapper=self.root.parent/'python-change-helper'
        helper=self.root.parent/'scripts/ontology_explorer_assets.py'
        executed=self.root.parent/'unverified-helper-executed'
        replacement='from pathlib import Path;Path('+repr(str(executed))+').write_text("bad")'
        wrapper.write_text('#!'+sys.executable+'\nimport sys\nfrom pathlib import Path\nPath('+repr(str(helper))+').write_text('+repr(replacement)+')\nexec(sys.argv[sys.argv.index("-c")+1])\n')
        wrapper.chmod(0o700);self.env['EXPLORER_PYTHON']=str(wrapper)
        self.publish(False)
        self.assertFalse(executed.exists())
        self.assertFalse((self.root/'assets').exists())

    def test_staged_write_failure_cleans_its_temporary_files(self):
        wrapper=self.root.parent/'python-fail-write'
        wrapper.write_text('#!'+sys.executable+'\nimport os,sys\ndef fail_write(*args): raise OSError("injected staged write failure")\nos.write=fail_write\nexec(sys.argv[sys.argv.index("-c")+1])\n')
        wrapper.chmod(0o700);self.env['EXPLORER_PYTHON']=str(wrapper)
        failure=self.publish(False)
        self.assertIn('injected staged write failure',failure.stderr)
        self.assertFalse((self.root/'assets/manifest.json').exists())
        self.assertFalse(list((self.root/'assets').rglob('.explorer-publish-*')))

    def test_rebuild_removes_only_obsolete_owned_assets(self):
        self.publish()
        previous=json.loads((self.root/'assets/manifest.json').read_text())
        marker=self.root/'assets/unrelated.txt';marker.write_text('preserved')
        source=self.root/'src/main.ts';source.write_text(source.read_text()+'\ndocument.title="second build";\n')
        built=subprocess.run(['npm','run','build'],cwd=self.root,env=self.env,text=True,capture_output=True,timeout=40)
        self.assertEqual(built.returncode,0,built.stdout+built.stderr)
        self.publish()
        current=json.loads((self.root/'assets/manifest.json').read_text())
        old={x['path'] for x in previous['assets']};new={x['path'] for x in current['assets']}
        self.assertTrue(old-new)
        self.assertTrue(all(not (self.root/'assets'/x).exists() for x in old-new))
        self.assertEqual(marker.read_text(),'preserved')

    def test_unknown_and_linked_output_rejected(self):
        (self.root/'dist/unreviewed.txt').write_text('do not ship');self.publish(False);self.assertFalse((self.root/'assets').exists())
        (self.root/'dist/unreviewed.txt').unlink();file=next((self.root/'dist/chunks').glob('*.js'));copyfile=self.root/'outside.js';shutil.copyfile(file,copyfile);file.unlink();file.symlink_to(copyfile);self.publish(False);self.assertFalse((self.root/'assets').exists())


if __name__ == '__main__':unittest.main(verbosity=2)
