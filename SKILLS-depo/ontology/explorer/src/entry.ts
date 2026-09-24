import type {EntryResponse,Header,Section,SourceRef} from './contracts';
import {button,coverage,el,heading,sourceButton,statuses} from './feedback';
export const sectionLabels:Record<Section,string>={header:'Summary',label:'Full name',definition:'Definition',aliases:'Aliases',scope_note:'Scope',examples:'Examples',non_examples:'Non-examples',details:'Details',qualifiers:'Qualifiers',sources:'Sources',process:'Process'};
export interface EntryActions {section:(section:Section,cursor?:string|null)=>void;source:(owner:string,reference:string,trigger:HTMLElement)=>void;map:()=>void;relationships:()=>void;copyId:()=>void;copyLink:()=>void}
export class EntryView {
  readonly element=el('article',undefined,'entry');readonly title=heading('Reading entry');
  private controls=el('nav',undefined,'section-tabs');private content=el('section');private header:Header|null=null;
  constructor(private actions:EntryActions){this.element.addEventListener('click',event=>{if(this.element.dataset.pending==='true'&&(event.target as HTMLElement).closest('button,a')){event.preventDefault();event.stopImmediatePropagation();}},true);this.controls.setAttribute('aria-label','Entry sections');this.element.append(this.title,this.controls,this.content);}
  pending(value:boolean):void {this.element.dataset.pending=String(value);this.element.setAttribute('aria-busy',String(value));for(const control of this.element.querySelectorAll('button'))control.disabled=value;for(const anchor of this.element.querySelectorAll('a')){if(value){anchor.tabIndex=-1;anchor.setAttribute('aria-disabled','true');}else{anchor.removeAttribute('tabindex');anchor.removeAttribute('aria-disabled');}}}
  showHeader(response:EntryResponse):void {
    this.pending(false);
    const header=response.data.header;if(!header)return;this.header=header;this.title.textContent=header.label;this.title.id='entry-title';
    const preface=el('div');preface.append(statuses(header.lifecycle,header.fact_kind,header.source_state));
    if(header.definition_excerpt){preface.append(el('p',header.definition_excerpt,'definition'));if(header.excerpt_truncated)preface.append(el('p','Definition preview. Read the Definition section for the exact continued text.','muted'));}
    if(header.label_truncated)preface.append(el('p','Name preview. The Full name section preserves the complete recorded label.','muted'));
    preface.append(el('p','Recorded lifecycle and classification describe this entry. They do not verify its truth or grant execution authority.','fine-print'));
    const actions=el('div',undefined,'actions');actions.append(button('View on map',this.actions.map),button('Relationships',this.actions.relationships),button('Copy stable ID',this.actions.copyId),button('Copy local link',this.actions.copyLink));
    const details=el('details');details.append(el('summary','Identity and provenance'),el('code',header.id,'identity'),el('p',header.module_id+(header.module_version?' · '+header.module_version:'')),el('p','Record kind: '+header.kind));preface.append(actions,details);
    const tabs=header.available_sections.filter(x=>x!=='header');this.controls.replaceChildren();for(const section of tabs){const tab=button(sectionLabels[section],()=>this.actions.section(section));tab.dataset.section=section;this.controls.append(tab);}
    this.element.replaceChildren(this.title,preface,this.controls,this.content);this.content.replaceChildren();
  }
  showSection(response:EntryResponse):void {
    const section=response.data.section;
    if(section==='header'){this.showHeader(response);return;}
    for(const node of this.controls.querySelectorAll<HTMLButtonElement>('button'))node.setAttribute('aria-pressed',String(node.dataset.section===section));
    this.content.replaceChildren(heading(sectionLabels[section],3),coverage(response));
    if(response.data.chunks.length){for(const chunk of response.data.chunks){const text=el(chunk.encoding==='canonical_json'?'pre':'p',chunk.text,chunk.encoding==='canonical_json'?'exact-json':'exact-text');text.dataset.offset=String(chunk.offset);if(chunk.item_index!==null)text.dataset.itemIndex=String(chunk.item_index);this.content.append(text);if(chunk.offset>0)this.content.append(el('p','Continuation at UTF-8 byte '+chunk.offset+'.','muted'));if(chunk.more_in_field)this.content.append(el('p','This field continues on the next page.','muted'));}}
    for(const ref of response.data.references){const block=el('div',undefined,'source-reference');block.append(sourceButton(ref,this.actions.source),el('p','Source: '+ref.source_state),el('code','Recorded SHA256: '+ref.recorded_sha256,'identity'));this.content.append(block);}
    if(!response.data.chunks.length&&!response.data.references.length&&section!=='process')this.content.append(el('p','No '+sectionLabels[section].toLowerCase()+' is recorded in this returned section.'));
    if(response.page.next_cursor)this.content.append(button('Continue '+sectionLabels[section].toLowerCase(),()=>this.actions.section(section,response.page.next_cursor)));
  }
  replaceSection(view:HTMLElement):void {this.content.replaceChildren(view);}
  currentHeader():Header|null{return this.header;}
}
export function referenceDetails(ref:SourceRef):HTMLElement {
  const node=el('details');node.append(el('summary','Source identity and version'),el('code','Reference: '+ref.reference_id,'identity'),el('code','Owner: '+ref.owner_id,'identity'),el('code','Recorded SHA256: '+ref.recorded_sha256,'identity'),el('code','Observed SHA256: '+(ref.observed_sha256??'unavailable'),'identity'));return node;
}
