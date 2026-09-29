import {boundedBytes} from './api';
import type {CapturedFragment} from './api';
import {decodeWire,isWire,utf8Length} from './contracts';
import type {SessionResponse} from './contracts';
import {parseRoute} from './routes';

export type RecordValue=Record<string,unknown>;
export interface ProjectResponse extends RecordValue {schema_version:1;operation:string;status:string;project_id:string|null;observed_at:string;issues:unknown[]}
export function object(value:unknown):RecordValue{return value!==null&&typeof value==='object'&&!Array.isArray(value)?value as RecordValue:{};}
export function text(value:unknown,fallback=''):string{return typeof value==='string'?value:fallback;}
export function records(value:unknown):RecordValue[]{return Array.isArray(value)?value.filter(item=>item!==null&&typeof item==='object'&&!Array.isArray(item)) as RecordValue[]:[];}
export const APP_PAGES=['home','work','knowledge','lessons','health','help','search','task','source','memory'] as const;
export type AppPage=typeof APP_PAGES[number];
export interface AppRoute {page:AppPage;id:string;query:string}
export function appHash(page:AppPage,id='',query=''):string{return '#/app/'+page+(id?'/'+encodeURIComponent(id):'')+(query?'?q='+encodeURIComponent(query):'');}
export function parseAppRoute(hash:string):AppRoute|null {
  if(utf8Length(hash)>2048)return null;
  try{
    const match=/^#\/app\/(home|work|knowledge|lessons|health|help|search|task|source|memory)(?:\/([^/?#]+))?(?:\?q=([^#&]*))?$/u.exec(hash);if(!match)return null;
    const page=match[1] as AppPage,id=decodeURIComponent(match[2]??''),query=decodeURIComponent(match[3]??'');
    if(['task','source','memory'].includes(page)!==!!id||id.length>512||/[\u0000-\u001f]/u.test(id)||query.length>300||!['search','lessons'].includes(page)&&query)return null;
    return {page,id,query};
  }catch{return null;}
}
export function safeProjectHash(hash:string):boolean {
  if(parseAppRoute(hash))return true;
  const id=/^#\/p\/([a-z0-9][a-z0-9-]{0,79})\//u.exec(hash)?.[1];return !!id&&parseRoute(hash,id).ok;
}
/** Remove launch credentials synchronously before any asynchronous work. */
export function captureProjectFragment():CapturedFragment {
  let bootstrap:string|null=null,desired='',invalid=false;
  try{
    const hash=location.hash;
    if(hash.startsWith('#bootstrap=')){
      const parts=hash.slice(1).split('&');if(parts.length>2||parts.length===2&&!parts[1]!.startsWith('route='))throw new Error();
      const token=parts[0]!.slice(10);if(!isWire('Token',token))throw new Error();bootstrap=token;
      desired=parts[1]?decodeURIComponent(parts[1].slice(6)):'';
    }else desired=hash;
    if(desired&&!safeProjectHash(desired))throw new Error();
  }catch{bootstrap=null;desired='';invalid=true;}
  history.replaceState(null,'',location.pathname+'?app=1'+desired);
  return {bootstrap,desired,invalid};
}

