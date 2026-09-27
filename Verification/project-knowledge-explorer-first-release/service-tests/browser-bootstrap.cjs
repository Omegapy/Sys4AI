// Real isolated Chrome page; credentials exist only in memory/private runtime.
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const metadata=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,interrupted=false,phase='private_file';
const safeCounts={page_errors:0,nonlocal_requests:0,session_exchanges:0,session_resumes:0};
const http=[];const safeUI=new Map([['Connecting to the local reader.','connecting'],['A fresh local reading session is required. Reopen the local reader.','session_required'],['Current knowledge is unavailable. Recorded text may be retained; reopen or inspect local reader health.','knowledge_unavailable'],['The local reader is unavailable. Reopen it with the explicit local command.','reader_unavailable'],['This local reader link is invalid. Reopen the local reader.','invalid_link'],['Connected to the selected project. This service bootstrap displays its recorded project context.','connected']]);
const fail=code=>{const e=new Error();e.safeCode=code;throw e;};
const need=(ok,code)=>{if(!ok)fail(code);};
process.once('SIGTERM',()=>{interrupted=true;void(async()=>{try{if(browser)await browser.close();}catch{}process.exit(2);})();});
(async()=>{
 let report={status:'failed',reason:'browser_check_failed'};
 try{
  const fd=fs.openSync(metadata.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
  let privateEntry;
  try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');privateEntry=JSON.parse(fs.readFileSync(fd,'utf8'));}finally{fs.closeSync(fd);}
  const bootstrap=new URL(privateEntry.url);need(bootstrap.origin===metadata.origin&&!bootstrap.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(bootstrap.hash),'private_entry');
  const secret=bootstrap.hash.slice(11);
  const privateUrl=privateEntry.url+'&route='+encodeURIComponent(metadata.desired_route);
  phase='launch';browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,
    args:['--disable-background-networking','--disable-component-update','--no-first-run']});
  phase='new_context';context=await browser.newContext({viewport:{width:1100,height:760}});
  let remoteRequests=0,pageErrors=0,sessionExchanges=0,sessionResumes=0;
  await context.route('**/*',route=>{const u=new URL(route.request().url());if(u.origin!==metadata.origin){remoteRequests++;safeCounts.nonlocal_requests++;void route.abort();}else void route.continue();});
  phase='new_page';page=await context.newPage();page.setDefaultTimeout(7000);
  page.on('pageerror',()=>{pageErrors++;safeCounts.page_errors++;});
  page.on('response',r=>{const part=new URL(r.url()).pathname.split('/').pop();if(['session','session-resume','session-close','context'].includes(part))http.push({operation:part,status:r.status()});});
  page.on('request',request=>{const p=new URL(request.url()).pathname;if(p==='/api/explorer/v1/session'){sessionExchanges++;safeCounts.session_exchanges++;}if(p==='/api/explorer/v1/session-resume'){sessionResumes++;safeCounts.session_resumes++;}});
  phase='navigation';const initial=await page.goto(privateUrl,{waitUntil:'domcontentloaded',timeout:10000});
  need(initial&&initial.status()===200,'document_response');
  phase='fragment_removal';await page.waitForFunction(()=>!location.hash.includes('bootstrap='));
  // No URL/text output is permitted before this positive admission.
  let clean=page.url();need(!clean.includes(secret)&&!clean.includes('bootstrap='),'fragment_not_removed');
  phase='recorded_heading';await page.getByRole('heading',{name:metadata.project_name,exact:true}).waitFor();
  need(page.url()===metadata.origin+'/'+metadata.desired_route,'desired_route');
  const title=await page.getByRole('heading',{name:metadata.project_name,exact:true}).textContent();
  need(title===metadata.project_name,'recorded_project');
  phase='cookie_policy';const cookies=await context.cookies(metadata.origin+'/api/explorer/v1/');
  const cookie=cookies.find(c=>c.name.startsWith('sys4ai_explorer_'));
  need(cookie&&cookie.httpOnly&&cookie.sameSite==='Strict'&&cookie.path==='/api/explorer/v1/'&&!cookie.secure,'cookie_policy');
  need(await page.evaluate(()=>document.cookie===''),'http_only');
  phase='reload';await page.reload({waitUntil:'domcontentloaded'});
  await page.getByRole('heading',{name:metadata.project_name,exact:true}).waitFor();
  need(page.url()===metadata.origin+'/'+metadata.desired_route&&sessionResumes===1,'resume');
  phase='session_close';await page.getByRole('button',{name:'Close reading session',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Reading session closed.'}).waitFor();
  need((await context.cookies(metadata.origin+'/api/explorer/v1/')).every(c=>!c.name.startsWith('sys4ai_explorer_')),'cookie_closed');
  need((await page.getByRole('heading',{name:metadata.project_name,exact:true}).textContent())===metadata.project_name,'recorded_text_preserved');
  phase='same_document_bootstrap_replay';await page.goto(privateUrl,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>!location.hash.includes('bootstrap='));
  need(!page.url().includes(secret)&&!page.url().includes('bootstrap='),'replay_fragment');
  await page.getByRole('status').filter({hasText:'A fresh local reading session is required.'}).waitFor();
  need(sessionExchanges===2,'same_document_exchange');
  phase='new_document_bootstrap_replay';await page.goto('about:blank',{waitUntil:'domcontentloaded'});
  await page.goto(privateUrl,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>!location.hash.includes('bootstrap='));
  need(!page.url().includes(secret)&&!page.url().includes('bootstrap='),'new_document_replay_fragment');
  await page.getByRole('status').filter({hasText:'A fresh local reading session is required.'}).waitFor();
  need(remoteRequests===0&&pageErrors===0&&sessionExchanges===3,'browser_errors');
  report={status:'passed',browser_version:browser.version(),playwright_version:require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json').version,
    actual_page_bootstrap:true,fragment_removed_before_inspection:true,desired_route_preserved:true,recorded_project_text:title,
    clean_url:clean,session_resume:true,http_only_cookie:true,isolated_cookie_closed:true,recorded_text_preserved_on_close:true,bootstrap_replay_rejected:true,same_document_fragment_removed:true,same_document_replay_rejected:true,new_document_replay_rejected:true,session_exchanges:sessionExchanges,session_resumes:sessionResumes,http,
    page_errors:pageErrors,nonlocal_page_requests:remoteRequests,csp:initial.headers()['content-security-policy'],
    qualification:'Real isolated headless Chrome using direct Playwright goto. This does not test OS default-browser --open dispatch or full frontend UX/accessibility/offline release.'};
 }catch(error){
  let ui='not_inspected',fragmentRemoved=false;
  if(page){try{fragmentRemoved=await page.evaluate(()=>!location.hash.includes('bootstrap='));if(fragmentRemoved)ui=safeUI.get(await page.locator('#status').textContent())||'other_fixed_state';}catch{}}
  report={status:'failed',reason:error.safeCode||'browser_operation_failed',phase,counts:safeCounts,http,fragment_removed:fragmentRemoved,ui_state:ui,interrupted,qualification:'Only fixed checkpoints, status codes, counts and whitelisted UI states. Raw URLs, exception messages, headers, credentials and traces are suppressed.'};
 }
 finally{try{if(context)await context.close();}catch{}try{if(browser)await browser.close();}catch{}}
 console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',reason:'browser_runner_failed'}));process.exitCode=1;});
