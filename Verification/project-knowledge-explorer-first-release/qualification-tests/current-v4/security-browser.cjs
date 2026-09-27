// Actual production DOM/CSP against inert hostile fixture strings.
const fs=require('node:fs');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const runtime=JSON.parse(fs.readFileSync(__dirname+'/test-browser-runtime.json','utf8'));
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private',checks=[],http=[],errors=0,dialogs=0,remote=0;
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const pass=name=>checks.push({name,status:'passed'});
function privateURL(){const fd=fs.openSync(meta.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');const v=JSON.parse(fs.readFileSync(fd,'utf8'));const url=new URL(v.url);need(url.origin===meta.origin&&!url.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(url.hash),'private_url');return v.url;}finally{fs.closeSync(fd);}}
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{let report;
try{
 const initial=privateURL()+'&route='+encodeURIComponent(meta.desired_route);
 phase='launch';browser=await chromium.launch({executablePath:runtime.executable,headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 need(browser.version()===runtime.supported_registry_entry.browserVersion,'browser_version');
 context=await browser.newContext({viewport:{width:1200,height:850}});
 await context.route('**/*',r=>{if(new URL(r.request().url()).origin!==meta.origin){remote++;return r.abort();}return r.continue();});
 await context.addInitScript(()=>{window.__security={csp:[],clean:[]};document.addEventListener('securitypolicyviolation',e=>window.__security.csp.push(e.effectiveDirective));const native=window.fetch.bind(window);window.fetch=(...args)=>{window.__security.clean.push(!location.hash.includes('bootstrap='));return native(...args);};});
 page=await context.newPage();page.setDefaultTimeout(8000);page.on('pageerror',()=>errors++);page.on('dialog',async d=>{dialogs++;await d.dismiss();});
 page.on('response',r=>{const op=new URL(r.url()).pathname.split('/').pop();if(['session','context','search','entry','source'].includes(op))http.push({operation:op,status:r.status()});});
 phase='malicious_label';await page.goto(initial,{waitUntil:'domcontentloaded',timeout:12000});await page.waitForFunction(()=>!location.hash.includes('bootstrap='));
 await page.getByRole('heading',{name:'<script>alert("inert label")</script>',exact:true}).waitFor();
 need(await page.locator('.entry script,.entry img,.entry iframe,.entry object').count()===0,'entry_inert_dom');
 pass('AT-27 malicious label is literal heading text without executable elements');
 phase='malicious_source';await page.getByRole('button',{name:'Sources',exact:true}).click();await page.locator('.source-reference button').first().click();await page.locator('.source-text').waitFor();
 const text=await page.locator('.source-text').allTextContents();need(text.join('').includes('<script>throw new Error("fixture text")</script>')&&text.join('').includes('[unsafe](javascript:alert(1))'),'source_literal_text');
 need(await page.locator('.source-drawer script,.source-drawer img,.source-drawer iframe,.source-drawer object,.source-drawer a[href^="javascript:"]').count()===0,'source_inert_dom');
 need(await page.locator('.entry').isVisible(),'entry_retained');pass('AT-27 hostile source HTML and javascript link are plain text with entry retained');
 phase='malicious_search';await page.getByRole('button',{name:'Close source',exact:true}).click();const search=page.getByRole('combobox',{name:'Search project knowledge',exact:true});await search.fill('<script>');await search.press('Enter');await page.getByRole('heading',{name:'Search results',exact:true}).waitFor();
 await page.locator('.results').getByRole('link',{name:'<script>alert("inert label")</script>',exact:true}).waitFor();
 need(await page.locator('.results script,.results img,.results iframe,.results object').count()===0,'search_inert_dom');pass('AT-27 malicious search result label remains inert literal text');
 const safety=await page.evaluate(()=>window.__security);need(safety.clean.every(Boolean),'fragment_before_fetch');need(safety.csp.length===0&&errors===0&&dialogs===0&&remote===0,'no_execution_or_external_request');
 pass('AT-27 real production CSP has no violations and no script/dialog/external execution');
 report={status:'passed',browser_version:browser.version(),checks,http,page_errors:errors,dialogs,nonlocal_requests:remote,csp_violations:safety.csp,fragment_removed_before_network:true,qualification:'Actual built UI over real HTTP. The diagnostic fetch wrapper records Boolean cleanliness only; source text is genuine fixture data. No AT scanner, VoiceOver or human comprehension claim.'};
}catch(e){report={status:'failed',phase,reason:e.safeCode||'browser_operation_failed',checks,http,page_errors:errors,dialogs,nonlocal_requests:remote,qualification:'Raw browser errors, URLs, headers and response values suppressed.'};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',phase,reason:'runner_failed'}));process.exitCode=1;});