/** Primary project reads have no dependency on an ontology context or graph. */
export class ProjectClient {
  private session:SessionResponse|null=null;
  private generation=0;
  private requests=new Set<AbortController>();
  projectId:string|null=null;
  message='Connecting to this project.';
  constructor(private build:string,private schema:string,private changed:()=>void){}
  get connected():boolean{return this.session!==null;}
  invalidate():void {++this.generation;for(const request of this.requests)request.abort();this.requests.clear();}
  disconnect(message:string):void {this.invalidate();this.session=null;this.message=message;this.changed();}
  private async post(path:string,body:unknown,csrf?:string,maximum=1048576):Promise<{response:Response;bytes:Uint8Array}>{
    const serialized=JSON.stringify(body);if(utf8Length(serialized)>8192)throw new Error('request_too_large');
    const controller=new AbortController();this.requests.add(controller);const timer=setTimeout(()=>controller.abort(),15000);
    try{const response=await fetch(path,{method:'POST',credentials:'same-origin',cache:'no-store',redirect:'error',signal:controller.signal,headers:{'Content-Type':'application/json',...(csrf?{'X-Explorer-CSRF':csrf}:{})},body:serialized});return {response,bytes:await boundedBytes(response,maximum)};}
    finally{clearTimeout(timer);this.requests.delete(controller);}
  }
  async connect(fragment:CapturedFragment):Promise<boolean>{
    this.invalidate();const generation=this.generation;this.session=null;this.projectId=null;
    if(fragment.invalid){this.disconnect('This Project app link is invalid. Open Launch Project.command again.');return false;}
    try{
      const exchange=fragment.bootstrap!==null,body={schema_version:1,client_build_id:this.build,schema_sha256:this.schema,...(exchange?{bootstrap:fragment.bootstrap}:{})};fragment.bootstrap=null;
      const {response,bytes}=await this.post('/api/explorer/v1/'+(exchange?'session':'session-resume'),body,undefined,1024);
      const result=decodeWire('SessionResponse',bytes);
      if(generation!==this.generation)return false;
      if(!response.ok||!result.ok||result.value.build_id!==this.build||result.value.schema_sha256!==this.schema){this.disconnect('A fresh reading session is required. Open Launch Project.command again. After a package update, restart the app.');return false;}
      this.session=result.value;this.message='Connected to this project.';this.changed();return true;
    }catch{if(generation===this.generation)this.disconnect('The local app could not be reached. Open Launch Project.command or the local Project App Setup.html guide.');return false;}
  }
  async read(operation:string,params:RecordValue={}):Promise<ProjectResponse|null>{
    const session=this.session,generation=this.generation;if(!session)return null;
    try{
      const {response,bytes}=await this.post('/api/project/v1/read',{operation,params},session.csrf);
      if(generation!==this.generation||session!==this.session)return null;
      if(response.status===401||response.status===403){this.disconnect('This reading session ended. Open Launch Project.command again.');return null;}
      const value=object(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)));
      if(!response.ok||value.schema_version!==1||value.operation!==operation||!['ready','partial','unavailable','disabled','error'].includes(text(value.status))||value.project_id!==null&&typeof value.project_id!=='string'||typeof value.observed_at!=='string'||!Array.isArray(value.issues))throw new Error('invalid_response');
      if(this.projectId!==null&&value.project_id!==this.projectId){this.disconnect('The response did not match the selected project. Reopen its own Launch Project.command.');return null;}
      if(operation==='context'){
        const identity=object(value.identity);
        if(identity.id&&identity.id!==value.project_id)throw new Error('invalid_identity');
        this.projectId=value.project_id as string|null;
      }
      return value as ProjectResponse;
    }catch{
      if(generation!==this.generation||session!==this.session)return null;
      this.message='This bounded read could not be completed. Retry this view or inspect Health and setup.';this.changed();return null;
    }
  }
  async end(stop:boolean):Promise<void>{
    const session=this.session;if(!session)return;
    // Reject already-running responses before dispatching the terminal action.
    this.invalidate();const generation=this.generation;this.session=null;
    this.message=stop?'Stopping this app…':'Closing this reading session…';this.changed();
    try{
      const {response,bytes}=await this.post(stop?'/api/project/v1/stop':'/api/explorer/v1/session-close',stop?{}:{schema_version:1,code_epoch:session.code_epoch},session.csrf,1024);
      const confirmed=stop?object(JSON.parse(new TextDecoder().decode(bytes))).stopped===true:decodeWire('SessionCloseResponse',bytes).ok;
      if(generation===this.generation){this.message=response.ok&&confirmed?(stop?'Stop app was accepted. This app is closing for all its reading tabs. Open Launch Project.command to start it again.':'Reading session closed. Tabs sharing this session can no longer read; the app remains running. Open Launch Project.command for a fresh session.'):(stop?'The app could not confirm shutdown. The browser has cleared its reading state; check the local launcher before assuming the service stopped.':'The app could not confirm session closure. The browser has cleared its reading state.');this.changed();}
    }catch{if(generation===this.generation){this.message=stop?'Shutdown could not be confirmed. The browser has cleared its reading state; the service may still be running.':'Session closure could not be confirmed. The browser has cleared its reading state.';this.changed();}}
  }
}
