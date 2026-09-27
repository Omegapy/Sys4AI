// Current production bundle over actual HTTP. Private credentials never leave memory.
const fs=require('node:fs');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const metadata=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private_file',http=[],errors=0,remote=0,checks=[];
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const pass=(name,extra={})=>checks.push({name,status:'passed',...extra});
function privateURL(file){const fd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');const v=JSON.parse(fs.readFileSync(fd,'utf8'));const url=new URL(v.url);need(url.origin===metadata.origin&&!url.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(url.hash),'private_entry');return v.url;}finally{fs.closeSync(fd);}}
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{let report;
 try{
  const first=privateURL(metadata.private_file)+'&route='+encodeURIComponent(metadata.desired_route);
  const second=metadata.second_private_file?privateURL(metadata.second_private_file)+'&route='+encodeURIComponent(metadata.second_route):null;
  phase='launch';browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
  context=await browser.newContext({viewport:{width:1200,height:850}});
  await context.route('**/*',route=>{if(new URL(route.request().url()).origin!==metadata.origin){remote++;return route.abort();}return route.continue();});
  await context.addInitScript(({mode})=>{
    const native=window.fetch.bind(window);window.__v2={events:[],csp:[],held:false,released:false,copied:null};
    document.addEventListener('securitypolicyviolation',event=>window.__v2.csp.push(event.effectiveDirective));
    Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.__v2.copied=text;}}});
    let delayed=false;
    window.fetch=async(input,options)=>{
      const op=new URL(typeof input==='string'?input:input.url,location.origin).pathname.split('/').pop();
      const clean=!location.hash.includes('bootstrap=');window.__v2.events.push({operation:op,clean_before_network:clean});
      const hold=!delayed&&((mode==='late_session'&&op==='session')||(mode==='late_context'&&op==='context'));
      if(!hold)return native(input,options);
      delayed=true;
      // Ignore abort intentionally, but retain the real bounded response bytes.
      const response=await native(input,{...options,signal:undefined});const raw=await response.arrayBuffer();
      return new Promise(resolve=>{window.__v2.held=true;window.__v2.release=()=>{window.__v2.released=true;resolve(new Response(raw,{status:response.status,headers:response.headers}));};});
    };
  },{mode:metadata.mode});
  page=await context.newPage();page.setDefaultTimeout(8000);page.on('pageerror',()=>errors++);
  page.on('response',r=>{const op=new URL(r.url()).pathname.split('/').pop();if(['session','session-resume','session-close','context','search','entry','source'].includes(op))http.push({operation:op,status:r.status()});});
  phase='initial_navigation';await page.goto(first,{waitUntil:'domcontentloaded',timeout:12000});
  await page.waitForFunction(()=>!location.hash.includes('bootstrap='));
  if(metadata.mode==='basic'){
    phase='overview';await page.getByRole('heading',{name:metadata.project_name,exact:true}).waitFor();
    need(page.url()===metadata.origin+'/'+metadata.desired_route,'desired_route');
    need(await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link').count()===4,'full_ui');
    const cookies=await context.cookies(metadata.origin+'/api/explorer/v1/'),cookie=cookies.find(c=>c.name.startsWith('sys4ai_explorer_'));
    need(cookie&&cookie.httpOnly&&cookie.sameSite==='Strict'&&cookie.path==='/api/explorer/v1/'&&!cookie.secure,'cookie');
    need(await page.evaluate(()=>document.cookie===''),'http_only');pass('full_ui_bootstrap_clean_route_cookie');
    phase='copied_link';await page.getByRole('link',{name:'Alignment',exact:true}).first().click();await page.locator('.entry .exact-text').waitFor();
    await page.getByRole('button',{name:'Copy local link',exact:true}).click();
    need(await page.evaluate(()=>typeof window.__v2.copied==='string'&&window.__v2.copied===location.href&&!/(?:bootstrap|csrf|session|cursor)=/i.test(window.__v2.copied)),'safe_copy');pass('copied_local_link_has_safe_route_only');
    need(await page.evaluate(()=>window.__v2.events.every(x=>x.clean_before_network)&&window.__v2.csp.length===0),'initial_network_safety');
    phase='reload';const safeRoute=page.url();await page.reload({waitUntil:'domcontentloaded'});await page.getByRole('heading',{name:'Alignment',exact:true}).waitFor();await page.locator('.entry .exact-text').waitFor();need(page.url()===safeRoute,'resume_route');
    need(http.filter(x=>x.operation==='session-resume'&&x.status===200).length===1,'resume');pass('resume_retains_exact_entry_route');
    phase='close';const oldText=await page.locator('.entry').textContent();await page.getByRole('button',{name:'Close reading session',exact:true}).click();await page.locator('#read-status').filter({hasText:'Reading session closed.'}).waitFor();
    need((await page.locator('.entry').textContent())===oldText,'recorded_retained');need((await context.cookies(metadata.origin+'/api/explorer/v1/')).every(c=>!c.name.startsWith('sys4ai_explorer_')),'closed_cookie');pass('isolated_close_retains_recorded_entry');
    phase='same_document_replay';await page.goto(first,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.locator('#read-status').filter({hasText:'A fresh local reading session is required.'}).waitFor();need(http.filter(x=>x.operation==='session').length===2,'same_document_exchange');pass('same_document_fragment_cleared_and_consumed_token_rejected');
    need(await page.evaluate(()=>window.__v2.events.every(x=>x.clean_before_network)&&window.__v2.csp.length===0),'resume_same_document_network_safety');
    phase='new_document_replay';await page.goto('about:blank');await page.goto(first,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.locator('#read-status').filter({hasText:'A fresh local reading session is required.'}).waitFor();need(http.filter(x=>x.operation==='session'&&x.status===401).length===2,'separate_replay');pass('new_document_fragment_cleared_and_consumed_token_rejected');
  }else{
    phase='hold_old_response';await page.waitForFunction(()=>window.__v2.held===true);need(second!==null,'second_entry');
    phase='fresh_same_document_connection';await page.goto(second,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:'Processes',exact:true}).waitFor();need(page.url()===metadata.origin+'/'+metadata.second_route,'new_route');
    const before=await page.evaluate(()=>({route:location.hash,text:document.querySelector('#reading').textContent,contexts:window.__v2.events.filter(x=>x.operation==='context').length}));
    phase='release_old_response';await page.evaluate(()=>window.__v2.release());await page.waitForTimeout(300);
    const after=await page.evaluate(()=>({route:location.hash,text:document.querySelector('#reading').textContent,contexts:window.__v2.events.filter(x=>x.operation==='context').length}));
    need(JSON.stringify(before)===JSON.stringify(after),'late_response_resurrection');
    need(await page.getByRole('button',{name:'Close reading session',exact:true}).isVisible(),'current_connected');
    need(after.contexts===(metadata.mode==='late_session'?1:2),'no_extra_context');
    pass(metadata.mode+'_ignored_after_fresh_same_document_connection',{abort_ignored_intentionally:true,real_http_response_held:true,current_route_and_text_retained:true,context_requests:after.contexts});
    await page.getByRole('button',{name:'Close reading session',exact:true}).click();await page.locator('#read-status').filter({hasText:'Reading session closed.'}).waitFor();
  }
  const safety=await page.evaluate(()=>({clean:window.__v2.events.every(x=>x.clean_before_network),csp:window.__v2.csp}));
  need(safety.clean,'pre_fetch_fragment');need(errors===0&&remote===0&&safety.csp.length===0,'browser_safety');
  report={status:'passed',mode:metadata.mode,browser_version:browser.version(),checks,http,fragment_removed_before_network:true,page_errors:errors,nonlocal_requests:remote,csp_violations:safety.csp,qualification:'Current actual production full UI over real HTTP in isolated Chrome. Clipboard capture and abort-insensitive response delay are explicitly test instrumentation. No native zoom, OS dispatch, VoiceOver, release or human usability claim.'};
 }catch(error){let clean=false;try{clean=await page?.evaluate(()=>!location.hash.includes('bootstrap='));}catch{}report={status:'failed',mode:metadata.mode,phase,reason:error.safeCode||'browser_operation_failed',checks,http,fragment_removed:clean,page_errors:errors,nonlocal_requests:remote,qualification:'Fixed checkpoints and counts only; raw errors, URLs, credentials and headers suppressed.'};}
 finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
 console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',reason:'runner_failed',phase}));process.exitCode=1;});
