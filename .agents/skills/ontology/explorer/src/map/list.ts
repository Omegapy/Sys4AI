import type {RelationshipModel,ModelIntent} from '../model';
import {orderedRelationships} from '../model';
import type {SourceRef} from '../contracts';
import {button,el,heading,sourceButton,statuses,warning} from '../feedback';
export function relationshipList(model:RelationshipModel,onIntent:(intent:ModelIntent,trigger?:HTMLElement)=>void,selected:string|null):HTMLElement {
  const section=el('section',undefined,'relationship-list');section.append(heading('Relationships in this view',3));
  if(!model.order.length)section.append(el('p',model.local_reasons.length||model.reads.some(read=>!read.coverage.complete)?'No relationship was returned within this incomplete view. Limits or filters may hide recorded relationships.':'No relationships are recorded in this view'));
  const nodes=el('details');nodes.open=true;nodes.append(el('summary','Terms in this returned view'));const nodeList=el('ul',undefined,'node-list');
  for(const node of Object.values(model.nodes)){const row=el('li');row.dataset.nodeId=node.id;row.classList.toggle('selected',node.id===selected);row.append(el('span',node.kind,'badge'),button(node.label,()=>onIntent({kind:'selectNode',id:node.id})),button('Focus here',()=>onIntent({kind:'focus',id:node.id})),button('More connections',()=>onIntent({kind:'expand',id:node.id})));nodeList.append(row);}nodes.append(nodeList);section.append(nodes);
  const list=el('ol',undefined,'relationship-rows');
  for(const item of orderedRelationships(model)){
    const row=el('li');row.dataset.relationId=item.id;row.classList.toggle('selected',item.id===selected);
    if('kind'in item){row.dataset.marker='true';row.append(warning('Full relationship requires a detail read ('+item.reason.replaceAll('_',' ')+'). No unconditional edge is implied.'),button('Read relationship qualifiers: '+item.id,()=>onIntent({kind:'selectEdge',id:item.id})));}
    else {
      const sentence=el('div',undefined,'relationship-sentence');
      sentence.append(button(model.nodes[item.subject]?.label??item.subject,()=>onIntent({kind:'selectNode',id:item.subject})),el('span',' → '),button(item.predicate_label,()=>onIntent({kind:'inspectPredicate',id:item.predicate})),el('span',' → '),button(model.nodes[item.object]?.label??item.object,()=>onIntent({kind:'selectNode',id:item.object})));
      row.append(sentence,button('Inspect relationship',()=>onIntent({kind:'selectEdge',id:item.id})),statuses(item.lifecycle,item.fact_kind));
      const details=el('details');details.append(el('summary','Exact relationship identity and direction'),el('code',item.id,'identity'),el('p','Subject → predicate → object'),el('code',item.subject+' → '+item.predicate+' → '+item.object,'identity'));row.append(details);
      const qualifiers=el('details');qualifiers.open=true;qualifiers.append(el('summary','Recorded qualifiers'),el('pre',JSON.stringify(item.qualifiers,null,2),'qualifiers'));row.append(qualifiers);
      if(item.qualifiers!==null&&JSON.stringify(item.qualifiers)!=='{}')row.append(el('p','Read these qualifiers with the relationship; it must not be treated as unconditional.','notice'));
      for(const ref of item.source_references){const source=sourceButton(ref,(owner,reference,trigger)=>onIntent({kind:'inspectSource',owner_id:owner,reference_id:reference},trigger));row.append(source);if(ref.source_state!=='current')row.append(warning('Source '+ref.source_state+': '+ref.path));}
      if(!item.sources_complete)row.append(warning('This relationship has additional recorded sources. Open its Sources section to continue.'));
      if(item.source_count===0)row.append(el('p','No source reference is recorded.','muted'));
    }list.append(row);
  }section.append(list);return section;
}
export function modelSummary(model:RelationshipModel):HTMLElement {
  const node=el('div',undefined,'model-summary');node.append(el('p',Object.keys(model.nodes).length+' terms and '+model.order.length+' relationships or detail markers retained in this view.'));
  for(const read of model.reads){const scope=read.scope;node.append(el('p','Read from '+scope.id+' · '+scope.direction+' · '+scope.lifecycles.join(', ')+' · '+scope.fact_kinds.join(', '),'scope'));if(scope.predicate_ids.length)node.append(el('p','Predicates: '+scope.predicate_ids.join(', '),'scope'));
    if(!read.coverage.complete)node.append(warning('Incomplete returned scope: '+(read.coverage.reasons.join(', ')||'not established')+'.'));if(read.coverage.filter_exclusions)node.append(el('p',read.coverage.filter_exclusions+' records excluded by selected filters in this read.'));
    for(const diagnostic of read.diagnostics)node.append(warning(diagnostic.message));
  }
  if(model.local_reasons.length)node.append(warning('Display limit reached. Choose a new focus, narrow filters, or reset before reading the remaining items.'));
  return node;
}
