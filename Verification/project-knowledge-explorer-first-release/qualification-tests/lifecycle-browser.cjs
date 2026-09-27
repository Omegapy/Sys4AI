// Real 60-second expiry or explicitly stopped owned service; no mocked response.
const fs=require('node:fs');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private',errors=0,remote=0,checks=[];
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{let report;
try{
 const fd=fs.openSync(meta.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let launch;
 try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');launch=JSON.parse(fs.readFileSync(fd,'utf8')).url;}finally{fs.closeSync(fd);}
 const u=new URL(launch);need(u.origin===meta.origin&&!u.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(u.hash),'private_url');
 browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 context=await browser.newContext({viewport:{width:1200,height:850}});await context.route('**/*',r=>{if(new URL(r.request().url()).origin!==meta.origin){remote++;return r.abort();}return r.continue();});
 await context.addInitScript(()=>{window.__lifecycle={csp:[],clean:[]};document.addEventListener('securitypolicyviolation',e=>window.__lifecycle.csp.push(e.effectiveDirective));const native=window.fetch.bind(window);window.fetch=(...args)=>{window.__lifecycle.clean.push(!location.hash.includes('bootstrap='));return native(...args);};});
 page=await context.newPage();page.setDefaultTimeout(9000);page.on('pageerror',()=>errors++);
 const start=performance.now(),sessionPromise=page.waitForResponse(r=>r.url().endsWith('/session')&&r.status()===200);
 phase='entry';await page.goto(launch+'&route='+encodeURIComponent(meta.desired_route),{waitUntil:'domcontentloaded',timeout:15000});launch=null;
 const session=await (await sessionPromise).json();need(session.expires_in===60,'actual_60_second_session');
 await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:'Alignment',exact:true}).waitFor();await page.locator('.entry .exact-text').waitFor();
 const retained={route:page.url(),text:await page.locator('.entry').textContent()};let elapsed,deadlineEvidence=null;
 if(meta.mode==='expiry'){
   phase='real_expiry';await page.locator('#read-status').filter({hasText:'The reading session expired.'}).waitFor({timeout:65000});elapsed=performance.now()-start;need(elapsed>=59000,'no_shortcut_clock');
 }else{
   phase='controlled_fault';fs.writeFileSync(meta.control_file,JSON.stringify({action:meta.mode==='stop'?'stop_service':'suspend_owned_worker'}),{flag:'wx',mode:0o600});
   const deadline=performance.now()+12000;while(!fs.existsSync(meta.control_ack)&&performance.now()<deadline)await sleep(50);
   need(fs.existsSync(meta.control_ack),'control_ack');const ack=JSON.parse(fs.readFileSync(meta.control_ack,'utf8'));
   if(meta.mode==='stop'){need(ack.service_stopped===true,'actual_stop_ack');await page.getByRole('button',{name:'Sources',exact:true}).click();await page.locator('#read-status').filter({hasText:'The local reader is unavailable.'}).waitFor();}
   else{need(ack.worker_suspended===true&&ack.request_seconds===5,'actual_owned_worker_suspend_ack');const response=page.waitForResponse(r=>r.url().endsWith('/entry')&&r.status()===504),readStart=performance.now();await page.getByRole('button',{name:'Sources',exact:true}).click();const actual=await response,body=await actual.json();need(body.status==='error'&&body.error.code==='deadline_exceeded'&&body.data===null,'actual_deadline_response');await page.locator('#read-status').filter({hasText:'The bounded local read did not finish.'}).waitFor();deadlineEvidence={http_status:actual.status(),error_code:body.error.code,elapsed_ms:performance.now()-readStart,request_seconds:ack.request_seconds};need(deadlineEvidence.elapsed_ms>=ack.request_seconds*1000,'real_deadline_wait');}
   elapsed=performance.now()-start;
 }
 need(page.url()===retained.route&&await page.locator('.entry').textContent()===retained.text,'recorded_route_and_text_retained');
 await page.getByText('Reader help',{exact:true}).click();need(await page.getByText('This page cannot restart Python.',{exact:false}).isVisible(),'honest_reopen_help');
 need(await page.getByRole('button',{name:/^restart/i}).count()===0,'no_restart_action');
 const safety=await page.evaluate(()=>window.__lifecycle);need(safety.clean.every(Boolean)&&safety.csp.length===0&&errors===0&&remote===0,'browser_safety');
 checks.push({name:(meta.mode==='entry_deadline'?'AT-06 ':'AT-23 ')+meta.mode+' retains exact recorded entry and desired route with explicit reopening guidance',status:'passed',elapsed_ms:elapsed,session_seconds:session.expires_in,clock_unchanged:true,deadline_evidence:deadlineEvidence});
 report={status:'passed',mode:meta.mode,browser_version:browser.version(),checks,page_errors:errors,nonlocal_requests:remote,csp_violations:safety.csp,qualification:'Expiry uses the real configured60-second session and browser timer. Stop uses only this test-owned service via a fixed control-file acknowledgement. The deadline mode SIGSTOPs only its retained owned worker Popen identity and observes real unchanged5-second handling/reaping; no arbitrary process channel. No timer patch, synthetic response or automatic process restart.'};
}catch(e){report={status:'failed',mode:meta.mode,phase,reason:e.safeCode||'browser_operation_failed',checks,page_errors:errors,nonlocal_requests:remote};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',phase,reason:'runner_failed'}));process.exitCode=1;});
