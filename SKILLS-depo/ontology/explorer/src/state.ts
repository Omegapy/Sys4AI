import {FACT_KINDS,LIFECYCLES,isWire,normalizeQuery,queryText,responseSemantics,stableJson,utf8Length} from './contracts';
import type {ContextResponse,Digest,Id,ProjectIdentity,ReadResponse,ResponseExpectation,SessionResponse,SuccessResponse,Cursor,Direction,Lifecycle,FactKind} from './contracts';
import {encodeRoute,parseRoute} from './routes';
import type {Route} from './routes';
import {DEFAULT_PREFERENCES,validPreferences} from './preferences';
import type {Preferences} from './preferences';

export const REGIONS=['context','search','entry','relationships','neighborhood','source'] as const;
export type Region=typeof REGIONS[number];
export type Selection={kind:'entry'|'relation';id:Id}|null;
export interface Filters {category:string|null; lifecycles:Lifecycle[];fact_kinds:FactKind[];predicate_ids:Id[];direction:Direction}
export interface Ticket {region:Region;sequence:number;route_generation:number;scope_key:string;target:'visible'|'refresh';refresh_generation:number|null;expected:ResponseExpectation}
export interface SafeCamera {x:number;y:number;zoom:number}
export interface SafeHistory {route:string;snapshot:Digest|null;selection:Selection;focus_id:Id|null;query:string|null;filters:Filters;expanded_ids:Id[];camera:SafeCamera|null;focus_target:string|null}
export interface RefreshStage {generation:number;required:Region[];context:ContextResponse|null;content:Partial<Record<Region,SuccessResponse>>}
export interface ReaderState {
  project:ProjectIdentity|null;root_scope_id:Digest|null;service_instance:string|null;session_scope:string|null;code_epoch:Digest|null;snapshot:Digest|null;
  route:Route|null;route_generation:number;selection:Selection;focus_id:Id|null;query:string|null;filters:Filters;expanded_ids:Id[];
  source_selection:{owner_id:Id;reference_id:Digest}|null;preferences:Preferences;
  regional_requests:Partial<Record<Region,Ticket>>;regional_sequences:Record<Region,number>;regional_errors:Partial<Record<Region,string>>;
  cursors:Partial<Record<Region,Cursor>>;content:Partial<Record<Region,SuccessResponse>>;refresh:RefreshStage|null;refresh_generation:number;
  freshness:'unconnected'|'current'|'stale'|'disconnected';history:SafeHistory[];history_index:number;camera:SafeCamera|null;
}
export type StateTransition={state:ReaderState;accepted:boolean;history:'push'|'replace'|'none';abort:Region[]};
function filters():Filters {return {category:null,lifecycles:['approved'],fact_kinds:['asserted'],predicate_ids:[],direction:'both'};}
export function createReaderState():ReaderState {return {project:null,root_scope_id:null,service_instance:null,session_scope:null,code_epoch:null,snapshot:null,route:null,route_generation:0,selection:null,focus_id:null,query:null,filters:filters(),expanded_ids:[],source_selection:null,preferences:{...DEFAULT_PREFERENCES},regional_requests:{},regional_sequences:{context:0,search:0,entry:0,relationships:0,neighborhood:0,source:0},regional_errors:{},cursors:{},content:{},refresh:null,refresh_generation:0,freshness:'unconnected',history:[],history_index:-1,camera:null};}
function result(state:ReaderState,accepted=true,history:StateTransition['history']='none',abort:Region[]=[]):StateTransition{return {state,accepted,history,abort};}
function stopRequests(s:ReaderState):Region[] {const active=Object.keys(s.regional_requests) as Region[];s.regional_requests={};return active;}
/** Metadata projection only: csrf/bootstrap/cookie values never enter state. */
export function connectIdentity(state:ReaderState,session:SessionResponse):StateTransition {
  if (!isWire('SessionResponse',session)) return result(state,false);
  const s=structuredClone(state),abort=stopRequests(s);
  s.service_instance=session.service_instance;s.session_scope=session.session_scope;s.code_epoch=session.code_epoch;s.cursors={};s.refresh=null;s.freshness=s.snapshot?'stale':'unconnected';
  return result(s,true,'none',abort);
}
function validFilters(v:Filters):boolean{return isWire('LF',v.lifecycles)&&isWire('FF',v.fact_kinds)&&isWire('PredicateIds',v.predicate_ids)&&isWire('Direction',v.direction)&&(v.category===null||isWire('CategoryId',v.category))&&Object.keys(v).length===5;}
function cleanFilters(v:Filters):Filters{return {category:v.category==='all'?null:v.category,lifecycles:LIFECYCLES.filter(x=>v.lifecycles.includes(x)),fact_kinds:FACT_KINDS.filter(x=>v.fact_kinds.includes(x)),predicate_ids:[...v.predicate_ids].sort(),direction:v.direction};}
function validCamera(v:SafeCamera|null):boolean{return v===null || Object.keys(v).length===3 && [v.x,v.y,v.zoom].every(Number.isFinite)&&Math.abs(v.x)<=1000000&&Math.abs(v.y)<=1000000&&v.zoom>=0.01&&v.zoom<=100;}
function validSelection(v:Selection):boolean{return v===null || Object.keys(v).length===2&&(v.kind==='entry'||v.kind==='relation')&&isWire('Id',v.id);}
export function safeHistory(state:ReaderState,focusTarget:string|null=null):SafeHistory|null {
  if (!state.project||!state.route||!validSelection(state.selection)||!validFilters(state.filters)||!validCamera(state.camera)||state.expanded_ids.length>100||!state.expanded_ids.every(x=>isWire('Id',x))||new Set(state.expanded_ids).size!==state.expanded_ids.length||!isWire('Query',state.query??'')||focusTarget!==null&&!/^[a-zA-Z][a-zA-Z0-9_-]{0,79}$/u.test(focusTarget)) return null;
  const encoded=encodeRoute(state.route,state.project.id);if(!encoded.ok)return null;
  return {route:encoded.hash,snapshot:state.snapshot,selection:state.selection?{...state.selection}:null,focus_id:state.focus_id,query:state.query,filters:cleanFilters(state.filters),expanded_ids:[...state.expanded_ids],camera:state.camera?{...state.camera}:null,focus_target:focusTarget};
}
function pushHistory(s:ReaderState):void {const h=safeHistory(s);if(h){s.history=s.history.slice(0,s.history_index+1);s.history.push(h);s.history=s.history.slice(-50);s.history_index=s.history.length-1;}}
export type NavigationIntent={kind:'select';selection:Exclude<Selection,null>;route:Route}|{kind:'focus';id:Id;route:Route}|{kind:'route';route:Route}|{kind:'query';query:string;filters:Filters}|{kind:'camera';camera:SafeCamera}|{kind:'preferences';preferences:Preferences}|{kind:'source';owner_id:Id;reference_id:Digest}|{kind:'closeSource'}|{kind:'expanded';id:Id};
export function navigate(state:ReaderState,intent:NavigationIntent):StateTransition {
  const s=structuredClone(state);
  if(intent.kind==='camera'){if(!validCamera(intent.camera))return result(state,false);s.camera={...intent.camera};const h=safeHistory(s);if(h&&s.history_index>=0)s.history[s.history_index]=h;return result(s,true,'replace');}
  if(intent.kind==='preferences'){if(!validPreferences(intent.preferences))return result(state,false);s.preferences={...intent.preferences};return result(s);}
  if(intent.kind==='expanded'){if(!isWire('Id',intent.id)||s.expanded_ids.length>=100)return result(state,false);if(!s.expanded_ids.includes(intent.id))s.expanded_ids.push(intent.id);return result(s);}
  if(intent.kind==='source'){if(!isWire('Id',intent.owner_id)||!isWire('Digest',intent.reference_id))return result(state,false);s.source_selection={owner_id:intent.owner_id,reference_id:intent.reference_id};delete s.regional_requests.source;delete s.cursors.source;return result(s,true,'none',['source']);}
  if(intent.kind==='closeSource'){s.source_selection=null;delete s.content.source;delete s.regional_requests.source;delete s.cursors.source;return result(s,true,'none',['source']);}
  if(intent.kind==='query') {
    if(!isWire('Query',intent.query)||!validFilters(intent.filters))return result(state,false);
    s.query=queryText(intent.query);s.filters=cleanFilters(intent.filters);s.expanded_ids=[];
    if(s.route)s.route={...s.route,options:{...s.route.options,q:s.query??'',category:s.filters.category??'all',lifecycles:s.filters.lifecycles,fact_kinds:s.filters.fact_kinds,predicates:s.filters.predicate_ids,direction:s.filters.direction}};
  } else {
    if(!s.project)return result(state,false);const e=encodeRoute(intent.route,s.project.id);if(!e.ok)return result(state,false);
    const parsed=parseRoute(e.hash,s.project.id);if(!parsed.ok)return result(state,false);s.route=parsed.route;
    if(intent.kind==='select'){if(!validSelection(intent.selection))return result(state,false);s.selection={...intent.selection};}
    if(intent.kind==='focus'){if(!isWire('Id',intent.id))return result(state,false);s.focus_id=intent.id;s.expanded_ids=[];s.camera=null;}
  }
  s.route_generation++;s.refresh=null;s.source_selection=null;s.cursors={};const abort=stopRequests(s);pushHistory(s);return result(s,true,'push',abort);
}
export function beginRequest(state:ReaderState,region:Region,requestId:string,scope:SuccessResponse['scope'],target:'visible'|'refresh'='visible'):{state:ReaderState;ticket:Ticket|null;abort:Region[]} {
  if(!REGIONS.includes(region)||!isWire('RequestId',requestId)||!state.code_epoch||!state.service_instance||!state.session_scope||state.freshness==='disconnected'||target==='visible'&&state.refresh!==null||target==='refresh'&&state.refresh===null)return {state,ticket:null,abort:[]};
  const s=structuredClone(state);let context=state.content.context?.operation==='context'?state.content.context:null;
  if(target==='refresh'&&s.refresh?.context)context=s.refresh.context;
  const scopeNames={context:'ContextScope',search:'SearchScope',entry:'EntryScope',relationships:'RelationshipsScope',neighborhood:'NeighborhoodScope',source:'SourceScope'} as const;
  if(!isWire(scopeNames[region],scope)||region!=='context'&&(!context||target==='refresh'&&!s.refresh?.context))return {state,ticket:null,abort:[]};
  if(region==='context'&&'refresh' in scope&&(target==='refresh'?!scope.refresh:state.snapshot!==null&&scope.refresh))return {state,ticket:null,abort:[]};
  if(region==='search'&&'query'in scope&&(scope.query!==s.query||scope.normalized_query!==(s.query===null?null:normalizeQuery(s.query))||scope.category!==s.filters.category||stableJson(scope.lifecycles)!==stableJson(s.filters.lifecycles)||stableJson(scope.fact_kinds)!==stableJson(s.filters.fact_kinds)))return {state,ticket:null,abort:[]};
  if(region==='entry'&&'id'in scope&&s.selection?.id!==scope.id)return {state,ticket:null,abort:[]};
  if(region==='source'&&'owner_id'in scope&&(scope.owner_id!==s.source_selection?.owner_id||scope.reference_id!==s.source_selection?.reference_id))return {state,ticket:null,abort:[]};
  if ((region==='relationships'||region==='neighborhood') && 'predicate_ids' in scope && (scope.direction!==s.filters.direction||stableJson(scope.predicate_ids)!==stableJson(s.filters.predicate_ids)||stableJson(scope.lifecycles)!==stableJson(s.filters.lifecycles)||stableJson(scope.fact_kinds)!==stableJson(s.filters.fact_kinds)||region==='neighborhood'&&scope.id!==s.focus_id)) return {state,ticket:null,abort:[]};
  const expected:ResponseExpectation={operation:region,request_id:requestId,code_epoch:s.code_epoch!,service_instance:s.service_instance!,session_scope:s.session_scope!,project:s.project,snapshot:region==='context'?target==='refresh'?null:s.snapshot:context!.snapshot,scope:structuredClone(scope),policy:context?.data.resource_policy??null};
  const ticket:Ticket={region,sequence:++s.regional_sequences[region],route_generation:s.route_generation,scope_key:stableJson(scope),target,refresh_generation:target==='refresh'?s.refresh!.generation:null,expected};
  const abort=s.regional_requests[region]?[region]:[];s.regional_requests[region]=ticket;delete s.regional_errors[region];return {state:s,ticket,abort};
}
function ticketCurrent(s:ReaderState,t:Ticket):boolean {const pending=s.regional_requests[t.region];return !!pending&&stableJson(pending)===stableJson(t)&&t.sequence===s.regional_sequences[t.region]&&t.route_generation===s.route_generation&&t.expected.code_epoch===s.code_epoch&&t.expected.service_instance===s.service_instance&&t.expected.session_scope===s.session_scope&&(t.target==='visible'||t.refresh_generation===s.refresh?.generation);}
export function applyResponse(state:ReaderState,ticket:Ticket,response:ReadResponse):StateTransition {
  if(!ticketCurrent(state,ticket))return result(state,false);
  if(!responseSemantics(response,ticket.expected))return failRequest(state,ticket,'invalid_response');
  if(response.status==='error')return failRequest(state,ticket,response.error.code);
  const s=structuredClone(state);delete s.regional_requests[ticket.region];delete s.regional_errors[ticket.region];
  if(ticket.target==='refresh'){
    if(!s.refresh)return result(state,false);
    if(response.operation==='context')s.refresh.context=structuredClone(response);
    s.refresh.content[ticket.region]=structuredClone(response);if(utf8Length(JSON.stringify({visible:s.content,staged:s.refresh.content}))>262144)return failRequest(state,ticket,'resource_limit');return result(s);
  }
  if(response.operation==='context') {
    if(s.project&&stableJson(s.project)!==stableJson(response.project)){const clean=createReaderState();clean.service_instance=s.service_instance;clean.session_scope=s.session_scope;clean.code_epoch=s.code_epoch;Object.assign(s,clean);}
    s.project=structuredClone(response.project);s.root_scope_id=response.project.root_scope_id;s.snapshot=response.snapshot;s.freshness='current';
    if(!s.route)s.route={project_id:response.project.id,destination:'overview',options:{}};
  }
  s.content[ticket.region]=structuredClone(response);if(utf8Length(JSON.stringify(s.content))>262144)return failRequest(state,ticket,'resource_limit');if(response.page.next_cursor)s.cursors[ticket.region]=response.page.next_cursor;else delete s.cursors[ticket.region];return result(s);
}
export function failRequest(state:ReaderState,ticket:Ticket,code:string):StateTransition {
  if(!ticketCurrent(state,ticket))return result(state,false);
  const s=structuredClone(state);delete s.regional_requests[ticket.region];s.regional_errors[ticket.region]=isWire('ErrorCode',code)||code==='invalid_response'?code:'invalid_response';
  if(ticket.target==='refresh'){s.refresh=null;s.freshness='stale';return result(s,true,'none',stopRequests(s));}
  if(['snapshot_changed','cursor_expired','source_observation_changed'].includes(code))s.freshness='stale';
  if(['package_changed','session_expired','session_invalid','csrf_forbidden'].includes(code)){s.freshness='disconnected';s.cursors={};s.refresh=null;s.session_scope=null;return result(s,true,'none',stopRequests(s));}
  return result(s);
}
export function beginRefresh(state:ReaderState,required:Region[]):StateTransition {
  if(!state.project||!state.snapshot||!state.code_epoch||!state.session_scope||state.refresh||required.some(r=>!REGIONS.includes(r)||r==='context'||r==='source')||new Set(required).size!==required.length)return result(state,false);
  const s=structuredClone(state),abort=stopRequests(s);s.refresh={generation:++s.refresh_generation,required:[...required],context:null,content:{}};s.freshness='stale';return result(s,true,'none',abort);
}
export function commitRefresh(state:ReaderState):StateTransition {
  const stage=state.refresh;if(!stage?.context||stage.required.some(r=>!stage.content[r]))return result(state,false);
  const context=stage.context;
  if(context.code_epoch!==state.code_epoch||context.service_instance!==state.service_instance||context.session_scope!==state.session_scope||stableJson(context.project)!==stableJson(state.project)||Object.values(stage.content).some(r=>r.snapshot!==context.snapshot||r.code_epoch!==context.code_epoch))return result(state,false);
  const s=structuredClone(state);s.snapshot=context.snapshot;s.content=structuredClone(stage.content);s.content.context=structuredClone(context);s.expanded_ids=[];s.source_selection=null;s.cursors={};s.refresh=null;s.freshness='current';const abort=stopRequests(s);
  if(s.filters.category!==null&&!context.data.categories.some(x=>x.id===s.filters.category)){s.filters.category=null;s.regional_errors.context='category_unavailable';}
  return result(s,true,'none',abort);
}
export function restoreHistory(state:ReaderState,index:number):StateTransition {
  if(!Number.isInteger(index)||index<0||index>=state.history.length||!state.project)return result(state,false);
  const h=state.history[index]!,route=parseRoute(h.route,state.project.id);if(!route.ok)return result(state,false);
  const s=structuredClone(state);s.history_index=index;s.route=route.route;s.selection=structuredClone(h.selection);s.focus_id=h.focus_id;s.query=h.query;s.filters=structuredClone(h.filters);s.expanded_ids=[...h.expanded_ids];s.camera=h.camera?{...h.camera}:null;s.route_generation++;s.source_selection=null;s.cursors={};s.refresh=null;if(h.snapshot!==s.snapshot)s.freshness='stale';return result(s,true,'none',stopRequests(s));
}
