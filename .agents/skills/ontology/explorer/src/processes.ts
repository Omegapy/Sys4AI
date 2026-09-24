import type {ContextResponse,EntryResponse} from './contracts';
import type {Route} from './routes';
import {button,coverage,el,heading,routeLink,warning} from './feedback';
export const MISSING_ORDER='An ordered description has not been recorded. These are the documented relationships.';
import type {CatalogReader} from './api';
export class ProcessCatalog {
  readonly element=el('section');private rows=new Map<string,{link:HTMLAnchorElement;status:HTMLElement;state:'pending'|'recorded'|'unavailable'}>();
  private retry:HTMLButtonElement;private running=false;private disposed=false;
  constructor(context:ContextResponse,private reader:CatalogReader|null,go:(route:Route)=>void){
    this.element.append(heading('Processes'),el('p','Read explicitly selected process descriptions and their recorded support.'));
    if(!context.data.process_ids.length)this.element.append(el('p','No process descriptions have been selected for this reader. You can still find related terms through Search.'));
    const list=el('ul',undefined,'results');
    for(const id of context.data.process_ids){const item=el('li'),summary=context.data.starting_points.find(entry=>entry.id===id),link=routeLink(summary?.label??'Read this process',{project_id:context.project.id,destination:'process',id,options:{}},go),status=el('p','Reading the recorded process name…','muted');
      item.dataset.processId=id;item.append(link,el('code',id,'identity'),status);list.append(item);this.rows.set(id,{link,status,state:'pending'});
    }
    this.retry=button('Retry process names',()=>void this.load());this.retry.hidden=true;this.element.append(list,this.retry);void this.load();
  }
  sync():void {if(this.disposed||this.reader?.valid())return;for(const row of this.rows.values())if(row.state!=='recorded'){row.state='unavailable';row.status.textContent='The recorded name has not been read. Refresh or reopen this reading view to try again; the exact process link remains available.';}this.updateRetry();}
  private updateRetry():void {const available=!!this.reader?.valid()&&[...this.rows.values()].some(row=>row.state==='unavailable');this.retry.hidden=!available&&document.activeElement!==this.retry;this.retry.setAttribute('aria-disabled',String(this.running||!available));this.retry.setAttribute('aria-busy',String(this.running));this.retry.textContent=this.running?'Reading process names…':available?'Retry process names':this.reader?.valid()?'Process names read':'Name reads stopped; refresh this reading view';}
  private async load():Promise<void> {
    if(this.disposed||this.running)return;if(!this.reader?.valid()){this.sync();return;}
    this.running=true;this.updateRetry();
    try {for(const [id,row] of this.rows){if(this.disposed||!this.reader.valid())break;if(row.state==='recorded')continue;row.state='pending';row.status.textContent='Reading the recorded process name…';const result=await this.reader.header(id);if(this.disposed)break;
      if(result.kind==='recorded'&&this.reader.valid()){row.link.textContent=result.label;row.state='recorded';row.status.textContent=result.label_truncated?'Name preview; open the process and its Full name section for the complete recorded name.':'Recorded process name.';}
      else {row.state='unavailable';row.status.textContent='The recorded name could not be read. This does not establish that the process or its name is absent. Open its exact link or retry the name read.';}
    }}finally{this.running=false;if(!this.disposed){this.sync();this.updateRetry();}}
  }
  dispose():void {if(this.disposed)return;this.disposed=true;this.reader?.cancel();}
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
