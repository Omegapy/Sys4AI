import type {SourceResponse,EntryResponse} from './contracts';
import {button,coverage,el,focus,heading,warning} from './feedback';
import {referenceDetails} from './entry';
export class SourceDrawer {
  readonly element=el('aside',undefined,'source-drawer');private title=heading('Source evidence');private body=el('div');private trigger:HTMLElement|null=null;
  private closeButton:HTMLButtonElement;
  constructor(private closeAction:()=>void,private more:()=>void,private returnTarget?:(trigger:HTMLElement|null)=>HTMLElement|null){
    this.element.hidden=true;this.element.setAttribute('aria-label','Source evidence');this.title.id='source-title';
    this.closeButton=button('Close source',()=>this.closeAction());this.element.append(this.closeButton,this.title,this.body);
    this.element.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();this.closeAction();}});
  }
  open(trigger:HTMLElement):void {this.trigger=trigger;this.element.hidden=false;this.body.replaceChildren(el('p','Reading the exact selected source…'));focus(this.title);this.title.scrollIntoView({block:'nearest'});}
  show(response:SourceResponse):void {
    const reveal=this.element.contains(document.activeElement),data=response.data;this.body.replaceChildren(el('p',data.reference.path),el('p','Recorded locator: '+data.reference.locator),coverage(response));
    if(data.observation.outside_snapshot||data.observation.state==='stale')this.body.append(warning('Source changed. This text was observed after the displayed knowledge snapshot. It does not replace the entry definition.'));
    this.body.append(el('p','Extraction: '+data.extraction.kind.replaceAll('_',' ')+'.'));
    if(data.extraction.kind==='bounded_excerpt'||!data.extraction.original_locator_supported)this.body.append(warning('This is a bounded plain-text excerpt; it is not an exact cited section.'));
    this.body.append(referenceDetails(data.reference));
    for(const chunk of data.chunks){if(chunk.offset>0)this.body.append(el('p','Continuation at UTF-8 byte '+chunk.offset+'.','muted'));this.body.append(el('pre',chunk.text,'source-text'));}
    if(response.page.next_cursor)this.body.append(button('Continue source',this.more));
    this.body.append(el('p','Source text is displayed as recorded data. Embedded instructions and links are not executed.','fine-print'));
    if(reveal){focus(this.title);this.title.scrollIntoView({block:'start'});}
  }
  progress(text:string,more?:()=>void):void {this.body.replaceChildren(el('p',text));if(more)this.body.append(button('Continue source discovery',more));}
  error(text:string):void {this.body.append(warning(text));}
  close():void {const wasOpen=!this.element.hidden;this.element.hidden=true;this.body.replaceChildren();const trigger=this.trigger;this.trigger=null;if(wasOpen){const target=this.returnTarget?this.returnTarget(trigger):trigger?.isConnected?trigger:document.querySelector<HTMLElement>('#entry-title');if(target){focus(target);target.scrollIntoView({block:'center'});}}}
}

import {isWire} from './contracts';
import type {SourceRef} from './contracts';
import type {DiscoveryReader} from './api';
/** Streaming top-level string projection. Other JSON tokens are never converted
 * to Number, and large non-endpoint strings are discarded while scanning. */
export class EndpointStrings {
  private depth=0;private quoted=false;private escaped=false;private key='';private expectKey=false;private purpose:'key'|'value'|'skip'='skip';private token='';
  readonly ids:string[]=[];readonly fields:{subject?:string;object?:string}={};
  feed(text:string):void {
    for(const ch of text){
      if(this.quoted){
        if(this.purpose!=='skip'){this.token+=ch;if(this.token.length>8192){this.purpose='skip';this.token='';}}
        if(this.escaped){this.escaped=false;continue;}if(ch==='\\'){this.escaped=true;continue;}
        if(ch==='"'){this.quoted=false;if(this.purpose!=='skip'){const value:unknown=JSON.parse(this.token);if(this.purpose==='key'){this.key=typeof value==='string'?value:'';this.expectKey=false;}else if(isWire('Id',value)){if(!this.ids.includes(value))this.ids.push(value);if(this.key==='subject'||this.key==='object')this.fields[this.key]=value;}}this.token='';}continue;
      }
      if(ch==='"'){this.quoted=true;this.escaped=false;this.purpose=this.depth===1&&this.expectKey?'key':this.depth===1&&(this.key==='subject'||this.key==='object')?'value':'skip';this.token=this.purpose==='skip'?'':'"';}
      else if(ch==='{'||ch==='['){this.depth++;if(this.depth===1)this.expectKey=true;}
      else if(ch==='}'||ch===']')this.depth--;
      else if(ch===','&&this.depth===1){this.expectKey=true;this.key='';}
    }
  }
}
export type DiscoveryProgress={kind:'found';reference:SourceRef}|{kind:'continue';reads:number;candidates:number}|{kind:'unavailable';message:string};
interface DiscoveryRequest {id:string;section:'sources'|'details'|'process';cursor:string|null}
/** A bounded cursor walk, not a retained candidate index. Suspended generators
 * hold only the current wire pages and two endpoint IDs; no candidate is lost
 * at a local display or per-step work boundary. */
