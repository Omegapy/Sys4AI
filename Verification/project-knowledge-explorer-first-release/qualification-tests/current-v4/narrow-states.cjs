// Additional current narrow states shared by the scanner and geometry collector.
// Real UI events establish each state; DOM reads are declared test observations.
const names = [
  'narrow_navigation_open', 'narrow_navigation_escape_closed',
  'narrow_navigation_destination_closed', 'narrow_details_closed',
  'narrow_details_reopened', 'narrow_details_late_response_hidden',
  'narrow_source_parent_dismissed', 'narrow_source_parent_returned'
];
module.exports.names = names;
module.exports.observe = async function(c) {
  const {page, theme, id, route, waitDefinition, scan, need, checkpoint, safeException, asyncFailures} = c;
  const checks=[];
  const record=(name,details)=>checks.push({name,theme,status:'passed',...details});
  const nav=page.getByRole('dialog',{name:'Reading navigation',exact:true});
  const open=page.getByRole('button',{name:'Open navigation',exact:true});
  checkpoint('narrow_navigation_'+theme);
  await open.click();await nav.waitFor();
  need(await nav.evaluate(el=>el.matches(':modal')&&el.contains(document.activeElement)),'native_modal_focus');
  await scan(names[0],theme);
  for(let i=0;i<12;i++){
    await page.keyboard.press('Tab');
    need(await nav.evaluate(el=>el.contains(document.activeElement)),'modal_tab_background_excluded');
  }
  await nav.getByRole('button',{name:'Close navigation',exact:true}).click();
  need(await open.evaluate(el=>document.activeElement===el&&el.getAttribute('aria-expanded')==='false'),'navigation_close_focus');
  await open.click();await nav.waitFor();await page.keyboard.press('Escape');
  need(!await nav.isVisible()&&await open.evaluate(el=>document.activeElement===el),'navigation_escape_focus');
  await scan(names[1],theme);
  await open.click();await nav.getByRole('link',{name:'Terms',exact:true}).click();
  await page.locator('.results>li').first().waitFor();
  need(!await nav.isVisible(),'navigation_destination_closes_dialog');
  await scan(names[2],theme);
  record('navigation_modal_close_escape_destination',{trusted_tab_steps:12,
    qualification:'Actual native modal state and real Tab focus containment; pointer opened/closed destinations. This is not a full keyboard-reachability or assistive-technology claim.'});

  await route('map',id(0));await page.locator('.relationship-rows>li').first().waitFor();
  await waitDefinition(id(0));await page.getByRole('button',{name:'List',exact:true}).click();
  const details=page.locator('#selected-map-details');
  const toggle=page.locator('#selected-details-toggle');
  const before=await page.evaluate(()=>({route:location.hash,history:history.length,
    nodes:[...document.querySelectorAll('.node-list>li')].map(e=>e.dataset.nodeId),
    relations:[...document.querySelectorAll('.relationship-rows>li')].map(e=>e.dataset.relationId)}));
  await details.getByRole('button',{name:'Close selected details',exact:true}).click();
  need(!await details.isVisible()&&await toggle.evaluate(el=>document.activeElement===el&&el.getAttribute('aria-expanded')==='false'),'details_close_focus');
  await scan(names[3],theme);
  await toggle.click();await waitDefinition(id(0));
  need(await details.isVisible(),'details_reopened');
  const after=await page.evaluate(()=>({route:location.hash,history:history.length,
    nodes:[...document.querySelectorAll('.node-list>li')].map(e=>e.dataset.nodeId),
    relations:[...document.querySelectorAll('.relationship-rows>li')].map(e=>e.dataset.relationId)}));
  need(JSON.stringify(before)===JSON.stringify(after),'details_presentation_preserves_context');
  await scan(names[4],theme);
  record('details_close_reopen_retains_context',{route_history_and_exact_member_ids_unchanged:true});

  checkpoint('narrow_late_entry_'+theme);
  let release,settle,intercepted=false;
  const settled=new Promise(resolve=>settle=resolve);
  const hold=async r=>{
    const params=r.request().postDataJSON()?.params;
    if(intercepted||params?.id!==id(1)||params?.section!=='header')return r.continue();
    intercepted=true;
    try{await new Promise(resolve=>release=resolve);await r.continue();}
    catch(e){asyncFailures.push(safeException(e));}finally{settle();}
  };
  await page.route('**/api/explorer/v1/entry',hold);
  try{
    await page.locator('.node-list>li').evaluateAll((rows,expected)=>{
      // Read-only presence check; actual selection follows through a real click.
      return rows.some(row=>row.dataset.nodeId===expected);
    },id(1)).then(found=>need(found,'late_entry_member_present'));
    const row=page.locator('.node-list>li[data-node-id="'+id(1)+'"]');
    await row.getByRole('button',{name:'Alignment',exact:true}).click();
    const end=performance.now()+6000;
    while(!release&&performance.now()<end)await new Promise(resolve=>setTimeout(resolve,20));
    need(!!release,'late_header_intercepted');
    await details.getByRole('button',{name:'Close selected details',exact:true}).click();
    release();await settled;await waitDefinition(id(1));
    need(!await details.isVisible()&&await toggle.evaluate(el=>document.activeElement===el),'late_response_does_not_reopen_details');
    await scan(names[5],theme);
  }finally{
    if(release){release();await settled;}
    await page.unroute('**/api/explorer/v1/entry',hold);
  }
  record('late_entry_keeps_details_dismissed',{selected_id:id(1),real_header_request_delayed:true});

  await toggle.click();await waitDefinition(id(1));
  await details.getByRole('button',{name:'Sources',exact:true}).click();
  const source=details.locator('.entry .source-link').first();
  await source.waitFor();await source.click();await page.locator('.source-text').waitFor();
  await details.getByRole('button',{name:'Close selected details',exact:true}).click();
  need(!await details.isVisible()&&await page.locator('.source-drawer').isVisible(),'source_with_dismissed_parent');
  await scan(names[6],theme);
  await page.getByRole('button',{name:'Close source',exact:true}).click();
  need(await details.isVisible()&&await source.evaluate(el=>document.activeElement===el&&!el.closest('[hidden]')),'source_return_reopens_exact_parent_trigger');
  await scan(names[7],theme);
  record('source_return_to_dismissed_parent',{exact_visible_trigger_focused:true,
    qualification:'Real pointer close-source action; separate keyboard Escape tests retain their own scope.'});
  // Restore the initial root/definition and open presentation for old-state coverage.
  await route('map',id(0));await page.locator('.relationship-rows>li').first().waitFor();
  const current=page.locator('#selected-map-details');
  if(!await current.isVisible())await page.locator('#selected-details-toggle').click();
  await waitDefinition(id(0));await page.getByRole('button',{name:'Map',exact:true}).click();
  await page.waitForFunction(()=>!!document.querySelector('.map-canvas')?._cyreg?.cy);
  return checks;
};
