import type {RelationshipModel} from '../model';
import type {SafeCamera} from '../state';
import type {ElementDefinition} from 'cytoscape';
export type RendererIntent={kind:'selectNode'|'selectEdge';id:string}|{kind:'viewportChanged';camera:SafeCamera};
export interface Renderer {updateModel(model:RelationshipModel,expansionSource?:string):void;setSelection(id:string|null):void;setCamera(camera:SafeCamera):void;fit():void;zoom(factor:number):void;arrange():void;dispose():void;}
export interface ViewOptions {focus:string|null;selected:string|null;dark:boolean;reducedMotion:boolean;onFailure:()=>void}
export async function mount(container:HTMLElement,initial:RelationshipModel,options:ViewOptions,onIntent:(intent:RendererIntent)=>void):Promise<Renderer> {
  // Vite may replace the authored stylesheet link and omit its id. Identify
  // the already loaded external rule before Cytoscape's default style injection.
  const styleId='__________cytoscape_stylesheet';
  const stylesheet=[...document.querySelectorAll<HTMLLinkElement>('link[rel=stylesheet]')].find(link=>new URL(link.href,location.href).origin===location.origin&&[...link.sheet?.cssRules??[]].some(rule=>rule instanceof CSSStyleRule&&rule.selectorText==='.'+'__________cytoscape_container'&&rule.style.position==='relative'));
  if(!stylesheet||document.getElementById(styleId)&&document.getElementById(styleId)!==stylesheet)throw new Error('renderer_stylesheet_unavailable');
  stylesheet.id=styleId;
  const imported=await import('cytoscape');
  const cytoscape=imported.default;
  let model=initial,disposed=false,selected=options.selected;const positions=new Map<string,{x:number;y:number}>();
  function place(next:RelationshipModel,around?:string):void {
    const started=performance.now(),center=around?positions.get(around)??{x:0,y:0}:{x:0,y:0};
    const ids=Object.keys(next.nodes).sort();let added=0;
    for(const id of ids){if(performance.now()-started>=300)throw new Error('layout_limit');if(positions.has(id))continue;
      if(id===options.focus&&!around)positions.set(id,{x:0,y:0});else {const index=added++,ring=Math.floor(index/12)+1,angle=(index%12)*Math.PI/6+(ring%2===0?Math.PI/12:0);let point={x:center.x+ring*190*Math.cos(angle),y:center.y+ring*155*Math.sin(angle)};
        for(let n=0;n<100&&[...positions.values()].some(p=>Math.abs(p.x-point.x)<90&&Math.abs(p.y-point.y)<60);n++)point={x:point.x+105,y:point.y+75};positions.set(id,point);}
    }
  }
  place(model);
  function elements(next:RelationshipModel):ElementDefinition[] {return [
    ...Object.values(next.nodes).map(node=>({group:'nodes' as const,data:{id:'node:'+node.id,canonicalId:node.id,label:node.label,displayLabel:node.label+(['concept','instance'].includes(node.kind)?'':' ['+node.kind+']'),kind:node.kind},position:positions.get(node.id)})),
    ...Object.values(next.edges).map(edge=>({group:'edges' as const,data:{id:'edge:'+edge.id,canonicalId:edge.id,source:'node:'+edge.subject,target:'node:'+edge.object,label:edge.predicate_label+(edge.qualifiers!==null&&JSON.stringify(edge.qualifiers)!=='{}'?' [qualified]':'')+(edge.lifecycle!=='approved'?' ['+edge.lifecycle+']':'')+(edge.fact_kind!=='asserted'?' ['+edge.fact_kind+']':''),predicate_label:edge.predicate_label,subject:edge.subject,object:edge.object,source_references:edge.source_references,predicate:edge.predicate,qualifiers:edge.qualifiers,lifecycle:edge.lifecycle,fact_kind:edge.fact_kind},classes:(edge.subject===edge.object?'self-loop ':edge.object===options.focus?'incoming-focus ':'')+(edge.qualifiers!==null&&JSON.stringify(edge.qualifiers)!=='{}'?'qualified ':'')+(edge.lifecycle==='deprecated'?'historical ':'')+(edge.fact_kind!=='asserted'?'classified ':'')}))];}
  const ink=options.dark?'#f1f5f9':'#19334d',edge=options.dark?'#94b4cd':'#52718b';
  const cy=cytoscape({container,elements:elements(model),layout:{name:'preset',fit:true,padding:50,animate:false},minZoom:0.1,maxZoom:3,wheelSensitivity:0.2,
    boxSelectionEnabled:false,autounselectify:true,style:[
      {selector:'node',style:{'background-color':options.dark?'#204e65':'#daeaf0','border-color':edge,'border-width':2,label:'data(displayLabel)','text-wrap':'wrap','text-max-width':'150px','font-size':13,color:ink,width:38,height:38,'text-valign':'bottom','text-margin-y':9}},
      {selector:'edge',style:{width:2,'line-color':edge,'target-arrow-color':edge,'target-arrow-shape':'triangle','curve-style':'bezier',label:'','target-label':'data(label)','target-text-offset':50,'target-text-rotation':'autorotate','font-size':11,'text-rotation':'autorotate','text-background-color':options.dark?'#101f2c':'#ffffff','text-background-opacity':0.9,'text-background-padding':'3px',color:ink,'loop-direction':'-45deg','loop-sweep':'60deg'}},
      {selector:'edge.incoming-focus',style:{'target-label':'','source-label':'data(label)','source-text-offset':50,'source-text-rotation':'autorotate'}},
      {selector:'edge.self-loop',style:{'target-label':'',label:'data(label)','text-rotation':'none'}},
      {selector:'.qualified',style:{'line-style':'dashed'}},{selector:'.historical',style:{'line-style':'dotted'}},
      {selector:'.selected',style:{'border-width':5,'border-color':'#b0600c','line-color':'#b0600c','target-arrow-color':'#b0600c',width:4,'font-weight':'bold'}},
      {selector:'node.selected',style:{width:45,height:45}},{selector:'.adjacent',style:{'font-weight':'bold'}}]});
  let frame=0,suppress=false;
  // Text remains readable in CSS pixels at a crowded fit. This changes only
  // text styling, never positions or the user's camera. Endpoint captions avoid
  // stacking every predicate near the common focus.
  function readableLabels():void {if(disposed)return;const scale=cy.zoom();cy.batch(()=>{cy.nodes().style('font-size',Math.max(13,11/scale));cy.edges().style({'font-size':Math.max(11,12/scale),'target-text-offset':32/scale,'source-text-offset':32/scale});});}
  function setSelection(id:string|null):void {selected=id;cy.elements().removeClass('selected adjacent');if(id){const found=cy.getElementById('node:'+id).union(cy.getElementById('edge:'+id));found.addClass('selected');found.connectedEdges().addClass('adjacent');found.connectedEdges().connectedNodes().addClass('adjacent');found.connectedNodes().addClass('adjacent');}readableLabels();}
  cy.on('tap','node',event=>onIntent({kind:'selectNode',id:event.target.data().canonicalId as string}));cy.on('tap','edge',event=>onIntent({kind:'selectEdge',id:event.target.data().canonicalId as string}));
  cy.on('zoom',readableLabels);
  cy.on('pan zoom',()=>{if(suppress||disposed)return;cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{if(!disposed)onIntent({kind:'viewportChanged',camera:{...cy.pan(),zoom:cy.zoom()}});});});
  const observer=new ResizeObserver(()=>{if(!disposed)cy.resize();});observer.observe(container);
  const lost=()=>{if(!disposed)options.onFailure();};container.addEventListener('webglcontextlost',lost,true);container.addEventListener('contextlost',lost,true);setSelection(selected);
  return {
    updateModel(next,source){if(disposed)return;try{for(const id of positions.keys())if(!next.nodes[id])positions.delete(id);cy.nodes().forEach(node=>{const id=node.data().canonicalId as string;if(next.nodes[id])positions.set(id,node.position());});place(next,source);cy.batch(()=>{cy.elements().forEach(item=>{if(item.id().startsWith('node:')?!next.nodes[item.data().canonicalId as string]:!next.edges[item.data().canonicalId as string])item.remove();});const definitions=elements(next);for(const item of definitions.filter(item=>item.group==='nodes')){const current=cy.getElementById(item.data.id!);if(current.length){current.data(item.data);current.classes(item.classes??'');}else cy.add(item);}for(const item of definitions.filter(item=>item.group==='edges')){const current=cy.getElementById(item.data.id!);if(current.length){if(current.data('source')!==item.data.source||current.data('target')!==item.data.target)current.move({source:item.data.source,target:item.data.target});current.data(item.data);current.classes(item.classes??'');}else cy.add(item);}});model=next;setSelection(selected);}catch{options.onFailure();}},
    setSelection,
    setCamera(camera){if(disposed)return;suppress=true;cy.zoom(camera.zoom);cy.pan({x:camera.x,y:camera.y});suppress=false;},
    fit(){if(!disposed)cy.fit(undefined,50);},zoom(factor){if(!disposed)cy.zoom(Math.max(0.1,Math.min(3,cy.zoom()*factor)));},
    arrange(){if(disposed)return;try{positions.clear();place(model);cy.batch(()=>cy.nodes().forEach(node=>{node.position(positions.get(node.data().canonicalId as string)!);}));cy.fit(undefined,50);}catch{options.onFailure();}},
    dispose(){if(disposed)return;disposed=true;cancelAnimationFrame(frame);observer.disconnect();container.removeEventListener('webglcontextlost',lost,true);container.removeEventListener('contextlost',lost,true);cy.off('tap pan zoom');cy.destroy();positions.clear();},
  };
}
