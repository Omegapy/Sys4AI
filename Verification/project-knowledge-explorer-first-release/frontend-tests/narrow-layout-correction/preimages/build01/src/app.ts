import {ReadClient,captureFragment} from './api';
import type {CapturedFragment} from './api';
import {FACT_KINDS,LIFECYCLES,isWire,queryText,stableJson} from './contracts';
import type {ContextResponse,EntryResponse,Header,Section,SuccessResponse,SourceRef} from './contracts';
import {beginRefresh,commitRefresh,navigate,restoreHistory,safeHistory} from './state';
import type {Filters,ReaderState,Region,SafeHistory} from './state';
import {encodeRoute,parseRoute} from './routes';
import type {Destination,Route} from './routes';
import {createPreferences} from './preferences';
import {admitGraphPage,resolveIntent} from './model';
import type {ContinuationIntent,ModelIntent,RelationshipModel} from './model';
import {button,el,errorText,focus,heading,labeled,routeLink,warning} from './feedback';
import {overview} from './overview';
import {SearchBox,filterControl,resultList} from './search';
import {EntryView} from './entry';
import {SourceDrawer,ProcessSourceDiscovery,EndpointStrings} from './sources';
import {ProcessCatalog,processSection} from './processes';
import {MapView} from './map/controller';
import {relationshipList,modelSummary} from './map/list';

