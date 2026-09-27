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
 const context={atob,btoa,AbortController,TextEncoder,TextDecoder,URL,URLSearchParams,Uint8Array,ArrayBuffer,structuredClone,crypto:crypto.webcrypto,
   setTimeout,clearTimeout,location,
   history:{replaceState(_s,_title,url){events.push({kind:'replace',url});location.hash=url.slice(pathname.length);}},
   document:{getElementById(id){if(!nodes.has(id))nodes.set(id,{hidden:true,textContent:'',addEventListener(){},replaceChildren(){}});return nodes.get(id);},createElement(){return {textContent:''};}},
   fetch(url,options){events.push({kind:'fetch',url,options});return new Promise(()=>{});}
 };
 context.window=context;context.addEventListener=()=>{};
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


const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'bootstrap-context-fixture.json'),'utf8'));
const flush=async()=>{for(let i=0;i<8;i++)await new Promise(resolve=>setTimeout(resolve,5));};
function environment(){
 const events=[],calls=[],nodes=new Map(),listeners=new Map();let timer=0;
 const location={hash:'#bootstrap='+crypto.randomBytes(32).toString('base64url'),pathname:'/'};
 const context={atob,btoa,AbortController,TextEncoder,TextDecoder,Uint8Array,ArrayBuffer,URL,URLSearchParams,structuredClone,crypto:crypto.webcrypto,location,
  setTimeout(){return ++timer;},clearTimeout(){},
  history:{replaceState(_s,_t,url){events.push('replace');location.hash=url.slice(1);}},
  document:{getElementById(id){if(!nodes.has(id))nodes.set(id,{hidden:true,textContent:'',children:[],addEventListener(){},replaceChildren(...items){this.children=items;}});return nodes.get(id);},createElement(){return {textContent:''};}},
  fetch(url,options){events.push('fetch');return new Promise(resolve=>calls.push({url,options,resolve}));},
  addEventListener(name,fn){listeners.set(name,fn);}
 };
 context.window=context;vm.runInNewContext(source,context,{timeout:1500});
 return {events,calls,nodes,context,hashchange(){location.hash='#bootstrap='+crypto.randomBytes(32).toString('base64url');listeners.get('hashchange')();}};
}
function session(scope){return {schema_version:1,status:'connected',csrf:crypto.randomBytes(32).toString('base64url'),session_scope:scope.repeat(32),expires_in:900,
 service_instance:fixture.service_instance,code_epoch:fixture.code_epoch,build_id:manifest.build_id,schema_sha256:fixture.data.service.schema_sha256};}
function contextReply(scope,name){const copy=structuredClone(fixture);copy.session_scope=scope.repeat(32);copy.data.project.name=name;return copy;}
function respond(call,value){call.resolve(new Response(JSON.stringify(value),{status:200,headers:{'content-length':String(Buffer.byteLength(JSON.stringify(value)))}}));}
(async()=>{
 for(const priorStage of ['session','context']){
  const env=environment();const oldSession=env.calls[0];let oldContext;
  if(priorStage==='context'){respond(oldSession,session('a'));await flush();oldContext=env.calls[1];assert.ok(oldContext?.url.endsWith('/context'));}
  const before=env.events.length;env.hashchange();assert.ok(env.events[before]==='replace'&&env.events[before+1]==='fetch','same-document cleanup order');
  assert.ok(!env.context.location.hash.includes('bootstrap='),'same-document fragment cleared');
  const fresh=env.calls.at(-1);respond(fresh,session('b'));await flush();
  const current=env.calls.at(-1);assert.ok(current.url.endsWith('/context'));respond(current,contextReply('b','Current connection'));await flush();
  assert.ok(env.nodes.get('reading').children[0]?.textContent==='Current connection','fresh context rendered');
  const count=env.calls.length;
  if(priorStage==='session')respond(oldSession,session('a'));else respond(oldContext,contextReply('a','Superseded connection'));
  await flush();assert.ok(env.calls.length===count&&env.nodes.get('reading').children[0]?.textContent==='Current connection','late response cannot resurrect old connection');
  reports.push({case:'same_document_late_'+priorStage,passed:true,clean_before_network:true,old_response_ignored:true});
 }
 console.log(JSON.stringify({status:'passed',asset_sha256:entry.sha256,cases:reports,
  qualification:'Actual built JavaScript with instrumented browser boundaries and intentionally abort-insensitive deferred responses. No claim of real browser history, HTTP authentication, accessibility or full UI.'}));
})().catch(error=>{console.error(error);process.exitCode=1;});
