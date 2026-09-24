import type {RelationshipModel,ModelIntent} from '../model';
import type {SafeCamera} from '../state';
import type {Renderer} from './renderer';
import {button,el,heading,warning} from '../feedback';
import {modelSummary,relationshipList} from './list';
export class MapView {
  readonly element=el('section',undefined,'map-view');
  private canvas=el('div',undefined,'map-canvas');private list=el('div');private summary=el('div');private failure=el('div');private renderer:Renderer|null=null;
  private model:RelationshipModel|null=null;private generation=0;private mode:'list'|'map'='list';private selected:string|null=null;private focusId:string|null=null;private camera:SafeCamera|null=null;
  private dark=false;private reduced=false;private disposed=false;
  private graphControls=el('div',undefined,'actions');
  constructor(private intent:(intent:ModelIntent,trigger?:HTMLElement)=>void,private cameraChanged:(camera:SafeCamera)=>void,private preference:(mode:'map'|'list')=>void){
    this.canvas.setAttribute('role','img');this.canvas.setAttribute('aria-label','Directed relationship map. All details and actions are also available in List.');
    this.canvas.hidden=true;
    const choices=el('div',undefined,'actions');choices.append(button('List',()=>this.show('list')),button('Map',()=>this.show('map')));
    this.graphControls.append(button('Zoom in',()=>this.renderer?.zoom(1.2)),button('Zoom out',()=>this.renderer?.zoom(1/1.2)),button('Fit',()=>this.renderer?.fit()),button('Reset view',()=>this.renderer?.arrange()));this.graphControls.hidden=true;
    this.element.append(heading('Connections'),el('p','Select a term to read it. Use Focus here to explore its connections.'),choices,this.failure,this.graphControls,this.canvas,this.summary,this.list);
    const legend=el('details');legend.append(el('summary','Map legend and reading guide'),el('p','Arrows run from the canonical subject to its object. Edge labels name the predicate. Dashed lines are qualified; dotted lines are historical. Select a relationship to read its exact qualifiers, classification, sources and identity.'),el('p','Bracketed node labels identify unusual canonical record kinds, such as a relation used as an endpoint. Position means only layout. It does not imply process order, dependency, causality, or importance. Parallel lines and self-loops remain separate recorded relationships.'));this.element.append(legend);
  }
  update(model:RelationshipModel,focusId:string|null,selected:string|null,options:{dark:boolean;reduced:boolean;camera:SafeCamera|null},expansionSource?:string):void {
    this.model=model;this.focusId=focusId;this.selected=selected;this.camera=options.camera;
    if(this.dark!==options.dark){this.renderer?.dispose();this.renderer=null;++this.generation;}
    const active=document.activeElement instanceof HTMLElement&&this.list.contains(document.activeElement)?document.activeElement:null,row=active?.closest<HTMLElement>('[data-node-id],[data-relation-id]');const activeId=row?.dataset.nodeId??row?.dataset.relationId,activeText=active?.textContent;
    this.dark=options.dark;this.reduced=options.reduced;this.summary.replaceChildren(modelSummary(model));this.list.replaceChildren(relationshipList(model,this.intent,selected));
    if(activeId){const replacement=[...this.list.querySelectorAll<HTMLElement>('[data-node-id],[data-relation-id]')].find(node=>(node.dataset.nodeId??node.dataset.relationId)===activeId);[...replacement?.querySelectorAll('button')??[]].find(node=>node.textContent===activeText)?.focus({preventScroll:true});}
    if(this.renderer)this.renderer.updateModel(model,expansionSource);else if(this.mode==='map')void this.load();
    this.renderer?.setSelection(selected);
  }
  select(id:string|null):void {this.selected=id;this.renderer?.setSelection(id);for(const row of this.list.querySelectorAll<HTMLElement>('[data-node-id],[data-relation-id]'))row.classList.toggle('selected',(row.dataset.nodeId??row.dataset.relationId)===id);}
  setCamera(camera:SafeCamera|null):void {this.camera=camera;if(camera)this.renderer?.setCamera(camera);}
  show(mode:'list'|'map',save=true):void {
    if(this.disposed)return;this.mode=mode;this.canvas.hidden=mode!=='map';this.graphControls.hidden=mode!=='map';
    // The semantic List remains visible with Map, including evidence and every
    // substantive action. Canvas failure can never remove those controls.
    if(save)this.preference(mode);
    if(mode==='map')void this.load();else {++this.generation;this.renderer?.dispose();this.renderer=null;}
  }
  private async load():Promise<void> {
    if(!this.model||this.renderer||this.disposed)return;const generation=++this.generation,model=this.model;
    try {const module=await import('./renderer');if(generation!==this.generation||this.disposed||this.mode!=='map')return;
      const renderer=await module.mount(this.canvas,model,{focus:this.focusId,selected:this.selected,dark:this.dark,reducedMotion:this.reduced,onFailure:()=>this.failed()},intent=>{if(intent.kind==='viewportChanged'){this.camera=intent.camera;this.cameraChanged(intent.camera);}else this.intent(intent);});
      if(generation!==this.generation||this.disposed||this.mode!=='map'){renderer.dispose();return;}
      this.renderer=renderer;if(this.model!==model)this.renderer.updateModel(this.model!);this.renderer.setSelection(this.selected);if(this.camera)this.renderer.setCamera(this.camera);this.failure.replaceChildren();
    } catch {if(generation===this.generation&&!this.disposed)this.failed();}
  }
  private failed():void {++this.generation;this.renderer?.dispose();this.renderer=null;this.canvas.hidden=true;this.graphControls.hidden=true;this.failure.replaceChildren(warning('The visual map is unavailable. List, entry reading, evidence, Focus here and More connections remain available.'),button('Retry map',()=>{this.canvas.hidden=false;this.graphControls.hidden=false;void this.load();}));}
  dispose():void {this.disposed=true;++this.generation;this.renderer?.dispose();this.renderer=null;}
}
