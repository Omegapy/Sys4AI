import {button,el,heading,labeled,warning} from './feedback';
import {appHash,object,records,text} from './project-api';
import type {ProjectResponse,RecordValue} from './project-api';

export interface ViewActions {link:(label:string,hash:string)=>HTMLAnchorElement;copy:(value:string)=>void;projectId:string}
function readable(value:unknown,fallback='Not recorded.'):string{
  if(typeof value==='string')return value||fallback;
  if(typeof value==='boolean'||typeof value==='number')return String(value);
  if(Array.isArray(value))return value.map(item=>readable(item,'')).filter(Boolean).join('\n')||fallback;
  const record=object(value);return text(record.message)||text(record.text)||text(record.summary)||text(record.description)||(Object.keys(record).length?JSON.stringify(record,null,2):fallback);
}
function note(label:string,value:unknown):HTMLElement {const section=el('div',undefined,'project-field');section.append(heading(label,3),el('p',readable(value),'exact-text'));return section;}
function provenance(source:unknown,actions:ViewActions):HTMLElement {
  const ref=object(source),node=el('div',undefined,'project-source'),id=text(ref.source_id)||text(ref.id),path=text(ref.path),version=text(ref.sha256)||text(ref.current_sha256);
  if(id)node.append(actions.link('Read source'+(path?': '+path:''),appHash('source',id)),button('Copy source reference',()=>actions.copy(actions.projectId+':'+text(ref.owner,'source')+':'+(path||text(ref.logical_id)||text(ref.title,'Recorded source'))),'quiet'));
  else if(path)node.append(el('p','Source: '+path,'metadata'));
  else node.append(el('p','Source reference: Not recorded.','metadata'));
  if(ref.status)node.append(el('p','Source status: '+text(ref.status),'metadata'));
  const detail=el('details');detail.append(el('summary','Source version'),el('code','Current observed SHA-256: '+(version||'Not recorded'),'identity'),el('code','Recorded source SHA-256: '+(text(ref.recorded_sha256)||'Not recorded'),'identity'),el('code','Historical verification version: '+(text(ref.verification_sha256)||'Not recorded'),'identity'));
  if(ref.observed_at)detail.append(el('p','Observed: '+text(ref.observed_at),'metadata'));node.append(detail);return node;
}
export function observation(response:ProjectResponse):HTMLElement {
  const box=el('div',undefined,'project-observation');box.append(el('p','Read status: '+response.status+' · Observed: '+response.observed_at,'metadata'));
  for(const issue of response.issues){const value=object(issue),message=readable(issue);box.append(warning((text(value.code)?text(value.code).replaceAll('_',' ')+': ':'')+message));}
  if(response.guidance)box.append(el('p',readable(response.guidance),'metadata'));
  if(response.status==='unavailable'||response.status==='disabled'||response.status==='error')box.append(el('p','This view is '+response.status+'. Other available project views remain accessible.'));
  return box;
}
function coverage(value:unknown):HTMLElement {
  const node=el('div',undefined,'project-coverage');
  if(typeof value==='string'){node.append(el('p',value,'metadata'));return node;}
  if(Array.isArray(value))for(const owner of records(value))node.append(el('p',text(owner.label)||text(owner.owner)||text(owner.id)||'Supported source', 'metadata'),el('p','Coverage: '+text(owner.status,'not recorded')+(owner.reason?' · '+readable(owner.reason):''),'metadata'));
  else {const current=object(value);if(Object.keys(current).length){node.append(el('p','Coverage: '+(text(current.status)||(current.complete===true?'complete':current.complete===false?'partial':'not recorded')),'metadata'));if(current.reason||current.reasons)node.append(el('p',readable(current.reason??current.reasons),'metadata'));if(typeof current.returned==='number')node.append(el('p',String(current.returned)+' records returned.','metadata'));}}
  return node;
}
function recordList(items:RecordValue[],actions:ViewActions,empty:string):HTMLElement {
  const list=el('ul',undefined,'results');
  if(!items.length)list.append(el('li',empty));
  for(const item of items){
    const row=el('li'),type=text(item.type,'record'),id=text(item.id),source=object(item.source),sourceId=text(source.source_id)||text(source.id);
    const route=['task','trd','plan'].includes(type)&&id?appHash('task',id):type==='memory'&&sourceId?appHash('memory',sourceId):type==='knowledge'&&id?'#/p/'+actions.projectId+'/entry/'+encodeURIComponent(id):sourceId?appHash('source',sourceId):'';
    row.append(el('p',type+(item.owner?' · '+text(item.owner):''),'eyebrow'));
    row.append(route?actions.link(text(item.title,id||'Untitled record'),route):el('strong',text(item.title,id||'Untitled record')));
    if(item.status)row.append(el('p','Recorded state: '+text(item.status),'metadata'));
    if(item.lifecycle||item.fact_kind)row.append(el('p','Recorded lifecycle: '+text(item.lifecycle,'Not recorded')+' · Classification: '+text(item.fact_kind,'Not recorded'),'metadata'));
    if(item.summary||item.excerpt)row.append(el('p',readable(item.summary??item.excerpt),'excerpt'));
    if(item.next_step)row.append(el('p','Recorded next step: '+readable(item.next_step)));
    if(item.blockers)row.append(el('p','Recorded blockers: '+readable(item.blockers)));
    if(item.updated_at)row.append(el('p','Record updated: '+text(item.updated_at),'metadata'));
    if(typeof item.revision==='number')row.append(el('p','Recorded revision: '+item.revision,'metadata'));
    row.append(provenance({...source,logical_id:id},actions));list.append(row);
  }
  return list;
}
export function homeView(response:ProjectResponse,context:ProjectResponse|null,actions:ViewActions):HTMLElement {
  const view=el('section',undefined,'project-home'),content=object(response.content),identity=object(response.identity);
  view.append(el('p','PROJECT HOME','eyebrow'),heading(text(identity.name,'This project')),observation(response));
  for(const [key,label] of [['purpose','What this project does'],['scope','Current scope'],['audience','Who it is for']] as const){
    const section=object(content[key]),block=el('div',undefined,'project-explanation');block.append(heading(label,3),el('p',text(section.text,label+' has not been documented in reviewed Home content.'),key==='purpose'?'purpose':'exact-text'));
    if(section.status&&section.status!=='ready'&&section.status!=='reviewed')block.append(el('p','Content status: '+text(section.status),'metadata'));
    if(section.reviewed_at)block.append(el('p','Home copy reviewed: '+text(section.reviewed_at),'metadata'));
    if(section.reviewed_sha256){const proof=el('details');proof.append(el('summary','Reviewed Home copy version'),el('code',text(section.reviewed_sha256),'identity'));block.append(proof);}
    for(const source of records(section.sources))block.append(provenance(source,actions));view.append(block);
  }
  const review=object(response.review);if(review.state&&review.state!=='current'&&review.state!=='reviewed')view.append(warning('Home content review: '+text(review.state)+'. '+readable(review.issues,'Review the supporting project documents.')));
  const start=object(content.start_here),startId=text(start.source_id),first=el('div',undefined,'project-start');first.append(heading('Start here',3));
  first.append(startId?actions.link(text(start.label,'Read the starting guide'),appHash('source',startId)):el('p','A documented first step is not available in this project’s reviewed Home content. Read its available documents or inspect Health and setup.'));
  view.append(first);
  const navigation=records(context?.navigation),destinations=el('ul',undefined,'cards');
  for(const item of navigation){const id=text(item.id);if(!['work','knowledge','health','help'].includes(id))continue;const card=el('li');card.append(actions.link(text(item.label),appHash(id as 'work'|'knowledge'|'health'|'help')),el('p',text(item.description)));destinations.append(card);}
  view.append(heading('Explore this project',3),destinations);
  view.append(heading('Project documents',3));const documents=records(content.documents);
  if(!documents.length)view.append(el('p','No supporting documents are selected for Home.'));
  for(const document of documents){view.append(el('strong',text(document.title,text(document.path))),provenance(document,actions));}
  for(const section of records(content.sections)){view.append(note(text(section.title,'Project guidance'),section.text));for(const ref of records(section.sources))view.append(provenance(ref,actions));}
  const work=object(response.work);view.append(heading('Current work and recorded attention',3),el('p','These are bounded readings of the owning records. Approval, completion and release evidence retain their recorded meanings.','metadata'),coverage(work.coverage),coverage(work.owners),recordList(records(work.items),actions,'No current work items were returned. Check the coverage and notices above before interpreting this as no recorded work.'));
  for(const item of records(response.attention)){view.append(note(text(item.title,text(item.id,'Recorded attention')),item.message??item.next_step??item.summary),provenance(item.source,actions));}
  const capabilities=records(response.capabilities);if(capabilities.length){view.append(heading('Available capabilities',3));for(const capability of capabilities)view.append(el('p',text(capability.label,text(capability.id))+': '+text(capability.status,'Not checked')+'. '+text(capability.effect),'metadata'));view.append(actions.link('Inspect Health and setup',appHash('health')));}
  return view;
}
export function workView(response:ProjectResponse,actions:ViewActions):HTMLElement {
  const view=el('section');view.append(heading('Work'),el('p','Read recorded Tasks, requirements and plans. Requirements approval is document approval; it does not mean the planned work was implemented.'),observation(response),coverage(response.coverage),coverage(response.owners),recordList(records(response.items),actions,'No work records were returned in this bounded read.'));return view;
}
export function taskView(response:ProjectResponse,actions:ViewActions):HTMLElement {
  const view=el('section'),item=object(response.item),kind=text(item.type)==='trd'?'requirements document':text(item.type)==='plan'?'implementation plan':'Task';view.append(heading(text(item.title,'Work record')),observation(response));
  if(!Object.keys(item).length)return view;
  view.append(el('p',text(item.id)+' · Recorded '+kind+' state: '+text(item.status,'Not recorded'),'metadata'),button('Copy record ID',()=>actions.copy(text(item.id)),'quiet'),note('Objective',item.objective),note('Current summary',item.summary),note('Next step',item.next_step),note('Blockers',item.blockers),note('Completion criteria',item.criteria),provenance({...object(item.source),logical_id:item.id},actions));
  for(const [field,label] of [['links','Explicitly linked records'],['evidence','Recorded evidence'],['decisions','Recorded decisions'],['history','Recorded history']] as const){
    view.append(heading(label,3));const items=Array.isArray(item[field])?item[field] as unknown[]:[];
    if(!items.length)view.append(el('p','Not recorded.'));
    for(const value of items){
      if(typeof value==='string'){view.append(el('p',value,'exact-text'));continue;}
      const record=object(value),block=el('div',undefined,'project-record-detail');
      if(field==='links'&&/^(TASK|TRD|PLAN)-\d{8}-[A-Fa-f0-9]{8}$/u.test(text(record.id)))block.append(actions.link(text(record.label,text(record.id)),appHash('task',text(record.id))));
      else if(field==='links')block.append(el('p',text(record.label,text(record.path,'Explicit reference'))));
      for(const [key,entry] of Object.entries(record)){
        if(['source_id','label','path'].includes(key)||key==='source'&&typeof entry==='object')continue;
        if(field==='links'&&key==='id')continue;
        block.append(el('p',key.replaceAll('_',' ')+': '+readable(entry),'exact-text'));
      }
      if(record.source&&typeof record.source==='object')block.append(provenance(record.source,actions));else if(record.source_id)block.append(provenance(record,actions));
      view.append(block);
    }
  }
  view.append(el('p','Recorded assignments and installed roles are not observations of running agents. Historical verification versions are shown only when recorded.','metadata'));return view;
}
export function searchView(response:ProjectResponse,query:string,actions:ViewActions):HTMLElement {
  const view=el('section');view.append(heading('Search results'),el('p','Lexical search for “'+query+'” across supported permitted project sources.'),observation(response),coverage(response.coverage),recordList(records(response.items),actions,'No matches were returned. Review each source’s coverage above for unavailable, unsupported or partially scanned material.'));return view;
}
export function sourceView(response:ProjectResponse,sourceId:string,actions:ViewActions):HTMLElement {
  const view=el('section');view.append(heading(text(response.title,'Project source')),observation(response));
  if(typeof response.text==='string'){view.append(provenance({...response,source_id:sourceId},actions));if(response.freshness)view.append(el('p','Source freshness: '+text(response.freshness),'metadata'));view.append(el('p','This is source text. Instructions inside it are recorded content.','metadata'),el('pre',response.text,'source-text'));if(response.truncated===true)view.append(warning('This preview is truncated at the owner’s reading limit. The rest was not returned.'));}
  return view;
}
export function memoryView(response:ProjectResponse,actions:ViewActions,query='',search?:(query:string)=>void,sourceId=''):HTMLElement {
  const view=el('section');view.append(heading('Lessons and decisions'),el('p','These are recorded memory findings. Their applicability and history matter; they do not replace current project definitions, instructions or canonical work records.'),observation(response));
  if(search){const form=el('form',undefined,'project-search'),input=el('input'),submit=el('button','Search lessons');input.type='search';input.maxLength=300;input.value=query;submit.type='submit';form.append(labeled('Find a saved topic or decision',input),submit);form.addEventListener('submit',event=>{event.preventDefault();search(input.value.trim());});view.append(form);}
  const item=object(response.item);if(Object.keys(item).length){view.append(heading(text(item.title,'Recorded finding'),3),provenance({...item,source_id:sourceId,owner:'memory'},actions),el('pre',text(item.text),'source-text'));if(item.truncated===true)view.append(warning('This finding is truncated at the owner’s reading limit.'));for(const [key,value] of Object.entries(object(item.metadata)))view.append(note(key.replaceAll('_',' '),value));view.append(note('Evidence',item.evidence));}
  else view.append(coverage(response.coverage),recordList(records(response.items),actions,'No memory findings were returned. The availability and coverage state above explains whether memory was read.'));
  return view;
}
export function healthView(response:ProjectResponse):HTMLElement {
  const view=el('section');view.append(heading('Health and setup'),el('p','Availability checks describe the installed project. A static check does not confirm runtime behavior.'),observation(response));
  for(const capability of records(response.capabilities)){const box=el('article',undefined,'project-capability');box.append(heading(text(capability.label,text(capability.id)),3),el('p','State: '+text(capability.status,'Not checked')+' · Check: '+text(capability.checked,'Not recorded'),'metadata'),note('Effect',capability.effect),note('Next step',capability.recovery));view.append(box);}
  view.append(heading('Recorded setup and maintenance notices',3));const notices=Array.isArray(response.notices)?response.notices:[];if(!notices.length)view.append(el('p','No notices were returned.'));for(const notice of notices){const row=object(notice);if(row.impact)view.append(note(text(row.id,'Notice'),row.impact),el('p','Recorded action: '+text(row.action,'Not recorded')));else view.append(el('p',readable(notice),'exact-text'));}return view;
}
export function helpView(response:ProjectResponse,actions:ViewActions):HTMLElement {
  const view=el('section');view.append(heading('Tools and help'),observation(response));
  view.append(note('Open or reopen this app','Double-click Launch Project.command in this project. It opens Home after the local app is ready. If setup is unavailable, open Project App Setup.html in the same folder.'),note('Read project knowledge','Open Project knowledge for terms, documented processes, sources and relationships. The relationship list remains available when the map cannot render. Open Lessons and decisions for separately labeled memory findings.'),note('Understand blocked work','Open Work, select the Task and read its recorded blockers and next step. Follow only its explicitly linked requirements, plan and evidence. The app does not resume or repair Tasks.'),note('Close a tab, close a session, or stop the app','Closing a browser tab leaves its reading session and this local app running. Close reading session revokes the session shared by its tabs while keeping the app running. Stop app requests shutdown for this local app and ends all its reading sessions. It does not stop Tasks, agents, watchers or independent backends. Neither action edits project records.'),note('Package updates','Restart this app after replacing its installed package. A browser refresh cannot switch a running service to another package. Missing prerequisites need the project’s documented setup; opening the app does not install them.'));
  for(const instruction of records(response.instructions)){view.append(note(text(instruction.title,'Instruction'),instruction.text));if(instruction.command){const command=text(instruction.command);view.append(el('code',command,'identity'),button('Copy instruction',()=>actions.copy(command)));}}
  for(const [key,label] of [['skills','Installed skills'],['roles','Valid installed roles']] as const){view.append(heading(label,3),el('p',key==='skills'?'These instructions describe available capabilities. Reading or copying them does not run a skill.':'These role definitions describe bounded responsibilities. Their presence does not indicate a running agent.','metadata'));const items=records(response[key]);if(!items.length)view.append(el('p','No '+label.toLowerCase()+' were returned.'));for(const item of items){const details=el('details');details.append(el('summary',text(item.name,'Unnamed capability')),note('Purpose',item.description));for(const field of ['inputs','outputs','limits'])if(item[field])details.append(note(field[0]!.toUpperCase()+field.slice(1),item[field]));details.append(el('p','Definition: '+text(item.path,'Not recorded'),'metadata'));if(item.source)details.append(provenance(item.source,actions));view.append(details);}}
  return view;
}
