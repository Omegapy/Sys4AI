import {isWire, plainObject, responseSemantics, utf8Length} from './contracts';
import type {ContextResponse, ProjectIdentity} from './contracts';

export interface Preferences {theme:'light'|'dark'|'system'; rail:'expanded'|'collapsed'; relationship_view:'list'|'map'; details:'open'|'closed'}
export const DEFAULT_PREFERENCES: Readonly<Preferences> = Object.freeze({theme:'system',rail:'expanded',relationship_view:'list',details:'open'});
export interface PreferenceStorage {getItem(key:string):string|null; setItem(key:string,value:string):void; removeItem(key:string):void}
export function preferenceKey(identity:ProjectIdentity):string|null {
  return isWire('ProjectIdentity',identity) && identity.namespace==='urn:sys4ai:ontology:project:'+identity.id+':'
    ? 'sys4ai-explorer:v1:'+identity.root_scope_id+':'+identity.id+':'+identity.namespace : null;
}
export function validPreferences(v:unknown):v is Preferences {
  return plainObject(v) && Object.keys(v).length===4 && ['theme','rail','relationship_view','details'].every(k=>Object.hasOwn(v,k)) && ['light','dark','system'].includes(String(v.theme)) && ['expanded','collapsed'].includes(String(v.rail)) && ['list','map'].includes(String(v.relationship_view)) && ['open','closed'].includes(String(v.details)) && Object.values(v).every(x=>typeof x==='string');
}
/** Only bind a context already admitted by decodeReadResponse and the regional
 * state ticket. This adapter never discovers identity in storage or a URL. */
export function createPreferences(context:ContextResponse|null, storage?:PreferenceStorage) {
  let key:string|null=null, value:Preferences={...DEFAULT_PREFERENCES}, persistent=false;
  function bind(next:ContextResponse|null):Preferences {
    const nextKey=next && responseSemantics(next)?preferenceKey(next.project):null;
    if (nextKey===key && key!==null) return {...value};
    key=nextKey; value={...DEFAULT_PREFERENCES}; persistent=key!==null && storage!==undefined;
    if (persistent && storage && key) {
      try { const raw=storage.getItem(key); if (raw!==null && utf8Length(raw)<=512) { const parsed:unknown=JSON.parse(raw); if (validPreferences(parsed)) value={...parsed}; } }
      catch { persistent=false; value={...DEFAULT_PREFERENCES}; }
    }
    return {...value};
  }
  bind(context);
  return {
    bind,
    current:()=>({...value}),
    identityKey:()=>key,
    isPersistent:()=>persistent,
    save(next:Preferences):Preferences {
      if (!validPreferences(next)) return {...value};
      value={...next};
      if (persistent && storage && key) { try { storage.setItem(key,JSON.stringify(value)); } catch { persistent=false; } }
      return {...value};
    },
    reset():Preferences {
      value={...DEFAULT_PREFERENCES};
      if (persistent && storage && key) { try { storage.removeItem(key); } catch { persistent=false; } }
      return {...value};
    },
  };
}
