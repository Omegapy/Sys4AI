// Keyboard input only after initial private navigation. DOM reads identify
// targets and report live-region text; they do not focus or activate controls.
const fs=require('node:fs');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private',checks=[],traversals=[],regions=[],errors=0,remote=0,blockedRenderer=0,processCatalogObservation=null;
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const pass=name=>checks.push({name,status:'passed'});
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{let report;
try{
 const fd=fs.openSync(meta.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let launch;
 try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');launch=JSON.parse(fs.readFileSync(fd,'utf8')).url;}finally{fs.closeSync(fd);}
 const u=new URL(launch);need(u.origin===meta.origin&&!u.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(u.hash),'private_url');
 browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 context=await browser.newContext({viewport:{width:1280,height:900}});
 await context.route('**/*',r=>{const u=new URL(r.request().url());if(u.origin!==meta.origin){remote++;return r.abort();}if(/\/chunks\/renderer-[^/]+\.js$/.test(u.pathname)){blockedRenderer++;return r.abort();}return r.continue();});
 page=await context.newPage();page.setDefaultTimeout(9000);page.on('pageerror',()=>errors++);
 await page.goto(launch+'&route='+encodeURIComponent(meta.desired_route),{waitUntil:'domcontentloaded',timeout:15000});launch=null;
 await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:'Explorer fixture explorer-keyboard',exact:true}).waitFor();
 async function live(label){regions.push({step:label,texts:await page.getByRole('status').allTextContents(),qualification:'DOM live-region text observation; not observed screen-reader speech.'});}
 async function reach(target,label){
   phase='keyboard_'+label;await target.waitFor();let tabs=0,reverse=0,maxCandidates=0;
   for(let n=0;n<180;n++){
     const state=await target.evaluate(el=>{const visible=x=>x.tabIndex>=0&&!x.disabled&&x.getBoundingClientRect().width>0&&x.getBoundingClientRect().height>0;const nodes=[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')].filter(visible);return {focused:el===document.activeElement,target:nodes.indexOf(el),active:nodes.indexOf(document.activeElement),count:nodes.length};});
     maxCandidates=Math.max(maxCandidates,state.count);
     if(state.focused){
       const view=await target.evaluate(el=>{const r=el.getBoundingClientRect(),x=Math.min(innerWidth-1,Math.max(0,r.x+r.width/2)),y=Math.min(innerHeight-1,Math.max(0,r.y+r.height/2)),top=document.elementFromPoint(x,y);return {center_visible:!!top&&(el===top||el.contains(top)),rect:{x:r.x,y:r.y,width:r.width,height:r.height},tag:el.tagName,id:el.id};});
       need(view.center_visible,'focused_target_center_unobscured');traversals.push({target:label,tab_presses:tabs,shift_tab_presses:reverse,max_visible_tabbable_candidates:maxCandidates,...view});return;
     }
     const backward=state.active>=0&&state.target>=0&&(state.active-state.target+state.count)%state.count<(state.target-state.active+state.count)%state.count;
     await page.keyboard.press(backward?'Shift+Tab':'Tab');if(backward)reverse++;else tabs++;
   }
   need(false,'bounded_keyboard_traversal_exhausted');
 }
 async function enter(target,label){await reach(target,label);await page.keyboard.press('Enter');}
 await reach(page.getByRole('combobox',{name:'Search project knowledge',exact:true}),'search');await page.keyboard.type('Orientation');await page.getByRole('listbox').waitFor();await page.keyboard.press('Escape');need(await page.getByRole('combobox',{name:'Search project knowledge',exact:true}).getAttribute('aria-expanded')==='false','escape_suggestions');
 await page.keyboard.press('Enter');await page.getByRole('heading',{name:'Search results',exact:true}).waitFor();await page.locator('.results>li>a').first().waitFor();await live('search_results');
 await enter(page.locator('.results>li>a').first(),'first_exact_result');await page.getByRole('heading',{name:'Alignment',exact:true}).waitFor();await page.locator('.entry .exact-text').waitFor();await live('entry_selected');pass('AT-29 actual keyboard typing, Escape, submit and result-to-entry');
 await enter(page.getByRole('button',{name:'Sources',exact:true}),'entry_sources');const source=page.locator('.entry .source-link').first();await enter(source,'selected_entry_source');await page.locator('.source-text').waitFor();await page.keyboard.press('Escape');need(await source.evaluate(el=>el===document.activeElement),'exact_source_focus_return');await reach(source,'returned_source_trigger');pass('AT-29 source read and exact Escape return by keyboard');
 await enter(page.getByRole('button',{name:'View on map',exact:true}),'open_relationships');await page.locator('.relationship-rows>li').first().waitFor();await enter(page.getByRole('button',{name:'Map',exact:true}),'request_renderer');await page.getByText('The visual map is unavailable.',{exact:false}).waitFor();need(blockedRenderer===1,'renderer_fault_observed');await enter(page.getByRole('button',{name:'List',exact:true}),'equivalent_list');
 const termRow=()=>page.locator('.node-list>li').filter({has:page.getByRole('button',{name:'FixtureTaskManager',exact:true})});
 await enter(termRow().getByRole('button',{name:'FixtureTaskManager',exact:true}),'list_select_term');await page.getByRole('heading',{name:'FixtureTaskManager',exact:true}).waitFor();await live('list_selection');
 const scopes=await page.locator('.model-summary .scope').count();await enter(termRow().getByRole('button',{name:'More connections',exact:true}),'list_more_connections');await page.waitForFunction(n=>document.querySelectorAll('.model-summary .scope').length>n,scopes);await live('more_connections');
 await enter(termRow().getByRole('button',{name:'Focus here',exact:true}),'list_focus_here');await page.waitForFunction(()=>document.querySelector('.model-summary')?.textContent.includes('entry-00002'));need(await page.locator('.model-summary .scope').count()===1,'deliberate_focus_new_scope');pass('AT-29 renderer-independent keyboard List selection, More connections and Focus here');
 await enter(page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link',{name:'Processes',exact:true}),'processes');await page.getByRole('heading',{name:'Processes',exact:true}).waitFor();const ordered=page.getByRole('link',{name:'Fixture ordered inspection',exact:true});await ordered.waitFor();const observedProcessLinks=await ordered.evaluate(el=>({href:el.getAttribute('href'),visible_text:el.textContent}));need(decodeURIComponent(observedProcessLinks.href).includes('entry-00014'),'exact_recorded_process_identity');processCatalogObservation={...observedProcessLinks,recorded_label:'Fixture ordered inspection',non_starting_process_label_read:true};await enter(ordered,'ordered_process_by_recorded_label');await page.getByRole('heading',{name:'Recorded step 1',exact:true}).waitFor();
 const step=page.getByRole('button',{name:'Read step source',exact:true}).first();await enter(step,'recorded_step_source');await page.locator('.source-text').waitFor();await page.keyboard.press('Escape');need(await step.evaluate(el=>el===document.activeElement),'step_source_focus_return');await live('ordered_process_source_return');pass('AT-29 keyboard process reading and exact step-source return');
 need(regions.some(r=>r.texts.some(t=>t.includes('entries returned')))&&regions.some(r=>r.texts.some(t=>t.includes('Selected FixtureTaskManager.')))&&regions.some(r=>r.texts.some(t=>t.includes('Returned connections updated.'))),'meaningful_live_region_updates');
 need(errors===0&&remote===0,'keyboard_runtime_safety');report={status:'passed',browser_version:browser.version(),checks,traversals,live_regions:regions,process_catalog_observation:processCatalogObservation,page_errors:errors,nonlocal_requests:remote,renderer_requests_explicitly_blocked:blockedRenderer,qualification:'All in-app activation and focus traversal used actual keyboard typing/Tab/Shift+Tab/Enter/Escape. Locator/evaluate operations only read DOM. Renderer failure is intentional request denial. Live-region strings are observed DOM updates, not VoiceOver speech. Target-center visibility is bounded geometry evidence, not complete manual focus/contrast certification.'};
}catch(e){report={status:'failed',phase,reason:e.safeCode||'browser_operation_failed',checks,traversals,live_regions:regions,process_catalog_observation:processCatalogObservation,page_errors:errors,nonlocal_requests:remote,renderer_requests_explicitly_blocked:blockedRenderer};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',phase,reason:'runner_failed'}));process.exitCode=1;});
