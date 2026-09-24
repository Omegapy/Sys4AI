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
  browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
  context=await browser.newContext({viewport:{width:1360,height:900}});
  await context.route('**/*',route=>{if(new URL(route.request().url()).origin!==metadata.origin){remote++;return route.abort();}return route.continue();});
  await context.addInitScript(()=>{window.__csp=[];document.addEventListener('securitypolicyviolation',event=>window.__csp.push({directive:event.effectiveDirective,blocked:event.blockedURI==='inline'?'inline':'resource'}));});
  page=await context.newPage();page.setDefaultTimeout(8000);page.on('pageerror',()=>errors++);page.on('response',r=>{const operation=new URL(r.url()).pathname.split('/').pop();if(['session','session-resume','context','search','entry','relationships','neighborhood','source'].includes(operation))http.push({operation,status:r.status()});});
  phase='bootstrap';const response=await page.goto(entry.url+'&route='+encodeURIComponent(metadata.desired_route),{waitUntil:'domcontentloaded',timeout:15000});entry=null;
  await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:metadata.project_name,exact:true}).waitFor();
  need(!page.url().includes('bootstrap='),'fragment');need(await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link').count()===4,'four_destinations');
  need(await page.locator('canvas').count()===0,'lazy_initial_map');pass('bootstrap_overview_four_reading_destinations_lazy_graph');
  phase='search';await page.getByRole('combobox',{name:'Search project knowledge'}).fill('Alignment');await page.getByRole('button',{name:'Search',exact:true}).click();
  await page.getByRole('heading',{name:'Search results',exact:true}).waitFor();await page.locator('.results>li>a').first().waitFor();need(await page.locator('.results>li>a').count()===2,'ambiguity');pass('explicit_search_preserves_two_exact_identities');
  phase='entry';await page.locator('.results>li>a').first().click();await page.locator('.entry .exact-text').waitFor();need((await page.locator('.entry .exact-text').textContent()).startsWith('Alignment means'),'definition');
  const selected=decodeURIComponent(new URL(page.url()).hash.split('/entry/')[1].split('?')[0]);pass('entry_exact_definition');
  phase='source';await page.getByRole('button',{name:'Sources',exact:true}).click();const source=page.locator('.entry .source-link').first();await source.waitFor();await source.click();await page.locator('.source-text').waitFor();need(await page.locator('#source-title').evaluate(el=>el===document.activeElement),'source_heading_focus');await page.keyboard.press('Escape');need(await source.evaluate(el=>el===document.activeElement),'source_trigger_focus');pass('source_read_and_exact_focus_return');
  phase='map';await page.getByRole('button',{name:'View on map',exact:true}).click();await page.locator('.relationship-rows>li').first().waitFor();need(await page.locator('canvas').count()===0,'list_renderer_absent');const listBefore=await page.locator('.relationship-rows>li').evaluateAll(rows=>rows.map(r=>({id:r.dataset.relationId,marker:r.dataset.marker==='true'})));
  await page.getByRole('button',{name:'Map',exact:true}).click();await page.waitForFunction(()=>!!document.querySelector('.map-canvas')?._cyreg?.cy);
  const graph=await page.locator('.map-canvas').evaluate(el=>{const cy=el._cyreg.cy;return {ids:cy.edges().map(x=>x.data().canonicalId).sort(),nodes:cy.nodes().length,loops:cy.edges().filter(x=>x.source().id()===x.target().id()).length,pan:cy.pan(),zoom:cy.zoom()};});
  need(JSON.stringify(graph.ids)===JSON.stringify(listBefore.filter(x=>!x.marker).map(x=>x.id).sort()),'map_list_ids');need(graph.loops>=1,'self_loop');pass('production_map_list_exact_ids_and_self_loop',{nodes:graph.nodes,edges:graph.ids.length});
  phase='selection';const beforeLength=await page.evaluate(()=>history.length);await page.locator('.node-list>li button').filter({hasText:'FixtureTaskManager'}).first().click();await page.getByRole('heading',{name:'FixtureTaskManager',exact:true}).waitFor();
  const after=await page.locator('.map-canvas').evaluate(el=>({pan:el._cyreg.cy.pan(),zoom:el._cyreg.cy.zoom()}));need(JSON.stringify(graph.pan)===JSON.stringify(after.pan)&&graph.zoom===after.zoom,'selection_camera');need(await page.evaluate(()=>history.length)===beforeLength+1,'one_history_item');pass('selection_one_history_event_camera_retained');
  phase='history';await page.goBack();await page.getByRole('heading',{name:'Alignment',exact:true}).waitFor();need(decodeURIComponent(new URL(page.url()).hash).includes(selected),'history_selection');pass('back_restores_selection_and_map');
  phase='viewport_320';await page.setViewportSize({width:320,height:850});phase='theme_dark';await page.getByRole('combobox',{name:'Theme',exact:true}).selectOption('dark');phase='reduced_motion';await page.emulateMedia({reducedMotion:'reduce'});phase='reflow_assertion';need(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'320_reflow');need(await page.getByRole('combobox',{name:'Search project knowledge'}).isVisible(),'search_visible');pass('320px_dark_reduced_motion');
  phase='storage';const stored=await page.evaluate(()=>Object.keys(localStorage).map(key=>({key,value:JSON.parse(localStorage.getItem(key))})));need(stored.every(x=>/^sys4ai-explorer:v1:/.test(x.key)&&Object.keys(x.value).sort().join(',')==='details,rail,relationship_view,theme'),'storage_scope');pass('preferences_only_storage');
  const retainedHeading=await page.locator('.entry h2, main h2').first().textContent();
  phase='closed';await page.getByRole('button',{name:'Close reading session',exact:true}).click();await page.locator('#read-status').filter({hasText:'Reading session closed.'}).waitFor();need(await page.getByRole('heading',{name:retainedHeading,exact:true}).isVisible(),'closed_retains');pass('session_close_retains_recorded_view');
  csp=await page.evaluate(()=>window.__csp);need(errors===0&&remote===0,'browser_errors');need(csp.length===0,'csp_violations');
  report={status:'passed',browser:browser.version(),checks,http,page_errors:errors,nonlocal_requests:remote,csp_violations:csp,qualification:'Actual isolated headless Chrome production frontend. No OS dispatch, VoiceOver or human usability claim.'};
 } catch(error){let clean=false;try{clean=await page?.evaluate(()=>!location.hash.includes('bootstrap='));if(clean)csp=await page.evaluate(()=>window.__csp);}catch{}report={status:'failed',phase,reason:error.safeCode||'browser_operation_failed',checks,http,page_errors:errors,nonlocal_requests:remote,fragment_removed:clean,csp_violations:csp,qualification:'Raw navigation errors, URLs, headers and credentials suppressed.'};}
 finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
 console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',reason:'runner_failed',phase}));process.exitCode=1;});
