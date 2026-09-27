import {element,button} from './app.js';
const CORE='urn:sys4ai:ontology:core:';
const typeDefaults={concept:'OntologyConcept',instance:'Artifact',predicate:'RelationshipType',relation:'Relationship',binding:'SourceBinding'};
const list=value=>value.split(/[\n,]/).map(v=>v.trim()).filter(Boolean);

export function mountEditor(app){
  const form=document.querySelector('#record-form');let context=null;
  const fields={};
  function field(label,name,value='',type='text',parent=form){
    const wrapper=element('label',label),input=element(type==='textarea'?'textarea':type==='select'?'select':'input');
    input.name=name;input.id='edit-'+name;if(type!=='textarea'&&type!=='select')input.type=type;
    if(type==='select'){for(const choice of value)input.append(element('option',choice.label||choice.value||choice,{value:choice.value||choice}));}
    else input.value=value??'';
    wrapper.append(input);parent.append(wrapper);fields[name]=input;return input;
  }
  function open(record=null,options={}){
    context={record,proposal:options.proposal||null};for(const key of Object.keys(fields))delete fields[key];
    form.replaceChildren();form.hidden=false;
    const error=element('p','',{role:'alert',class:'finding'});error.hidden=true;form.append(error);
    const grid=element('div',null,{class:'form-grid'});form.append(grid);
    const id=field('Stable project ID','id',record?.['@id']||'','text',grid);id.placeholder='new-concept';id.required=true;if(record)id.readOnly=true;
    const kind=field('Record kind','kind',['concept','instance','predicate','relation','binding'],'select',grid);kind.value=record?.kind||(options.related?'relation':'concept');kind.disabled=!!record;
    field('Label','label',record?.label||'','text',grid).required=true;
    const types=field('Type IDs (one per line)','types',(record?.['@type']||[CORE+typeDefaults[kind.value]]).join('\n'),'textarea',grid);if(record)types.readOnly=true;
    const definition=field('Definition','definition',record?.definition||'','textarea',grid);definition.parentElement.className='wide';
    field('Aliases (one per line)','aliases',(record?.aliases||[]).join('\n'),'textarea',grid);
    field('Scope and distinctions','scope_note',record?.scope_note||'','textarea',grid);
    const lifecycle=field('Intended lifecycle after publication','lifecycle',['approved','draft','deprecated'],'select',grid);lifecycle.value=record?.lifecycle||'approved';
    field('Replacement ID (for deprecation)','replacement',record?.replacement||'','text',grid);
    const specialized=element('fieldset');specialized.append(element('legend','Properties, relationships and constraints'));form.append(specialized);
    const specializedGrid=element('div',null,{class:'form-grid'});specialized.append(specializedGrid);
    function special(){
      specializedGrid.replaceChildren();
      if(!record)types.value=CORE+typeDefaults[kind.value];
      const visible=kind.value;
      if(visible==='predicate'){
        field('Permitted domain type IDs','domain',(record?.domain||[CORE+'Artifact']).join('\n'),'textarea',specializedGrid);
        field('Permitted range type IDs','range',(record?.range||[CORE+'Artifact']).join('\n'),'textarea',specializedGrid);
        field('Minimum outgoing relationships','min',record?.cardinality?.min??0,'number',specializedGrid).min='0';
        field('Maximum (blank means unbounded)','max',record?.cardinality?.max??'','number',specializedGrid).min='0';
        const acyclic=field('Must be acyclic','acyclic',['false','true'],'select',specializedGrid);acyclic.value=String(record?.acyclic??false);
      }
      if(visible==='relation'){
        field('Subject ID','subject',record?.subject||options.related||'','text',specializedGrid);
        field('Predicate ID','predicate',record?.predicate||'','text',specializedGrid);
        field('Object ID','object',record?.object||'','text',specializedGrid);
      }
      if(visible==='binding'){
        field('Bound entity ID','entity',record?.entity||options.related||'','text',specializedGrid);
        const binding=field('Binding type','binding_type',['artifact','skill','role','specification','registry'],'select',specializedGrid);binding.value=record?.binding_type||'artifact';
      }
      if(visible==='concept'||visible==='instance')specializedGrid.append(element('p','Relationships are separate records. Create a relation draft to connect this identity to another concept.',{class:'meta'}));
      if(visible==='predicate'||visible==='relation'){
        const group=element('div',null,{class:'wide'});group.append(element('h3',visible==='predicate'?'Qualifier property definitions':'Qualifier property values'));
        const rows=element('div');group.append(rows);
        function qualifier(name='',value={}){
          const row=element('div',null,{class:'form-grid qualifier-row'});rows.append(row);
          const nameField=element('label','Property name'),nameInput=element('input');nameInput.value=name;nameInput.className='qualifier-name';nameField.append(nameInput);row.append(nameField);
          const typeField=element('label','Value type'),typeInput=element('select');typeInput.className='qualifier-type';for(const type of ['string','integer','number','boolean'])typeInput.append(element('option',type));typeInput.value=visible==='predicate'?(value.type||'string'):(typeof value==='boolean'?'boolean':typeof value==='number'?'number':'string');typeField.append(typeInput);row.append(typeField);
          const valueField=element('label',visible==='predicate'?'Required':'Value'),valueInput=element(visible==='predicate'?'select':'input');valueInput.className='qualifier-value';if(visible==='predicate'){for(const val of ['false','true'])valueInput.append(element('option',val));valueInput.value=String(value.required??false);}else valueInput.value=typeof value==='object'?'':String(value);valueField.append(valueInput);row.append(valueField);
          row.append(button('Remove property',()=>row.remove(),'secondary'));
        }
        for(const [name,value] of Object.entries(record?.qualifiers||{}))qualifier(name,value);
        group.append(button('Add property',()=>qualifier()));specializedGrid.append(group);
      }
    }
    kind.addEventListener('change',special);special();
    const sources=element('fieldset');sources.append(element('legend','Source bindings'));const sourceRows=element('div');sources.append(sourceRows);form.append(sources);
    function sourceRow(value={path:app.state.source_choices.includes('SPECS.md')?'SPECS.md':app.state.source_choices[0],locator:'line:1'}){
      const row=element('div',null,{class:'form-grid source-row'});const pathLabel=element('label','Selected source'),path=element('select');path.className='source-path';for(const choice of [...new Set([...app.state.source_choices,value.path])])if(choice)path.append(element('option',choice));path.value=value.path;pathLabel.append(path);
      const locatorLabel=element('label','Locator (section, lines or JSON pointer)'),locator=element('input');locator.className='source-locator';locator.value=value.locator||'line:1';locatorLabel.append(locator);row.append(pathLabel,locatorLabel,button('Remove source',()=>row.remove()));sourceRows.append(row);
    }
    for(const source of record?.sources?.length?record.sources:[undefined])sourceRow(source);sources.append(button('Add source binding',()=>sourceRow()));
    const reason=field('Reason for this change','reason',context.proposal?.revision.rationale||'','textarea');reason.required=true;
    const actions=element('div',null,{class:'actions'});const submit=element('button','Save draft',{type:'submit'});actions.append(submit,button('Cancel editing',()=>{form.hidden=true;app.message('Editing closed. Saved proposals and canonical content are preserved.');}));form.append(actions);
    document.querySelector('#editor-context').textContent=(context.proposal?'Revising '+context.proposal.head.proposal_id+' · revision '+context.proposal.head.revision:record?'Draft change to '+record.label:'New project draft')+'. Intended lifecycle is applied only after authorized publication.';
    form.onsubmit=async event=>{
      event.preventDefault();error.hidden=true;submit.disabled=true;app.message('Saving the unpublished candidate…');
      try{
        const rid=id.value.startsWith('urn:')?id.value:app.state.project.namespace+id.value.trim();
        const data={id:rid,kind:kind.value,label:fields.label.value,definition:fields.definition.value,types:list(types.value),aliases:list(fields.aliases.value),scope_note:fields.scope_note.value,lifecycle:lifecycle.value,reason:reason.value,sources:[...sourceRows.querySelectorAll('.source-row')].map(row=>({path:row.querySelector('.source-path').value,locator:row.querySelector('.source-locator').value}))};
        if(fields.replacement.value)data.replacement=fields.replacement.value;
        if(data.lifecycle==='deprecated')data.deprecation_reason=reason.value;
        if(data.kind==='predicate'){data.domain=list(fields.domain.value);data.range=list(fields.range.value);data.acyclic=fields.acyclic.value==='true';data.cardinality={min:Number(fields.min.value),max:fields.max.value===''?null:Number(fields.max.value)};data.qualifier_schema={};}
        if(data.kind==='relation'){for(const key of ['subject','predicate','object'])data[key]=fields[key].value;data.qualifiers={};}
        if(data.kind==='binding'){data.entity=fields.entity.value;data.binding_type=fields.binding_type.value;}
        for(const row of specializedGrid.querySelectorAll('.qualifier-row')){const name=row.querySelector('.qualifier-name').value,type=row.querySelector('.qualifier-type').value,value=row.querySelector('.qualifier-value').value;if(!name)throw new Error('Every added qualifier property needs a name.');if(data.kind==='predicate')data.qualifier_schema[name]={type,required:value==='true'};else{if(type==='boolean'&&!['true','false'].includes(value))throw new Error('Boolean qualifier values must be true or false.');data.qualifiers[name]=type==='boolean'?value==='true':['integer','number'].includes(type)?Number(value):value;}}
        const target=record?.location||app.state.targets.find(t=>data.kind==='binding'?t.path.startsWith('ONTOLOGY/bindings/'):t.path.endsWith('.jsonld')&&t.path.startsWith('ONTOLOGY/modules/project/'))?.path;
        const selected=app.state.targets.find(t=>t.path===target);if(!selected)throw new Error('The current trusted session cannot edit this target.');
        const result=await app.api('draft',{form:data,expected_target_sha256:record?.target_sha256||selected.sha256,...(context.proposal?{proposal_id:context.proposal.head.proposal_id,expected_revision:context.proposal.head.revision}:{})});
        context.proposal=result;await app.refresh();app.review.show(result);app.message('Draft saved as '+result.head.proposal_id+' revision '+result.head.revision+'. Approved content is unchanged.');
      }catch(failure){error.textContent=failure.message;error.hidden=false;app.message(failure.message,true);}finally{submit.disabled=false;}
    };
    document.querySelector('#editor').scrollIntoView({block:'start'});id.focus();
  }
  return {open};
}
