// Declared axe instrumentation; native announcements and uninstrumented CSP
// acceptance remain separate tests. This never modifies production package bytes.
const fs=require('node:fs'),crypto=require('node:crypto');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const runtime=JSON.parse(fs.readFileSync(__dirname+'/test-browser-runtime.json','utf8'));
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private',checkpoints=['private'],scans=[],errors=0,remote=0,asyncFailures=[],initialHttp=[],labelActivations=[];
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const checkpoint=name=>{phase=name;checkpoints.push(name);};
const safeException=e=>({exception_class:['Error','TypeError','ReferenceError','SyntaxError','RangeError','TimeoutError'].includes(e?.name)?e.name:'OtherError',frames:[...String(e?.stack??'').matchAll(/visual-browser\.cjs:(\d+):(\d+)/g)].slice(0,5).map(m=>({file:'visual-browser.cjs',line:Number(m[1]),column:Number(m[2])})),phase});
process.on('unhandledRejection',e=>{asyncFailures.push(safeException(e));process.exitCode=1;});
process.once('uncaughtException',e=>{console.log(JSON.stringify({status:'failed',reason:'uncaught_test_operation',diagnostic:safeException(e),checkpoints,scans,async_failures:asyncFailures,initial_http:initialHttp}));process.exit(1);});
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
 need(browser.version()===runtime.supported_registry_entry.browserVersion,'admitted_headless_shell_version');
 context=await browser.newContext({viewport:{width:1360,height:900}});await context.route('**/*',r=>{if(new URL(r.request().url()).origin!==meta.origin){remote++;return r.abort();}return r.continue();});
 page=await context.newPage();page.setDefaultTimeout(9000);page.on('pageerror',()=>errors++);
 page.on('response',r=>{const operation=new URL(r.url()).pathname.split('/').pop();if(['session','context'].includes(operation))initialHttp.push({operation,status:r.status()});});
 const sessionResponse=page.waitForResponse(r=>r.url().endsWith('/session')&&r.status()===200);void sessionResponse.catch(()=>{});
 await page.goto(launch+'&route='+encodeURIComponent(meta.desired_route),{waitUntil:'domcontentloaded',timeout:15000});launch=null;
 const session=await (await sessionResponse).json();need(typeof session.csrf==='string'&&session.csrf.length===43,'session_privacy_bound');
 const knownSecrets=[privateBootstrap,session.csrf,...(await context.cookies(meta.origin+'/api/explorer/v1/')).map(c=>c.value)];
 await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:'Explorer fixture explorer-a11y',exact:true}).waitFor();
 // DevTools evaluation is explicitly test instrumentation, not an inline script
 // exception or CSP waiver in the shipping page.
 // Geometry observations use actual DOM/CSS/hit testing; no axe result is substituted.
 async function route(destination,ident='',query=''){checkpoint('navigate_'+destination+(query?'_empty_query':''));await page.goto(meta.origin+'/#/p/explorer-a11y/'+destination+(ident?'/'+encodeURIComponent(ident):'')+query,{waitUntil:'domcontentloaded'});checkpoint('await_'+destination+(query?'_empty_query':'')+'_state');}
 async function waitDefinition(ident,selectedPage=page){
   checkpoint('await_exact_entry_definition_'+ident.split(':').pop());
   await selectedPage.waitForFunction(expected=>{
     const article=document.querySelector('.entry-host>article.entry:not([hidden])');
     return article?.querySelector(':scope > div > details > code.identity')?.textContent===expected&&article.dataset.pending==='false'&&article.querySelector('nav.section-tabs button[data-section=definition][aria-pressed=true]')!==null&&article.querySelector(':scope > section > h3')?.textContent==='Definition'&&article.querySelectorAll(':scope > section > .exact-text').length>0;
   },ident);
 }
 async function capture(name,theme,selector){
   checkpoint('visible_'+name+'_'+theme);
   need(new URL(page.url()).origin===meta.origin&&!page.url().includes('bootstrap='),'clean_owned_screenshot_url');
   const before=await page.evaluate(()=>({x:scrollX,y:scrollY}));
   const target=page.locator(selector).first();await target.scrollIntoViewIfNeeded();
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   const observed=await target.evaluate((el,{name,theme})=>{
     const rect=n=>{const r=n.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};
     const descendants=name.includes('source')?[el]:name.includes('sentence')?[...el.querySelectorAll('.relationship-sentence>span')]:[el.querySelector('p:first-child'),el.querySelector('.scope')].filter(Boolean);
     const elements=descendants.map(n=>{const r=rect(n),c=getComputedStyle(n),ancestors=[];for(let p=n;p;p=p.parentElement){const s=getComputedStyle(p);ancestors.push({tag:p.tagName,background:s.backgroundColor,background_image:s.backgroundImage,opacity:s.opacity,filter:s.filter,mix_blend_mode:s.mixBlendMode});}const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return{text:n.textContent,codepoints:[...n.textContent.trim()].map(x=>x.codePointAt(0)),rect:r,foreground:c.color,font_size:c.fontSize,font_weight:c.fontWeight,text_shadow:c.textShadow,ancestors,entire_rect_in_viewport:r.x>=0&&r.y>=0&&r.x+r.width<=innerWidth&&r.y+r.height<=innerHeight,center_hit:hit===n||n.contains(hit)};});
     return{name,theme,document_theme:document.documentElement.dataset.theme,viewport:{width:innerWidth,height:innerHeight},scroll:{x:scrollX,y:scrollY},context_text:el.textContent,context_rect:rect(el),source_parent_state:name.includes('source')?{details_hidden:document.querySelector('#selected-map-details')?.hidden===true,drawer_visible:document.querySelector('.source-drawer')?.hidden===false,path:document.querySelector('.source-drawer>div>p:first-child')?.textContent,locator:document.querySelector('.source-drawer>div>p:nth-child(2)')?.textContent}:null,elements};
   },{name,theme});
   need(observed.document_theme===theme&&observed.elements.length===(name.includes('source')?1:2),'visible_theme_and_elements');
   need(observed.elements.every(e=>e.entire_rect_in_viewport&&e.center_hit),'actual_visible_unobscured_text');
   if(name.includes('sentence'))need(observed.elements.every(e=>e.codepoints.length===1&&e.codepoints[0]===8594),'actual_arrow_codepoint');
   if(name.includes('source'))need(observed.source_parent_state.details_hidden&&observed.source_parent_state.drawer_visible&&observed.source_parent_state.path==='SPECS.md'&&observed.source_parent_state.locator==='Recorded locator: section:Specification','exact_source_with_dismissed_parent');
   const stem=String(scans.length).padStart(2,'0')+'-'+name+'-'+theme,png=meta.raw_dir+'/'+stem+'.png';
   await page.screenshot({path:png,fullPage:false});fs.chmodSync(png,0o600);const image=fs.readFileSync(png);
   const raw=JSON.stringify({...observed,scroll_before:before,source_selector:selector},null,2)+'\n';
   need(knownSecrets.every(secret=>secret.length>0&&!raw.includes(secret))&&!/(?:[?&#](?:bootstrap|csrf|session|cursor)=|sys4ai_explorer_)/i.test(raw),'visual_secret_boundary');
   const rawPath=meta.raw_dir+'/'+stem+'.json';fs.writeFileSync(rawPath,raw,{flag:'wx',mode:0o600});
   scans.push({name,theme,raw_report:{path:rawPath,sha256:crypto.createHash('sha256').update(raw).digest('hex'),bytes:Buffer.byteLength(raw)},screenshot:{path:png,sha256:crypto.createHash('sha256').update(image).digest('hex'),bytes:image.length},candidate_count:0});
 }
 for(const theme of ['light','dark']){
   await page.getByRole('combobox',{name:'Theme',exact:true}).selectOption(theme);
   await route('map',id(0));await page.locator('.relationship-rows>li').first().waitFor();await page.getByRole('button',{name:'List',exact:true}).click();
   await page.locator('.model-summary').getByText('Incomplete returned scope:',{exact:false}).first().waitFor();
   await capture('list_first_sentence',theme,'.relationship-rows>li');
   await page.getByRole('button',{name:'Map',exact:true}).click();await page.waitForFunction(()=>!!document.querySelector('.map-canvas')?._cyreg?.cy);
   await page.setViewportSize({width:320,height:850});await capture('map_320_summary',theme,'.model-summary');await capture('map_320_first_sentence',theme,'.relationship-rows>li');
   await route('map',id(1));await page.locator('.relationship-rows>li').first().waitFor();await waitDefinition(id(1));
   const details=page.locator('#selected-map-details');need(await details.isVisible(),'source_starting_parent_visible');
   await details.getByRole('button',{name:'Sources',exact:true}).click();const source=details.locator('.entry .source-link').first();await source.click();await page.locator('.source-text').waitFor();
   await details.getByRole('button',{name:'Close selected details',exact:true}).click();need(!await details.isVisible()&&await page.locator('.source-drawer').isVisible(),'source_parent_dismissed');
   await capture('source_320_parent_dismissed',theme,'.source-drawer .source-text');
   await page.getByRole('button',{name:'Close source',exact:true}).click();need(await details.isVisible()&&await source.evaluate(el=>document.activeElement===el&&!el.closest('[hidden]')),'source_exact_return');
   await page.setViewportSize({width:1360,height:900});await page.evaluate(()=>scrollTo(0,0));
 }
 need(scans.length===8&&errors===0&&remote===0&&asyncFailures.length===0,'visual_observation_completion');
 report={status:'passed',observation_execution_complete:true,manual_acceptance:'pending review',browser_version:browser.version(),runtime:'Headless Shell 151.0.7922.34 / revision1234',scans,async_failures:asyncFailures,initial_http:initialHttp,page_errors:errors,nonlocal_requests:remote,qualification:'Eight actual scrolled screenshots of first relationship sentence,320px model summary and source text with dismissed parent in both themes. Exact text, arrow codepoints, colors, viewport rectangles, center hit testing and before/after scroll retained. Static visual review only; no actual VoiceOver or native-focus claim.'};
}catch(e){report={status:'failed',phase,reason:e.safeCode||'browser_operation_failed',diagnostic:safeException(e),async_failures:asyncFailures,initial_http:initialHttp,checkpoints,scans,page_errors:errors,nonlocal_requests:remote};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
await new Promise(resolve=>setImmediate(resolve));
if(asyncFailures.length){report.status='failed';report.reason='asynchronous_test_operation_failed';report.async_failures=asyncFailures;}
console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',phase,reason:'runner_failed'}));process.exitCode=1;});