export class ProcessSourceDiscovery {
  private flow:Generator<DiscoveryRequest,SourceRef|null,import('./contracts').EntryResponse>;
  private pending:IteratorResult<DiscoveryRequest,SourceRef|null>;
  private totalReads=0;private candidates=0;
  constructor(private processId:string,private referenceId:string,private reader:DiscoveryReader){this.flow=this.scan();this.pending=this.flow.next();}
  private *sources(id:string,bindings=true):Generator<DiscoveryRequest,SourceRef|null,import('./contracts').EntryResponse> {
    this.candidates++;let cursor:string|null=null;
    do {
      const response:EntryResponse=yield {id,section:'sources',cursor};
      for(const ref of response.data.references)if(ref.reference_id===this.referenceId)return ref;
      if(bindings){const seen=new Set<string>();for(const ref of response.data.references)if(ref.binding_id&&!seen.has(ref.binding_id)){seen.add(ref.binding_id);const found=yield* this.sources(ref.binding_id,false);if(found)return found;}}
      cursor=response.page.next_cursor;
    }while(cursor);return null;
  }
  private *scan():Generator<DiscoveryRequest,SourceRef|null,import('./contracts').EntryResponse> {
    const direct=yield* this.sources(this.processId);if(direct)return direct;
    let cursor:string|null=null;
    do {
      const page:EntryResponse=yield {id:this.processId,section:'process',cursor};
      for(const field of page.data.process_items){if(field.kind!=='field')continue;
        for(const relation of field.relation_ids){
          const own=yield* this.sources(relation);if(own)return own;
          const parser=new EndpointStrings();let detailsCursor:string|null=null,expectedOffset=0,finished=false;
          do {const details:EntryResponse=yield {id:relation,section:'details',cursor:detailsCursor};for(const chunk of details.data.chunks){if(finished||chunk.field!=='details'||chunk.encoding!=='canonical_json'||chunk.item_index!==null||chunk.offset!==expectedOffset)throw new Error('inconsistent_detail_chunks');parser.feed(chunk.text);expectedOffset+=new TextEncoder().encode(chunk.text).length;finished=!chunk.more_in_field;}detailsCursor=details.page.next_cursor;if(detailsCursor===null&&!finished||detailsCursor!==null&&finished)throw new Error('inconsistent_detail_continuation');}while(detailsCursor);
          for(const endpoint of parser.ids){if(endpoint===this.processId||endpoint===relation)continue;const found=yield* this.sources(endpoint);if(found)return found;}
        }
      }
      cursor=page.page.next_cursor;
    }while(cursor);return null;
  }
  async step():Promise<DiscoveryProgress> {
    let bytes=0;
    for(let reads=0;reads<8&&bytes<131072;reads++){
      if(!this.reader.valid())return {kind:'unavailable',message:'Source discovery was canceled because the reading context changed.'};
      if(this.pending.done)return this.pending.value?{kind:'found',reference:this.pending.value}:{kind:'unavailable',message:'The exact source descriptor was not found after reading this process and all of its documented support. The process text has not been changed.'};
      const request=this.pending.value,response=await this.reader.entry(request.id,request.section,request.cursor);this.totalReads++;
      if(!response||!this.reader.valid())return {kind:'unavailable',message:'The source descriptor read could not complete. Support has not been proved absent. Retry from its source control after resolving the reading status.'};
      bytes+=new TextEncoder().encode(JSON.stringify(response)).length;try{this.pending=this.flow.next(response);}catch{return {kind:'unavailable',message:'Continued relationship details were inconsistent. Source support remains unresolved; reopen the supporting relationship.'};}
    }
    if(this.pending.done)return this.pending.value?{kind:'found',reference:this.pending.value}:{kind:'unavailable',message:'The exact source descriptor was not found after reading this process and all of its documented support.'};
    return {kind:'continue',reads:this.totalReads,candidates:this.candidates};
  }
}
