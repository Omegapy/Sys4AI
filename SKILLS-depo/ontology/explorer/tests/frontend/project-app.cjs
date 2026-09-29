// Focused Project-app guards. Run with the prepared Node runtime; no build or install.
// node --experimental-transform-types tests/frontend/project-app.cjs
const assert=require('node:assert/strict');
const {registerHooks}=require('node:module');
const {pathToFileURL}=require('node:url');
const path=require('node:path');
registerHooks({resolve(specifier,context,next){
  if(specifier.startsWith('.')&&!path.extname(specifier))return next(specifier+'.ts',context);
  return next(specifier,context);
}});
const source=path.resolve(__dirname,'../../src');
const json=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
const session={schema_version:1,status:'connected',csrf:Buffer.alloc(32,1).toString('base64url'),session_scope:'a'.repeat(32),service_instance:'b'.repeat(32),code_epoch:'c'.repeat(64),build_id:'d'.repeat(64),schema_sha256:'e'.repeat(64)};
const envelope=(data={})=>({schema_version:1,operation:'context',status:'ready',project_id:'fixture-alpha',observed_at:'2026-09-29T00:00:00Z',issues:[],...data});
function delayed(){let resolve;return {promise:new Promise(done=>resolve=done),resolve:value=>resolve(value)};}
(async()=>{
  const {ProjectClient,captureProjectFragment,appHash,parseAppRoute}=await import(pathToFileURL(path.join(source,'project-api.ts')));
  let replaced;
  global.location={pathname:'/',hash:'#bootstrap='+session.csrf+'&route='+encodeURIComponent('#/app/home')};
  global.history={replaceState:(state,unused,url)=>replaced={state,url}};
  const fragment=captureProjectFragment();assert.equal(fragment.bootstrap,session.csrf);assert.deepEqual(replaced,{state:null,url:'/?app=1#/app/home'});
  assert.equal(parseAppRoute('#/app/task'),null);assert.equal(parseAppRoute('#/app/home/path'),null);
  assert.equal(parseAppRoute(appHash('search','','<literal>')).query,'<literal>');

  // App connection does not fetch ontology context. A canceled source may
  // finish at the network layer but cannot be returned for display.
  let calls=[];global.fetch=async(url,options)=>{calls.push(url);return json(session);};
  const client=new ProjectClient(session.build_id,session.schema_sha256,()=>{});
  assert.equal(await client.connect({bootstrap:session.csrf,desired:'',invalid:false}),true);
  assert.deepEqual(calls,['/api/explorer/v1/session']);
  global.fetch=async()=>json(envelope({identity:{id:'fixture-alpha',name:'Fixture'}}));
  assert.ok(await client.read('context'));
  const late=delayed();global.fetch=()=>late.promise;
  const pending=client.read('source',{source_id:'old'});client.invalidate();
  global.fetch=async()=>json(envelope({operation:'source',text:'current'}));
  assert.equal((await client.read('source',{source_id:'new'})).text,'current');
  late.resolve(json(envelope({operation:'source',text:'obsolete'})));assert.equal(await pending,null);
  global.fetch=async()=>json(envelope({operation:'work',text:'wrong operation'}));assert.equal(await client.read('source',{source_id:'new'}),null);

  // A source response cannot reconnect a reading session after Stop app.
  const afterStop=delayed();global.fetch=url=>url==='/api/project/v1/stop'?Promise.resolve(json({schema_version:1,status:'stopping',stopped:true})):afterStop.promise;
  const revoked=client.read('home');await client.end(true);afterStop.resolve(json(envelope({operation:'home',text:'revoked'})));
  assert.equal(await revoked,null);assert.equal(client.connected,false);assert.match(client.message,/accepted/);

  // Source bytes render only as text and copied logical references do not
  // contain the opaque server handle or a launch/session credential.
  class Node{
    constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.handlers={};}
    append(...children){this.children.push(...children);}
    addEventListener(name,callback){this.handlers[name]=callback;}
    set innerHTML(value){throw new Error('Unsafe HTML insertion');}
  }
  global.document={createElement:tag=>new Node(tag)};
  const {sourceView}=await import(pathToFileURL(path.join(source,'project-views.ts')));
  let copied='';const raw='<img src=x onerror=alert(1)>';
  const view=sourceView(envelope({title:'Fixture source',text:raw,path:'README.md',owner:'documents',sha256:'f'.repeat(64)}),'opaque-handle',{projectId:'fixture-alpha',link:(label,hash)=>{const node=new Node('a');node.textContent=label;node.href=hash;return node;},copy:value=>copied=value});
  const nodes=[];function walk(node){nodes.push(node);node.children.forEach(walk);}walk(view);
  assert.ok(nodes.some(node=>node.tag==='pre'&&node.textContent===raw));assert.ok(!nodes.some(node=>node.tag==='img'));
  nodes.find(node=>node.textContent==='Copy source reference').handlers.click();assert.equal(copied,'fixture-alpha:documents:README.md');
  console.log(JSON.stringify({status:'passed',checks:['synchronous credential scrub and bounded routes','independent primary session','late source invalidation','stop invalidation','safe source text and logical copy']},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
