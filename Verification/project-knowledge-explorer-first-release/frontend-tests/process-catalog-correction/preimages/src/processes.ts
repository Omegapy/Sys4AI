import type {ContextResponse,EntryResponse} from './contracts';
import type {Route} from './routes';
import {button,coverage,el,heading,routeLink,warning} from './feedback';
export const MISSING_ORDER='An ordered description has not been recorded. These are the documented relationships.';
export function processCatalog(context:ContextResponse,go:(route:Route)=>void):HTMLElement {
  const view=el('section');view.append(heading('Processes'),el('p','Read explicitly selected process descriptions and their recorded support.'));
  if(!context.data.process_ids.length)view.append(el('p','No process descriptions have been selected for this reader. You can still find related terms through Search.'));
  const list=el('ul',undefined,'results');for(const id of context.data.process_ids){const name=context.data.starting_points.find(x=>x.id===id)?.label??id;const item=el('li');item.append(routeLink(name,{project_id:context.project.id,destination:'process',id,options:{}},go));list.append(item);}view.append(list);return view;
}
export function processSection(response:EntryResponse,read:(id:string)=>void,source:(owner:string,reference:string,trigger:HTMLElement)=>void,more:()=>void):HTMLElement {
  const view=el('section');view.append(heading('Recorded process',3),coverage(response));
  const metadata=response.data.process;
  if(metadata?.order_state!=='recorded'){view.append(warning(MISSING_ORDER));if(metadata&&metadata.order_state!=='missing')view.append(el('p','Order evidence: '+metadata.order_state+'.'));}
  else view.append(el('p','The numbered passages below are explicitly supported by the selected source. Position on a map supplies no process order.'));
  for(const item of response.data.process_items){
    const block=el('section',undefined,'process-field');
    if(item.kind==='ordered_step'){
      block.append(heading('Recorded step '+item.ordinal,3));const trigger=button('Read step source',()=>source(response.data.id,item.reference_id,trigger));block.append(trigger,el('pre',item.text,'exact-text'));if(item.more_in_step)block.append(el('p','The recorded step continues.','muted'));
    } else {
      block.append(heading(item.name.replaceAll('_',' '),3));
      if(item.part==='relations'){for(const id of item.relation_ids)block.append(button('Read supporting relationship: '+id,()=>read(id)));}
      if(item.part==='references'){for(const id of item.reference_ids){const trigger=button('Read supporting source',()=>source(response.data.id,id,trigger));trigger.dataset.referenceId=id;block.append(trigger);}}
      if(item.part==='text'&&item.text!==null){block.append(el('pre',item.text,'exact-text'));if(item.name==='purpose'||item.name==='scope')block.append(button('Read canonical '+item.name,()=>read(response.data.id)));}
      if(item.offset>0)block.append(el('p','Continuation at UTF-8 byte '+item.offset+'.','muted'));if(item.more_in_field)block.append(el('p','This field continues.','muted'));
    }view.append(block);
  }
  if(response.page.next_cursor)view.append(button('Continue process description',more));
  view.append(el('p','These are reading links. They do not execute a skill, process, or action.','fine-print'));return view;
}
