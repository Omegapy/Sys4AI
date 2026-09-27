// Read-only compression baseline; execute only after the original TASK024 gate.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),zlib=require('node:zlib');
const assets=path.join(__dirname,'SKILLS-depo/ontology/explorer/assets');
const manifest=JSON.parse(fs.readFileSync(path.join(assets,'manifest.json'),'utf8'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const rows=[];
for(const member of manifest.assets){
 const file=path.join(assets,member.path);if(path.relative(assets,file).startsWith('..'))throw new Error('asset_confinement');
 const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let raw;try{const s=fs.fstatSync(fd);if(!s.isFile()||s.nlink!==1||s.size!==member.bytes)throw new Error('asset_shape');raw=fs.readFileSync(fd);}finally{fs.closeSync(fd);}
 if(sha(raw)!==member.sha256)throw new Error('asset_digest');
 rows.push({group:member.path.includes('cytoscape.esm-')?'vendor':'application',path:member.path,sha256:member.sha256,raw_bytes:raw.length,gzip_bytes:zlib.gzipSync(raw,{level:9}).length,brotli_bytes:zlib.brotliCompressSync(raw,{params:{[zlib.constants.BROTLI_PARAM_QUALITY]:11,[zlib.constants.BROTLI_PARAM_MODE]:zlib.constants.BROTLI_MODE_GENERIC}}).length});
}
if(rows.length!==5||rows.filter(r=>r.group==='vendor').length!==1)throw new Error('runtime_member_inventory');
const groups=Object.fromEntries(['vendor','application'].map(group=>[group,Object.fromEntries(['raw_bytes','gzip_bytes','brotli_bytes'].map(k=>[k,rows.filter(r=>r.group===group).reduce((n,r)=>n+r[k],0)]))]));
console.log(JSON.stringify({groups,status:'passed',build_id:manifest.build_id,node:process.version,zlib:process.versions.zlib,brotli:process.versions.brotli,settings:{gzip_level:9,brotli_quality:11,brotli_mode:'generic'},members:rows,totals:{raw_bytes:rows.reduce((n,r)=>n+r.raw_bytes,0),gzip_bytes:rows.reduce((n,r)=>n+r.gzip_bytes,0),brotli_bytes:rows.reduce((n,r)=>n+r.brotli_bytes,0)},qualification:'Measured compressed sizes of exact raw runtime files, including separate vendor member. A regression baseline, not a claim the local HTTP server applies these encodings.'}));
