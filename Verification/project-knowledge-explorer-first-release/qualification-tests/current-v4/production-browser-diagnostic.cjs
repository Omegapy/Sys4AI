// Current production gap checks. Other scenarios require their separately
// bound current evidence; no earlier-bundle receipt is promoted by this run.
const fs=require('node:fs');
const {chromium}=require('/Users/alex.omegapy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const runtime=JSON.parse(fs.readFileSync(__dirname+'/test-browser-runtime.json','utf8'));
const meta=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
let browser,context,page,phase='private',checks=[],http=[],errors=0,remote=0;
let operation='initial',progress={query_kind:null,repetition:null,page_ordinal:0,response_items:null,collected_items:0,expected_items:null},operationTrace=[],operationCount=0,asyncFailures=[];
const mark=(name,updates={})=>{operation=name;Object.assign(progress,updates);operationCount++;operationTrace.push({operation,...progress,http_response_count:http.length});if(operationTrace.length>128)operationTrace.shift();};
const safeException=e=>({exception_class:['Error','TypeError','ReferenceError','SyntaxError','RangeError','TimeoutError'].includes(e?.name)?e.name:'OtherError',frames:[...String(e?.stack??'').matchAll(/production-browser\.cjs:(\d+):(\d+)/g)].slice(0,5).map(m=>({file:'production-browser.cjs',line:Number(m[1]),column:Number(m[2])})),phase,operation,progress:{...progress}});
process.on('unhandledRejection',e=>{asyncFailures.push(safeException(e));process.exitCode=1;});
const need=(ok,code)=>{if(!ok){const e=new Error();e.safeCode=code;throw e;}};
const pass=(name,details={})=>checks.push({name,status:'passed',...details});
const ns='urn:sys4ai:ontology:project:explorer-alpha:',id=n=>ns+'entry-'+String(n).padStart(5,'0');
function privateURL(){const fd=fs.openSync(meta.private_file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const st=fs.fstatSync(fd);need(st.isFile()&&st.nlink===1&&st.size<=8192&&(st.mode&0o777)===0o600,'private_file');const v=JSON.parse(fs.readFileSync(fd,'utf8'));const u=new URL(v.url);need(u.origin===meta.origin&&!u.search&&/^#bootstrap=[A-Za-z0-9_-]{43}$/u.test(u.hash),'private_url');return v.url;}finally{fs.closeSync(fd);}}
process.once('SIGTERM',()=>void(async()=>{try{await browser?.close();}catch{}process.exit(2);})());
(async()=>{let report;
try{
 const initial=privateURL()+'&route='+encodeURIComponent(meta.desired_route);
 browser=await chromium.launch({executablePath:runtime.executable,headless:true,args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 need(browser.version()===runtime.supported_registry_entry.browserVersion,'browser_version');
 context=await browser.newContext({viewport:{width:1360,height:900}});
 await context.route('**/*',r=>{if(new URL(r.request().url()).origin!==meta.origin){remote++;return r.abort();}return r.continue();});
 await context.addInitScript(()=>{
   window.__qualification={csp:[],clean:[],holdNext:false,held:false};const native=window.fetch.bind(window);
   document.addEventListener('securitypolicyviolation',e=>window.__qualification.csp.push(e.effectiveDirective));
   window.fetch=async(input,options)=>{const q=window.__qualification;q.clean.push(!location.hash.includes('bootstrap='));
     const op=new URL(typeof input==='string'?input:input.url,location.origin).pathname.split('/').pop();
     if(q.holdNext&&op==='entry'){q.holdNext=false;const response=await native(input,{...options,signal:undefined});const raw=await response.arrayBuffer();return new Promise(resolve=>{q.held=true;q.release=()=>resolve(new Response(raw,{status:response.status,headers:response.headers}));});}
     return native(input,options);
   };
 });
 page=await context.newPage();page.setDefaultTimeout(9000);page.on('pageerror',()=>errors++);
 page.on('response',r=>{const op=new URL(r.url()).pathname.split('/').pop();if(['session','context','search','entry','source','relationships','neighborhood'].includes(op))http.push({operation:op,status:r.status()});});
 phase='bootstrap';const initialContext=page.waitForResponse(r=>r.url().endsWith('/context')&&r.status()===200);void initialContext.catch(()=>{});await page.goto(initial,{waitUntil:'domcontentloaded',timeout:15000});const ctx=await (await initialContext).json();
 await page.waitForFunction(()=>!location.hash.includes('bootstrap='));await page.getByRole('heading',{name:'Explorer fixture explorer-alpha',exact:true}).waitFor();
 need(ctx.data.capabilities.authoring===false&&ctx.data.capabilities.semantic_search===false,'read_capabilities');
 need(await page.getByRole('navigation',{name:'Reading destinations'}).getByRole('link').count()===4,'four_destinations');
 need(await page.getByRole('button',{name:/^(Publish|Draft|Review|Generate|Execute|Run agent|Run skill|Advanced)$/i}).count()===0,'no_authoring_controls');
 pass('AT-01 AT-32 production read destinations and disabled authoring/semantic capabilities');
 async function route(destination,ident='',query=''){await page.goto(meta.origin+'/#/p/explorer-alpha/'+destination+(ident?'/'+encodeURIComponent(ident):'')+query,{waitUntil:'domcontentloaded'});}
 async function search(text,queryKind,repetition,expectedCount){
   mark('search_input_fill',{query_kind:queryKind,repetition,page_ordinal:0,response_items:null,collected_items:0,expected_items:expectedCount});
   const input=page.getByRole('combobox',{name:'Search project knowledge',exact:true});await input.fill(text);
   mark('search_response_wait_registered');
   const response=page.waitForResponse(r=>r.url().endsWith('/search')&&r.status()===200&&r.request().postDataJSON()?.params?.query===text);void response.catch(()=>{});
   mark('search_submit_click');await page.getByRole('button',{name:'Search',exact:true}).click();
   mark('search_first_response_json');let value=await (await response).json();
   mark('search_heading_wait');await page.getByRole('heading',{name:text?'Search results':'Terms',exact:true}).waitFor();
   const items=[],snapshot=value.snapshot;let pages=0;
   while(true){
     mark('page_items_decode',{page_ordinal:pages+1,response_items:Array.isArray(value.data?.items)?value.data.items.length:null});
     const ids=value.data.items.map(x=>x.kind==='entry'?x.entry.id:x.id);items.push(...value.data.items);pages++;
     mark('page_snapshot_assert',{collected_items:items.length});need(value.snapshot===snapshot,'search_snapshot');
     mark('page_rendered_ids_wait');
     if(ids.length)await page.waitForFunction(expected=>[...document.querySelectorAll('.results>li a')].map(x=>decodeURIComponent(x.hash.split('/entry/')[1]?.split('?')[0]||'')).join('|')===expected.join('|'),ids);
     mark('page_continuation_check');if(!value.page.has_more)break;
     const next=page.waitForResponse(r=>r.url().endsWith('/search')&&r.status()===200&&r.request().postDataJSON()?.params?.query===text);void next.catch(()=>{});
     mark('page_continue_click');await page.getByRole('button',{name:'Continue results',exact:true}).click();
     mark('page_next_response_json');value=await (await next).json();need(pages<60,'finite_ranked_search');
   }
   mark('search_repetition_complete');return {items,pages,snapshot};
 }
 phase='deterministic_search';
 for(const [query,topIds,reason] of [['FixtureTaskManager',[id(2)],'preferred_label'],['Orientation',[id(0),id(1)],'alias'],[id(2),[id(2)],'stable_id'],['coordinates',[id(0)],'lexical']]){
   const expected=meta.expected_queries[query];
   const first=await search(query,reason,1,expected.length),second=await search(query,reason,2,expected.length);
   mark('complete_query_assertions');
   const summary=v=>v.items.map(x=>x.kind==='entry'?{id:x.entry.id,label:x.entry.label,reason:x.entry.match_reason,alias:x.entry.matched_alias}:{id:x.id,reason:x.reason,detail:x.detail});
   need(JSON.stringify(summary(first))===JSON.stringify(summary(second)),'deterministic_repeated_search');
   need(JSON.stringify(summary(first).map(x=>x.id))===JSON.stringify(expected.map(x=>x.id)),'complete_canonical_ranked_ids');
   need(first.items.every((x,i)=>{const want=expected[i];return x.kind==='entry'?x.entry.match_reason===want.reason&&x.entry.label===want.label&&x.entry.matched_alias===want.matched_alias:want.label_requires_detail&&x.reason==='field_limit'&&x.detail.section==='label'&&x.detail.id===want.id;}),'every_match_has_canonical_evidence');
   need(JSON.stringify(expected.slice(0,topIds.length).map(x=>x.id))===JSON.stringify(topIds)&&expected.slice(0,topIds.length).every(x=>x.reason===reason),'intended_match_leads');
   need(expected.every(x=>x.reason!=='lexical'||Object.keys(x.field_overlap_proof).length>0),'every_lexical_extra_justified');
   pass('AT-02 '+reason+' browser search',{query_kind:reason,top_target_ids:topIds,total_ranked_matches:expected.length,pages_per_repetition:first.pages,repeated_identical:true,all_ordered_ids_and_reasons_match_canonical:true,all_additional_lexical_matches_have_field_evidence:true});
 }
 phase='filtered_continuation';
 const firstPage=page.waitForResponse(r=>r.url().endsWith('/search')&&r.status()===200&&r.request().postDataJSON()?.params?.category==='artifacts');void firstPage.catch(()=>{});
 await route('terms','','?category=artifacts');let value=await (await firstPage).json(),all=[],pages=0,snap=value.snapshot;
 while(true){
   need(value.snapshot===snap,'one_snapshot');const ids=value.data.items.map(x=>x.kind==='entry'?x.entry.id:x.id);all.push(...ids);pages++;
   await page.waitForFunction(expected=>[...document.querySelectorAll('.results>li>a')].map(x=>decodeURIComponent(x.hash.split('/entry/')[1]?.split('?')[0]||'')).join('|')===expected.join('|'),ids);
   if(!value.page.has_more)break;
   need(value.coverage.complete===false&&value.coverage.reasons.length>0,'bounded_coverage');need(await page.getByText('This returned view is incomplete',{exact:false}).first().isVisible(),'visible_incomplete');
   const next=page.waitForResponse(r=>r.url().endsWith('/search')&&r.status()===200);void next.catch(()=>{});await page.getByRole('button',{name:'Continue results',exact:true}).click();value=await (await next).json();need(pages<40,'finite_paging');
 }
 need(pages>1&&new Set(all).size===all.length,'no_duplicate_page_ids');need(JSON.stringify([...all].sort())===JSON.stringify([...meta.expected_artifact_ids].sort()),'no_missing_filtered_ids');
 pass('AT-04 AT-05 AT-06 filtered continuation preserves every expected later identity',{pages,entries:all.length,exact_fixture_ids:true,one_snapshot:true,visible_bound_reason:true});
 phase='explicit_classifications';
 for(const [ident,lf,ff] of [[id(6),'draft','asserted'],[id(7),'approved','inferred']]){
   const response=page.waitForResponse(r=>r.url().endsWith('/search')&&r.status()===200&&r.request().postDataJSON()?.params?.query===ident);void response.catch(()=>{});
   await route('terms','','?q='+encodeURIComponent(ident)+'&lifecycles='+lf+'&fact_kinds='+ff);
   const data=await (await response).json();need(data.data.items.length===1&&data.data.items[0].entry.lifecycle===lf&&data.data.items[0].entry.fact_kind===ff,'explicit_filter_classification');
   await page.locator('.results>li>a').first().click();await page.locator('.entry .meaning').waitFor();const text=await page.locator('.entry .meaning').textContent();need(text.includes('Lifecycle: '+lf)&&text.includes('Classification: '+ff),'visible_classification');
 }
 pass('AT-09 explicit draft and inferred results retain visible lifecycle/classification');
 phase='incoming_semantics';await route('map',id(0),'?direction=incoming&lifecycles=approved&fact_kinds=asserted');await page.locator('.relationship-rows>li').first().waitFor();await page.getByRole('button',{name:'Map',exact:true}).click();await page.waitForFunction(()=>!!document.querySelector('.map-canvas')?._cyreg?.cy);
 const incoming=await page.locator('.map-canvas').evaluate((el,focus)=>{const cy=el._cyreg.cy;return {count:cy.edges().length,correct:cy.edges().every(e=>{const d=e.data(),row=[...document.querySelectorAll('.relationship-rows>li')].find(r=>r.dataset.relationId===d.canonicalId);return d.object===focus&&e.source().data().canonicalId===d.subject&&e.target().data().canonicalId===d.object&&row?.textContent.includes(d.subject+' → '+d.predicate+' → '+d.object);})};},id(0));
 need(incoming.count>0&&incoming.correct,'incoming_direction_preserved');pass('AT-14 incoming traversal preserves actual canonical endpoints and arrow',{edges:incoming.count});
 phase='late_entry';await route('entry',id(0));await page.getByRole('heading',{name:'Alignment',exact:true}).waitFor();
 await page.evaluate(()=>{window.__qualification.holdNext=true;window.__qualification.held=false;});await route('entry',id(2));await page.waitForFunction(()=>window.__qualification.held===true);
 await route('entry',id(12));await page.getByRole('heading',{name:'Fixture entry 00012',exact:true}).waitFor();await page.locator('.entry .exact-text').waitFor();const before={url:page.url(),text:await page.locator('.entry').textContent()};
 await page.evaluate(()=>window.__qualification.release());await page.waitForTimeout(300);need(page.url()===before.url&&await page.locator('.entry').textContent()===before.text,'late_entry_cannot_replace');
 pass('AT-22 late real entry response is ignored after newer entry',{real_response_held:true,abort_ignored_intentionally:true,route_and_text_retained:true});
 const safety=await page.evaluate(()=>window.__qualification);need(safety.clean.every(Boolean)&&safety.csp.length===0&&errors===0&&remote===0,'production_safety');
 report={status:'passed',browser_version:browser.version(),checks,http,page_errors:errors,nonlocal_requests:remote,csp_violations:safety.csp,fragment_removed_before_network:true,qualification:'Current actual production bundle. Repeated search and page comparisons use actual responses plus rendered DOM. Delayed entry response deliberately ignores abort but uses real HTTP bytes. No native AT, human comprehension or performance claim.'};
}catch(e){report={status:'failed',phase,operation,progress,diagnostic:safeException(e),reason:e.safeCode||'browser_operation_failed',checks,http,page_errors:errors,nonlocal_requests:remote,qualification:'Raw browser errors, URLs, headers and response values suppressed.'};}
finally{try{await context?.close();}catch{}try{await browser?.close();}catch{}}
await new Promise(resolve=>setImmediate(resolve));
report.operation=operation;report.progress=progress;report.operation_trace=operationTrace;report.operation_trace_count=operationCount;report.operation_trace_retained_limit=128;report.async_failures=asyncFailures;
if(asyncFailures.length){report.status='failed';report.reason='asynchronous_test_operation_failed';}
console.log(JSON.stringify(report));process.exitCode=report.status==='passed'?0:1;
})().catch(e=>{console.log(JSON.stringify({status:'failed',phase,operation,progress,diagnostic:safeException(e),reason:'runner_failed'}));process.exitCode=1;});
