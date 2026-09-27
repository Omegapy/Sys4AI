// Prepared browser timing driver. Execution remains behind TASK023 and a
// manager-reviewed frozen runtime binding. Instrumentation changes no product files.
const fs=require('node:fs'),crypto=require('node:crypto'),zlib=require('node:zlib');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const executable='/Users/alex.omegapy/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell';
let browser,context,page,phase='private',errors=0,remote=0,asyncFailures=0,metrics=[],report;
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
process.on('unhandledRejection',()=>{asyncFailures++;process.exitCode=1;});
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{
try{
 const fd=fs.openSync(meta.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let launch;
 try{const s=fs.fstatSync(fd);need(s.isFile()&&s.nlink===1&&s.size<=8192&&(s.mode&0o777)===0o600,'private_file');launch=JSON.parse(fs.readFileSync(fd,'utf8')).url;}finally{fs.closeSync(fd);}
 const u=new URL(launch);need(u.origin===meta.origin&&!u.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(u.hash),'private_url');
 const nodeStart=performance.now();browser=await chromium.launch({executablePath:executable,headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});need(browser.version()==='151.0.7922.34','runtime_version');
 const browserReady=performance.now();context=await browser.newContext({viewport:{width:1360,height:900}});await context.route('**/*',r=>{if(new URL(r.request().url()).origin!==meta.origin){remote++;return r.abort();}return r.continue();});page=await context.newPage();page.setDefaultTimeout(12000);page.on('pageerror',()=>errors++);
 const navigationStart=performance.now();await page.goto(launch,{waitUntil:'domcontentloaded',timeout:20000});launch=null;await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:meta.project_name,exact:true}).waitFor();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const firstReadable=performance.now();console.log(JSON.stringify({event:'first_readable',node_to_first_readable_ms:firstReadable-nodeStart,browser_launch_ms:browserReady-nodeStart,navigation_to_first_readable_ms:firstReadable-navigationStart}));
 const id=n=>'urn:sys4ai:ontology:project:'+meta.project_id+':entry-'+String(n).padStart(5,'0');
 async function timed(mode,wanted,action){
  phase='timing_'+mode;await page.evaluate(({mode,wanted})=>{
   const oldList=document.querySelector('.results'),oldEntry=document.querySelector('.entry-host>.entry:not([hidden])'),oldCy=document.querySelector('.map-canvas')?._cyreg?.cy;
   const state={start:null,end:null,failed:false,same_renderer:null,actual_nodes:null,actual_edges:null};window.__qualificationTiming=state;let done=false,frame,deadline;
   const finish=()=>{if(done)return;done=true;cancelAnimationFrame(frame);clearTimeout(deadline);requestAnimationFrame(()=>requestAnimationFrame(()=>{state.end=performance.now();}));};
   const test=()=>{
    if(state.start!==null){let ready=false;
     if(mode==='search'){const list=document.querySelector('.results');ready=list!==oldList&&list?.querySelector('a')?.textContent===wanted&&!document.querySelector('#read-status .loading');}
     if(mode==='entry'){const entry=document.querySelector('.entry-host>.entry:not([hidden])');ready=entry!==oldEntry&&entry?.querySelector('h2')?.textContent===wanted&&!!entry.querySelector('.exact-text')&&!document.querySelector('#read-status .loading');}
     if(mode==='map'){const cy=document.querySelector('.map-canvas')?._cyreg?.cy;ready=!!cy&&cy.nodes().length>0&&!document.querySelector('#read-status .loading');if(ready){state.actual_nodes=cy.nodes().length;state.actual_edges=cy.edges().length;}}
     if(mode==='selection'){const cy=document.querySelector('.map-canvas')?._cyreg?.cy;state.same_renderer=cy===oldCy;ready=!!cy&&cy.getElementById('node:'+wanted).hasClass('selected');}
     if(ready){finish();return;}
    }frame=requestAnimationFrame(test);
   };
   document.addEventListener(mode==='search'?'submit':'click',()=>{state.start=performance.now();},{once:true,capture:true});frame=requestAnimationFrame(test);deadline=setTimeout(()=>{done=true;cancelAnimationFrame(frame);state.failed=true;},10000);
  },{mode,wanted});
  await action();await page.waitForFunction(()=>window.__qualificationTiming?.end!==null||window.__qualificationTiming?.failed);const sample=await page.evaluate(()=>window.__qualificationTiming);need(!sample.failed&&sample.start!==null&&sample.end!==null,'timed_state_complete');if(mode==='selection')need(sample.same_renderer,'selection_renderer_retained');metrics.push({mode,elapsed_ms:sample.end-sample.start,actual_nodes:sample.actual_nodes,actual_edges:sample.actual_edges,same_renderer:sample.same_renderer});
 }
 // Four samples per fresh browser; outer runner requests five trials =>20 warm samples.
 for(let i=0;i<4;i++){
  const wanted=i%2?'FixtureTaskManager':'Alignment',query=i%2?'FixtureTaskManager':'Orientation';const search=page.getByRole('combobox',{name:'Search project knowledge',exact:true});await search.fill(query);await search.press('Escape');
  await timed('search',wanted,()=>search.press('Enter'));await timed('entry',wanted,()=>page.locator('.results>li>a').first().click());
 }
 // Establish default Map preference once, then time an actual fresh focus read.
 await page.goto(meta.origin+'/#/p/'+meta.project_id+'/entry/'+encodeURIComponent(id(0)),{waitUntil:'domcontentloaded'});await page.locator('.entry-host>.entry:not([hidden]) .exact-text').waitFor();await page.getByRole('button',{name:'View on map',exact:true}).click();await page.getByRole('button',{name:'Map',exact:true}).click();await page.waitForFunction(()=>!!document.querySelector('.map-canvas')?._cyreg?.cy);
 await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link',{name:'Overview',exact:true}).click();await page.goto(meta.origin+'/#/p/'+meta.project_id+'/entry/'+encodeURIComponent(id(0)),{waitUntil:'domcontentloaded'});await page.locator('.entry-host>.entry:not([hidden]) .exact-text').waitFor();await timed('map',null,()=>page.getByRole('button',{name:'View on map',exact:true}).click());
 await page.getByRole('button',{name:'List',exact:true}).click();
 for(let i=0;i<4;i++){const ident=id(i%2?0:2);const target=page.locator('.node-list>li[data-node-id='+JSON.stringify(ident)+']').getByRole('button',{name:i%2?'Alignment':'FixtureTaskManager',exact:true});await timed('selection',ident,()=>target.click());await page.locator('.entry-host>.entry:not([hidden]) .exact-text').waitFor();}
 let continuation=null;
 if(meta.run_fault_observation){
  phase='bounded_continuation_cancellation';await page.evaluate(()=>{const original=window.fetch;window.__qContinuation={held:false,released:false};window.fetch=async(input,options)=>{if(String(input).endsWith('/relationships')&&!window.__qContinuation.held){window.__qContinuation.held=true;const copy={...options};delete copy.signal;const response=await original(input,copy);await new Promise(resolve=>window.__qContinuation.release=resolve);window.__qContinuation.released=true;return response;}return original(input,options);};});
  const beforeIds=await page.locator('.relationship-rows>li').evaluateAll(nodes=>nodes.map(n=>n.dataset.relationId));await page.locator('.node-list>li[data-node-id='+JSON.stringify(id(2))+']').getByRole('button',{name:'More connections',exact:true}).click();await page.waitForFunction(()=>typeof window.__qContinuation?.release==='function');need(await page.locator('#read-status .loading').count()>0,'visible_pending_connections');need(JSON.stringify(await page.locator('.relationship-rows>li').evaluateAll(nodes=>nodes.map(n=>n.dataset.relationId)))===JSON.stringify(beforeIds),'existing_view_usable_while_pending');
  const start=performance.now();await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link',{name:'Overview',exact:true}).click();await page.getByRole('heading',{name:meta.project_name,exact:true}).waitFor();const route=page.url();await page.evaluate(()=>window.__qContinuation.release());await page.waitForFunction(()=>window.__qContinuation.released);await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));need(page.url()===route&&await page.getByRole('heading',{name:meta.project_name,exact:true}).isVisible(),'late_connection_cannot_restore_old_view');continuation={real_response_held:true,abort_ignored_intentionally:true,old_rows_retained:true,visible_pending:true,actual_navigation_cancels_view:true,cancellation_and_late_release_observation_ms:performance.now()-start};
 }
 need(metrics.filter(x=>x.mode==='search').length===4&&metrics.filter(x=>x.mode==='entry').length===4&&metrics.filter(x=>x.mode==='map').length===1&&metrics.filter(x=>x.mode==='selection').length===4,'sample_counts');need(errors===0&&remote===0,'browser_safety');report={status:'passed',browser_version:browser.version(),runtime:'Explicit test-only headless-shell1234; no Chrome154/native equivalence.',metrics,continuation,page_errors:errors,nonlocal_requests:remote,measurement_boundary:'Browser capture-phase submit/click event to matched actual rendered DOM/model plus two animation frames. Search explicitly cancels suggestion debounce before submission. Selection uses real List controls with the already-loaded identical graph renderer retained. Map reports actual returned counts under existing default budgets. Process/reader cold does not mean cold OS filesystem caches.'};
}catch(e){report={status:'failed',phase,reason:e.safeCode||'browser_operation_failed',metrics,page_errors:errors,nonlocal_requests:remote};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
await new Promise(resolve=>setImmediate(resolve));if(asyncFailures){report.status='failed';report.reason='asynchronous_test_operation';report.async_failure_count=asyncFailures;}console.log(JSON.stringify({event:'result',...report}));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({event:'result',status:'failed',phase,reason:'runner_failed'}));process.exitCode=1;});
