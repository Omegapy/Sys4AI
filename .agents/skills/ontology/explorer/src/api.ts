import {decodeReadResponse,decodeWire,isWire,scopeForRequest,stableJson,utf8Length} from './contracts';
import type {Operation,ReadRequest,SessionResponse,SuccessResponse} from './contracts';
import {applyResponse,beginRequest,connectIdentity,createReaderState,failRequest} from './state';
import type {ReaderState,Region,StateTransition} from './state';
import {parseRoute} from './routes';

export interface CapturedFragment {bootstrap:string|null;desired:string;invalid:boolean}
function safeRoute(value:string):string {
  const project=/^#\/p\/([a-z0-9][a-z0-9-]{0,79})\//u.exec(value)?.[1];
  return project&&parseRoute(value,project).ok?value:'';
}
/** Must run synchronously on initial load and every same-document fragment. */
export function captureFragment():CapturedFragment {
  const hash=location.hash;let bootstrap:string|null=null,desired='',invalid=false;
  try {
    if(hash.startsWith('#bootstrap=')) {
      const fields=hash.slice(1).split('&');
      if(fields.length>2||!fields[0]?.startsWith('bootstrap=')||fields.length===2&&!fields[1]?.startsWith('route='))throw new Error();
      const token=fields[0].slice(10);if(!isWire('Token',token))throw new Error();bootstrap=token;
      if(fields[1]){desired=safeRoute(decodeURIComponent(fields[1].slice(6)));if(!desired)throw new Error();}
    } else {desired=safeRoute(hash);invalid=!!hash&&!desired;}
  } catch {bootstrap=null;desired='';invalid=true;}
  const previous=history.state;
  const safeHistory=previous&&typeof previous==='object'&&!Array.isArray(previous)&&Object.keys(previous).length===1&&Number.isSafeInteger(previous.explorer)&&previous.explorer>0?{explorer:previous.explorer}:null;
  history.replaceState(safeHistory,'',location.pathname+desired);
  return {bootstrap,desired,invalid};
}
export async function boundedBytes(response:Response,maximum:number):Promise<Uint8Array> {
  const length=response.headers.get('content-length');
  if(length!==null&&(!/^\d+$/u.test(length)||Number(length)>maximum))throw new Error('invalid_response');
  if(!response.body)throw new Error('invalid_response');
  const reader=response.body.getReader(),chunks:Uint8Array[]=[];let total=0;
  try {while(true){const part=await reader.read();if(part.done)break;total+=part.value.byteLength;if(total>maximum)throw new Error('invalid_response');chunks.push(part.value);}}
  catch {await reader.cancel();throw new Error('invalid_response');}
  const bytes=new Uint8Array(total);let offset=0;for(const part of chunks){bytes.set(part,offset);offset+=part.byteLength;}return bytes;
}
export class ReadClient {
  state:ReaderState=createReaderState();
  message='Connecting to the local reader.';
  private session:SessionResponse|null=null;
  private generation=0;
  private sequence=0;
  private catalogGeneration=0;
  private catalogController:AbortController|null=null;
  private discoveryGeneration=0;
  private discoveryController:AbortController|null=null;
  private connection:AbortController|null=null;
  private controllers=new Map<Region,AbortController>();
  private expiry:ReturnType<typeof setTimeout>|undefined;
  constructor(private build:string,private schema:string,private changed:()=>void){}
  get connected():boolean{return this.session!==null&&this.state.freshness!=='disconnected';}
  apply(transition:StateTransition):boolean {
    if(!transition.accepted)return false;
    const next=transition.state,prior=this.state;
    if(next.route_generation!==prior.route_generation||next.snapshot!==prior.snapshot||next.session_scope!==prior.session_scope||next.code_epoch!==prior.code_epoch||next.service_instance!==prior.service_instance||next.root_scope_id!==prior.root_scope_id||next.refresh)this.cancelCatalog();
    if(transition.abort.length||transition.state.source_selection?.owner_id!==this.state.source_selection?.owner_id||transition.state.source_selection?.reference_id!==this.state.source_selection?.reference_id)this.cancelDiscovery();
    for(const region of transition.abort){this.controllers.get(region)?.abort();this.controllers.delete(region);}
    this.state=transition.state;this.changed();return true;
  }
  cancelCatalog():void {++this.catalogGeneration;this.catalogController?.abort();this.catalogController=null;}
  processCatalog():CatalogReader|null {
    const session=this.session,state=this.state,context=state.content.context;
    if(!session||!this.connected||state.freshness!=='current'||state.refresh||state.route?.destination!=='processes'||context?.operation!=='context'||context.snapshot!==state.snapshot||context.data.process_ids.length>64)return null;
    this.cancelCatalog();const generation=this.catalogGeneration,connection=this.generation,routeGeneration=state.route_generation,snapshot=state.snapshot;
    const rootScope=state.root_scope_id,ids=new Set(context.data.process_ids),project=stableJson(state.project),policy=stableJson(context.data.resource_policy);let busy=false;
    const valid=()=>{const currentContext=this.state.content.context;return generation===this.catalogGeneration&&connection===this.generation&&this.session===session&&this.connected&&this.state.freshness==='current'&&!this.state.refresh&&this.state.route?.destination==='processes'&&this.state.route_generation===routeGeneration&&this.state.snapshot===snapshot&&this.state.code_epoch===session.code_epoch&&this.state.service_instance===session.service_instance&&this.state.session_scope===session.session_scope&&this.state.root_scope_id===rootScope&&stableJson(this.state.project)===project&&currentContext?.operation==='context'&&stableJson(currentContext.data.resource_policy)===policy;};
    return {valid,cancel:()=>{if(generation===this.catalogGeneration)this.cancelCatalog();},header:async(id)=>{
      if(!valid())return {kind:'canceled'};
      if(!ids.has(id)||!isWire('Id',id))return {kind:'unavailable',code:'unselected_process'};
      if(busy)return {kind:'unavailable',code:'service_busy'};
      busy=true;const controller=new AbortController();this.catalogController=controller;
      const request={schema_version:1,request_id:'catalog-'+(++this.sequence),code_epoch:session.code_epoch,snapshot,params:{id,section:'header',cursor:null}};
      const scope=scopeForRequest('entry',request);if(!scope){busy=false;this.catalogController=null;return {kind:'unavailable',code:'invalid_request'};}let expired=false,timer:ReturnType<typeof setTimeout>|undefined;
      const canceled=():CatalogHeader=>({kind:'canceled'});
      const work=async():Promise<CatalogHeader>=>{try{
        const response=await this.post('entry',request,controller.signal,session.csrf);
        const decoded=await decodeReadResponse(await boundedBytes(response,context.data.resource_policy.response_bytes),{operation:'entry',request_id:request.request_id,code_epoch:session.code_epoch,service_instance:session.service_instance,session_scope:session.session_scope,project:state.project,snapshot,scope,policy:context.data.resource_policy});
        if(!valid()||expired)return canceled();
        if(!decoded.ok)return {kind:'unavailable',code:'invalid_response'};
        if(decoded.value.status==='error'){
          const error=decoded.value.error;
          if(error.retry==='refresh'){this.state={...this.state,freshness:'stale'};this.cancelCatalog();this.changed();}
          if(error.retry==='reopen')this.disconnect('The reading session ended. Reopen the local reader.');
          return {kind:'unavailable',code:error.code};
        }
        const header=decoded.value.operation==='entry'?decoded.value.data.header:null;
        return header&&header.id===id?{kind:'recorded',label:header.label,label_truncated:header.label_truncated}:{kind:'unavailable',code:'invalid_response'};
      }catch{return valid()&&!expired?{kind:'unavailable',code:'read_unavailable'}:canceled();}};
      try{return await Promise.race([work(),new Promise<CatalogHeader>(resolve=>{timer=setTimeout(()=>{expired=true;controller.abort();resolve(valid()?{kind:'unavailable',code:'deadline_exceeded'}:canceled());},10000);})]);}
      finally {if(timer!==undefined)clearTimeout(timer);busy=false;if(this.catalogController===controller)this.catalogController=null;}
    }};
  }
  cancelDiscovery():void {++this.discoveryGeneration;this.discoveryController?.abort();this.discoveryController=null;}
  discover(processId:string,referenceId:string):DiscoveryReader|null {return this.inspector(processId,referenceId);}
  inspectFocus(id:string):DiscoveryReader|null {return this.inspector(id,null);}
  private inspector(processId:string,referenceId:string|null):DiscoveryReader|null {
    const session=this.session,state=this.state,context=state.content.context;
    if(!session||!context||context.operation!=='context'||(referenceId===null?state.focus_id!==processId:state.selection?.id!==processId)||referenceId!==null&&!isWire('Digest',referenceId)||state.refresh)return null;
    this.cancelDiscovery();const generation=this.discoveryGeneration,connection=this.generation,routeGeneration=state.route_generation,snapshot=state.snapshot;
    const valid=()=>generation===this.discoveryGeneration&&connection===this.generation&&this.session===session&&this.state.snapshot===snapshot&&this.state.route_generation===routeGeneration&&(referenceId===null?this.state.focus_id===processId:this.state.selection?.id===processId)&&!this.state.refresh;
    return {valid,cancel:()=>this.cancelDiscovery(),entry:async(id,section,cursor)=>{
      if(!valid()||!isWire('Id',id))return null;
      const request={schema_version:1,request_id:'discovery-'+(++this.sequence),code_epoch:session.code_epoch,snapshot,params:{id,section,cursor}};
      const scope=scopeForRequest('entry',request);if(!scope)return null;
      const controller=new AbortController();this.discoveryController=controller;const deadline=setTimeout(()=>controller.abort(),10000);
      try {
        const response=await this.post('entry',request,controller.signal,session.csrf);
        const checked=await decodeReadResponse(await boundedBytes(response,context.data.resource_policy.response_bytes),{operation:'entry',request_id:request.request_id,code_epoch:session.code_epoch,service_instance:session.service_instance,session_scope:session.session_scope,project:state.project,snapshot,scope,policy:context.data.resource_policy});
        if(!valid()||!checked.ok)return null;
        if(checked.value.status==='error'){if(checked.value.error.retry==='refresh'){this.state={...this.state,freshness:'stale'};this.changed();}if(checked.value.error.retry==='reopen')this.disconnect('The reading session ended. Reopen the local reader.');return null;}
        return checked.value.operation==='entry'?checked.value:null;
      } catch {return null;} finally {clearTimeout(deadline);if(this.discoveryController===controller)this.discoveryController=null;}
    }};
  }
  private async post(path:string,body:unknown,signal:AbortSignal,csrf?:string):Promise<Response> {
    const serialized=JSON.stringify(body);
    const max=path.startsWith('session')?1024:this.state.content.context?.operation==='context'?(this.state.refresh?.context??this.state.content.context).data.resource_policy.request_bytes:8192;
    if(utf8Length(serialized)>max)throw new Error('request_too_large');
    return fetch('/api/explorer/v1/'+path,{method:'POST',credentials:'same-origin',cache:'no-store',redirect:'error',signal,
      headers:{'Content-Type':'application/json',...(csrf?{'X-Explorer-CSRF':csrf}:{})},body:serialized});
  }
  disconnect(message:string):void {
    this.cancelCatalog();this.cancelDiscovery();++this.generation;this.session=null;this.connection?.abort();for(const c of this.controllers.values())c.abort();this.controllers.clear();
    if(this.expiry!==undefined)clearTimeout(this.expiry);
    this.state={...this.state,freshness:'disconnected',session_scope:null,cursors:{},regional_requests:{},refresh:null};
    this.message=message;this.changed();
  }
  async connect(fragment:CapturedFragment):Promise<SuccessResponse|null> {
    this.cancelCatalog();this.cancelDiscovery();const generation=++this.generation;this.connection?.abort();for(const c of this.controllers.values())c.abort();this.controllers.clear();
    if(this.expiry!==undefined)clearTimeout(this.expiry);this.session=null;
    this.state={...this.state,regional_requests:{},cursors:{},refresh:null,freshness:this.state.snapshot?'stale':'unconnected'};
    const controller=new AbortController();this.connection=controller;
    this.message='Connecting to the local reader.';this.changed();
    if(fragment.invalid){this.disconnect('This local reader link is invalid. Reopen the local reader.');return null;}
    try {
      const exchange=fragment.bootstrap!==null;
      const body=exchange?{schema_version:1,bootstrap:fragment.bootstrap,client_build_id:this.build,schema_sha256:this.schema}:{schema_version:1,client_build_id:this.build,schema_sha256:this.schema};fragment.bootstrap=null;
      const response=await this.post(exchange?'session':'session-resume',body,controller.signal);
      const result=decodeWire('SessionResponse',await boundedBytes(response,1024));
      if(generation!==this.generation)return null;
      if(!response.ok||!result.ok||result.value.build_id!==this.build||result.value.schema_sha256!==this.schema){this.disconnect('A fresh local reading session is required. Reopen the local reader.');return null;}
      const session=result.value;this.session=session;
      // A fresh authenticated session starts a coherent context; the UI retains
      // the old recorded DOM until that new context has been admitted.
      this.state=connectIdentity(createReaderState(),session).state;
      this.expiry=setTimeout(()=>{if(generation===this.generation&&this.session===session)this.disconnect('The reading session expired. Reopen the local reader to continue.');},session.expires_in*1000);
      const context=await this.read('context',{refresh:false});
      if(generation!==this.generation||this.session!==session)return null;
      if(!context||context.operation!=='context'){this.disconnect('Current knowledge is unavailable. Reopen or inspect local reader health.');return null;}
      this.message='Connected to the selected project.';this.changed();return context;
    } catch {if(generation===this.generation)this.disconnect('The local reader is unavailable. Reopen it with the explicit local command.');return null;}
  }
  async close():Promise<void> {
    const session=this.session,generation=this.generation;if(!session)return;
    try {const response=await this.post('session-close',{schema_version:1,code_epoch:session.code_epoch},new AbortController().signal,session.csrf);
      const result=decodeWire('SessionCloseResponse',await boundedBytes(response,1024));
      if(generation===this.generation&&this.session===session)this.disconnect(response.ok&&result.ok?'Reading session closed.':'The local reader could not confirm session closure.');
    } catch {if(generation===this.generation&&this.session===session)this.disconnect('The local reader is unavailable.');}
  }
  async read(operation:Operation,params:ReadRequest['params'],target:'visible'|'refresh'='visible'):Promise<SuccessResponse|null> {
    const session=this.session,generation=this.generation;if(!session||!this.connected)return null;
    const staged=target==='refresh'?this.state.refresh?.context:null;
    const request={schema_version:1,request_id:'read-'+(++this.sequence),code_epoch:session.code_epoch,snapshot:operation==='context'?target==='refresh'?null:this.state.snapshot:staged?.snapshot??this.state.snapshot,params};
    const scope=scopeForRequest(operation,request);if(!scope){this.message='This reading request is not valid.';this.changed();return null;}
    const visibleFilters=this.state.filters;
    const missingCategory=target==='refresh'&&operation==='search'&&'category' in scope&&scope.category===null&&visibleFilters.category!==null&&!!staged&&!staged.data.categories.some(item=>item.id===visibleFilters.category);
    const admissionState=missingCategory?{...this.state,filters:{...visibleFilters,category:null}}:this.state;
    const started=beginRequest(admissionState,operation,request.request_id,scope,target);
    // The new category applies only at commitRefresh; old visible state stays coherent.
    if(missingCategory)started.state.filters=visibleFilters;if(!started.ticket)return null;
    for(const region of started.abort)this.controllers.get(region)?.abort();
    this.state=started.state;const ticket=started.ticket,controller=new AbortController();this.controllers.set(operation,controller);this.changed();
    // Browser cancellation is advisory; the ticket remains the admission gate.
    const deadline=setTimeout(()=>controller.abort(),10000);
    try {
      const response=await this.post(operation,request,controller.signal,session.csrf);
      const expectation=operation==='context'?{...ticket.expected,policy:null}:ticket.expected;
      const decoded=await decodeReadResponse(await boundedBytes(response,expectation.policy?.response_bytes??32000),expectation);
      if(generation!==this.generation||this.session!==session)return null;
      if(!decoded.ok){this.apply(failRequest(this.state,ticket,'invalid_response'));return null;}
      const accepted=this.apply(applyResponse(this.state,ticket,decoded.value));
      if(accepted&&this.state.freshness==='disconnected'){this.disconnect('The reading connection ended. Reopen the correct local reader.');return null;}
      const committed=ticket.target==='refresh'?this.state.refresh?.content[operation]:this.state.content[operation];
      return accepted&&decoded.value.status!=='error'&&committed?.request_id===ticket.expected.request_id?decoded.value:null;
    } catch(error) {
      if(generation===this.generation&&this.session===session){
        const code=error instanceof Error&&['request_too_large','invalid_response'].includes(error.message)?error.message:'deadline_exceeded';
        const accepted=this.apply(failRequest(this.state,ticket,code));
        if(accepted&&!controller.signal.aborted&&code!=='request_too_large'&&code!=='invalid_response')this.disconnect('The local reader is unavailable. Recorded text remains from the displayed snapshot. Reopen the local reader.');
      }return null;
    } finally {clearTimeout(deadline);if(this.controllers.get(operation)===controller)this.controllers.delete(operation);}
  }
}

export interface DiscoveryReader {entry:(id:string,section:'header'|'sources'|'details'|'process',cursor:string|null)=>Promise<import('./contracts').EntryResponse|null>;valid:()=>boolean;cancel:()=>void}

export type CatalogHeader={kind:'recorded';label:string;label_truncated:boolean}|{kind:'unavailable';code:string}|{kind:'canceled'};
export interface CatalogReader {valid:()=>boolean;cancel:()=>void;header:(id:string)=>Promise<CatalogHeader>}
