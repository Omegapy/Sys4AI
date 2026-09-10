import {mountEditor} from './editor.js';
import {mountReview} from './review.js';
import {mountAdvanced} from './advanced.js';

export function element(tag, text, attributes={}) {
  const node=document.createElement(tag);
  if(text!==undefined && text!==null) node.textContent=String(text);
  for(const [key,value] of Object.entries(attributes)) node.setAttribute(key,String(value));
  return node;
}
export function button(label, action, style='secondary') {
  const node=element('button',label,{type:'button',class:style});
  node.addEventListener('click',()=>Promise.resolve(action()).catch(error=>app.message(error.message,true)));
  return node;
}
const status=document.querySelector('#status');
export const app={state:null,selected:null,records:[],proposal:null,csrf:null,
  message(text,error=false){status.textContent=text;status.classList.toggle('error',error);},
  async api(endpoint,data={}){
    const response=await fetch('/api/'+endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-Ontology-CSRF':this.csrf||''},body:JSON.stringify(data),credentials:'same-origin'});
    const value=await response.json();
    if(!response.ok){const error=new Error((value.error?.message||value.status)+' Your entered content is preserved.');error.code=value.error?.code;error.detail=value;throw error;}
    return value;
  },
  async refresh(){
    this.state=await this.api('state');
    document.querySelector('#project-name').textContent=this.state.project.name+' · '+this.state.project.id;
    document.querySelector('#readiness').textContent='Local service · Standards: '+this.state.readiness.status+' · '+(this.state.authoring?'Trusted authoring session':'Browsing session');
    document.querySelector('#new-record').disabled=!this.state.authoring;
    this.review.refreshList();
  },
  async search(){
    this.message('Loading selected ontology records…');
    const value=await this.api('records',{query:document.querySelector('#search').value,module:document.querySelector('#filter-module').value,kind:document.querySelector('#filter-kind').value,type:document.querySelector('#filter-type').value,lifecycle:document.querySelector('#filter-lifecycle').value,fact_kind:document.querySelector('#filter-fact').value});
    this.records=value.records;const list=document.querySelector('#record-list');list.replaceChildren();
    for(const row of value.records){const li=element('li');const item=button(row.label,()=>this.inspect(row['@id']),'');item.dataset.id=row['@id'];item.append(element('small',row.kind+' · '+row.lifecycle+' · '+row.classification));li.append(item);list.append(li);}
    for(const [id,values] of [['filter-module',value.filters.modules],['filter-type',value.filters.types]]){
      const field=document.getElementById(id),current=field.value;const first=field.options[0].textContent;
      field.replaceChildren(element('option',first,{value:''}));for(const value of values)field.append(element('option',value.split(':').pop(),{value}));field.value=current;
    }
    document.querySelector('#result-count').textContent=value.records.length+' shown'+(value.truncated?' · Results are bounded. Narrow the search for more.':'');
    this.message('Ontology records loaded. Select a result to inspect its meaning and sources.');
  },
  async source(reference){const value=await this.api('source',{reference});document.querySelector('#source-reference').textContent=value.reference.path+' · '+value.reference.locator+' · Current source';document.querySelector('#source-text').textContent=value.text;const panel=document.querySelector('#source-panel');panel.open=true;panel.scrollIntoView({block:'nearest'});document.querySelector('#source-text').focus();},
  async inspect(id){
    const value=await this.api('inspect',{id});this.selected=value.record;
    const local=this.records.find(row=>row['@id']===id);
    const node=document.querySelector('#inspector');node.replaceChildren(element('h2',value.record.label));
    for(const text of [value.record.kind,value.record.lifecycle,id.startsWith('urn:sys4ai:ontology:core:')?'Imported · protected':value.record.fact_kind])node.append(element('span',text,{class:'badge'}));
    node.append(element('p',value.record.definition),element('p',id,{class:'meta'}));
    if(value.record.aliases?.length)node.append(element('p','Aliases: '+value.record.aliases.join(', ')));
    if(value.record.scope_note)node.append(element('p',value.record.scope_note));
    const editable=this.state.scope.includes(local?.location||value.record.location);
    if(local?.editable||editable)node.append(button('Edit as draft',()=>this.editor.open(local||value.record)));
    if(this.state.authoring)node.append(button('Create a relationship draft',()=>this.editor.open(null,{related:id})));
    node.append(element('h3','Source evidence'));
    for(const source of value.record.sources||[])node.append(button(source.path+' · '+source.locator,()=>this.source(source),'secondary source-button'));
    node.append(element('h3','Typed relationships'));
    const relations=element('ul',null,{class:'relation-list'});
    for(const edge of value.relations){const li=element('li');li.append(button(edge.subject.split(':').pop(),()=>this.inspect(edge.subject)),document.createTextNode(' → '+edge.predicate.split(':').pop()+' → '),button(edge.object.split(':').pop(),()=>this.inspect(edge.object)));li.append(element('small',' · '+edge.fact_kind+' · '+edge.lifecycle));relations.append(li);}node.append(relations);
    this.drawGraph(id,value.relations);for(const item of document.querySelectorAll('#record-list button'))item.setAttribute('aria-current',String(item.dataset.id===id));
    this.message('Inspecting '+value.record.label+'. Relationships are available as buttons in the list and graph.');
  },
  drawGraph(id,edges){
    const box=document.querySelector('#graph');box.replaceChildren();const ns='http://www.w3.org/2000/svg';
    const graph=document.createElementNS(ns,'svg');graph.setAttribute('viewBox','0 0 900 320');graph.setAttribute('role','group');graph.setAttribute('aria-label','Bounded relationship graph; each node is a keyboard-operable concept button.');
    const ids=[id,...new Set(edges.flatMap(e=>[e.subject,e.object]).filter(v=>v!==id))].slice(0,9);
    const positions=new Map(ids.map((rid,n)=>[rid,n===0?[450,160]:[450+330*Math.cos((n-1)*2*Math.PI/(ids.length-1)),160+115*Math.sin((n-1)*2*Math.PI/(ids.length-1))]]));
    for(const edge of edges){if(!positions.has(edge.subject)||!positions.has(edge.object))continue;const a=positions.get(edge.subject),b=positions.get(edge.object);const line=document.createElementNS(ns,'line');for(const[k,v]of Object.entries({x1:a[0],y1:a[1],x2:b[0],y2:b[1]}))line.setAttribute(k,v);graph.append(line);}
    for(const rid of ids){const[x,y]=positions.get(rid),g=document.createElementNS(ns,'g');g.setAttribute('role','button');g.setAttribute('tabindex','0');g.setAttribute('aria-label','Inspect '+rid.split(':').pop());const rect=document.createElementNS(ns,'rect');for(const[k,v]of Object.entries({x:x-88,y:y-20,width:176,height:40,rx:6}))rect.setAttribute(k,v);const text=document.createElementNS(ns,'text');text.setAttribute('x',x);text.setAttribute('y',y+4);text.setAttribute('text-anchor','middle');text.textContent=rid.split(':').pop().slice(0,23);g.append(rect,text);const action=()=>this.inspect(rid).catch(e=>this.message(e.message,true));g.addEventListener('click',action);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();action();}});graph.append(g);}box.append(graph,element('p','Showing up to 9 nodes. Every returned relationship and its direction appears in the inspector list.',{class:'meta'}));
  }
};

async function start(){
  const token=new URLSearchParams(location.hash.slice(1)).get('bootstrap');
  if(token){history.replaceState(null,'',location.pathname);const session=await app.api('session',{bootstrap:token});app.csrf=session.csrf;sessionStorage.setItem('ontology-csrf',app.csrf);}
  else app.csrf=sessionStorage.getItem('ontology-csrf');
  if(!app.csrf){const error=new Error('Start a new local workbench session. Saved drafts remain available.');error.code='session_expired';throw error;}
  app.editor=mountEditor(app);app.review=mountReview(app);mountAdvanced(app);
  await app.refresh();await app.search();
  document.querySelector('#new-record').addEventListener('click',()=>app.editor.open());
  document.querySelector('#search-form').addEventListener('submit',e=>{e.preventDefault();app.search().catch(error=>app.message(error.message,true));});
}
start().catch(error=>{
  document.querySelector('#project-name').textContent='Session unavailable';
  document.querySelector('#readiness').textContent='The local project is not connected. Saved drafts remain available.';
  app.message(error.code==='session_expired'?'This session link expired. Start a new local workbench session. Saved drafts remain available.':'The local session could not connect. Start a new local workbench session. '+error.message,true);
  document.querySelector('#new-record').disabled=true;
});
