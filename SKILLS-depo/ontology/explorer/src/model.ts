import {isWire, responseSemantics, stableJson, utf8Length} from './contracts';
import type {Coverage, Cursor, Diagnostic, Edge, Id, Marker, NeighborhoodResponse, Node, ProjectIdentity, ReadLimits, RelationshipsResponse, SuccessResponse} from './contracts';
export type GraphResponse = NeighborhoodResponse | RelationshipsResponse;
export interface ModelRead {scope:GraphResponse['scope']; operation:GraphResponse['operation']; coverage:Coverage; limits:ReadLimits; status:SuccessResponse['status']; diagnostics:Diagnostic[]; received:number; admitted:number; has_more:boolean|null}
export interface RelationshipModel {
  identity:{project:ProjectIdentity; snapshot:string; code_epoch:string; service_instance:string; session_scope:string};
  nodes:Record<Id,Node>; edges:Record<Id,Edge>; markers:Record<Id,Marker>;
  order:Id[]; reads:ModelRead[]; local_reasons:('display_limit')[];
}
export interface ModelBounds {nodes:number; edges:number; bytes:number}
export type ContinuationIntent = {kind:'continue'; cursor:Cursor|null; has_more:boolean|null} | {kind:'retry_after_reset'; pre_request_cursor:Cursor|null; admitted:number; discarded:number; message:string};
export type ModelAdmission = {ok:true; model:RelationshipModel; continuation:ContinuationIntent} | {ok:false; error:'invalid_response'|'model_scope_changed'|'model_conflict'|'invalid_limits'};
export type ModelIntent = {kind:'selectNode'|'selectEdge'|'focus'|'expand'; id:Id} | {kind:'inspectPredicate'; id:Id} | {kind:'inspectSource'; owner_id:Id; reference_id:string};
const DEFAULT_BOUNDS:ModelBounds={nodes:100,edges:200,bytes:2097152};
function identity(r:GraphResponse):RelationshipModel['identity'] { return {project:r.project,snapshot:r.snapshot,code_epoch:r.code_epoch,service_instance:r.service_instance,session_scope:r.session_scope}; }
function filters(s:GraphResponse['scope']):unknown { return {direction:s.direction,predicate_ids:s.predicate_ids,lifecycles:s.lifecycles,fact_kinds:s.fact_kinds}; }
function fits(m:RelationshipModel,b:ModelBounds):boolean { return Object.keys(m.nodes).length<=b.nodes && Object.keys(m.edges).length+Object.keys(m.markers).length<=b.edges && utf8Length(JSON.stringify(m))<=b.bytes; }
/** Complete-prefix admission. Discarded suffixes never advance continuation.
 * No renderer, fetch, browser storage, source body or full knowledge cache. */
export function admitGraphPage(current:RelationshipModel|null, response:GraphResponse, preRequestCursor:Cursor|null, requested:Partial<ModelBounds>={}):ModelAdmission {
  if (!responseSemantics(response) || preRequestCursor!==null && !isWire('Cursor',preRequestCursor)) return {ok:false,error:'invalid_response'};
  const bounds={...DEFAULT_BOUNDS,...requested};
  if (Object.keys(requested).some(k=>!['nodes','edges','bytes'].includes(k)) || !Object.values(bounds).every(x=>Number.isSafeInteger(x)&&x>0) || bounds.nodes>100 || bounds.edges>200 || bounds.bytes>2097152) return {ok:false,error:'invalid_limits'};
  if (current && (stableJson(current.identity)!==stableJson(identity(response)) || current.reads.some(x=>stableJson(filters(x.scope))!==stableJson(filters(response.scope))))) return {ok:false,error:'model_scope_changed'};
  let model:RelationshipModel=current?structuredClone(current):{identity:structuredClone(identity(response)),nodes:{},edges:{},markers:{},order:[],reads:[],local_reasons:[]};
  if (!fits(model,bounds)) return {ok:false,error:'invalid_limits'};
  const nodes=new Map(response.data.nodes.map(n=>[n.id,n]));
  const read:ModelRead={scope:structuredClone(response.scope),operation:response.operation,coverage:structuredClone(response.coverage),limits:structuredClone(response.limits),status:response.status,diagnostics:structuredClone(response.diagnostics),received:response.data.items.length,admitted:0,has_more:response.page.has_more};
  model.reads.push(read);
  if (response.operation==='neighborhood') { const focus=nodes.get(response.data.focus); if (focus) { const trial=structuredClone(model); trial.nodes[focus.id]=structuredClone(focus); if (fits(trial,bounds)) model=trial; } }
  let admitted=0, conflict=false;
  for (const item of response.data.items) {
    const trial=structuredClone(model), id=item.kind==='edge'?item.edge.id:item.id;
    if (item.kind==='edge') {
      if (trial.markers[id] || trial.edges[id] && stableJson(trial.edges[id])!==stableJson(item.edge)) { conflict=true; break; }
      for (const endpoint of new Set([item.edge.subject,item.edge.object])) {
        const node=nodes.get(endpoint)!;
        if (trial.nodes[endpoint] && stableJson(trial.nodes[endpoint])!==stableJson(node)) { conflict=true; break; }
        trial.nodes[endpoint]=structuredClone(node);
      }
      trial.edges[id]=structuredClone(item.edge);
    } else {
      if (trial.edges[id] || trial.markers[id] && stableJson(trial.markers[id])!==stableJson(item)) { conflict=true; break; }
      trial.markers[id]=structuredClone(item);
    }
    if (conflict) break;
    if (!trial.order.includes(id)) trial.order.push(id);
    trial.reads[trial.reads.length-1]!.admitted=admitted+1;
    // Reserve the local warning in the measured model so the final warning can
    // never push an accepted prefix beyond its byte ceiling.
    trial.local_reasons=['display_limit'];
    if (!fits(trial,bounds)) break;
    admitted++; model=trial;
  }
  if (conflict) return {ok:false,error:'model_conflict'};
  const discarded=response.data.items.length-admitted;
  if (discarded) model.local_reasons=['display_limit'];
  else model.local_reasons=current?.local_reasons.length?['display_limit']:[];
  if (!fits(model,bounds)) return {ok:false,error:'invalid_limits'};
  return {ok:true,model,continuation:discarded?{kind:'retry_after_reset',pre_request_cursor:preRequestCursor,admitted,discarded,message:'Display limit reached. Choose a new focus, change filters, or reset this view before reading the remaining items.'}:{kind:'continue',cursor:response.page.next_cursor,has_more:response.page.has_more}};
}
export function orderedRelationships(model:RelationshipModel):(Edge|Marker)[] { return model.order.map(id=>model.edges[id]??model.markers[id]!).filter((x):x is Edge|Marker=>x!==undefined); }
export function resolveIntent(model:RelationshipModel,intent:ModelIntent):ModelIntent|null {
  if (intent.kind==='inspectSource') return isWire('Id',intent.owner_id)&&isWire('Digest',intent.reference_id)&&Object.values(model.edges).some(e=>e.id===intent.owner_id&&e.source_references.some(s=>s.reference_id===intent.reference_id))?{...intent}:null;
  if (!isWire('Id',intent.id)) return null;
  if (intent.kind==='selectEdge') return model.edges[intent.id]||model.markers[intent.id]?{...intent}:null;
  if (intent.kind==='inspectPredicate') return Object.values(model.edges).some(e=>e.predicate===intent.id)?{...intent}:null;
  return model.nodes[intent.id]?{...intent}:null;
}