/** Route admission fills all request fields before any request can be issued. */
export function hydrateRoute(state:ReaderState,route:Route):ReaderState|null {
  if(!state.project)return null;const encoded=encodeRoute(route,state.project.id);if(!encoded.ok)return null;
  const parsed=parseRoute(encoded.hash,state.project.id);if(!parsed.ok)return null;
  const transition=navigate(state,{kind:'route',route:parsed.route});if(!transition.accepted)return null;
  const next=transition.state,options=parsed.route.options;next.query=queryText(options.q??'');
  next.filters={category:options.category??null,lifecycles:options.lifecycles??['approved'],fact_kinds:options.fact_kinds??['asserted'],predicate_ids:options.predicates??[],direction:options.direction??'both'};
  const context=state.content.context;if(next.filters.category&&context?.operation==='context'&&!context.data.categories.some(item=>item.id===next.filters.category)){next.filters.category=null;next.route!.options.category='all';next.regional_errors.context='category_unavailable';}
  if(parsed.route.destination==='map'){next.focus_id=parsed.route.id??null;next.selection=options.selected?{kind:state.selection?.id===options.selected?state.selection.kind:'entry',id:options.selected}:parsed.route.id?{kind:'entry',id:parsed.route.id}:state.selection;if(next.focus_id!==state.focus_id){next.expanded_ids=[];next.camera=null;}}
  else if(parsed.route.id)next.selection={kind:'entry',id:parsed.route.id};
  // The pure route transition intentionally leaves hydration to this boundary.
  // Replace its provisional metadata with one coherent post-hydration entry.
  next.history=state.history.slice(0,state.history_index+1);const safe=safeHistory(next);if(safe){next.history.push(safe);next.history=next.history.slice(-50);next.history_index=next.history.length-1;}return next;
}
export class ExplorerApp {
  readonly client:ReadClient;
  private reading=el('main');private projectName=el('p','Project Knowledge Explorer','project-name');private status=el('div');private announce=el('p',undefined,'sr-only');private close=button('Close reading session',()=>void this.client.close());
  private search:SearchBox;private source:SourceDrawer;private prefs:ReturnType<typeof createPreferences>;private theme=el('select');private context:ContextResponse|null=null;
  private entry:EntryView|null=null;private retainedEntry:HTMLElement|null=null;private entryHost=el('div',undefined,'entry-host');private mapView:MapView|null=null;private model:RelationshipModel|null=null;
  private continuation:ContinuationIntent|null=null;private continuationId:string|null=null;private graphControls=el('div');private searchResults=el('div');
  private navigation=el('nav');private routeSerial=0;private historySerial=0;private browserHistory=new Map<number,SafeHistory>();private currentHistory:number|null=null;private modelRevision=0;private historyModels=new Map<number,number>();
  private catalog:ProcessCatalog|null=null;
  private sourceCursor:string|null=null;private sourceSerial=0;
  private narrow=matchMedia('(max-width:760px)');private rail=el('aside',undefined,'rail');private shell=el('div',undefined,'shell');private navigationDrawer=el('dialog',undefined,'navigation-drawer');
  private navigationToggle=button('Open navigation',()=>this.openNavigation());private navigationClose=button('Close navigation',()=>this.closeNavigation());
  private detailsOpen=true;private mapDetails:HTMLElement|null=null;private detailsToggle:HTMLButtonElement|null=null;private detailsClose:HTMLButtonElement|null=null;private detailsHeading:HTMLElement|null=null;
  private color=matchMedia('(prefers-color-scheme: dark)');private motion=matchMedia('(prefers-reduced-motion: reduce)');
  private announcement='';
  constructor(root:HTMLElement,build:string,schema:string){
    this.client=new ReadClient(build,schema,()=>this.connectionChanged());
    let storage:Storage|undefined;try{storage=localStorage;}catch{/* Presentation remains memory-only. */}this.prefs=createPreferences(null,storage);
    this.search=new SearchBox((text,generation)=>void this.previewSearch(text,generation),text=>this.submitSearch(text),id=>this.openEntry(id));
    this.source=new SourceDrawer(()=>this.closeSource(),()=>void this.readSource(this.sourceCursor),trigger=>this.sourceReturnTarget(trigger));
    this.status.id='read-status';this.status.setAttribute('role','status');this.announce.setAttribute('role','status');this.announce.setAttribute('aria-live','polite');
    this.reading.id='reading';this.reading.tabIndex=-1;this.navigation.setAttribute('aria-label','Reading destinations');
    for(const value of ['system','light','dark']){const option=el('option',value[0]!.toUpperCase()+value.slice(1));option.value=value;this.theme.append(option);}this.theme.addEventListener('change',()=>this.savePreferences({...this.prefs.current(),theme:this.theme.value as 'system'|'light'|'dark'}));
    const tools=el('div',undefined,'reader-tools'),help=el('details');help.append(el('summary','Reader help'),el('p','Read-only project knowledge. Approved is a recorded lifecycle, not verified truth. Relationships do not grant execution authority. Source changed means a version mismatch, not that a claim is false.'),el('p','Local links need the correct running local reader and a current reading session. Stable IDs identify entries independently of a port.'),el('p','To reopen an expired or stopped reader, use the project’s explicit local explore --open command. This page cannot restart Python.'),el('p','If the installed package is incomplete, use the selected Explorer BUILD.md maintenance instructions.'));
    tools.append(labeled('Theme',this.theme),button('Reset presentation preferences',()=>{this.client.state.preferences=this.prefs.reset();this.presentPreferences();this.mapView?.show(this.prefs.current().relationship_view,false);}),help,this.close);
    const header=el('header',undefined,'site-header');header.append(this.projectName,this.navigationToggle,this.search.element);
    this.navigationDrawer.id='reading-navigation';this.navigationDrawer.setAttribute('aria-label','Reading navigation');this.navigationToggle.setAttribute('aria-controls',this.navigationDrawer.id);this.navigationToggle.setAttribute('aria-expanded','false');
    this.navigationClose.className='navigation-close';this.rail.append(this.navigationClose,this.navigation,tools);
    this.navigationDrawer.addEventListener('cancel',event=>{event.preventDefault();this.closeNavigation();});
    const workspace=el('div',undefined,'workspace');workspace.append(this.reading,this.source.element);
    const content=el('div',undefined,'content');content.append(this.status,workspace,this.announce);
    this.shell.append(this.rail,content);
    const skip=el('a','Skip to reading','skip-link');skip.href='#reading';skip.addEventListener('click',event=>{event.preventDefault();focus(this.reading);});root.append(skip,header,this.shell,this.navigationDrawer);
    this.narrow.addEventListener('change',()=>this.responsiveLayout());this.responsiveLayout();
    this.color.addEventListener('change',()=>this.presentPreferences());this.motion.addEventListener('change',()=>this.updateMap());
    window.addEventListener('popstate',()=>this.restoreBrowserHistory());
    window.addEventListener('hashchange',()=>{const next=captureFragment();if(next.bootstrap!==null||next.invalid){void this.start(next);return;}if(this.context&&next.desired!==this.currentHash()){const parsed=parseRoute(next.desired,this.context.project.id);if(parsed.ok)void this.go(parsed.route,false);else this.client.disconnect('This link belongs to another project. Open its correct local reader.');}});
  }
  private openNavigation():void {if(!this.narrow.matches||this.navigationDrawer.open)return;this.navigationDrawer.showModal();this.navigationToggle.setAttribute('aria-expanded','true');focus(this.navigationClose);this.navigationClose.scrollIntoView({block:'start'});}
  private closeNavigation():void {if(!this.navigationDrawer.open)return;this.navigationDrawer.close();this.navigationToggle.setAttribute('aria-expanded','false');if(this.narrow.matches){focus(this.navigationToggle);this.navigationToggle.scrollIntoView({block:'nearest'});}}
  private responsiveLayout():void {
    const active=document.activeElement instanceof HTMLElement?document.activeElement:null,wasInRail=!!active&&this.rail.contains(active),wasToggle=active===this.navigationToggle;
    if(this.navigationDrawer.open)this.navigationDrawer.close();this.navigationToggle.setAttribute('aria-expanded','false');
    this.navigationToggle.hidden=!this.narrow.matches;this.navigationClose.hidden=!this.narrow.matches;
    if(this.narrow.matches){this.navigationDrawer.append(this.rail);if(wasInRail){focus(this.navigationToggle);this.navigationToggle.scrollIntoView({block:'nearest'});}}
    else {this.shell.prepend(this.rail);if(wasInRail||wasToggle){const target=wasInRail&&active!==this.navigationClose?active:this.navigation.querySelector<HTMLElement>('[aria-current=page]')??this.navigation.querySelector<HTMLElement>('a');focus(target??this.search.input);}}
    this.presentDetails();
  }
  private presentDetails():void {
    if(!this.mapDetails||!this.detailsToggle||!this.detailsClose)return;
    const active=document.activeElement,hide=this.narrow.matches&&!this.detailsOpen;
    this.detailsToggle.hidden=!this.narrow.matches;
    if(hide&&this.mapDetails.contains(active)){focus(this.detailsToggle);this.detailsToggle.scrollIntoView({block:'center'});}
    this.mapDetails.hidden=hide;
    if(!this.narrow.matches&&(active===this.detailsToggle||active===this.detailsClose))focus(this.entryFocusTarget());
    this.detailsClose.hidden=!this.narrow.matches;
    this.detailsToggle.textContent=hide?'Show selected details':'Hide selected details';this.detailsToggle.setAttribute('aria-expanded',String(!hide));
  }
  private setDetailsOpen(open:boolean,moveFocus=true):void {
    this.detailsOpen=open;this.presentDetails();if(!moveFocus||!this.narrow.matches)return;
    const target=open?this.entryFocusTarget():this.detailsToggle;focus(target);target?.scrollIntoView({block:'center'});
  }
  private entryFocusTarget():HTMLElement {return this.entry&&!this.entry.element.hidden?this.entry.title:this.retainedEntry?.querySelector<HTMLElement>('h2')??this.detailsHeading??this.reading.querySelector<HTMLElement>('h2')??this.reading;}
  private sourceReturnTarget(trigger:HTMLElement|null):HTMLElement|null {
    if(trigger?.isConnected){if(this.mapDetails?.contains(trigger)&&this.mapDetails.hidden)this.setDetailsOpen(true,false);if(!trigger.closest('[hidden]')&&!trigger.matches(':disabled'))return trigger;}
    if(this.mapDetails?.hidden)return this.detailsToggle;return this.entryFocusTarget();
  }
  private mapFrame():HTMLElement {
    const frame=el('div',undefined,'map-layout'),primary=el('div',undefined,'map-primary');
    this.detailsToggle=button('Hide selected details',()=>this.setDetailsOpen(!this.detailsOpen));this.detailsToggle.id='selected-details-toggle';this.detailsToggle.setAttribute('aria-controls','selected-map-details');
    this.detailsClose=button('Close selected details',()=>this.setDetailsOpen(false));this.detailsHeading=heading('Selected details',3);this.detailsHeading.id='selected-details-title';
    this.mapDetails=el('section',undefined,'map-selected-details');this.mapDetails.id='selected-map-details';this.mapDetails.setAttribute('aria-labelledby',this.detailsHeading.id);
    this.mapDetails.append(this.detailsClose,this.detailsHeading,this.entryHost);this.mapDetails.addEventListener('keydown',event=>{if(event.key==='Escape'&&this.narrow.matches&&!event.defaultPrevented){event.preventDefault();event.stopPropagation();this.setDetailsOpen(false);}});
    primary.append(this.detailsToggle,this.mapView!.element);frame.append(primary,this.mapDetails);this.presentDetails();return frame;
  }
  private currentHash():string {const s=this.client.state;if(!s.route||!s.project)return '';const route=encodeRoute(s.route,s.project.id);return route.ok?route.hash:'';}
  private options():Route['options'] {const s=this.client.state;return {q:s.query??'',category:s.filters.category??'all',lifecycles:s.filters.lifecycles,fact_kinds:s.filters.fact_kinds,predicates:s.filters.predicate_ids,direction:s.filters.direction};}
  private route(destination:Destination,id?:string):Route {return {project_id:this.context!.project.id,destination,...(id?{id}:{}),options:this.options()};}
  async start(fragment:CapturedFragment):Promise<void> {
    this.closeNavigation();++this.routeSerial;this.search.cancelTimer();this.search.hide();const desired=fragment.desired;
    const context=await this.client.connect(fragment);if(!context||context.operation!=='context')return;
    const route=desired?parseRoute(desired,context.project.id):{ok:true as const,route:{project_id:context.project.id,destination:'overview' as const,options:{}}};
    if(!route.ok){this.client.disconnect('This link belongs to another project. Open its correct local reader.');return;}
    this.context=context;++this.sourceSerial;this.source.close();this.model=null;this.mapView?.dispose();this.mapView=null;this.entry=null;this.retainedEntry=null;this.browserHistory.clear();this.historyModels.clear();this.currentHistory=null;
    this.client.state.preferences=this.prefs.bind(context);this.presentPreferences();this.projectName.textContent=context.data.project.name;this.nav();await this.go(route.route,false);
  }
  private nav():void {if(!this.context)return;this.navigation.replaceChildren();for(const [destination,label] of [['overview','Overview'],['terms','Terms'],['processes','Processes'],['map','Map']] as const){const route=this.route(destination,destination==='map'?this.client.state.focus_id??this.client.state.selection?.id:undefined);if(destination==='map'&&this.client.state.focus_id&&this.client.state.selection)route.options.selected=this.client.state.selection.id;const link=routeLink(label,route,value=>void this.go(value));link.dataset.destination=destination;this.navigation.append(link);}}
  private connectionChanged():void {
    const state=this.client.state;this.catalog?.sync();this.close.hidden=!this.client.connected;this.status.replaceChildren();
    if(state.freshness==='disconnected')this.status.append(warning(this.client.message));
    else if(state.refresh)this.status.append(el('p','Refreshing a coherent reading view. The previous snapshot remains visible.'));
    else if(state.freshness==='stale'){this.status.append(warning('This displayed knowledge view is stale. Refresh to read a coherent current snapshot.'),button('Refresh reading view',()=>void this.refresh()));}
    else if(!state.project)this.status.append(el('p',this.client.message));
    const active=Object.keys(state.regional_requests);if(active.length)this.status.append(el('p','Reading '+active.join(', ')+'…','loading'));
    for(const [region,code] of Object.entries(state.regional_errors)){this.status.append(warning(region+': '+errorText(code)));}
    if(state.snapshot){const snapshot=el('details');snapshot.append(el('summary','Displayed knowledge version'),el('code',state.snapshot,'identity'));this.status.append(snapshot);}
    if(state.project&&!state.refresh&&state.freshness==='current')this.status.append(button('Refresh knowledge',()=>void this.refresh(),'quiet'));
  }
  private say(text:string):void {if(text!==this.announcement){this.announcement=text;this.announce.textContent=text;}}
  private savePreferences(preferences:ReturnType<typeof this.prefs.current>):void {this.client.state.preferences=this.prefs.save(preferences);this.presentPreferences();}
  private presentPreferences():void {const p=this.prefs.current();this.theme.value=p.theme;document.documentElement.dataset.theme=p.theme==='system'?(this.color.matches?'dark':'light'):p.theme;this.updateMap();}
  private updateMap(expansionSource?:string):void {if(this.mapView&&this.model)this.mapView.update(this.model,this.client.state.focus_id,this.client.state.selection?.id??null,{dark:document.documentElement.dataset.theme==='dark',reduced:this.motion.matches,camera:this.client.state.camera},expansionSource);}
  private saveBrowserHistory(push:boolean):void {
    const safe=safeHistory(this.client.state,document.activeElement instanceof HTMLElement?document.activeElement.id||null:null);if(!safe)return;
    const id=push||this.currentHistory===null?++this.historySerial:this.currentHistory;this.currentHistory=id;this.browserHistory.set(id,safe);this.historyModels.set(id,this.modelRevision);while(this.browserHistory.size>50){const oldest=this.browserHistory.keys().next().value!;this.browserHistory.delete(oldest);this.historyModels.delete(oldest);}
    history[push?'pushState':'replaceState']({explorer:id},'',location.pathname+safe.route);
  }
  private rememberCurrent():void {if(this.currentHistory!==null){const safe=safeHistory(this.client.state);if(safe){this.browserHistory.set(this.currentHistory,safe);this.historyModels.set(this.currentHistory,this.modelRevision);}}}
  private restoreBrowserHistory():void {
    if(!this.context)return;this.closeNavigation();this.rememberCurrent();this.search.cancelTimer();this.search.hide();const id=history.state?.explorer;const safe=typeof id==='number'?this.browserHistory.get(id):undefined;
    if(safe){const old=this.client.state,transition=restoreHistory({...old,history:[safe],history_index:0},0);if(transition.accepted){this.client.apply(transition);this.currentHistory=id;const sameMap=old.route?.destination==='map'&&transition.state.route?.destination==='map'&&old.focus_id===transition.state.focus_id&&stableJson(old.filters)===stableJson(transition.state.filters)&&stableJson(old.expanded_ids)===stableJson(transition.state.expanded_ids)&&this.historyModels.get(id)===this.modelRevision;
      ++this.routeSerial;++this.sourceSerial;this.source.close();this.search.setValue(transition.state.query??'',true);if(transition.state.freshness==='stale'){this.say('This history entry belongs to an older snapshot. Refresh to restore its reading view.');return;}
      void this.renderRoute(sameMap,true,safe.expanded_ids).then(()=>{const target=safe.focus_target?document.getElementById(safe.focus_target):this.entry?.title??this.reading.querySelector<HTMLElement>('h2');focus(target?.closest('[hidden]')?this.detailsToggle:target);});return;}}
    const captured=captureFragment();if(captured.bootstrap||captured.invalid){void this.start(captured);return;}const parsed=parseRoute(captured.desired,this.context.project.id);if(parsed.ok)void this.go(parsed.route,false);
  }
  async go(route:Route,push=true):Promise<void> {
    if(!this.context)return;this.closeNavigation();this.rememberCurrent();const previous=this.client.state,next=hydrateRoute(previous,route);if(!next){this.say('This local route is invalid for the authenticated project.');return;}
    const sameMap=previous.route?.destination==='map'&&next.route?.destination==='map'&&previous.focus_id===next.focus_id&&stableJson(previous.filters)===stableJson(next.filters);
    this.client.apply({state:next,accepted:true,history:push?'push':'replace',abort:['context','search','entry','relationships','neighborhood','source']});++this.routeSerial;++this.sourceSerial;this.source.close();this.sourceCursor=null;this.search.cancelTimer();this.search.hide();this.search.setValue(next.query??'',true);if(!push)this.currentHistory=null;this.saveBrowserHistory(push);this.nav();
    await this.renderRoute(sameMap,false,[]);
  }
  private async renderRoute(sameMap:boolean,restoring:boolean,expansions:string[]):Promise<void> {
    const state=this.client.state,route=state.route;if(!route||!this.context)return;const serial=this.routeSerial;
    this.catalog?.dispose();this.catalog=null;
    for(const item of this.navigation.querySelectorAll<HTMLElement>('[data-destination]')){const active=route.destination==='entry'?'terms':route.destination==='process'?'processes':route.destination;item.setAttribute('aria-current',item.dataset.destination===active?'page':'false');}
    if(route.destination!=='map'){this.mapView?.dispose();this.mapView=null;this.model=null;this.continuation=null;this.mapDetails=null;this.detailsToggle=null;this.detailsClose=null;this.detailsHeading=null;this.detailsOpen=true;}
    if(route.destination==='overview'){this.entry=null;this.retainedEntry=null;this.reading.replaceChildren(overview(this.context,r=>void this.go(r)));}
    else if(route.destination==='terms'){this.entry=null;this.retainedEntry=null;this.searchResults=el('div');this.reading.replaceChildren(heading(state.query?'Search results':'Terms'),filterControl(this.context,state.filters,value=>this.changeFilters(value)),this.searchResults);await this.searchPage(null);}
    else if(route.destination==='processes'){this.entry=null;this.retainedEntry=null;this.showProcessCatalog(this.context);}
    else if(route.destination==='entry'||route.destination==='process'){this.reading.replaceChildren();this.makeEntry();this.reading.append(this.entryHost);await this.loadEntry(route.destination==='process');}
    else if(route.destination==='map'){
      if(!state.focus_id){this.mapView?.dispose();this.mapView=null;this.model=null;this.entry=null;this.mapDetails=null;this.detailsToggle=null;this.detailsClose=null;this.detailsHeading=null;const picker=el('section');picker.append(heading('Choose a focus'),el('p','Choose a starting term or search for an exact entry. The first map reads only its bounded one-step neighborhood.'));for(const item of this.context.data.starting_points)picker.append(button(item.label,()=>this.focusHere(item.id)));picker.append(button('Browse terms',()=>void this.go(this.route('terms'))));this.reading.replaceChildren(picker);}
      else {
        if(!sameMap&&!await this.normalizeMapFocus(state.focus_id))return;
        if(serial!==this.routeSerial)return;
        if(!sameMap||!this.mapView){if(restoring)this.client.state.expanded_ids=[];this.mapView?.dispose();this.model=null;this.continuation=null;this.makeEntry();this.mapView=new MapView((intent,trigger)=>void this.graphIntent(intent,trigger),camera=>{this.client.apply(navigate(this.client.state,{kind:'camera',camera}));this.saveBrowserHistory(false);},mode=>this.savePreferences({...this.prefs.current(),relationship_view:mode}));this.graphControls=el('div');this.reading.replaceChildren(filterControl(this.context,state.filters,value=>this.changeFilters(value),true),this.graphControls,this.mapFrame());await this.graphRead(state.focus_id,null,false);if(serial!==this.routeSerial)return;this.mapView.show(this.prefs.current().relationship_view,false);}
        else {this.mapView.select(state.selection?.id??null);this.mapView.setCamera(state.camera);}
        if(serial!==this.routeSerial)return;await this.loadEntry(false);
        if(restoring&&serial===this.routeSerial){for(const id of expansions){if(id!==state.focus_id&&this.model?.nodes[id]&&!this.model.local_reasons.length){await this.graphRead(id,null,true);if(serial!==this.routeSerial)break;}}if(!sameMap)this.graphControls.append(el('p','Connections were re-read for this history view. Continue from the returned page to read more.'));}
      }
    }
    if(serial===this.routeSerial&&!sameMap&&!restoring)focus(this.mapDetails?.hidden?this.detailsToggle:this.entryFocusTarget());
  }
  private showProcessCatalog(context:ContextResponse):void {this.catalog?.dispose();this.catalog=new ProcessCatalog(context,this.client.processCatalog(),route=>void this.go(route));this.reading.replaceChildren(this.catalog.element);}
  private makeEntry():void {this.entry?.pending(true);const retained=this.retainedEntry,previous=retained??this.entry?.element??null;this.entry=new EntryView({section:(section,cursor)=>void this.loadSection(section,cursor??null),source:(owner,reference,trigger)=>void this.openSource(owner,reference,trigger),map:()=>this.focusHere(this.client.state.selection!.id),relationships:()=>void this.entryRelationships(),copyId:()=>void this.copy(this.client.state.selection!.id,'Stable ID copied.'),copyLink:()=>void this.copyLocalLink()});this.entryHost=el('div',undefined,'entry-host');if(previous){this.retainedEntry=retained??el('section',undefined,'retained-entry');if(!retained)this.retainedEntry.append(warning('Previous recorded entry retained while the new selection is read. Its controls are temporarily unavailable.'),previous);this.entry.element.hidden=true;this.entryHost.append(this.retainedEntry);}this.entryHost.append(this.entry.element);}
  private showEntryHeader(response:EntryResponse):void {this.retainedEntry?.remove();this.retainedEntry=null;if(this.entry){this.entry.element.hidden=false;this.entry.showHeader(response);}}
  openEntry(id:string):void {if(!this.context)return;const route=this.route('entry',id);void this.go(route);}
  private async loadEntry(process:boolean):Promise<void> {
    const id=this.client.state.selection?.id,serial=this.routeSerial;if(!id||!this.entry)return;
    this.entry.pending(true);const response=await this.client.read('entry',{id,section:'header',cursor:null});if(!response||response.operation!=='entry'||serial!==this.routeSerial)return;
    this.showEntryHeader(response);if(response.data.header?.kind==='relation')this.client.state.selection={kind:'relation',id};this.say('Selected '+(response.data.header?.label??id)+'.');
    const section=process&&response.data.header?.available_sections.includes('process')?'process':response.data.header?.available_sections.includes('definition')?'definition':response.data.header?.available_sections.includes('qualifiers')?'qualifiers':null;
    if(section)await this.loadSection(section,null);
  }
  private async loadSection(section:Section,cursor:string|null):Promise<void> {
    const id=this.client.state.selection?.id,serial=this.routeSerial;if(!id||!this.entry)return;
    const response=await this.client.read('entry',{id,section,cursor});if(!response||response.operation!=='entry'||serial!==this.routeSerial)return;
    if(section==='process')this.entry.replaceSection(processSection(response,id=>this.openEntry(id),(owner,reference,trigger)=>void this.openProcessSource(owner,reference,trigger),()=>void this.loadSection('process',response.page.next_cursor)));
    else this.entry.showSection(response);
  }
  private async previewSearch(text:string,generation:number):Promise<void> {
    const state=this.client.state;if(!this.context||!this.client.connected||!isWire('Query',text))return;
    this.client.state={...state,query:queryText(text)};
const response=await this.client.read('search',this.searchParams(null));if(response?.operation==='search')this.search.suggestions(response,generation);
  }
  private submitSearch(text:string):void {if(!this.context)return;if(!isWire('Query',text)){this.say('The query exceeds the supported size. Shorten it.');return;}const route=this.route('terms');route.options.q=text;void this.go(route);}
  private searchParams(cursor:string|null){const s=this.client.state,context=s.refresh?.context??this.context!;return {query:s.query??'',category:s.filters.category&&context.data.categories.some(item=>item.id===s.filters.category)?s.filters.category:null,lifecycles:s.filters.lifecycles,fact_kinds:s.filters.fact_kinds,sort:s.query?'relevance' as const:'label' as const,limit:context.data.resource_policy.default_page_items,cursor};}
  private async searchPage(cursor:string|null):Promise<void> {const serial=this.routeSerial,response=await this.client.read('search',this.searchParams(cursor));if(!response||response.operation!=='search'||serial!==this.routeSerial)return;this.searchResults.replaceChildren(resultList(response,this.context!,route=>void this.go(route),()=>void this.searchPage(response.page.next_cursor),()=>this.changeFilters({...this.client.state.filters,category:null,lifecycles:[...LIFECYCLES],fact_kinds:[...FACT_KINDS]})));this.say(response.page.returned+' entries returned'+(response.coverage.complete?'.':'; the view is incomplete.'));}
  private changeFilters(filters:Filters):void {const transition=navigate(this.client.state,{kind:'query',query:this.client.state.query??'',filters});if(!transition.accepted){this.say('Choose valid nonempty filters and exact predicate IDs.');return;}const route=this.client.state.route!;void this.go({...route,options:{...route.options,q:transition.state.query??'',category:filters.category??'all',lifecycles:filters.lifecycles,fact_kinds:filters.fact_kinds,predicates:filters.predicate_ids,direction:filters.direction}});}
  private graphParams(id:string,cursor:string|null){const s=this.client.state,p=(s.refresh?.context??this.context!).data.resource_policy;return {id,direction:s.filters.direction,predicate_ids:s.filters.predicate_ids,lifecycles:s.filters.lifecycles,fact_kinds:s.filters.fact_kinds,limit:Math.min(p.initial_edges,p.page_items),node_limit:Math.min(p.initial_nodes,p.display_nodes,p.visited_nodes),cursor};}
  private async graphRead(id:string,cursor:string|null,append:boolean):Promise<void> {
    if(!this.context||this.client.state.refresh)return;const serial=this.routeSerial;
    // Neighborhood is reserved for the actual focus. Expansion uses the same
    // bounded incident-relationship API and keeps focus unchanged.
    const operation=id===this.client.state.focus_id?'neighborhood':'relationships';const params=this.graphParams(id,cursor);const {node_limit,...relations}=params;
    const response=await this.client.read(operation,operation==='neighborhood'?params:relations);if(!response||(response.operation!=='relationships'&&response.operation!=='neighborhood')||serial!==this.routeSerial)return;
    const p=this.context.data.resource_policy,admission=admitGraphPage(append?this.model:null,response,cursor,{nodes:p.display_nodes,edges:p.display_edges,bytes:p.client_model_bytes});
    if(!admission.ok){const message='The returned graph could not be admitted: '+admission.error+'. The previous returned view remains displayed.';this.graphControls.append(warning(message));this.say(message);return;}
    this.model=admission.model;++this.modelRevision;this.continuation=admission.continuation;this.continuationId=id;
    if(append)this.client.apply(navigate(this.client.state,{kind:'expanded',id}));this.updateMap(append?id:undefined);this.graphContinuation();this.rememberCurrent();this.say('Returned connections updated. '+this.model.order.length+' relationship records or detail markers are retained.');
  }
  private graphContinuation():void {
    this.graphControls.replaceChildren();if(!this.continuation)return;
    if(this.continuation.kind==='continue'&&this.continuation.cursor){const cursor=this.continuation.cursor,id=this.continuationId!;this.graphControls.append(button('Continue connections',()=>void this.graphRead(id,cursor,true)));}
    else if(this.continuation.kind==='retry_after_reset'){const cursor=this.continuation.pre_request_cursor,id=this.continuationId!;this.graphControls.append(warning(this.continuation.message),button('Reset returned scope and read remaining page',()=>void this.graphRead(id,cursor,false)));}
  }
  private async normalizeMapFocus(id:string):Promise<boolean> {
    // An explicit focus+selection route already names the intended returned
    // node, including unusual endpoint kinds. Only bare relation intent changes focus.
    if(this.client.state.route?.options.selected!==undefined)return true;
    const inspector=this.client.inspectFocus(id);if(!inspector)return false;
    const header=await inspector.entry(id,'header',null);if(!header||!inspector.valid())return false;
    if(header.data.header?.kind!=='relation')return true;
    const parser=new EndpointStrings();let cursor:string|null=null,offset=0,finished=false;const pending=el('section');pending.append(heading('Read this relationship on the map'),el('p','Resolving the recorded subject before displaying this relationship.'));
    this.reading.replaceChildren(pending);
    const step=async():Promise<void>=>{
      pending.replaceChildren(heading('Read this relationship on the map'),el('p','Reading its exact canonical subject…'));
      for(let reads=0;reads<8;reads++){
        const details=await inspector.entry(id,'details',cursor);if(!details||!inspector.valid())return;
        for(const chunk of details.data.chunks){if(finished||chunk.field!=='details'||chunk.encoding!=='canonical_json'||chunk.item_index!==null||chunk.offset!==offset){pending.append(warning('The continued relationship details were inconsistent. Reopen the entry.'));return;}parser.feed(chunk.text);offset+=new TextEncoder().encode(chunk.text).length;finished=!chunk.more_in_field;}
        cursor=details.page.next_cursor;if(cursor===null){if(!finished||!parser.fields.subject){pending.append(warning('The recorded subject could not be read. The relationship remains available in its entry.'));return;}
          const route=this.route('map',parser.fields.subject);route.options.selected=id;await this.go(route,false);return;}
      }
      pending.append(el('p','Canonical details continue. No endpoint has been inferred.'),button('Continue reading relationship focus',()=>void step()));
    };await step();return false;
  }
  private focusHere(id:string,explicit=false):void {this.mapView?.dispose();this.mapView=null;this.model=null;const route=this.route('map',id);if(explicit)route.options.selected=id;void this.go(route);}
  private async graphIntent(intent:ModelIntent,trigger?:HTMLElement):Promise<void> {
    if(!this.model||!resolveIntent(this.model,intent))return;
    if(intent.kind==='focus'){this.focusHere(intent.id,true);return;}if(intent.kind==='expand'){if(this.model.local_reasons.length){this.graphControls.append(warning('The display limit is reached. Use Focus here, narrow the filters, or reset the returned scope before continuing.'));return;}if(this.continuationId===intent.id&&this.continuation?.kind==='continue'){if(this.continuation.cursor)await this.graphRead(intent.id,this.continuation.cursor,true);else this.graphControls.append(el('p','This returned connection sequence has no continuation. Inspect detail markers or use Focus here to read another scope.'));return;}if(this.client.state.expanded_ids.includes(intent.id)){this.graphControls.append(el('p','This term has already been expanded. Use Focus here to read its complete bounded sequence separately.'));return;}await this.graphRead(intent.id,null,true);return;}
    if(intent.kind==='inspectSource'){if(trigger)await this.openSource(intent.owner_id,intent.reference_id,trigger);return;}
    const id=intent.id,marker=this.model.markers[intent.id];if(intent.kind==='inspectPredicate'){this.openEntry(id);return;}
    const route=this.route('map',this.client.state.focus_id??undefined);route.options.selected=id;const navigation=this.go(route),serial=this.routeSerial;await navigation;if(marker&&serial===this.routeSerial&&this.client.state.selection?.id===id)await this.loadSection(marker.detail.section,null);
  }
  private async entryRelationships(cursor:string|null=null):Promise<void> {
    const id=this.client.state.selection?.id,serial=this.routeSerial;if(!id||!this.context||!this.entry)return;
    const {node_limit,...params}=this.graphParams(id,cursor),response=await this.client.read('relationships',params);if(!response||response.operation!=='relationships'||serial!==this.routeSerial)return;
    const p=this.context.data.resource_policy,admission=admitGraphPage(null,response,cursor,{nodes:p.display_nodes,edges:p.display_edges,bytes:p.client_model_bytes});if(!admission.ok)return;
    const model=admission.model;const view=el('section');view.append(modelSummary(model),relationshipList(model,(intent,trigger)=>{if(intent.kind==='inspectSource'){if(trigger)void this.openSource(intent.owner_id,intent.reference_id,trigger);}else if(intent.kind==='focus'||intent.kind==='expand')this.focusHere(intent.id);else this.openEntry(intent.id);},id));if(admission.continuation.kind==='continue'&&admission.continuation.cursor)view.append(button('Continue relationships',()=>void this.entryRelationships(response.page.next_cursor)));this.entry.replaceSection(view);
  }
  private async openSource(owner:string,reference:string,trigger:HTMLElement):Promise<void> {++this.sourceSerial;this.client.apply(navigate(this.client.state,{kind:'source',owner_id:owner,reference_id:reference}));this.sourceCursor=null;this.source.open(trigger);await this.readSource(null);}
  private async readSource(cursor:string|null):Promise<void> {const selected=this.client.state.source_selection,serial=this.sourceSerial;if(!selected)return;const response=await this.client.read('source',{...selected,cursor});if(serial!==this.sourceSerial)return;if(response?.operation==='source'){this.sourceCursor=response.page.next_cursor;this.source.show(response);}else {const code=this.client.state.regional_errors.source;if(code)this.source.error(errorText(code));}}
  private closeSource():void {this.client.apply(navigate(this.client.state,{kind:'closeSource'}));this.sourceCursor=null;++this.sourceSerial;this.source.close();}
  private async openProcessSource(owner:string,reference:string,trigger:HTMLElement):Promise<void> {
    const id=this.client.state.selection?.id;if(!id)return;
    this.client.apply(navigate(this.client.state,{kind:'closeSource'}));const serial=++this.sourceSerial;
    const reader=this.client.discover(id,reference);if(!reader)return;const discovery=new ProcessSourceDiscovery(id,reference,reader);this.source.open(trigger);
    const step=async()=>{this.source.progress('Resolving the exact recorded source descriptor from this process and its documented support…');const progress=await discovery.step();if(!reader.valid()||serial!==this.sourceSerial)return;
      if(progress.kind==='found')await this.openSource(progress.reference.owner_id,progress.reference.reference_id,trigger);
      else if(progress.kind==='continue')this.source.progress('Source discovery is incomplete after '+progress.reads+' bounded reads across '+progress.candidates+' candidate entries. Continue to inspect the remaining documented support.',()=>void step());
      else this.source.progress(progress.message);
    };await step();
  }

