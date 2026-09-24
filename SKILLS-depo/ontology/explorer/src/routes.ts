import {FACT_KINDS, LIFECYCLES, isWire, plainObject, queryText, utf8Length, validUnicode} from './contracts';
import type {CategoryId, Direction, FactKind, Id, Lifecycle, ProjectId} from './contracts';

export type Destination = 'overview' | 'terms' | 'processes' | 'entry' | 'process' | 'map';
export interface RouteOptions {
  q?: string; category?: CategoryId; lifecycles?: Lifecycle[]; fact_kinds?: FactKind[];
  predicates?: Id[]; direction?: Direction; selected?: Id;
}
export interface Route {project_id: ProjectId; destination: Destination; id?: Id; options: RouteOptions}
export type RouteResult = {ok:true; route:Route} | {ok:false; reason:'invalid_route'|'wrong_project'};
export type EncodedRoute = {ok:true; hash:string; omitted:boolean; notice:string|null} | {ok:false; reason:'invalid_route'|'wrong_project'};
const KEYS = ['q','category','lifecycles','fact_kinds','predicates','direction','selected'] as const;
const DESTINATIONS: Destination[] = ['overview','terms','processes','entry','process','map'];
const OMITTED = 'Query and filter state was omitted to keep this local link within its size limit.';
function safeQuery(q:string): boolean { return isWire('Query',q) && validUnicode(q) && !/(?:#|[?&])(?:bootstrap|csrf|session|cursor)=/iu.test(q); }
function options(v:unknown): RouteOptions | null {
  if (!plainObject(v) || Object.keys(v).some(k=>!KEYS.includes(k as typeof KEYS[number]))) return null;
  const out: RouteOptions = {};
  if ('q' in v) { if (typeof v.q !== 'string' || !safeQuery(v.q)) return null; const q=queryText(v.q); if (q !== null) out.q=q; }
  if ('category' in v) { if (!isWire('CategoryId',v.category)) return null; if (v.category !== 'all') out.category=v.category; }
  if ('lifecycles' in v) { if (!isWire('LF',v.lifecycles)) return null; out.lifecycles=LIFECYCLES.filter(x=>v.lifecycles instanceof Array && v.lifecycles.includes(x)); }
  if ('fact_kinds' in v) { if (!isWire('FF',v.fact_kinds)) return null; out.fact_kinds=FACT_KINDS.filter(x=>v.fact_kinds instanceof Array && v.fact_kinds.includes(x)); }
  if ('predicates' in v) { if (!isWire('PredicateIds',v.predicates)) return null; out.predicates=[...v.predicates].sort(); }
  if ('direction' in v) { if (!isWire('Direction',v.direction)) return null; out.direction=v.direction; }
  if ('selected' in v) { if (!isWire('Id',v.selected)) return null; out.selected=v.selected; }
  return out;
}
export function encodeRoute(value:Route, authenticatedProject:ProjectId): EncodedRoute {
  if (!plainObject(value) || Object.keys(value).some(k=>!['project_id','destination','id','options'].includes(k)) || !isWire('ProjectId',value.project_id) || !isWire('ProjectId',authenticatedProject) || !DESTINATIONS.includes(value.destination)) return {ok:false,reason:'invalid_route'};
  if (value.project_id !== authenticatedProject) return {ok:false,reason:'wrong_project'};
  if ((value.destination === 'entry' || value.destination === 'process') && !isWire('Id',value.id) || value.id !== undefined && (value.destination !== 'entry' && value.destination !== 'process' && value.destination !== 'map' || !isWire('Id',value.id))) return {ok:false,reason:'invalid_route'};
  const opts=options(value.options); if (!opts) return {ok:false,reason:'invalid_route'};
  const base='#/p/'+value.project_id+'/'+value.destination+(value.id === undefined?'':'/'+encodeURIComponent(value.id));
  const pairs:string[]=[];
  for (const k of KEYS) { const v=opts[k]; if (v !== undefined) pairs.push(k+'='+encodeURIComponent(Array.isArray(v)?v.join(','):v)); }
  const full=base+(pairs.length?'?'+pairs.join('&'):'');
  return utf8Length(full)<=2048 ? {ok:true,hash:full,omitted:false,notice:null} : {ok:true,hash:base,omitted:true,notice:OMITTED};
}
export function parseRoute(hash:string, authenticatedProject:ProjectId): RouteResult {
  if (typeof hash !== 'string' || !validUnicode(hash) || utf8Length(hash)>2048 || !isWire('ProjectId',authenticatedProject)) return {ok:false,reason:'invalid_route'};
  try {
    const split=hash.split('?'); if (split.length>2) return {ok:false,reason:'invalid_route'};
    const match=/^#\/p\/([a-z0-9][a-z0-9-]{0,79})\/(overview|terms|processes|entry|process|map)(?:\/([^/?#]+))?$/u.exec(split[0]!);
    if (!match) return {ok:false,reason:'invalid_route'};
    if (match[1]!==authenticatedProject) return {ok:false,reason:'wrong_project'};
    const opts:Record<string,unknown>={};
    if (split.length===2) {
      if (!split[1]) return {ok:false,reason:'invalid_route'};
      for (const pair of split[1].split('&')) {
        const at=pair.indexOf('='); if (at<1) return {ok:false,reason:'invalid_route'};
        const k=decodeURIComponent(pair.slice(0,at).replace(/\+/gu,' '));
        const v=decodeURIComponent(pair.slice(at+1).replace(/\+/gu,' '));
        if (Object.hasOwn(opts,k) || !KEYS.includes(k as typeof KEYS[number])) return {ok:false,reason:'invalid_route'};
        opts[k]=['lifecycles','fact_kinds','predicates'].includes(k)?v===''&&k==='predicates'?[]:v.split(','):v;
      }
    }
    const parsed=options(opts); if (!parsed) return {ok:false,reason:'invalid_route'};
    const route:Route={project_id:authenticatedProject,destination:match[2] as Destination,options:parsed};
    if (match[3]!==undefined) { const id=decodeURIComponent(match[3]); if (!isWire('Id',id)) return {ok:false,reason:'invalid_route'}; route.id=id; }
    const check=encodeRoute(route,authenticatedProject); if (!check.ok || check.omitted) return {ok:false,reason:'invalid_route'};
    return {ok:true,route};
  } catch { return {ok:false,reason:'invalid_route'}; }
}
