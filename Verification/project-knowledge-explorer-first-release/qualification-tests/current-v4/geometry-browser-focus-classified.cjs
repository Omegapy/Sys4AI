// Declared axe instrumentation; native announcements and uninstrumented CSP
// acceptance remain separate tests. This never modifies production package bytes.
const fs=require('node:fs'),crypto=require('node:crypto');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const narrowStates=require('./narrow-states.cjs');
const requiredStates=JSON.parse(fs.readFileSync(__dirname+'/required-a11y-states.json','utf8')).geometry;
const narrowChecks=[];
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private',checkpoints=['private'],scans=[],errors=0,remote=0,asyncFailures=[],initialHttp=[],labelActivations=[];
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const checkpoint=name=>{phase=name;checkpoints.push(name);};
const safeException=e=>({exception_class:['Error','TypeError','ReferenceError','SyntaxError','RangeError','TimeoutError'].includes(e?.name)?e.name:'OtherError',frames:[...String(e?.stack??'').matchAll(/((?:geometry-browser|narrow-states)\.cjs):(\d+):(\d+)/g)].slice(0,5).map(m=>({file:m[1],line:Number(m[2]),column:Number(m[3])})),phase});
process.on('unhandledRejection',e=>{asyncFailures.push(safeException(e));process.exitCode=1;});
process.once('uncaughtException',e=>{console.log(JSON.stringify({status:'failed',reason:'uncaught_test_operation',modal_focus_trace:narrowStates.focusTrace,diagnostic:safeException(e),checkpoints,scans,async_failures:asyncFailures,initial_http:initialHttp}));process.exit(1);});
const axeFile='/private/tmp/explorer-qualification-axe-4.13.0/axe.min.js';
const axeFd=fs.openSync(axeFile,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let axe;try{const st=fs.fstatSync(axeFd);need(st.isFile()&&st.nlink===1&&st.size===580491,'axe_file');axe=fs.readFileSync(axeFd,'utf8');}finally{fs.closeSync(axeFd);}need(crypto.createHash('sha256').update(axe).digest('hex')==='c24f097bd2f451d4f933e8bc7d8d539f8672a2ebcb5cc9f9f3eec8ca9470a0c1','axe_bytes');
const ns='urn:sys4ai:ontology:project:explorer-a11y:',id=n=>ns+'entry-'+String(n).padStart(5,'0');
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{let report;
try{
 const fd=fs.openSync(meta.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let launch;
 try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');launch=JSON.parse(fs.readFileSync(fd,'utf8')).url;}finally{fs.closeSync(fd);}
 const u=new URL(launch);const privateBootstrap=u.hash.slice('#bootstrap='.length);need(u.origin===meta.origin&&!u.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(u.hash),'private_url');
 browser=await chromium.launch({executablePath:'/Users/alex.omegapy/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell',headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 need(browser.version()==='151.0.7922.34','admitted_headless_shell_version');
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
 const selectedStates=new Set(['overview','terms_browse','filters_open','combobox_suggestions','ambiguous_search','empty_search','relationship_list','map_surrounding_controls','map_controls_320_css_pixels','display_limit_list','display_limit_map_controls','renderer_unavailable_list_retained','process_names_pending','processes_index','process_names_unavailable_retry']);
 for(const name of narrowStates.names)selectedStates.add(name);
 async function scan(name,theme){
   if(!selectedStates.has(name))return;checkpoint('geometry_'+name+'_'+theme);
   need(new URL(page.url()).origin===meta.origin&&!page.url().includes('bootstrap='),'clean_owned_screenshot_url');
   const collected=await page.evaluate(()=>{
     const selector=el=>{if(el.id&&document.querySelectorAll('#'+CSS.escape(el.id)).length===1)return '#'+CSS.escape(el.id);const parts=[];for(let p=el;p&&p!==document.documentElement;p=p.parentElement){const siblings=p.parentElement?[...p.parentElement.children].filter(x=>x.tagName===p.tagName):[p];parts.unshift(p.tagName.toLowerCase()+':nth-of-type('+(siblings.indexOf(p)+1)+')');}return parts.join(' > ');};
     const rect=el=>{const r=el.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,document_x:r.x+scrollX,document_y:r.y+scrollY};};
     const hidden=el=>{const reasons=[];const modal=document.querySelector('dialog:modal');if(modal&&!modal.contains(el))reasons.push('outside_open_modal_dialog');for(let p=el;p;p=p.parentElement){const s=getComputedStyle(p);if(p.hidden)reasons.push('hidden_attribute');if(s.display==='none')reasons.push('display_none');if(s.visibility==='hidden'||s.visibility==='collapse')reasons.push('visibility_hidden');if(p.tagName==='DETAILS'&&!p.open){const summary=[...p.children].find(c=>c.tagName==='SUMMARY');if(!summary?.contains(el)&&summary!==el)reasons.push('closed_details');}}return [...new Set(reasons)];};
     const controls=[...document.querySelectorAll('button,a[href],input,select,textarea,summary,[role=option]')];
     const targets=controls.map((el,index)=>{const box=rect(el),labels=[...(el.labels??[])].map(l=>({selector:selector(l),rect:rect(l),associated_control:l.control===el}));const reasons=hidden(el);return{index,selector:selector(el),tag:el.tagName.toLowerCase(),input_type:el.getAttribute('type'),text_preview:(el.getAttribute('aria-label')??el.textContent??'').trim().slice(0,160),text_preview_truncated:(el.textContent??'').length>160,rect:box,labels,hidden_reasons:reasons,disabled:!!el.disabled,aria_disabled:el.getAttribute('aria-disabled'),below24:box.width>0&&box.height>0&&(box.width<24||box.height<24)};});
     const textSelectors=[...document.querySelectorAll('.relationship-sentence>span'),'#read-status > details > summary','.quiet','#reading > h2','.model-summary > p:nth-child(1)','.scope'].map(x=>typeof x==='string'?document.querySelector(x):x).filter(Boolean);
     const colors=textSelectors.map(el=>{const ancestors=[];for(let p=el;p;p=p.parentElement){const c=getComputedStyle(p);ancestors.push({selector:selector(p),background:c.backgroundColor,background_image:c.backgroundImage,opacity:c.opacity,filter:c.filter,mix_blend_mode:c.mixBlendMode});}const style=getComputedStyle(el);return{selector:selector(el),text:el.classList.contains('scope')?'[scope text]':el.textContent.slice(0,180),codepoints:[...el.textContent.trim()].slice(0,5).map(c=>c.codePointAt(0)),rect:rect(el),foreground:style.color,font_size:style.fontSize,font_weight:style.fontWeight,text_shadow:style.textShadow,hidden_reasons:hidden(el),ancestors};});
     return{targets,colors,actual_theme:{document:document.documentElement.dataset.theme,color_scheme:getComputedStyle(document.documentElement).colorScheme},viewport:{width:innerWidth,height:innerHeight,scrollX,scrollY},active_element:document.activeElement?selector(document.activeElement):null};
   });
   need(collected.actual_theme.document===theme&&collected.actual_theme.color_scheme===theme,'resolved_document_theme');
   const stem=String(scans.length).padStart(2,'0')+'-'+name+'-'+theme;
   const screen=meta.raw_dir+'/'+stem+'.png';await page.screenshot({path:screen,fullPage:false});fs.chmodSync(screen,0o600);const image=fs.readFileSync(screen);
   const candidates=[];
   for(const candidate of collected.targets.filter(t=>t.below24)){
     if(candidate.hidden_reasons.length||candidate.disabled){candidates.push({...candidate,disposition:'rectangle_only_not_active_in_this_state',qualification:'Explicit hidden ancestor/closed-details, outside actual open modal, or native disabled observation. Opened-filter states are measured separately.'});continue;}
     const measurement=await page.evaluate(selector=>{
       const el=document.querySelector(selector);if(!el)return{unavailable:true};const labels=[...(el.labels??[])].filter(l=>l.control===el);const target=labels.length===1?labels[0]:el;
       const old={x:scrollX,y:scrollY};target.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});
       const box=n=>{const r=n.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};
       const eligible=n=>{if(n.disabled)return false;const modal=document.querySelector('dialog:modal');if(modal&&!modal.contains(n))return false;for(let p=n;p;p=p.parentElement){const s=getComputedStyle(p);if(p.hidden||s.display==='none'||s.visibility==='hidden')return false;if(p.tagName==='DETAILS'&&!p.open){const summary=[...p.children].find(c=>c.tagName==='SUMMARY');if(!summary?.contains(n)&&summary!==n)return false;}}const r=box(n);return r.width>0&&r.height>0;};
       const own=box(target),center={x:own.x+own.width/2,y:own.y+own.height/2};const accepts=n=>n===el||el.contains(n)||labels.some(l=>n===l||l.contains(n));
       const hits=[];for(const dx of [-11.5,0,11.5])for(const dy of [-11.5,0,11.5]){const x=center.x+dx,y=center.y+dy,inside=x>=0&&y>=0&&x<innerWidth&&y<innerHeight,top=inside?document.elementFromPoint(x,y):null;hits.push({x,y,inside_viewport:inside,belongs_to_target:!!top&&accepts(top),top_tag:top?.tagName??null});}
       const others=[...document.querySelectorAll('button,a[href],input,select,textarea,summary,[role=option]')].filter(n=>n!==el&&eligible(n));const neighbors=[];
       for(const n of others){const labs=[...(n.labels??[])].filter(l=>l.control===n),effective=labs.length===1?labs[0]:n;if(effective===target)continue;const r=box(effective),nx=r.x+r.width/2,ny=r.y+r.height/2;const nearestX=Math.max(r.x,Math.min(center.x,r.x+r.width)),nearestY=Math.max(r.y,Math.min(center.y,r.y+r.height));const rectangleDistance=Math.hypot(center.x-nearestX,center.y-nearestY),circleDistance=Math.hypot(center.x-nx,center.y-ny),small=r.width<24||r.height<24;
         if(rectangleDistance<60||circleDistance<60)neighbors.push({tag:n.tagName.toLowerCase(),text_preview:(n.getAttribute('aria-label')??n.textContent??'').trim().slice(0,100),rect:r,undersized:small,distance_from_candidate_center_to_rect:rectangleDistance,center_distance:circleDistance,circle_intersects_target:rectangleDistance<12,circles_intersect:small&&circleDistance<24});}
       const centerTop=(center.x>=0&&center.y>=0&&center.x<innerWidth&&center.y<innerHeight)?document.elementFromPoint(center.x,center.y):null;const result={effective_target:labels.length===1?'associated_html_label':'element',label_control_association:labels.length===1&&labels[0].control===el,rect:own,center,center_hit_belongs_to_target:!!centerTop&&accepts(centerTop),sampled_24_square_hits:hits,neighbor_observations:neighbors,scroll_before:old,scroll_during:{x:scrollX,y:scrollY},aria_disabled:el.getAttribute('aria-disabled'),qualification:'Measured CSS geometry and hit testing after declared center scrolling. Rectangles/circle intersections are evidence for human review, not automatic WCAG or native-focus acceptance.'};window.scrollTo(old.x,old.y);return result;
     },candidate.selector);candidates.push({...candidate,measurement,disposition:'requires_explicit_size_spacing_or_other_review'});
   }
   const raw=JSON.stringify({name,theme,...collected,candidates},null,2)+'\n';need(knownSecrets.every(secret=>secret.length>0&&!raw.includes(secret))&&!/(?:[?&#](?:bootstrap|csrf|session|cursor)=|sys4ai_explorer_)/i.test(raw),'geometry_secret_boundary');const rawPath=meta.raw_dir+'/'+stem+'.json';fs.writeFileSync(rawPath,raw,{flag:'wx',mode:0o600});scans.push({name,theme,raw_report:{path:rawPath,sha256:crypto.createHash('sha256').update(raw).digest('hex'),bytes:Buffer.byteLength(raw)},screenshot:{path:screen,sha256:crypto.createHash('sha256').update(image).digest('hex'),bytes:image.length},candidate_count:candidates.length,actual_theme:collected.actual_theme});checkpoint('geometry_complete_'+name+'_'+theme);
 }
 async function labelActivation(theme){
   checkpoint('label_activation_'+theme);
   await route('terms');await page.locator('.results>li').first().waitFor();
   const observations=[];
   const initial=await page.locator('.filter-control input[type=checkbox]').evaluateAll(elements=>elements.map(el=>({value:el.value,checked:el.checked})));
   for(let i=0;i<2;i++){
     const details=page.locator('.filter-control details');
     if(!await details.evaluate(el=>el.open))await page.locator('.filter-control summary').click();
     need(await details.evaluate(el=>el.open),'filters_open_before_label_action');
     const input=page.locator('.filter-control input[value=draft]');await input.waitFor();
     const proof=await input.evaluate(el=>{
       const label=el.labels?.[0];if(!label||label.control!==el)return null;
       label.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});
       const r=label.getBoundingClientRect(),b=el.getBoundingClientRect();
       window.__labelActivation={input_clicks:0,changes:0,trusted:true};
       el.addEventListener('click',e=>{window.__labelActivation.input_clicks++;window.__labelActivation.trusted&&=e.isTrusted;},{once:true});
       el.addEventListener('change',()=>window.__labelActivation.changes++,{once:true});
       return{before:el.checked,lifecycles_before:[...el.closest('fieldset').querySelectorAll('input:checked')].map(n=>n.value),label:{x:r.x,y:r.y,width:r.width,height:r.height},input:{x:b.x,y:b.y,width:b.width,height:b.height},point:{x:r.right-2,y:r.y+r.height/2},association:true,point_outside_input:r.right-2>b.right,point_hits_label:label.contains(document.elementFromPoint(r.right-2,r.y+r.height/2))};
     });
     need(!!proof&&proof.point_outside_input&&proof.point_hits_label,'checkbox_label_association');
     const expected=proof.before?proof.lifecycles_before.filter(value=>value!=='draft'):[...proof.lifecycles_before,'draft'];
     const responsePromise=page.waitForResponse(r=>r.url().endsWith('/search')&&r.request().method()==='POST');void responsePromise.catch(()=>{});
     await page.mouse.click(proof.point.x,proof.point.y);
     await page.waitForFunction(()=>window.__labelActivation.changes>0);
     const response=await responsePromise,requested=response.request().postDataJSON().params.lifecycles;
     need(response.status()===200&&JSON.stringify([...requested].sort())===JSON.stringify([...expected].sort()),'label_filter_request_transition');
     await page.waitForFunction(expected=>document.querySelector('.filter-control input[value=draft]')?.checked===expected&&!document.querySelector('#read-status .loading'),!proof.before);
     const after=await page.locator('.filter-control input[value=draft]').isChecked(),events=await page.evaluate(()=>window.__labelActivation);
     need(after!==proof.before&&events.trusted&&events.input_clicks===1&&events.changes===1,'actual_label_pointer_activation');
     observations.push({...proof,after,...events,requested_lifecycles:requested,response_status:response.status()});
   }
   const restored=await page.locator('.filter-control input[type=checkbox]').evaluateAll(elements=>elements.map(el=>({value:el.value,checked:el.checked})));
   need(JSON.stringify(initial)===JSON.stringify(restored),'complete_checkbox_filter_restoration');
   if(await page.locator('.filter-control details').evaluate(el=>el.open))await page.locator('.filter-control summary').click();
   need(!await page.locator('.filter-control details').evaluate(el=>el.open),'filters_closed_after_label_actions');
   labelActivations.push({theme,observations,original_checkbox_filters:initial,restored_checkbox_filters:restored,original_draft_filter_restored:true});
   await route('entry',id(5));await waitDefinition(id(5));
 }
 for(const theme of ['light','dark']){
   phase='theme_'+theme;await page.getByRole('combobox',{name:'Theme',exact:true}).selectOption(theme);
   await route('overview');await page.getByRole('heading',{name:'Explorer fixture explorer-a11y',exact:true}).waitFor();await scan('overview',theme);
   await route('terms');await page.locator('.results>li').first().waitFor();await scan('terms_browse',theme);await page.locator('.filter-control summary').click();await scan('filters_open',theme);await page.locator('.filter-control summary').click();
   checkpoint('prepare_search_suggestions_'+theme);const search=page.getByRole('combobox',{name:'Search project knowledge',exact:true});await search.fill('Orientation');await page.getByRole('listbox').waitFor();await scan('combobox_suggestions',theme);await search.press('Escape');checkpoint('await_ambiguous_search_'+theme);await page.getByRole('button',{name:'Search',exact:true}).click();await page.getByRole('heading',{name:'Search results',exact:true}).waitFor();await page.locator('.results>li').first().waitFor();await scan('ambiguous_search',theme);
   await route('terms','','?q=qzxvplmnbvtrewq');await page.getByText('No matching entries in this filtered view.',{exact:false}).waitFor();await scan('empty_search',theme);
   await route('entry',id(0));await waitDefinition(id(0));await scan('entry_definition',theme);await page.getByText('Identity and provenance',{exact:true}).click();await scan('identity_details_open',theme);await page.getByText('Identity and provenance',{exact:true}).click();
   await page.getByRole('button',{name:'Sources',exact:true}).click();await page.locator('.entry .source-link').first().click();await page.locator('.source-text').waitFor();await scan('source_drawer',theme);await page.keyboard.press('Escape');
   await page.getByText('Reader help',{exact:true}).click();await scan('reader_help_open',theme);await page.getByText('Reader help',{exact:true}).click();
   await route('entry',id(10));await waitDefinition(id(10));await page.getByRole('button',{name:'Sources',exact:true}).click();await page.locator('.entry .source-link').first().click();await page.locator('.source-text').waitFor();await page.getByText('Source changed.',{exact:false}).first().waitFor();await scan('changed_source_warning',theme);await page.keyboard.press('Escape');
   await route('entry',id(13));await waitDefinition(id(13));await page.getByRole('button',{name:'Sources',exact:true}).click();await page.locator('.entry .source-link').first().click();await page.locator('.source-drawer').getByText('The selected source is unavailable.',{exact:false}).waitFor();await scan('unavailable_source_regional_error',theme);await page.keyboard.press('Escape');
   await route('entry',id(0));await waitDefinition(id(0));
   let release,settled,pending=false;const routed=new Promise(resolve=>settled=resolve);const delayed=async r=>{if(pending)return r.continue();pending=true;try{await new Promise(resolve=>release=resolve);await r.continue();}catch(e){asyncFailures.push(safeException(e));}finally{settled();}};await page.route('**/api/explorer/v1/entry',delayed);await route('entry',id(2));
   const waitUntil=performance.now()+6000;while(!release&&performance.now()<waitUntil)await new Promise(r=>setTimeout(r,20));need(!!release,'pending_entry_interception');await page.locator('.retained-entry').waitFor();await scan('loading_retained_entry',theme);checkpoint('release_retained_entry_'+theme);release();await routed;await page.unroute('**/api/explorer/v1/entry',delayed);await page.getByRole('heading',{name:'FixtureTaskManager',exact:true}).waitFor();await waitDefinition(id(2));checkpoint('new_entry_complete_'+theme);

   await route('map',id(0));await page.locator('.relationship-rows>li').first().waitFor();await waitDefinition(id(0));await page.getByRole('button',{name:'List',exact:true}).click();await page.locator('.model-summary').getByText('Incomplete returned scope:',{exact:false}).first().waitFor();await scan('relationship_list',theme);
   await page.getByRole('button',{name:'Map',exact:true}).click();await page.waitForFunction(()=>!!document.querySelector('.map-canvas')?._cyreg?.cy);await page.locator('.model-summary').getByText('Incomplete returned scope:',{exact:false}).first().waitFor();await scan('map_surrounding_controls',theme);
   await page.setViewportSize({width:320,height:850});await scan('map_controls_320_css_pixels',theme);narrowChecks.push(...await narrowStates.observe({page,theme,id,route,waitDefinition,scan,need,checkpoint,safeException,asyncFailures}));await page.setViewportSize({width:1360,height:900});
   await page.getByRole('button',{name:'List',exact:true}).click();let continuationPages=0;while(await page.getByRole('button',{name:'Continue connections',exact:true}).count()){const count=await page.locator('.model-summary .scope').count();await page.getByRole('button',{name:'Continue connections',exact:true}).click();await page.waitForFunction(n=>document.querySelectorAll('.model-summary .scope').length>n,count);need(++continuationPages<20,'bounded_display_continuation');}await page.locator('.model-summary').getByText('Display limit reached.',{exact:false}).waitFor();await scan('display_limit_list',theme);await page.getByRole('button',{name:'Map',exact:true}).click();await page.waitForFunction(()=>!!document.querySelector('.map-canvas')?._cyreg?.cy);await scan('display_limit_map_controls',theme);
   const primary=page,fallback=await context.newPage();fallback.on('pageerror',()=>errors++);await fallback.route('**/chunks/renderer-*.js',r=>r.abort());await fallback.goto(meta.origin+'/#/p/explorer-a11y/map/'+encodeURIComponent(id(0)),{waitUntil:'domcontentloaded'});await fallback.getByText('The visual map is unavailable.',{exact:false}).waitFor();page=fallback;await scan('renderer_unavailable_list_retained',theme);page=primary;await fallback.close();

   let catalogRelease,catalogSettled;const catalogRouted=new Promise(resolve=>catalogSettled=resolve);const holdCatalog=async r=>{if(catalogRelease)return r.continue();try{await new Promise(resolve=>catalogRelease=resolve);await r.continue();}catch(e){asyncFailures.push(safeException(e));}finally{catalogSettled();}};
   await page.route('**/api/explorer/v1/entry',holdCatalog);await route('processes');await page.getByRole('heading',{name:'Processes',exact:true}).waitFor();await page.getByText('Reading the recorded process name…',{exact:true}).first().waitFor();await scan('process_names_pending',theme);need(!!catalogRelease,'catalog_pending_interception');catalogRelease();await catalogRouted;await page.unroute('**/api/explorer/v1/entry',holdCatalog);await page.getByRole('link',{name:'Fixture ordered inspection',exact:true}).waitFor();await scan('processes_index',theme);
   await route('overview');await page.getByRole('heading',{name:'Explorer fixture explorer-a11y',exact:true}).waitFor();const failCatalog=r=>r.abort();await page.route('**/api/explorer/v1/entry',failCatalog);await route('processes');await page.getByRole('button',{name:'Retry process names',exact:true}).waitFor();await scan('process_names_unavailable_retry',theme);await page.unroute('**/api/explorer/v1/entry',failCatalog);await page.getByRole('button',{name:'Retry process names',exact:true}).click();await page.getByRole('link',{name:'Fixture ordered inspection',exact:true}).waitFor();
   await route('process',id(14));await page.getByRole('heading',{name:'Recorded step 1',exact:true}).waitFor();await scan('ordered_process',theme);
   await route('process',id(15));await page.getByText('An ordered description has not been recorded. These are the documented relationships.',{exact:true}).first().waitFor();await scan('unordered_process',theme);
   await route('entry',id(5));await waitDefinition(id(5));await scan('deprecated_entry',theme);
   const activePage=page,disconnected=await context.newPage();disconnected.on('pageerror',()=>errors++);await disconnected.goto(meta.origin+'/#/p/explorer-a11y/entry/'+encodeURIComponent(id(0)),{waitUntil:'domcontentloaded'});await waitDefinition(id(0),disconnected);await disconnected.route('**/api/explorer/v1/entry',r=>r.abort());await disconnected.getByRole('button',{name:'Sources',exact:true}).click();await disconnected.locator('#read-status').getByText('The local reader is unavailable. Recorded text remains from the displayed snapshot. Reopen the local reader.',{exact:true}).waitFor();page=disconnected;await scan('disconnected_retained_entry',theme);page=activePage;await disconnected.close();await labelActivation(theme);
 }
 phase='closed_state';await page.getByRole('button',{name:'Close reading session',exact:true}).click();await page.locator('#read-status').filter({hasText:'Reading session closed.'}).waitFor();await scan('closed_session_retained_entry','dark');await page.getByRole('combobox',{name:'Theme',exact:true}).selectOption('light');await scan('closed_session_retained_entry','light');
 need(JSON.stringify(scans.map(s=>s.name+'/'+s.theme).sort())===JSON.stringify(requiredStates.map(s=>s.name+'/'+s.theme).sort()),'complete_original_and_added_named_states');
 need(errors===0&&remote===0&&asyncFailures.length===0,'instrumentation_runtime_errors');
 report={narrow_checks:narrowChecks,modal_focus_trace:narrowStates.focusTrace,status:'passed',observation_execution_complete:true,manual_acceptance:'pending review',browser_version:browser.version(),runtime:'Headless Shell151.0.7922.34/revision1234; no native/Chrome154 equivalence.',scans,label_activations:labelActivations,async_failures:asyncFailures,initial_http:initialHttp,page_errors:errors,nonlocal_requests:remote,qualification:'Measured actual CSS rectangles, associated labels, pointer activation, circle-neighbor geometry, rendered colors and clean-owned-page screenshots for46 named state/theme combinations, retaining all original30 and adding16 narrow states. No blanket inline exception, no automatic target/WCAG acceptance and no native VoiceOver/focus claim.'};
}catch(e){report={narrow_checks:narrowChecks,modal_focus_trace:narrowStates.focusTrace,status:'failed',phase,reason:e.safeCode||'browser_operation_failed',diagnostic:safeException(e),async_failures:asyncFailures,initial_http:initialHttp,checkpoints,scans,page_errors:errors,nonlocal_requests:remote};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
await new Promise(resolve=>setImmediate(resolve));
if(asyncFailures.length){report.status='failed';report.reason='asynchronous_test_operation_failed';report.async_failures=asyncFailures;}
console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(()=>{console.log(JSON.stringify({status:'failed',phase,reason:'runner_failed',modal_focus_trace:narrowStates.focusTrace}));process.exitCode=1;});