  private async copy(value:string,message:string):Promise<void> {try{await navigator.clipboard.writeText(value);this.say(message);}catch{const text=el('textarea');text.readOnly=true;text.value=value;const box=el('div');box.append(labeled('Select and copy',text),button('Close copy field',()=>box.remove()));this.status.append(box);text.focus();text.select();}}
  private async copyLocalLink():Promise<void> {const state=this.client.state;if(!state.route||!state.project)return;const route=encodeRoute(state.route,state.project.id);if(!route.ok)return;await this.copy(location.origin+location.pathname+route.hash,'Local link copied. It needs the correct running local reader and a current session.'+(route.notice?' '+route.notice:''));}
  private async refresh():Promise<void> {
    if(!this.context||!this.client.connected)return;const route=this.client.state.route,serial=this.routeSerial;if(!route)return;
    const required:Region[]=[];if(route.destination==='terms')required.push('search');if(this.client.state.selection&&(route.destination==='entry'||route.destination==='process'||route.destination==='map'))required.push('entry');if(route.destination==='map'&&this.client.state.focus_id)required.push('neighborhood');
    if(!this.client.apply(beginRefresh(this.client.state,required)))return;
    const context=await this.client.read('context',{refresh:true},'refresh');if(!context||context.operation!=='context'||serial!==this.routeSerial)return;
    let header:EntryResponse|null=null,section:EntryResponse|null=null,newModel:RelationshipModel|null=null,newContinuation:ContinuationIntent|null=null,search:SuccessResponse|null=null;
    if(required.includes('search'))search=await this.client.read('search',this.searchParams(null),'refresh');
    if(required.includes('entry')){const id=this.client.state.selection!.id;const result=await this.client.read('entry',{id,section:'header',cursor:null},'refresh');if(result?.operation==='entry'){header=result;const selectedSection=route.destination==='process'&&result.data.header?.available_sections.includes('process')?'process':result.data.header?.available_sections.includes('definition')?'definition':null;if(selectedSection){const page=await this.client.read('entry',{id,section:selectedSection,cursor:null},'refresh');if(page?.operation==='entry')section=page;else return;}}else return;}
    if(required.includes('neighborhood')){const response=await this.client.read('neighborhood',this.graphParams(this.client.state.focus_id!,null),'refresh');if(!response||response.operation!=='neighborhood')return;const p=context.data.resource_policy,admission=admitGraphPage(null,response,null,{nodes:p.display_nodes,edges:p.display_edges,bytes:p.client_model_bytes});if(!admission.ok){this.client.state.refresh=null;this.client.state.freshness='stale';this.connectionChanged();return;}newModel=admission.model;newContinuation=admission.continuation;}
    if(serial!==this.routeSerial||!this.client.apply(commitRefresh(this.client.state)))return;
    this.context=context;++this.sourceSerial;this.source.close();this.sourceCursor=null;this.model=newModel;++this.modelRevision;this.continuation=newContinuation;this.continuationId=this.client.state.focus_id;this.prefs.bind(context);if(this.client.state.route)this.client.state.route.options.category=this.client.state.filters.category??'all';this.nav();this.saveBrowserHistory(false);
    if(route.destination==='terms'&&search?.operation==='search')this.searchResults.replaceChildren(resultList(search,context,r=>void this.go(r),()=>void this.searchPage(search!.page.next_cursor),()=>this.changeFilters({...this.client.state.filters,category:null})));
    else if(header&&this.entry){this.showEntryHeader(header);if(section){if(section.data.section==='process')this.entry.replaceSection(processSection(section,id=>this.openEntry(id),(owner,reference,trigger)=>void this.openProcessSource(owner,reference,trigger),()=>void this.loadSection('process',section!.page.next_cursor)));else this.entry.showSection(section);}this.updateMap();this.graphContinuation();}
    else if(route.destination==='overview')this.reading.replaceChildren(overview(context,r=>void this.go(r)));else if(route.destination==='processes')this.showProcessCatalog(context);
    const filters=this.reading.querySelector('.filter-control');if(filters&&(route.destination==='terms'||route.destination==='map')){const open=filters.querySelector('details')?.open??false,next=filterControl(context,this.client.state.filters,value=>this.changeFilters(value),route.destination==='map');next.querySelector('details')!.open=open;filters.replaceWith(next);}
    this.say('A coherent current snapshot is now displayed. Previous expansions, source reading and continuations were cleared.');
  }
}
