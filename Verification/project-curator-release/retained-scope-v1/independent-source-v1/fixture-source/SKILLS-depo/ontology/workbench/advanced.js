import {element,button} from './app.js';
export function mountAdvanced(app){
  const box=document.querySelector('#advanced-controls');
  const label=element('label','SPARQL query'),query=element('textarea');query.value='SELECT ?subject ?predicate ?object WHERE { ?subject ?predicate ?object } LIMIT 10';label.append(query);box.append(label);
  const graphLabel=element('label','Selected named graph'),graph=element('select');for(const value of ['asserted','inferred','derived','external'])graph.append(element('option',value));graphLabel.append(graph);box.append(graphLabel);
  const output=element('pre','No advanced operation has run.',{tabindex:'0','aria-label':'Advanced operation results'});
  const inferenceView=element('div',null,{'aria-label':'Inferred conclusions and explanations'});
  const short=value=>typeof value==='string'?value.split(/[:/#]/).pop():JSON.stringify(value);
  async function run(operation){app.message('Running '+operation+' with the selected local profile…');const result=await app.api('advanced',{operation,...(operation==='query'?{query:query.value,graphs:[graph.value]}:operation==='validate'?{graphs:[graph.value]}:{})});output.textContent=JSON.stringify(result,null,2);inferenceView.replaceChildren();if(operation==='infer'){
    inferenceView.append(element('h3','Inferred conclusions'),element('p',result.trusted?'The inference completed without conflicts. These conclusions remain derived knowledge.':'This result does not establish trustworthy conclusions. Inspect its conflicts or unavailable state.',{class:'note'}));
    const proofs=new Map((result.proofs||[]).map(proof=>[proof.id,proof]));
    for(const proof of (result.proofs||[]).filter(proof=>proof.rule!=='premise').slice(0,50)){
      const card=element('details');card.append(element('summary','Inferred: '+proof.triple.map(short).join(' → ')));
      const visit=(current,depth,seen)=>{const group=element('div');if(!current||depth>8||seen.has(current.id)){group.append(element('p','Proof continuation is bounded; inspect the exact result below.'));return group;}const next=new Set(seen);next.add(current.id);group.append(element('p',(current.rule==='premise'?'Approved premise':'Rule '+current.rule)+': '+current.triple.map(short).join(' → ')));for(const source of current.sources||[])group.append(button(source.path+' · '+source.locator,()=>app.source(source),'secondary source-button'));for(const id of current.premises||[])group.append(visit(proofs.get(id),depth+1,next));return group;};
      card.append(visit(proof,0,new Set()));inferenceView.append(card);
    }
  }app.message(operation+': '+result.status+(result.complete===false?' · Could not complete.':''),result.complete===false);}
  const actions=element('div',null,{class:'actions'});actions.append(button('Run read-only query',()=>run('query')),button('Inspect inference and derivations',()=>run('infer')),button('Validate selected graph',()=>run('validate')),button('Check backend readiness',()=>run('health')));box.append(actions,inferenceView,output);
  const generation=element('fieldset');generation.append(element('legend','Prepare an AI proposal request'));
  const instructionLabel=element('label','Bounded change to propose'),instruction=element('textarea');instruction.placeholder='Describe a concept or correction grounded in selected project evidence.';instructionLabel.append(instruction);
  const sourceLabel=element('label','Permitted source path'),source=element('input');source.value='SPECS.md';sourceLabel.append(source);
  const locatorLabel=element('label','Source locator'),locator=element('input');locator.value='line:1';locatorLabel.append(locator);
  const idsLabel=element('label','Approved context IDs (one per line)'),ids=element('textarea');ids.placeholder='urn:sys4ai:ontology:core:Artifact';idsLabel.append(ids);
  generation.append(instructionLabel,sourceLabel,locatorLabel,idsLabel,button('Prepare native generation request',async()=>{
    const result=await app.api('generate',{instruction:instruction.value,sources:[{path:source.value,locator:locator.value}],context_ids:ids.value.split('\n').map(v=>v.trim()).filter(Boolean)});
    output.textContent=JSON.stringify({status:result.status,runtime_invoked:result.runtime_invoked,request_id:result.request.request_id,request_sha256:result.request.request_sha256,handoff:result.handoff},null,2);
    app.message('Request prepared. Generation has not run. The trusted native agent must capture its actual sourced result.');
  }));box.append(generation);
  const imports=element('fieldset');imports.append(element('legend','Stage an RDF import for review'));
  const importSourceLabel=element('label','Selected RDF source path'),importSource=element('input');importSourceLabel.append(importSource);
  const formatLabel=element('label','RDF format'),format=element('select');for(const value of ['json-ld','turtle','xml'])format.append(element('option',value));formatLabel.append(format);
  const manifestLabel=element('label','Selected export manifest path (required for Turtle or RDF/XML)'),manifestPath=element('input');manifestLabel.append(manifestPath);
  const importReasonLabel=element('label','Reason for this import'),importReason=element('input');importReasonLabel.append(importReason);
  const targetLabel=element('label','Optional selected extension target'),target=element('input');target.placeholder='Leave blank to retain an RDF draft';targetLabel.append(target);
  imports.append(importSourceLabel,formatLabel,manifestLabel,importReasonLabel,targetLabel,button('Stage selected RDF source',async()=>{
    let manifest;if(manifestPath.value){const evidence=await app.api('source',{reference:{path:manifestPath.value,locator:'line:1'}});manifest=JSON.parse(evidence.text);}
    const result=await app.api('import',{source:{path:importSource.value,locator:'line:1'},format:format.value,reason:importReason.value,...(manifest?{manifest}:{}),...(target.value?{target_extension:target.value}:{})});output.textContent=JSON.stringify(result,null,2);await app.refresh();app.message('RDF import: '+result.status+'. Imported data remains unpublished.');
  }),button('Inspect durable RDF drafts',async()=>{await app.refresh();output.textContent=JSON.stringify(app.state.rdf_imports,null,2);}));box.append(imports);
}
