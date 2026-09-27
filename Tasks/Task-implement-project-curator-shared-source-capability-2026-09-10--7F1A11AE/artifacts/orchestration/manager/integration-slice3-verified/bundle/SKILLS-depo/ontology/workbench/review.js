import {element,button} from './app.js';
export function mountReview(app){
  const select=document.querySelector('#proposal-select'),detail=document.querySelector('#proposal-detail');
  function refreshList(){const chosen=select.value;select.replaceChildren(element('option','Select a proposal',{value:''}));for(const head of app.state.proposals)select.append(element('option',head.proposal_id+' · r'+head.revision+' · '+head.state,{value:head.proposal_id}));select.value=chosen;}
  async function open(id){show(await app.api('proposal',{id}));}
  async function action(endpoint,data){app.message('Running '+endpoint+' for the exact saved revision…');try{const result=await app.api(endpoint,data);await app.refresh();show(result.proposal||result);if(result.receipt){app.message(result.status==='published'?'Published and reopened the canonical result.':'Partial publication. The review shows committed and pending files.',result.status!=='published');}else app.message('Proposal state: '+(result.head?.state||result.status)+'.');}catch(error){app.message(error.message,true);const note=element('p',error.message,{class:'finding',role:'alert'});detail.prepend(note);}}
  function show(value){
    app.proposal=value;select.value=value.head.proposal_id;detail.replaceChildren();
    const head=value.head,revision=value.revision;detail.append(element('h3',head.proposal_id+' · Revision '+revision.revision));
    detail.append(element('span',value.superseded?'Superseded revision':head.state,{class:'badge draft'}),element('p',revision.rationale));
    detail.append(element('p',revision.generator?.claim||'Saved form candidate. Generation was not invoked.',{class:'meta'}));
    if(revision.source_packet)detail.append(element('p','Source request: '+revision.source_packet.request_id,{class:'meta'}));
    for(const text of revision.uncertainty)detail.append(element('p','Uncertainty: '+text,{class:'note'}));
    const refs=element('details');refs.append(element('summary','Supporting evidence and attribution'));for(const ref of revision.evidence)refs.append(button(ref.path+' · '+ref.locator,()=>app.source(ref),'secondary source-button'));refs.append(element('pre',JSON.stringify({generator:revision.generator,source_packet:revision.source_packet,revision_sha256:revision.revision_sha256},null,2)));detail.append(refs);
    const diff=element('div');diff.append(element('h3','Semantic diff'));
    for(const change of revision.semantic_diff){const card=element('div',null,{class:'diff-card'});card.append(element('strong',change.change+' · '+(change.id?.split(':').pop()||change.path)),element('p',change.path,{class:'meta'}));for(const [field,values] of Object.entries(change.fields)){card.append(element('h4',field));const pair=element('div',null,{class:'diff-fields'});for(const side of ['before','after']){const col=element('div');col.append(element('strong',side==='before'?'Current canonical value':'Candidate value'),element('pre',JSON.stringify(values[side],null,2)));pair.append(col);}card.append(pair);}diff.append(card);}detail.append(diff);
    if(value.validation){const report=value.validation;detail.append(element('h3',report.eligible?'Validation: eligible for exact review':'Validation: unresolved findings'));for(const item of report.findings)detail.append(element('p',item.code+': '+item.message+(item.record_id?' · '+item.record_id:''),{class:'finding'}));detail.append(element('p','Core: '+(report.core.valid?'valid':'invalid')+' · Standards: '+report.standards.status+' · Inference: '+report.inference.status+' · Competency: '+(report.competency.valid?'passed':'failed'),{class:'meta'}));const impact=element('details');impact.append(element('summary','Inspect wiki, query and relationship impact'),element('pre',JSON.stringify(report.impact,null,2)));detail.append(impact);}
    if(value.review)detail.append(element('p','Exact review recorded. Current native authorization and a canonical publication receipt are still required.',{class:'note'}));
    const reasonLabel=element('label','Review reason'),reason=element('textarea');reason.value='Reviewed the exact candidate, source evidence, validation and semantic impact.';reasonLabel.append(reason);detail.append(reasonLabel);
    const actions=element('div',null,{class:'actions'});const common={id:head.proposal_id,revision:head.revision};
    if(!value.superseded&&app.state.authoring){
      if(!['published','partial'].includes(head.state)){
        actions.append(button('Validate saved draft',()=>action('validate',common)));
        actions.append(button('Add a record to this draft',()=>app.editor.open(null,{proposal:value})));
        actions.append(button('Revise in editor',()=>{const change=revision.semantic_diff.find(item=>item.id);if(!change)throw new Error('This advanced document needs the trusted native candidate editor.');const file=revision.candidate.changes.find(item=>item.path===change.path),record=JSON.parse(file.content)['@graph'].find(item=>item['@id']===change.id);app.editor.open({...record,location:change.path,target_sha256:file.expected_sha256},{proposal:value});}));
        if(value.validation?.eligible)actions.append(button('Accept exact review',()=>action('decide',{...common,decision:'accept',reason:reason.value,validation_sha256:head.validation_sha256})));
        if(head.state==='reviewed')actions.append(button('Publish reviewed change',()=>action('publish',{...common,review_sha256:head.review_sha256}),''));
        actions.append(button('Reject proposal',()=>action('decide',{...common,decision:'reject',reason:reason.value}),'danger'));
        actions.append(button('Discard draft',()=>action('decide',{...common,decision:'discard',reason:reason.value}),'danger'));
        if(['rejected','discarded','superseded'].includes(head.state))actions.append(button('Reopen draft',()=>action('decide',{...common,decision:'reopen',reason:reason.value})));
      }else if(head.state==='partial')actions.append(button('Recover exact operation',()=>action('recover',common)));
      else actions.append(button('Reopen canonical result',async()=>{await app.refresh();await app.search();const change=revision.semantic_diff.find(item=>item.id);if(change)await app.inspect(change.id);document.querySelector('#browse').scrollIntoView({block:'start'});}));
    }
    detail.append(actions);
    for(const event of value.events.filter(event=>['published','partial'].includes(event.decision))){const evidence=element('details');evidence.open=true;evidence.append(element('summary','Actual '+event.decision+' receipt and reopened target hashes'),element('pre',JSON.stringify(event.details,null,2)));detail.append(evidence);}
    const history=element('details');history.append(element('summary','Revision and decision history'));for(const event of value.events){const row=element('p','Revision '+event.revision+' · '+event.decision+' · '+event.at+' ');row.append(button('Open revision '+event.revision,async()=>show(await app.api('proposal',{id:head.proposal_id,revision:event.revision}))));history.append(row);}detail.append(history);
  }
  select.addEventListener('change',()=>{if(select.value)open(select.value).catch(error=>app.message(error.message,true));});
  document.querySelector('#refresh-proposals').addEventListener('click',()=>app.refresh().catch(error=>app.message(error.message,true)));
  return {show,open,refreshList};
}
