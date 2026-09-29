import type {CapturedFragment} from './api';
import {ExplorerApp} from './app';
import {button,el,focus,heading,labeled,warning} from './feedback';
import {appHash,captureProjectFragment,object,parseAppRoute,ProjectClient,safeProjectHash,text} from './project-api';
import type {AppPage,ProjectResponse} from './project-api';
import {healthView,helpView,homeView,memoryView,searchView,sourceView,taskView,workView} from './project-views';
import type {ViewActions} from './project-views';

const DESTINATIONS:[AppPage,string,string][]=[
  ['home','Home','Understand this project and find a starting point.'],
  ['work','Work','Read Tasks, requirements, plans and recorded evidence.'],
  ['knowledge','Project knowledge','Read terms, processes, sources and relationships.'],
  ['health','Health and setup','Inspect capability availability and setup guidance.'],
  ['help','Tools and help','Understand installed tools and how to use this app.'],
];
export class ProjectApp {
  private client:ProjectClient;
  private context:ProjectResponse|null=null;
  private serial=0;
  private current='';
  private terminal=false;
  private reading=el('main',undefined,'project-reading');
  private knowledgeHost=el('div',undefined,'project-knowledge');
  private knowledge:ExplorerApp|null=null;
  private status=el('div',undefined,'project-status');
  private title=el('p','Project app','project-name');
  private identity=el('p',undefined,'project-root metadata');
  private navigation=el('nav',undefined,'project-navigation');
  private query=el('input');
  private close=button('Close reading session',()=>void this.end(false));
  private stop=button('Stop app',()=>void this.end(true));
  constructor(private root:HTMLElement,private build:string,private schema:string){
    this.client=new ProjectClient(build,schema,()=>this.connectionChanged());
    root.classList.add('project-app');this.reading.id='project-reading';this.reading.tabIndex=-1;
    this.status.setAttribute('role','status');this.status.setAttribute('aria-live','polite');this.status.tabIndex=-1;
    this.navigation.setAttribute('aria-label','Project destinations');
    for(const [page,label,description] of DESTINATIONS){const link=this.link(label,appHash(page));link.dataset.page=page;link.title=description;this.navigation.append(link);}
    const form=el('form',undefined,'project-search');form.setAttribute('role','search');this.query.type='search';this.query.maxLength=300;this.query.placeholder='Search IDs, titles or text';this.query.autocomplete='off';
    const submit=el('button','Search');submit.type='submit';form.append(labeled('Search this project',this.query),submit);
    form.addEventListener('submit',event=>{event.preventDefault();void this.go(appHash('search','',this.query.value.trim()));});
    const header=el('header',undefined,'project-header'),name=el('div');name.append(this.title,this.identity);header.append(name,form);
    const skip=el('a','Skip to project reading','skip-link');skip.href='#project-reading';skip.addEventListener('click',event=>{event.preventDefault();focus(this.knowledgeHost.hidden?this.reading:this.knowledgeHost.querySelector<HTMLElement>('main'));});
    const controls=el('div',undefined,'project-session-controls');controls.append(this.close,this.stop);
    const footer=el('footer',undefined,'project-footer');footer.append(el('p','Reading only. Project records are managed by their existing owners.','metadata'),controls);
    this.knowledgeHost.hidden=true;root.append(skip,header,this.navigation,this.status,this.reading,this.knowledgeHost,footer);
    window.addEventListener('popstate',()=>{if(!this.terminal)void this.go(location.hash,false);});
    window.addEventListener('hashchange',()=>{if(this.terminal)return;const fragment=captureProjectFragment();if(fragment.bootstrap||fragment.invalid){void this.start(fragment);return;}if(fragment.desired!==this.current)void this.go(fragment.desired,false);});
    this.connectionChanged();
  }
  private link(label:string,hash:string):HTMLAnchorElement {
    const link=el('a',label);link.href=hash;
    link.addEventListener('click',event=>{if(event.button===0&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey&&!event.altKey){event.preventDefault();void this.go(hash);}});return link;
  }
  private actions():ViewActions{return {link:(label,hash)=>this.link(label,hash),copy:value=>void this.copy(value),projectId:this.client.projectId??''};}
  private connectionChanged():void {
    this.close.disabled=!this.client.connected;this.stop.disabled=!this.client.connected;
    this.status.replaceChildren(el('p',this.client.message,'metadata'));
    if(!this.client.connected&&this.context&&!this.terminal){this.terminal=true;++this.serial;this.knowledge?.suspend();this.knowledgeHost.hidden=true;this.reading.hidden=false;this.reading.replaceChildren(warning('The reading session is unavailable. Reopen Launch Project.command for this project.'));}
  }
  async start(fragment:CapturedFragment):Promise<void>{
    const serial=++this.serial;this.terminal=false;this.context=null;this.knowledge?.suspend();this.knowledgeHost.hidden=true;this.reading.hidden=false;this.reading.replaceChildren(heading('Opening project'),el('p','Reading the selected project’s identity and available capabilities.'));
    const desired=fragment.desired;
    const connected=await this.client.connect(fragment);if(serial!==this.serial)return;
    if(!connected){this.reading.replaceChildren(heading('Open this project locally'),warning(this.client.message));return;}
    const context=await this.client.read('context');
    if(serial!==this.serial)return;
    if(!context){this.reading.replaceChildren(heading('Project context is unavailable'),warning(this.client.message),button('Retry project context',()=>void this.start({bootstrap:null,desired,invalid:false})));return;}
    this.context=context;const identity=object(context.identity);this.title.textContent=text(identity.name,'Project identity unavailable');this.identity.textContent=text(identity.root);document.title=this.title.textContent+' · Project app';
    await this.go(desired||appHash('home'),false);
  }
  private setHistory(hash:string,push:boolean):void {
    this.current=hash;history[push?'pushState':'replaceState'](null,'',location.pathname+'?app=1'+hash);
    const page=hash.startsWith('#/p/')?'knowledge':parseAppRoute(hash)?.page;
    for(const item of this.navigation.querySelectorAll<HTMLElement>('[data-page]'))item.setAttribute('aria-current',item.dataset.page===(page==='lessons'||page==='memory'?'knowledge':page==='task'?'work':page)?'page':'false');
  }
  private async go(hash:string,push=true):Promise<void>{
    if(this.terminal||!this.client.connected||!this.context)return;
    const serial=++this.serial;this.client.invalidate();hash=hash||appHash('home');
    if(!safeProjectHash(hash)){this.knowledge?.suspend();this.reading.hidden=false;this.knowledgeHost.hidden=true;this.reading.replaceChildren(heading('Unknown reading link'),warning('This reading link is invalid. Choose a destination above.'));return;}
    this.setHistory(hash,push);this.status.replaceChildren(el('p','Reading this view…','metadata'));
    const route=parseAppRoute(hash),knowledge=hash.startsWith('#/p/')||route?.page==='knowledge';
    if(knowledge){
      this.reading.hidden=false;this.reading.replaceChildren(heading('Project knowledge'),el('p','Read the project’s recorded definitions, processes and relationships.'),this.link('Lessons and decisions',appHash('lessons')));
      this.knowledgeHost.hidden=false;
      if(!this.knowledge)this.knowledge=new ExplorerApp(this.knowledgeHost,this.build,this.schema,{navigate:(next,pushed)=>{if(!this.terminal&&!this.knowledgeHost.hidden)this.setHistory(next,pushed);}});
      const id=this.client.projectId;
      if(!id){this.status.replaceChildren(warning('A valid project identity is required to read knowledge. Inspect Health and setup.'));return;}
      await this.knowledge.openRoute(hash.startsWith('#/p/')?hash:'#/p/'+id+'/overview');
      if(serial===this.serial){this.status.replaceChildren(el('p','Project knowledge uses its own recorded versions and availability checks.','metadata'));}
      return;
    }
    this.knowledge?.suspend();this.knowledgeHost.hidden=true;this.reading.hidden=false;this.reading.replaceChildren(heading('Reading…'));
    if(!route)return;
    let response:ProjectResponse|null=null;
    if(route.page==='search'&&!route.query){this.status.replaceChildren();this.reading.replaceChildren(heading('Search this project'),el('p','Enter a known ID, title or word in Search this project above. Search uses supported permitted source text; no semantic service is required.'));return;}
    const operation=route.page==='lessons'?'memory':route.page;
    const params=route.page==='task'?{id:route.id}:route.page==='source'||route.page==='memory'?{source_id:route.id}:route.page==='search'||route.page==='lessons'?{query:route.query}:{};
    response=await this.client.read(operation,params);
    if(serial!==this.serial||this.terminal)return;
    this.status.replaceChildren();
    if(!response){this.reading.replaceChildren(heading('This view is unavailable'),warning(this.client.message),button('Retry this view',()=>void this.go(hash,false)));return;}
    const actions=this.actions();let view:HTMLElement;
    switch(route.page){
      case 'home':view=homeView(response,this.context,actions);break;
      case 'work':view=workView(response,actions);break;
      case 'task':view=taskView(response,actions);break;
      case 'search':this.query.value=route.query;view=searchView(response,route.query,actions);break;
      case 'source':view=sourceView(response,route.id,actions);break;
      case 'lessons':case 'memory':view=memoryView(response,actions,route.query,query=>void this.go(appHash('lessons','',query)),route.id);break;
      case 'health':view=healthView(response);break;
      case 'help':view=helpView(response,actions);break;
      default:view=el('section');view.append(heading('This view is unavailable'));
    }
    const refresh=button('Refresh this view',()=>void this.go(hash,false),'quiet');
    this.reading.replaceChildren(refresh,view);focus(view.querySelector<HTMLElement>('h2'));window.scrollTo({top:0});
  }
  private async end(stop:boolean):Promise<void>{
    this.terminal=true;++this.serial;this.knowledge?.suspend();this.knowledgeHost.hidden=true;this.knowledgeHost.replaceChildren();this.reading.hidden=false;
    this.reading.replaceChildren(heading(stop?'Stop app':'Close reading session'),el('p',stop?'Requesting shutdown of this local app. Its reading sessions will end for all tabs.':'Revoking this reading session. The local app remains running.'));
    await this.client.end(stop);this.reading.replaceChildren(heading(stop?'App shutdown':'Reading session'),el('p',this.client.message));focus(this.reading);
  }
  private async copy(value:string):Promise<void>{
    try{await navigator.clipboard.writeText(value);if(!this.terminal)this.status.replaceChildren(el('p','Reference or instruction copied. Copying does not run an action or grant authority.','metadata'));}
    catch{if(this.terminal)return;const field=el('textarea');field.readOnly=true;field.value=value;const box=el('div');box.append(labeled('Select and copy this reference or instruction',field),button('Close copy field',()=>box.remove()));this.status.append(box);field.focus();field.select();}
  }
}
