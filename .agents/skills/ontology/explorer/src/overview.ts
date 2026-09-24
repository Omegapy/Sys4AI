import type {ContextResponse} from './contracts';
import type {Route} from './routes';
import {coverage,el,heading,routeLink} from './feedback';
export function overview(context:ContextResponse,go:(route:Route)=>void):HTMLElement {
  const view=el('section',undefined,'overview'),project=context.project.id;
  view.append(el('p','PROJECT KNOWLEDGE','eyebrow'),heading(context.data.project.name),el('p',context.data.project.purpose,'purpose'));
  if(context.data.local_additions==='absent')view.append(el('p','Imported vocabulary is available. No local additions are recorded in this view.','notice'));
  view.append(el('p','Read the terms, relationships, and recorded evidence used by this project. Start with a question in Search or browse a category.'));
  const starting=el('section');starting.append(heading('Starting points',3));
  if(context.data.starting_points.length){const list=el('ul',undefined,'cards');for(const item of context.data.starting_points){const row=el('li');row.append(routeLink(item.label,{project_id:project,destination:'entry',id:item.id,options:{}},go),el('p',item.definition_excerpt));if(item.excerpt_truncated)row.append(el('span','Preview; open the entry for the full definition.','muted'));list.append(row);}starting.append(list);}
  else starting.append(el('p','No starting entries have been selected. Browse the recorded categories or use Search.'));
  view.append(starting);
  const categories=el('section');categories.append(heading('Browse terms',3));const links=el('ul',undefined,'category-links');
  for(const category of context.data.categories){const item=el('li');item.append(routeLink(category.label,{project_id:project,destination:'terms',options:{category:category.id}},go));links.append(item);}categories.append(links);view.append(categories);
  const map=routeLink('Explore connections',{project_id:project,destination:'map',options:{}},go);map.className='button-link';view.append(map,coverage(context));return view;
}
