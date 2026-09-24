import type {ContextResponse,SearchResponse,Summary} from './contracts';
import type {Route} from './routes';
import type {Filters} from './state';
import {FACT_KINDS,LIFECYCLES} from './contracts';
import {button,coverage,el,labeled,routeLink,statuses,warning} from './feedback';

export class SearchBox {
  readonly element=el('form',undefined,'search-box');readonly input=el('input');
  private list=el('ul',undefined,'suggestions');private active=-1;private items:Summary[]=[];private timer:ReturnType<typeof setTimeout>|undefined;
  private inputGeneration=0;
  constructor(private query:(text:string,generation:number)=>void,submit:(text:string)=>void,private select:(id:string)=>void){
    this.input.type='search';this.input.id='global-search';this.input.autocomplete='off';this.input.setAttribute('role','combobox');this.input.setAttribute('aria-autocomplete','list');this.input.setAttribute('aria-expanded','false');this.input.setAttribute('aria-controls','search-suggestions');
    this.list.id='search-suggestions';this.list.setAttribute('role','listbox');this.list.hidden=true;
    const submitButton=el('button','Search');submitButton.type='submit';this.element.append(labeled('Search project knowledge',this.input),submitButton,this.list);
    this.element.addEventListener('submit',event=>{event.preventDefault();this.cancelTimer();this.hide();submit(this.input.value);});
    this.input.addEventListener('input',()=>{this.cancelTimer();this.hide();const text=this.input.value,generation=this.inputGeneration;this.timer=setTimeout(()=>{this.timer=undefined;this.query(text,generation);},175);});
    this.input.addEventListener('keydown',event=>{
      if(event.key==='Escape'){event.preventDefault();this.cancelTimer();this.hide();}
      else if((event.key==='ArrowDown'||event.key==='ArrowUp')&&this.items.length&&!this.list.hidden){event.preventDefault();this.active=this.active<0?(event.key==='ArrowDown'?0:this.items.length-1):(this.active+(event.key==='ArrowDown'?1:-1)+this.items.length)%this.items.length;this.highlight();}
      else if(event.key==='Enter'&&this.active>=0&&!this.list.hidden){event.preventDefault();const item=this.items[this.active];this.hide();if(item)this.select(item.id);}
    });
    this.input.addEventListener('blur',()=>{this.cancelTimer();this.hide();});
  }
  cancelTimer():void {if(this.timer!==undefined)clearTimeout(this.timer);this.timer=undefined;}
  setValue(value:string,force=false):void {if(force||document.activeElement!==this.input)this.input.value=value;}
  hide():void {++this.inputGeneration;this.list.hidden=true;this.input.setAttribute('aria-expanded','false');this.input.removeAttribute('aria-activedescendant');this.active=-1;}
  suggestions(response:SearchResponse,generation:number):void {
    if(document.activeElement!==this.input||generation!==this.inputGeneration)return;
    this.items=response.data.items.filter((x):x is {kind:'entry';entry:Summary}=>x.kind==='entry').map(x=>x.entry).slice(0,8);this.list.replaceChildren();this.active=-1;
    for(const [index,item] of this.items.entries()){const row=el('li',item.label+' · '+item.module_id);row.dataset.entryId=item.id;if(this.items.some(other=>other.id!==item.id&&other.label===item.label&&other.module_id===item.module_id))row.append(el('code',item.id,'identity'));row.id='suggestion-'+index;row.setAttribute('role','option');row.setAttribute('aria-selected','false');row.addEventListener('mousedown',event=>event.preventDefault());row.addEventListener('click',()=>{this.hide();this.select(item.id);});this.list.append(row);}
    this.list.hidden=!this.items.length;this.input.setAttribute('aria-expanded',String(!!this.items.length));
  }
  private highlight():void {for(const [index,node] of [...this.list.children].entries())node.setAttribute('aria-selected',String(index===this.active));const current=this.list.children[this.active];if(current){this.input.setAttribute('aria-activedescendant',current.id);current.scrollIntoView({block:'nearest'});}}
}
export function resultList(response:SearchResponse,context:ContextResponse,go:(route:Route)=>void,more:()=>void,clear:()=>void):HTMLElement {
  const view=el('section');view.append(coverage(response));
  if(response.status==='ambiguous')view.append(warning('Several entries match. Choose the exact identity you mean; equal labels remain separate entries.'));
  if(!response.data.items.length){view.append(el('p',response.coverage.complete?'No matching entries in this filtered view. Try a preferred label, alias, exact ID, or a shorter query.':'This bounded read did not return an entry. Its limits do not establish that no match exists.'));view.append(button('Clear filters',clear));}
  const list=el('ul',undefined,'results');
  for(const item of response.data.items){const row=el('li');
    if(item.kind==='detail_required'){row.append(warning('This item needs a detail read ('+item.reason.replaceAll('_',' ')+').'),routeLink(item.id,{project_id:context.project.id,destination:'entry',id:item.id,options:{}},go));}
    else {const entry=item.entry;row.append(routeLink(entry.label,{project_id:context.project.id,destination:'entry',id:entry.id,options:{}},go),el('p',entry.definition_excerpt,'excerpt'));
      if(entry.excerpt_truncated)row.append(el('p','Definition preview; open the entry to read the full text.','muted'));
      const categories=entry.category_ids.map(id=>context.data.categories.find(x=>x.id===id)?.label??id);row.append(el('p',categories.join(' · ')+' · '+entry.module_id+(entry.module_version?' '+entry.module_version:''),'metadata'));
      row.append(el('p','Match: '+entry.match_reason.replaceAll('_',' ')+(entry.matched_alias!==null?' · '+entry.matched_alias+(entry.matched_alias_truncated?' (preview)':''):''),'metadata'),el('code',entry.id,'identity'),statuses(entry.lifecycle,entry.fact_kind,entry.source_state));
    }list.append(row);
  }view.append(list);
  view.append(el('p',String(response.page.returned)+' entries returned in this page'+(response.page.total?', '+(response.page.total.exact?'exact ':'estimated ')+response.page.total.value+' in the filtered query':'')+'.','muted'));
  if(response.page.next_cursor)view.append(button('Continue results',more));return view;
}
export function filterControl(context:ContextResponse,current:Filters,change:(filters:Filters)=>void,graph=false):HTMLElement {
  const wrap=el('section',undefined,'filter-control'),details=el('details'),summary=el('summary','Filters');details.append(summary);
  const category=el('select');for(const value of context.data.categories){const option=el('option',value.label);option.value=value.id;category.append(option);}category.value=current.category??'all';
  category.addEventListener('change',()=>change({...current,category:category.value==='all'?null:category.value}));if(!graph)details.append(labeled('Category',category));
  for(const [label,key,values] of [['Lifecycle','lifecycles',LIFECYCLES],['Classification','fact_kinds',FACT_KINDS]] as const){
    const field=el('fieldset');field.append(el('legend',label));for(const value of values){const input=el('input');input.type='checkbox';input.checked=(current[key] as string[]).includes(value);input.addEventListener('change',()=>{const selected=[...field.querySelectorAll('input:checked')].map(x=>(x as HTMLInputElement).value);if(!selected.length){input.checked=true;return;}change({...current,[key]:selected});});input.value=value;field.append(labeled(value,input));}details.append(field);
  }
  if(graph){const direction=el('select');for(const value of ['both','incoming','outgoing'] as const){const option=el('option',value);option.value=value;direction.append(option);}direction.value=current.direction;direction.addEventListener('change',()=>change({...current,direction:direction.value as Filters['direction']}));details.append(labeled('Direction from focus',direction));
    const predicates=el('textarea');predicates.value=current.predicate_ids.join('\n');predicates.rows=2;details.append(labeled('Exact predicate IDs (one per line)',predicates),button('Apply predicate filter',()=>change({...current,predicate_ids:predicates.value.split('\n').map(x=>x.trim()).filter(Boolean)})));
  }
  const chips=el('div',undefined,'chips');if(current.category)chips.append(button('Remove category: '+(context.data.categories.find(x=>x.id===current.category)?.label??current.category),()=>change({...current,category:null})));
  if(current.lifecycles.length!==3)chips.append(button('Lifecycle: '+current.lifecycles.join(', ')+' · show all',()=>change({...current,lifecycles:[...LIFECYCLES]})));
  if(current.fact_kinds.length!==4)chips.append(button('Classification: '+current.fact_kinds.join(', ')+' · show all',()=>change({...current,fact_kinds:[...FACT_KINDS]})));
  for(const predicate of current.predicate_ids)chips.append(button('Remove predicate: '+predicate,()=>change({...current,predicate_ids:current.predicate_ids.filter(x=>x!==predicate)})));
  wrap.append(details,chips);return wrap;
}
