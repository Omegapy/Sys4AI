// Real production browser checks. Private launch URL never enters diagnostics.
const fs=require('node:fs');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const metadata=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private_file',checks=[],http=[],errors=0,remote=0,csp=[];
const need=(ok,code)=>{if(!ok){const error=new Error();error.safeCode=code;throw error;}};
const pass=(name,details={})=>checks.push({name,status:'passed',...details});
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{
 let report;
 try {
  const fd=fs.openSync(metadata.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let entry;try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');entry=JSON.parse(fs.readFileSync(fd,'utf8'));}finally{fs.closeSync(fd);}
  need(new URL(entry.url).origin===metadata.origin,'origin');
  browser=await chromium.launch({executablePath:'/Users/alex.omegapy/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell',headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
  need(browser.version()==='151.0.7922.34','admitted_browser_version');context=await browser.newContext({viewport:{width:1360,height:900}});
  await context.route('**/*',route=>{if(new URL(route.request().url()).origin!==metadata.origin){remote++;return route.abort();}return route.continue();});
  await context.addInitScript(()=>{window.__csp=[];document.addEventListener('securitypolicyviolation',event=>window.__csp.push({directive:event.effectiveDirective,blocked:event.blockedURI==='inline'?'inline':'resource'}));});
  page=await context.newPage();page.setDefaultTimeout(8000);page.on('pageerror',()=>errors++);page.on('response',r=>{const operation=new URL(r.url()).pathname.split('/').pop();if(['session','session-resume','context','search','entry','relationships','neighborhood','source'].includes(operation))http.push({operation,status:r.status()});});
  phase='bootstrap';const response=await page.goto(entry.url+'&route='+encodeURIComponent(metadata.desired_route),{waitUntil:'domcontentloaded',timeout:15000});entry=null;
  await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:metadata.project_name,exact:true}).waitFor();
  need(!page.url().includes('bootstrap='),'fragment');need(await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link').count()===4,'four_destinations');
  need(await page.locator('canvas').count()===0,'lazy_initial_map');pass('bootstrap_overview_four_reading_destinations_lazy_graph');
  phase='neutral_message';await page.getByText('Imported vocabulary is available. No local additions are recorded in this view.',{exact:true}).waitFor();need(await page.locator('.category-links a').count()>0,'categories_available');pass('neutral_overview_explains_imported_vocabulary_and_keeps_browse');
  phase='neutral_terms';await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link',{name:'Terms',exact:true}).click();await page.locator('.results>li>a').first().waitFor();need(await page.locator('.results>li>a').count()>0,'imported_terms');pass('neutral_terms_browse_recorded_core');
  phase='neutral_processes';await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link',{name:'Processes',exact:true}).click();await page.getByText('No process descriptions have been selected for this reader.',{exact:false}).waitFor();pass('neutral_process_gap_is_truthful');
  phase='empty_query';await page.getByRole('combobox',{name:'Search project knowledge'}).fill('UniqueUnrecordedQueryZZQ');await page.getByRole('button',{name:'Search',exact:true}).click();await page.getByText('No matching entries in this filtered view.',{exact:false}).waitFor();need(await page.getByRole('combobox',{name:'Search project knowledge'}).inputValue()==='UniqueUnrecordedQueryZZQ','query_preserved');pass('empty_search_preserves_query_and_clear_filters');
  phase='empty_relationships';await page.goto(metadata.origin+'/#/p/explorer-neutral/map/'+encodeURIComponent('urn:sys4ai:ontology:core:ActionType'),{waitUntil:'domcontentloaded'});await page.getByText('No relationships are recorded in this view',{exact:true}).waitFor();need(await page.locator('.relationship-rows>li').count()===0,'empty_relation_rows');pass('proved_empty_returned_view_uses_exact_absence_message');
  phase='preferences_reset';await page.getByRole('combobox',{name:'Theme',exact:true}).selectOption('light');need(await page.evaluate(()=>document.documentElement.dataset.theme)==='light','light_theme');await page.getByRole('button',{name:'Reset presentation preferences',exact:true}).click();need(await page.evaluate(()=>Object.keys(localStorage).filter(key=>key.startsWith('sys4ai-explorer:')).length)===0,'reset_only_preferences');pass('light_system_reset_presentation_only');
  csp=await page.evaluate(()=>window.__csp);need(errors===0&&remote===0,'browser_errors');need(csp.length===0,'csp_violations');
  report={status:'passed',browser:browser.version(),checks,http,page_errors:errors,nonlocal_requests:remote,csp_violations:csp,qualification:'Actual isolated headless Chrome production frontend. No OS dispatch, VoiceOver or human usability claim.'};
 } catch(error){let clean=false;try{clean=await page?.evaluate(()=>!location.hash.includes('bootstrap='));if(clean)csp=await page.evaluate(()=>window.__csp);}catch{}report={status:'failed',phase,reason:error.safeCode||'browser_operation_failed',checks,http,page_errors:errors,nonlocal_requests:remote,fragment_removed:clean,csp_violations:csp,qualification:'Raw navigation errors, URLs, headers and credentials suppressed.'};}
 finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
 console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',reason:'runner_failed',phase}));process.exitCode=1;});
