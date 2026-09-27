// Declared axe instrumentation; native announcements and uninstrumented CSP
// acceptance remain separate tests. This never modifies production package bytes.
const fs=require('node:fs'),crypto=require('node:crypto');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const runtime=JSON.parse(fs.readFileSync(__dirname+'/test-browser-runtime.json','utf8'));
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private',scans=[],errors=0,remote=0,asyncFailures=[];
const safeException=e=>({class:['Error','TypeError','RangeError','TimeoutError'].includes(e?.name)?e.name:'OtherError',frames:[...String(e?.stack||'').matchAll(/expiry-accessibility-browser\.cjs:(\d+):(\d+)/g)].slice(0,4).map(x=>({line:Number(x[1]),column:Number(x[2])}))});
process.on('unhandledRejection',e=>asyncFailures.push({phase,...safeException(e)}));
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const axeFile='/private/tmp/explorer-qualification-axe-4.13.0/axe.min.js';
const axeFd=fs.openSync(axeFile,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let axe;try{const st=fs.fstatSync(axeFd);need(st.isFile()&&st.nlink===1&&st.size===580491,'axe_file');axe=fs.readFileSync(axeFd,'utf8');}finally{fs.closeSync(axeFd);}need(crypto.createHash('sha256').update(axe).digest('hex')==='c24f097bd2f451d4f933e8bc7d8d539f8672a2ebcb5cc9f9f3eec8ca9470a0c1','axe_bytes');
const ns='urn:sys4ai:ontology:project:explorer-a11y:',id=n=>ns+'entry-'+String(n).padStart(5,'0');
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{let report;
try{
 const fd=fs.openSync(meta.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let launch;
 try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');launch=JSON.parse(fs.readFileSync(fd,'utf8')).url;}finally{fs.closeSync(fd);}
 const u=new URL(launch);const privateBootstrap=u.hash.slice('#bootstrap='.length);need(u.origin===meta.origin&&!u.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(u.hash),'private_url');
 browser=await chromium.launch({executablePath:runtime.executable,headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 need(browser.version()===runtime.supported_registry_entry.browserVersion,'browser_version');
 context=await browser.newContext({viewport:{width:1360,height:900}});await context.route('**/*',r=>{if(new URL(r.request().url()).origin!==meta.origin){remote++;return r.abort();}return r.continue();});
 page=await context.newPage();page.setDefaultTimeout(9000);page.on('pageerror',()=>errors++);
 const sessionResponse=page.waitForResponse(r=>r.url().endsWith('/session')&&r.status()===200);sessionResponse.catch(()=>{});
 await page.goto(launch+'&route='+encodeURIComponent(meta.desired_route),{waitUntil:'domcontentloaded',timeout:15000});launch=null;
 const session=await (await sessionResponse).json();need(typeof session.csrf==='string'&&session.csrf.length===43,'session_privacy_bound');
 const knownSecrets=[privateBootstrap,session.csrf,...(await context.cookies(meta.origin+'/api/explorer/v1/')).map(c=>c.value)];
 await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:'Explorer fixture explorer-a11y',exact:true}).waitFor();
 // DevTools evaluation is explicitly test instrumentation, not an inline script
 // exception or CSP waiver in the shipping page.
 await page.evaluate(axe);need(await page.evaluate(()=>window.axe.version)==='4.13.0','axe_version');
 async function route(destination,ident='',query=''){await page.goto(meta.origin+'/#/p/explorer-a11y/'+destination+(ident?'/'+encodeURIComponent(ident):'')+query,{waitUntil:'domcontentloaded'});}
 async function scan(name,theme){
   phase='scan_'+name+'_'+theme;
   const result=await page.evaluate(async()=>{
     const r=await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
     const clean=s=>/(?:bootstrap=|csrf|sys4ai_explorer_)/i.test(s)?'[sensitive selector redacted]':s.slice(0,400);
     const rows=v=>v.map(x=>({id:x.id,impact:x.impact,tags:x.tags,nodes:x.nodes.map(n=>({targets:n.target.map(t=>clean(String(t))),checks:[...n.any,...n.all,...n.none].map(c=>({id:c.id,impact:c.impact,data:c.id==='color-contrast'?c.data:null}))}))}));
     const targets=[...document.querySelectorAll('button,a,input,select,textarea,summary')].flatMap((el,index)=>{const r=el.getBoundingClientRect(),style=getComputedStyle(el);if(!r.width||!r.height||style.visibility==='hidden')return[];return[{index,tag:el.tagName.toLowerCase(),id:el.id,width:r.width,height:r.height,below24:r.width<24||r.height<24}];});
     return {raw:r,rendered_state:{read_status:document.querySelector('#read-status')?.textContent??'',map_warnings:[...document.querySelectorAll('.model-summary .warning')].map(x=>x.textContent),node_count:document.querySelectorAll('.node-list>li').length,relationship_count:document.querySelectorAll('.relationship-rows>li').length},actual_theme:{document:document.documentElement.dataset.theme,color_scheme:getComputedStyle(document.documentElement).colorScheme,background_color:getComputedStyle(document.documentElement).backgroundColor,text_color:getComputedStyle(document.documentElement).color},violations:rows(r.violations),incomplete:rows(r.incomplete),passes:r.passes.map(x=>x.id),inapplicable:r.inapplicable.map(x=>x.id),target_count:targets.length,targets_below24:targets.filter(t=>t.below24),viewport:{width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth},axe_version:r.testEngine.version};
   });
   need(result.actual_theme.document===theme&&result.actual_theme.color_scheme===theme,'resolved_document_theme');
   const raw=JSON.stringify(result.raw,null,2)+'\n';need(knownSecrets.every(secret=>secret.length>0&&!raw.includes(secret))&&!/(?:[?&#](?:bootstrap|csrf|session|cursor)=|sys4ai_explorer_)/i.test(raw),'axe_raw_secret_boundary');
   need(/^\/private\/tmp\/explorer-a11y-evidence-[A-Za-z0-9_-]+$/.test(meta.raw_dir),'owned_raw_directory');const rawPath=meta.raw_dir+'/'+String(scans.length).padStart(2,'0')+'-'+name+'-'+theme+'.json';fs.writeFileSync(rawPath,raw,{flag:'wx',mode:0o600});
   delete result.raw;scans.push({name,theme,raw_report:{path:rawPath,sha256:crypto.createHash('sha256').update(raw).digest('hex'),bytes:Buffer.byteLength(raw)},...result});
 }
 need(session.expires_in===60,'actual_sixty_second_session');await route('entry',id(0));await page.locator('.entry .exact-text').waitFor();const retained=await page.locator('.entry .exact-text').allTextContents(),retainedRoute=page.url(),started=performance.now();
 phase='real_expiry';await page.locator('#read-status').getByText('The reading session expired. Reopen the local reader to continue.',{exact:true}).waitFor({timeout:75000});const elapsed=performance.now()-started;need(elapsed>=58000&&elapsed<75000,'real_unmodified_expiry_interval');need(page.url()===retainedRoute&&JSON.stringify(await page.locator('.entry .exact-text').allTextContents())===JSON.stringify(retained),'expired_recorded_view_retained');
 for(const theme of ['light','dark']){await page.getByRole('combobox',{name:'Theme',exact:true}).selectOption(theme);await scan('expired_session_retained_entry',theme);}
 need(errors===0&&remote===0,'instrumentation_runtime_errors');
 report={status:scans.every(s=>s.violations.length===0)?'passed':'failed',scan_execution_complete:true,actual_configured_session_seconds:session.expires_in,real_wait_ms:elapsed,clock_modified:false,browser_version:browser.version(),axe_version:'4.13.0',scans,violation_nodes:scans.reduce((n,s)=>n+s.violations.reduce((m,v)=>m+v.nodes.length,0),0),incomplete_nodes:scans.reduce((n,s)=>n+s.incomplete.reduce((m,v)=>m+v.nodes.length,0),0),page_errors:errors,nonlocal_requests:remote,qualification:'Automated scanner observations of listed states and themes only. Axe was injected through test evaluation after the private fragment was removed. This is not production inline execution/CSP proof, actual screen-reader observation, complete manual target-exception review, or a WCAG compliance declaration. Sub24px rectangles are manual-review candidates; label hit areas, spacing, inactive controls and applicable exceptions require separate observed review.'};
}catch(e){report={status:'failed',phase,reason:e.safeCode||'browser_operation_failed',exception:safeException(e),scans,page_errors:errors,nonlocal_requests:remote};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
report.async_failures=asyncFailures;if(asyncFailures.length)report.status='failed';
console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(e=>{console.log(JSON.stringify({status:'failed',phase,reason:'runner_failed',exception:safeException(e),async_failures:asyncFailures,scans}));process.exitCode=1;});
