import type {SuccessResponse,SourceRef,Lifecycle,FactKind,SourceState} from './contracts';
export function el<K extends keyof HTMLElementTagNameMap>(tag:K,text?:string,className?:string):HTMLElementTagNameMap[K] {
  const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;
}
export function button(label:string,action:()=>void,className?:string):HTMLButtonElement {
  const node=el('button',label,className);node.type='button';node.addEventListener('click',action);return node;
}
export function heading(text:string,level:2|3=2):HTMLHeadingElement {const node=el(level===2?'h2':'h3',text);node.tabIndex=-1;return node;}
export function focus(node:HTMLElement|null):void {node?.focus({preventScroll:true});}
export function labeled(label:string,control:HTMLElement):HTMLLabelElement {const node=el('label');node.append(el('span',label),control);return node;}
export function warning(text:string):HTMLElement{return el('p',text,'warning');}
export function statuses(lifecycle:Lifecycle,fact:FactKind,source?:SourceState):HTMLElement {
  const node=el('div',undefined,'meaning');node.append(el('span','Lifecycle: '+lifecycle,'badge'),el('span','Classification: '+fact,'badge'));
  if(source)node.append(el('span','Sources: '+source,'badge'));
  if(lifecycle==='deprecated')node.append(warning('Historical entry. Read its recorded replacement and qualifications in Details.'));
  if(lifecycle==='draft')node.append(warning('Draft is the recorded lifecycle.'));
  if(fact!=='asserted')node.append(warning(fact+' is the recorded classification; this reader does not execute inference or verify the claim.'));
  if(source==='stale')node.append(warning('Source changed: its bytes differ from the recorded version.'));
  if(source==='unavailable')node.append(warning('A recorded source is unavailable.'));
  if(source==='unrecorded')node.append(warning('No source reference is recorded.'));
  return node;
}
export function coverage(response:SuccessResponse):HTMLElement {
  const node=el('div',undefined,'coverage');
  if(!response.coverage.complete)node.append(warning('This returned view is incomplete'+(response.coverage.reasons.length?': '+response.coverage.reasons.map(x=>x.replaceAll('_',' ')).join(', '):'')+'. Narrow the request or continue where offered.'));
  if(response.coverage.filter_exclusions)node.append(el('p',String(response.coverage.filter_exclusions)+' records excluded by the selected filters in this read.'));
  for(const diagnostic of response.diagnostics)node.append(warning(diagnostic.message));
  return node;
}
export function sourceButton(ref:SourceRef,open:(owner:string,reference:string,trigger:HTMLElement)=>void):HTMLButtonElement {
  const node=button('Read source: '+ref.path+' · '+ref.locator,()=>open(ref.owner_id,ref.reference_id,node),'source-link');
  node.dataset.referenceId=ref.reference_id;node.dataset.ownerId=ref.owner_id;return node;
}
export const errorMessages:Record<string,string>={
  invalid_response:'The reader returned an invalid response. Retained text has not been replaced.',
  snapshot_changed:'Knowledge changed. Refresh this reading view to continue.',cursor_expired:'This continuation expired. Refresh the reading view.',
  source_observation_changed:'The source changed during this reading sequence. Reopen the source.',
  resource_limit:'This read cannot fit the selected limits. Narrow the request.',deadline_exceeded:'The bounded local read did not finish. Retry this read or narrow its scope.',
  service_busy:'The local reader is busy. Retry this read.',knowledge_updating:'A coherent knowledge view is not available yet. Retry this read.',
  identity_unavailable:'This exact identity is unavailable in the selected snapshot.',source_unavailable:'The selected source is unavailable.',
  source_locator_invalid:'The recorded locator is not valid for the current source bytes.',request_too_large:'This request is too large. Narrow the query or filters.',
  category_unavailable:'The previous category is no longer available. Showing all supported categories.',
};
export function errorText(code:string):string{return errorMessages[code]??'This read could not be completed ('+code+'). Retained text keeps its original snapshot.';}
import {encodeRoute} from './routes';
import type {Route} from './routes';
export function routeLink(label:string,route:Route,go:(route:Route)=>void):HTMLAnchorElement {
  const node=el('a',label),encoded=encodeRoute(route,route.project_id);node.href=encoded.ok?encoded.hash:'#';
  node.addEventListener('click',event=>{if(event.button===0&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey&&!event.altKey){event.preventDefault();go(route);}});return node;
}
