// Execute the actual production bundle with instrumented browser boundaries.
// This proves synchronous bootstrap removal order; browser UX remains separate.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(process.argv[2]);
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
const entry=manifest.assets.find(a=>a.mime==='text/javascript');assert.ok(entry);
const source=fs.readFileSync(path.join(root,entry.path),'utf8');
assert.ok(crypto.createHash('sha256').update(source).digest('hex')===entry.sha256);
const token=crypto.randomBytes(32).toString('base64url');
const safe='#/p/fixture/entry/'+encodeURIComponent('urn:sys4ai:ontology:project:fixture:Example');
const cases=[
 ['bootstrap','#bootstrap='+token,'',true],
 ['desired','#bootstrap='+token+'&route='+encodeURIComponent(safe),safe,true],
 ['nested','#bootstrap='+token+'&route='+encodeURIComponent(safe),safe,true],
 ['resume',safe,safe,true],
 ['duplicate','#bootstrap='+token+'&bootstrap='+token,'',false],
 ['unknown','#bootstrap='+token+'&other=value','',false],
 ['external-route','#bootstrap='+token+'&route='+encodeURIComponent('https://outside.invalid'),' ',false],
 ['bad-token','#bootstrap=invalid','',false],
 ['query-credential','#/p/fixture/overview?bootstrap=hidden','',false],
];
const reports=[];
for(const [name,hash,clean,fetchExpected] of cases){
 const events=[],nodes=new Map();const pathname=name==='nested'?'/nested/page.html':'/';
 const location={hash,pathname};
 const context={atob,btoa,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,ArrayBuffer,structuredClone,crypto:crypto.webcrypto,
   setTimeout,clearTimeout,location,
   history:{replaceState(_s,_title,url){events.push({kind:'replace',url});location.hash=url.slice(pathname.length);}},
   document:{getElementById(id){if(!nodes.has(id))nodes.set(id,{hidden:true,textContent:'',addEventListener(){},replaceChildren(){}});return nodes.get(id);},createElement(){return {textContent:''};}},
   fetch(url,options){events.push({kind:'fetch',url,options});return new Promise(()=>{});}
 };
 vm.runInNewContext(source,context,{timeout:1500});
 assert.ok(events[0]?.kind==='replace',name+': first effect');
 assert.ok(!events[0].url.includes('bootstrap')&&!events[0].url.includes(token),name+': clean history');
 if(clean.trim())assert.ok(events[0].url===pathname+clean,name+': desired route preserved');
 const calls=events.filter(e=>e.kind==='fetch');assert.ok(calls.length===(fetchExpected?1:0),name+': admission');
 if(fetchExpected){
   assert.ok(events.indexOf(calls[0])>0,name+': removal precedes first network call');
   assert.ok(!calls[0].url.includes(token),name+': credentials absent from request URL');
   assert.ok(calls[0].options.redirect==='error'&&calls[0].options.credentials==='same-origin',name+': transport');
   const body=JSON.parse(calls[0].options.body);
   assert.ok(body.client_build_id===manifest.build_id,name+': compiled build identity');
   if(name!=='resume')assert.ok(body.bootstrap===token,name+': private exchange only');
 }
 reports.push({case:name,passed:true,clean_before_network:true});
}
console.log(JSON.stringify({status:'passed',asset_sha256:entry.sha256,cases:reports,qualification:'Actual built JavaScript with instrumented browser boundaries. No claim of real browser history, DOM accessibility or full reader UI.'}));
