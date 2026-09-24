// Explicit build-only tooling. Importing this module computes nothing and writes nothing.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { parseSync } from 'vite';

export const targets = ['chrome111', 'edge111', 'firefox114', 'safari16.4'];
const MAX_FILE = 8388608, MAX_TOTAL = 16777216, MAX_FILES = 64;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function requireThat(value, reason) { if (!value) throw new Error(reason); }
function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (value !== null && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(key => [key, sorted(value[key])]));
  return value;
}
export function canonicalBytes(value) { return Buffer.from(JSON.stringify(sorted(value), null, 2) + '\n'); }
function regular(filename, max = MAX_FILE) {
  const absolute = path.resolve(filename);
  let prefix = path.parse(absolute).root;
  for (const part of absolute.slice(prefix.length).split(path.sep).slice(0, -1)) {
    prefix = path.join(prefix, part);
    requireThat(fs.lstatSync(prefix).isDirectory() && !fs.lstatSync(prefix).isSymbolicLink(), 'unsafe input parent');
  }
  const fd = fs.openSync(absolute, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
  try {
    const before = fs.fstatSync(fd, { bigint: true });
    requireThat(before.isFile() && before.nlink === 1n && before.size > 0n && before.size <= BigInt(max), 'unsafe or oversized input');
    const buffer = Buffer.alloc(Number(before.size));
    let count = 0;
    while (count < buffer.length) {
      const n = fs.readSync(fd, buffer, count, buffer.length - count, null);
      requireThat(n > 0, 'short input read'); count += n;
    }
    const after = fs.fstatSync(fd, { bigint: true });
    requireThat(['dev', 'ino', 'size', 'mtimeNs', 'ctimeNs', 'nlink'].every(key => before[key] === after[key]), 'input changed during read');
    return buffer;
  } finally { fs.closeSync(fd); }
}
function walk(root, relative = '', result = []) {
  const dir = path.join(root, relative);
  const st = fs.lstatSync(dir);
  requireThat(st.isDirectory() && !st.isSymbolicLink(), 'unsafe input directory');
  const names = fs.readdirSync(dir).sort();
  requireThat(names.length <= 1024 && result.length + names.length <= 1024, 'input file count');
  for (const name of names) {
    requireThat(/^[A-Za-z0-9._-]+$/.test(name) && name !== '.' && name !== '..' && (!name.startsWith('.') || name === '.explorer-build.json'), 'unsafe input name');
    const rel = relative ? `${relative}/${name}` : name;
    const item = fs.lstatSync(path.join(root, rel));
    requireThat(!item.isSymbolicLink(), 'input symlink');
    if (item.isDirectory()) walk(root, rel, result);
    else { requireThat(item.isFile() && item.nlink === 1, 'unsafe input file'); result.push(rel); }
  }
  return result;
}
function runtime(root) {
  const pkg = JSON.parse(regular(path.join(root, 'package.json')).toString('utf8'));
  const actualNode = process.versions.node;
  const npm = spawnSync('npm', ['--version'], { cwd: root, encoding: 'utf8', timeout: 10000, maxBuffer: 1024, shell: false });
  requireThat(npm.status === 0 && !npm.error, 'npm version unavailable');
  const actualNpm = npm.stdout.trim();
  requireThat(actualNode === '25.9.0' && pkg.engines.node === actualNode && pkg.packageManager === `npm@${actualNpm}` && /^\d+\.\d+\.\d+$/.test(actualNpm), 'toolchain version mismatch');
  for (const [name, version] of [['typescript', '7.0.2'], ['vite', '8.3.0'], ['cytoscape', '3.34.3']]) {
    const installed = JSON.parse(regular(path.join(root, 'node_modules', name, 'package.json')).toString('utf8'));
    requireThat(installed.version === version, `installed ${name} version mismatch`);
  }
  return { node: actualNode, npm: actualNpm };
}
function schemaPath(root) {
  if (process.env.EXPLORER_SCHEMA) return path.resolve(process.env.EXPLORER_SCHEMA);
  const candidates = [path.resolve(root, '../../../ONTOLOGY-depo/schema/explorer-v1.json'), path.resolve(root, '../../../../reference-assets/ONTOLOGY-depo/schema/explorer-v1.json')];
  const found = candidates.filter(p => fs.existsSync(p));
  requireThat(found.length === 1, 'set EXPLORER_SCHEMA to the exact selected schema');
  return found[0];
}
export function buildInputs(root) {
  root = path.resolve(root);
  const toolchain = runtime(root);
  const fixed = ['index.html', 'package.json', 'package-lock.json', 'THIRD_PARTY_NOTICES.md', 'vite.config.ts', 'tsconfig.json', 'BUILD.md', 'scripts/package-runtime.mjs'];
  const authored = walk(path.join(root, 'src')).map(p => `src/${p}`);
  requireThat(authored.every(p => /\.(ts|css|html|json)$/.test(p)), 'unsupported authored source');
  const files = [...fixed, ...authored].sort().map(p => { const b = regular(path.join(root, p)); return { path: p, bytes: b.length, sha256: sha(b) }; });
  const schema = regular(schemaPath(root));
  const helper = regular(path.resolve(root, '../scripts/ontology_explorer_assets.py'));
  files.push({ path: '$schema/explorer-v1.json', bytes: schema.length, sha256: sha(schema) }, { path: '$tooling/ontology_explorer_assets.py', bytes: helper.length, sha256: sha(helper) });
  files.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
  requireThat(files.reduce((n, f) => n + f.bytes, 0) <= 67108864, 'build source byte limit');
  const record = { domain: 'sys4ai-explorer-sources-v1', files, toolchain };
  const source_digest = sha(canonicalBytes(record));
  const lock_sha256 = files.find(f => f.path === 'package-lock.json').sha256;
  const notices_sha256 = files.find(f => f.path === 'THIRD_PARTY_NOTICES.md').sha256;
  const schema_sha256 = sha(schema);
  const identity = { domain: 'sys4ai-explorer-build-v1', source_digest, lock_sha256, notices_sha256, node: '25.9.0', npm: toolchain.npm, api_version: 1, schema_sha256 };
  return { record, source_digest, lock_sha256, notices_sha256, schema_sha256, toolchain, build_id: sha(canonicalBytes(identity)) };
}
export function prepareBuild(root) {
  const inputs = buildInputs(root);
  return {
    inputs,
    define: { 'import.meta.env.EXPLORER_BUILD_ID': JSON.stringify(inputs.build_id), 'import.meta.env.EXPLORER_SCHEMA_SHA256': JSON.stringify(inputs.schema_sha256) },
    plugin: {
      name: 'explorer-reviewed-build-inputs',
      buildStart() {
        requireThat(buildInputs(root).source_digest === inputs.source_digest, 'source changed before build');
      },
      writeBundle() {
        requireThat(buildInputs(root).source_digest === inputs.source_digest, 'source changed during build');
        const dist = path.join(root, 'dist');
        const outputs = walk(dist).filter(p => p !== '.explorer-build.json').map(p => {
          const bytes = regular(path.join(dist, p));
          return { path: p, bytes: bytes.length, sha256: sha(bytes) };
        });
        fs.writeFileSync(path.join(dist, '.explorer-build.json'), canonicalBytes({ inputs, outputs }), { flag: 'wx', mode: 0o600 });
      },
    },
  };
}

// Node has no dir_fd/openat API. This fixed Python 3.12 body is build-only,
// invoked with no shell and bounded JSON data. It never accepts caller code.
// The runtime helper imports no publication code and exposes no write entry.
const PUBLISH_PYTHON = String.raw`
import json,os,stat,sys,uuid,hashlib,types
from pathlib import Path
assert sys.version_info[:2]==(3,12), 'Python 3.12 required'
payload=json.loads(sys.stdin.buffer.read(131073))
assert set(payload)=={'stage','destination','helper','helper_sha256','schema','old_manifest_sha256'}
# Verify the exact selected helper bytes before executing them. Neither a changed
# helper nor a symlink inserted after JS source hashing becomes build-time code.
hp=Path(payload['helper']).absolute()
hd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
try:
 for part in hp.parts[1:-1]:
  assert part not in ('.','..')
  nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=hd)
  os.close(hd);hd=nxt
 hf=os.open(hp.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=hd)
 try:
  hs=os.fstat(hf)
  assert stat.S_ISREG(hs.st_mode) and hs.st_nlink==1 and 0<hs.st_size<=2000000
  parts=[];remaining=2000001
  while remaining:
   block=os.read(hf,min(remaining,65536))
   if not block:break
   parts.append(block);remaining-=len(block)
  hb=b''.join(parts)
  assert len(hb)==hs.st_size and hashlib.sha256(hb).hexdigest()==payload['helper_sha256']
 finally:os.close(hf)
finally:os.close(hd)
a=types.ModuleType('explorer_asset_validation');a.__file__=str(hp)
sys.modules[a.__name__]=a;exec(compile(hb,str(hp),'exec'),a.__dict__)
new=a.load_assets(payload['stage'],schema_sha256=payload['schema'])
dest=Path(payload['destination']).absolute()
parent=a.directory_fd(dest.parent)
try:
 try: os.mkdir(dest.name,0o755,dir_fd=parent)
 except FileExistsError: pass
 root=os.open(dest.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
finally: os.close(parent)
created=[]
staged=[]
def digest(b):return hashlib.sha256(b).hexdigest()
def subdir(rel,create=False):
 fd=os.dup(root)
 try:
  for part in rel.split('/')[:-1]:
   if create:
    try:os.mkdir(part,0o755,dir_fd=fd)
    except FileExistsError:pass
   nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
   os.close(fd);fd=nxt
  return fd
 except BaseException:os.close(fd);raise
def write_temp(relative,data):
 fd=subdir(relative,True);name='.explorer-publish-'+uuid.uuid4().hex
 try:out=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644,dir_fd=fd)
 except BaseException:os.close(fd);raise
 staged.append((fd,name,relative,data))
 try:
  view=memoryview(data)
  while view:
   n=os.write(out,view)
   if n<=0:raise OSError('short output write')
   view=view[n:]
  os.fsync(out)
 finally:os.close(out)
def unchanged(relative,member):
 data=a._read_at(root,relative,member['bytes'])
 if len(data)!=member['bytes'] or digest(data)!=member['sha256']:raise ValueError('owned output changed')
def current_manifest():
 try:return a._read_at(root,'manifest.json',a.MAX_MANIFEST_BYTES)
 except FileNotFoundError:return None
try:
 oldraw=current_manifest()
 expected=payload['old_manifest_sha256']
 if (digest(oldraw) if oldraw else None)!=expected:raise ValueError('reviewed output manifest changed')
 old=a.load_assets(dest) if oldraw else None
 oldmembers=dict(old.members) if old else {}
 # Refuse every collision outside the exact prior validated inventory.
 for rel,m in new.members.items():
  try:
   fd=subdir(rel)
   try:present=os.stat(rel.split('/')[-1],dir_fd=fd,follow_symlinks=False)
   finally:os.close(fd)
  except FileNotFoundError:present=None
  if present is not None and rel not in oldmembers:raise ValueError('unowned output collision')
  if rel in oldmembers:unchanged(rel,oldmembers[rel])
 for rel,m in oldmembers.items():unchanged(rel,m)
 # Every byte is staged and validated before changing a manifested target.
 for rel,m in new.members.items():
  data,mime=new.read('/'+rel);write_temp(rel,data)
 write_temp('manifest.json',new.manifest_bytes)
 if current_manifest()!=oldraw:raise ValueError('manifest changed before publication')
 if old: a.load_assets(dest)
 if (os.fstat(root).st_dev,os.fstat(root).st_ino)!=(os.stat(dest,follow_symlinks=False).st_dev,os.stat(dest,follow_symlinks=False).st_ino):raise ValueError('output directory replaced')
 # The final staged item is the manifest. An interrupted publication remains
 # fail-closed; an old manifest cannot authenticate partial/new output bytes.
 for fd,temp,rel,data in staged[:-1]:
  if rel in oldmembers:unchanged(rel,oldmembers[rel])
  else:
   try:os.stat(rel.split('/')[-1],dir_fd=fd,follow_symlinks=False)
   except FileNotFoundError:pass
   else:raise ValueError('new unowned collision')
  os.replace(temp,rel.split('/')[-1],src_dir_fd=fd,dst_dir_fd=fd);os.fsync(fd)
 for rel,m in oldmembers.items():
  if rel not in new.members:
   unchanged(rel,m);fd=subdir(rel)
   try:os.unlink(rel.split('/')[-1],dir_fd=fd);os.fsync(fd)
   finally:os.close(fd)
 fd,temp,rel,data=staged[-1]
 if current_manifest()!=oldraw:raise ValueError('manifest changed before commit')
 os.replace(temp,'manifest.json',src_dir_fd=fd,dst_dir_fd=fd);os.fsync(fd)
 final=a.load_assets(dest,schema_sha256=payload['schema'])
 print(json.dumps({'status':'published','manifest_sha256':final.manifest_sha256,'build_id':final.manifest['build_id'],'assets':len(final.members),'removed':sorted(set(oldmembers)-set(new.members))}))
finally:
 for fd,temp,rel,data in staged:
  try:os.unlink(temp,dir_fd=fd)
  except FileNotFoundError:pass
  os.close(fd)
 os.close(root)
`;

export function publishRuntime(root) {
  root = path.resolve(root);
  const inputs = buildInputs(root);
  const dist = path.join(root, 'dist'), dest = path.join(root, 'assets');
  const record = JSON.parse(regular(path.join(dist, '.explorer-build.json'), 131072).toString('utf8'));
  requireThat(canonicalBytes(record.inputs).equals(canonicalBytes(inputs)), 'stale build: inputs changed since production build');
  const names = walk(dist).filter(p => p !== '.explorer-build.json');
  requireThat(names.length > 0 && names.length <= MAX_FILES, 'asset count');
  let total = 0;
  const files = names.map(p => {
    requireThat(p.length <= 240 && /^[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)*$/.test(p), 'unsafe output path');
    const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' }[path.extname(p)];
    requireThat(mime, 'unsupported output file');
    const size = fs.lstatSync(path.join(dist, p)).size;
    requireThat(size > 0 && size <= MAX_FILE && (total += size) <= MAX_TOTAL, 'asset aggregate bytes');
    const bytes = regular(path.join(dist, p));
    return { path: p, bytes, mime };
  });
  requireThat(files.reduce((n, f) => n + f.bytes.length, 0) <= MAX_TOTAL, 'asset aggregate bytes');
  requireThat(canonicalBytes(record.outputs).equals(canonicalBytes(files.map(f => ({ path: f.path, bytes: f.bytes.length, sha256: sha(f.bytes) })))), 'stale or tampered production output');
  const html = files.filter(f => f.mime === 'text/html');
  requireThat(html.length === 1 && html[0].path === 'index.html', 'one index.html required');
  const manifest = { schema_version: 1, api_version: 1, build_id: inputs.build_id, entry: html[0].path, assets: files.map(f => ({ path: f.path, sha256: sha(f.bytes), bytes: f.bytes.length, mime: f.mime })), source_digest: inputs.source_digest, lock_sha256: inputs.lock_sha256, notices_sha256: inputs.notices_sha256, toolchain: inputs.toolchain, build_command: 'npm run build && npm run package:runtime' };
  const raw = canonicalBytes(manifest);
  requireThat(raw.length <= 131072, 'manifest bytes');
  // Parse the actual production JS with the pinned build parser. This is an
  // additional syntax gate; runtime closure validation stays standard-library.
  for (const file of files.filter(f => f.mime === 'text/javascript')) {
    const parsed = parseSync(file.path, file.bytes.toString('utf8'), { sourceType: 'module' });
    requireThat(parsed.errors.length === 0, 'invalid production JavaScript');
    const queue = [parsed.program];
    while (queue.length) {
      const item = queue.pop();
      if (!item || typeof item !== 'object') continue;
      if (item.type === 'ImportExpression') requireThat(((item.source?.type === 'Literal' && typeof item.source.value === 'string') || (item.source?.type === 'TemplateLiteral' && item.source.expressions.length === 0)), 'computed production import');
      for (const value of Object.values(item)) {
        if (Array.isArray(value)) queue.push(...value);
        else if (value && typeof value === 'object') queue.push(value);
      }
    }
  }
  const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'sys4ai-explorer-package-'));
  fs.chmodSync(stage, 0o700);
  try {
    for (const file of files) {
      const target = path.join(stage, file.path);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, file.bytes, { flag: 'wx', mode: 0o644 });
    }
    fs.writeFileSync(path.join(stage, 'manifest.json'), raw, { flag: 'wx', mode: 0o644 });
    requireThat(buildInputs(root).source_digest === inputs.source_digest, 'source changed while staging');
    let oldHash = null;
    try { oldHash = sha(regular(path.join(dest, 'manifest.json'), 131072)); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    const python = process.env.EXPLORER_PYTHON || 'python3';
    const payload = { stage: fs.realpathSync(stage), destination: dest, helper: path.resolve(root, '../scripts/ontology_explorer_assets.py'), helper_sha256: inputs.record.files.find(f => f.path === '$tooling/ontology_explorer_assets.py').sha256, schema: inputs.schema_sha256, old_manifest_sha256: oldHash };
    const result = spawnSync(python, ['-I', '-B', '-c', PUBLISH_PYTHON], { input: JSON.stringify(payload), encoding: 'utf8', shell: false, timeout: 30000, maxBuffer: 65536, env: { PATH: process.env.PATH, PYTHONDONTWRITEBYTECODE: '1' } });
    requireThat(!result.error && result.status === 0, `package validation/publication failed: ${result.stderr?.slice(-3000) || result.error?.message || result.status}`);
    return JSON.parse(result.stdout);
  } finally { fs.rmSync(stage, { recursive: true, force: true }); }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    requireThat(process.argv.length === 2, 'package publisher accepts no positional arguments');
    process.stdout.write(JSON.stringify(publishRuntime(process.cwd())) + '\n');
  } catch (error) {
    process.stderr.write(`Explorer package failed: ${error.message}\n`);
    process.exitCode = 1;
  }
}
