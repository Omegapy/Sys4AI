"""Closed, memory-only Explorer reads over one byte-verified immutable view.

The service authenticates sessions and supervises absolute deadlines/RSS. Load
this module, source, retrieval and the snapshot/core closure through the same
VerifiedPackage. No optional search, authoring, memory or URL retrieval occurs.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
import math
import re
import time

from ontology_core import canonical_bytes
from ontology_retrieval import query_text, normalize, match
from ontology_explorer_snapshot import thaw
import ontology_explorer_source as sources

OPERATIONS = ("context", "search", "entry", "relationships", "neighborhood", "source")
LIFECYCLES = ("draft", "approved", "deprecated")
FACTS = ("asserted", "derived", "inferred", "external")
SECTIONS = ("header", "label", "definition", "aliases", "scope_note", "examples", "non_examples", "details", "qualifiers", "sources", "process")
FIELDS = ("applicability", "roles", "inputs", "outputs", "related_skills", "related_documents", "prerequisites")
REASONS = ("item_limit", "byte_limit", "time_limit", "visited_limit", "scan_limit", "display_limit", "item_omitted", "field_limit")
DIAGNOSTICS = dict(zip(("source_changed", "source_unavailable", "source_unrecorded", "source_excerpt", "results_incomplete", "item_omitted", "ordering_unavailable", "diagnostics_omitted"), (
    "Source bytes differ from the recorded version.", "Selected source is unavailable.", "No source reference is recorded.",
    "This is a bounded excerpt, not an exact cited section.", "This response does not cover the complete requested view.",
    "Open the indicated entry section to read this omitted item.",
    "An ordered description has not been recorded. These are the documented relationships.",
    "Additional diagnostics are omitted at this response limit.")))
READ_CLOSURE = ("ontology_core", "ontology_modules", "ontology_validate", "ontology_retrieval",
                "ontology_explorer_snapshot", "ontology_explorer_source", "ontology_explorer_read")


class ReaderError(ValueError):
    """A closed error code; wire messages come exclusively from the pinned schema."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(condition, code="invalid_request"):
    if not condition:
        raise ReaderError(code)


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError()
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def validate(value, name, schema):
    """Finite local Draft-2020-12 vocabulary used by the pinned wire schema.

    No remote refs, formats, defaults, coercion, or general schema discovery.
    Full jsonschema validation is independently applied by the acceptance tests.
    """
    def check(v, r, depth=0):
        if depth > 40:
            return False
        if "$ref" in r:
            ref = r["$ref"]
            if not ref.startswith("#/$defs/") or not check(v, schema["$defs"][ref[8:]], depth+1):
                return False
        typ = r.get("type")
        predicates = {"null": lambda x:x is None, "boolean":lambda x:type(x) is bool,
                      "integer":lambda x:type(x) is int, "number":lambda x:type(x) is int or (type(x) is float and math.isfinite(x)),
                      "string":lambda x:type(x) is str, "array":lambda x:type(x) is list, "object":lambda x:type(x) is dict}
        if typ is not None and (typ not in predicates or not predicates[typ](v)):
            return False
        if "const" in r and (type(v) is not type(r["const"]) or v != r["const"]):
            return False
        if "enum" in r and not any(type(v) is type(x) and v == x for x in r["enum"]):
            return False
        if "allOf" in r and not all(check(v,x,depth+1) for x in r["allOf"]): return False
        if "anyOf" in r and not any(check(v,x,depth+1) for x in r["anyOf"]): return False
        if "oneOf" in r and sum(check(v,x,depth+1) for x in r["oneOf"]) != 1: return False
        if "not" in r and check(v,r["not"],depth+1): return False
        if "if" in r:
            branch = "then" if check(v,r["if"],depth+1) else "else"
            if branch in r and not check(v,r[branch],depth+1): return False
        if type(v) is dict:
            props = r.get("properties", {})
            if not set(r.get("required", ())) <= v.keys(): return False
            if r.get("additionalProperties") is False and not v.keys() <= props.keys(): return False
            for k,x in v.items():
                rule = props.get(k, r.get("additionalProperties", {}))
                if isinstance(rule,dict) and not check(x,rule,depth+1): return False
        if type(v) is list:
            if not r.get("minItems",0) <= len(v) <= r.get("maxItems",100000): return False
            if r.get("uniqueItems") and len({compact(x) for x in v}) != len(v): return False
            if "items" in r and not all(check(x,r["items"],depth+1) for x in v): return False
        if type(v) is str:
            try: size = len(v.encode("utf-8"))
            except UnicodeError: return False
            if not r.get("minLength",0) <= len(v) <= r.get("maxLength",2000000): return False
            if size > r.get("x-max-utf8-bytes",8000000): return False
            if "pattern" in r and re.fullmatch(r["pattern"],v) is None: return False
        if type(v) in (int,float):
            if type(v) is float and not math.isfinite(v): return False
            if "minimum" in r and v < r["minimum"]: return False
            if "maximum" in r and v > r["maximum"]: return False
        return True
    return check(value, schema["$defs"][name])


def prefix(value):
    text = value[:240]
    while len(text.encode()) > 960:
        text = text[:-1]
    return text, text != value


def safe_wire_numbers(value):
    """Canonical data may retain wider integers than a JSON/JS wire value."""
    if type(value) is int: return -(2**53-1) <= value <= 2**53-1
    if type(value) is float: return math.isfinite(value) and not (value == 0 and math.copysign(1,value) < 0)
    if isinstance(value, dict): return all(safe_wire_numbers(x) for x in value.values())
    if isinstance(value, (tuple,list)): return all(safe_wire_numbers(x) for x in value)
    return True


def marker(identifier, kind, reason, section):
    return dict(kind="detail_required", id=identifier, item_kind=kind, reason=reason,
                detail=dict(id=identifier, section=section))


def section_key(section, stream, field=None, index=None, part="text", offset=0, observed=None):
    return dict(kind="section", section=section, stream=stream, field=field, item_index=index,
                part=part, offset=offset, observed_sha256=observed)


class Reader:
    error_type = ReaderError

    def __init__(self, store, *, service_instance, build_id, schema_sha256, service_secret,
                 started_monotonic=None, clock=time.monotonic):
        self.store, self.schema, self.clock = store, store.schema, clock
        need(validate(service_instance,"InstanceId",self.schema))
        need(validate(build_id,"Digest",self.schema) and validate(schema_sha256,"Digest",self.schema))
        need(type(service_secret) is bytes and len(service_secret) == 32)
        need(schema_sha256 == sha(store.package.member_bytes["schema"]), "package_incomplete")
        need(store.current is None, "package_incomplete")
        self.instance, self.build_id, self.schema_sha256 = service_instance, build_id, schema_sha256
        self.secret = service_secret
        self.started = clock() if started_monotonic is None else started_monotonic
        self._deadline = float("inf")
        self._request_started = clock()
        self.errors = {r["properties"]["code"]["const"]:({k:v["const"] for k,v in r["properties"].items()},r["x-http-status"])
                       for r in self.schema["$defs"]["Error"]["oneOf"]}
        store.validate_view = self.validate_view

    def now(self):
        return max(0, int((self.clock()-self.started)*1000))

    def tick(self):
        need(self.clock() < self._deadline, "deadline_exceeded")

    def error_response(self, code, *, operation=None, request_id=None, limits=None):
        error, http = self.errors.get(code, self.errors["internal_error"])
        if operation not in OPERATIONS: operation = None
        if not validate(request_id,"RequestId",self.schema): request_id = None
        bound = dict(items=1,bytes=1024,visited_nodes=1,seconds=1) if limits is None else limits
        result = dict(schema_version=1, request_id=request_id, operation=operation, code_epoch=None,
                      service_instance=None,session_scope=None,project=None,snapshot=None,status="error",scope={},data=None,
                      page=dict(returned=0,next_cursor=None,has_more=None,total=None),limits=bound,
                      coverage=dict(complete=False,reasons=[],filter_exclusions=None,visited_nodes=None,returned_nodes=None,returned_edges=None),
                      diagnostics=[],error=dict(error))
        need(len(compact(result)) <= 1024 and validate(result,"ErrorResponse",self.schema), "internal_error")
        return http,result

    def policy(self, view):
        defs = self.schema["$defs"]
        configured = (view.presentation or {}).get("limits", {})
        p = {k:configured.get(k,v["default"]) for k,v in defs["ConfiguredLimits"]["properties"].items()}
        p.update({k:v["const"] for k,v in defs["EffectivePolicy"]["properties"].items() if "const" in v})
        canonical = view.project.config["retrieval"]
        p["page_items"] = min(p["page_items"], canonical["max_limit"],100)
        p["response_bytes"] = min(p["response_bytes"], canonical["max_context_bytes"],32000)
        p["visited_nodes"] = min(100,canonical["max_limit"])
        p["default_page_items"] = min(p["page_items"],canonical["default_limit"])
        p["initial_nodes"] = min(p["initial_nodes"],p["display_nodes"],p["visited_nodes"],p["page_items"])
        p["initial_edges"] = min(p["initial_edges"],p["display_edges"],p["page_items"])
        p["cursor_seconds"] = min(p["cursor_seconds"],p["session_seconds"])
        for k,v in self.store.limits.items(): p[k] = min(p[k],v)
        return p

    def categories(self, view):
        configured = (view.presentation or {}).get("categories", ())
        records = view.project.records
        groups, omitted = [{"id":"all","label":"All","type_ids":[],"entry_ids":[]}],False
        if configured:
            choices = [thaw(x) for x in configured]
        else:
            used = {t for r in records if r["kind"] != "binding" for t in r["@type"]}
            eligible = [r for r in records if r["kind"] == "concept" and r["@id"] in used]
            choices, seen = [],set()
            for r in sorted(eligible,key=lambda r:r["@id"]):
                label = r["label"]
                if not 1 <= len(label) <= 80 or any(ord(c)<32 or ord(c)==127 for c in label):
                    omitted = True; continue
                cid = "type-" + sha(r["@id"].encode())[:32]
                need(cid not in seen,"presentation_invalid");seen.add(cid)
                if len(choices) >= 31: omitted = True;continue
                choices.append(dict(id=cid,label=label,type_ids=[r["@id"]],entry_ids=[]))
        for c in choices:
            if any(r["kind"] != "binding" and self.in_category(r,c) for r in records): groups.append(c)
        return groups,omitted

    @staticmethod
    def in_category(record, category):
        return category["id"] == "all" or record["@id"] in category["entry_ids"] or bool(set(record["@type"]) & set(category["type_ids"]))

    def category_ids(self, record, groups):
        return [c["id"] for c in groups if self.in_category(record,c)]

    def validate_view(self, view):
        try:
            self._validate_view(view)
        except (ReaderError,sources.SourceError) as exc:
            code = exc.code if exc.code in ("snapshot_changed","deadline_exceeded","resource_limit") else "presentation_invalid"
            raise self.store.error_type(code) from None

    def _validate_view(self, view):
        cfg, by = view.presentation or {},view.project.by_id
        types = {t for r in view.project.records for t in r["@type"]}
        def unique(items,key): need(len({x[key] for x in items}) == len(items),"presentation_invalid")
        for group,key in (("categories","id"),("predicate_labels","predicate_id"),("process_views","id")):
            unique(cfg.get(group,()),key)
        for ident in cfg.get("starting_ids",()): need(ident in by and by[ident]["kind"] not in ("binding","relation"),"presentation_invalid")
        for category in cfg.get("categories",()):
            need(len(category["type_ids"])+len(category["entry_ids"]) <=32,"presentation_invalid")
            need(all(x in types for x in category["type_ids"]) and all(x in by for x in category["entry_ids"]),"presentation_invalid")
        for label in cfg.get("predicate_labels",()): need(label["predicate_id"] in by and by[label["predicate_id"]]["kind"]=="predicate","presentation_invalid")
        cache = {}
        for mapping in cfg.get("process_views",()):
            self.tick()
            ident = mapping["id"]
            need(ident in by and by[ident]["kind"] not in ("binding","relation"),"presentation_invalid")
            direct = {ident} | {r["@id"] for r in view.project.records if r["kind"]=="binding" and r["entity"]==ident}
            allowed = set(direct)
            for selectors in mapping["field_relations"].values():
                for selector in selectors:
                    pred = selector["predicate_id"]
                    need(pred in by and by[pred]["kind"]=="predicate","presentation_invalid")
                    for r in self.selected_relations(view,ident,selector): allowed.update((r["@id"],r["subject"],r["object"]))
            for selectors in mapping["field_sources"].values():
                for selector in selectors:
                    need(selector["owner_id"] in allowed,"presentation_invalid")
                    ref = sources.resolve(view,selector["owner_id"],selector["reference_id"])
                    raw = self.source_bytes(view,ref,cache)
                    if raw is not None and ref["source_state"]=="current" and selector["extract_locator"] is not None:
                        need(sources.contained(sources.extract(raw,ref["locator"]),sources.extract(raw,selector["extract_locator"])),"presentation_invalid")
            ordered = mapping["ordered_source"]
            if ordered is not None:
                need(ordered["owner_id"] in direct,"presentation_invalid")
                need([x["number"] for x in ordered["steps"]] == list(range(1,len(ordered["steps"])+1)),"presentation_invalid")
                need(len({x["locator"] for x in ordered["steps"]})==len(ordered["steps"]),"presentation_invalid")
                ref = sources.resolve(view,ordered["owner_id"],ordered["reference_id"])
                raw = self.source_bytes(view,ref,cache)
                if raw is not None and ref["source_state"]=="current":
                    parent = sources.extract(raw,ref["locator"])
                    last_end = -1
                    for step in ordered["steps"]:
                        child = sources.extract(raw,step["locator"])
                        need(sources.contained(parent,child) and child.span is not None and child.span[0]>=last_end,"presentation_invalid")
                        last_end = child.span[1]
        self.categories(view)

    def source_bytes(self,view,ref,cache):
        self.tick()
        if ref["path"] not in cache: cache[ref["path"]]=sources.candidate_bytes(view,ref)
        return cache[ref["path"]]

    @staticmethod
    def selected_relations(view,ident,selector):
        index = view.outgoing if selector["direction"]=="outgoing" else view.incoming
        return [view.project.by_id[r] for r in sorted(index.get(ident,())) if view.project.by_id[r]["predicate"]==selector["predicate_id"]]

    def module_version(self,view,record):
        return next((m.get("version") for m in view.project.modules if m.get("id",m.get("module_id"))==record["module"]),None)

    def summary(self,view,record,groups,reason="browse",query=None):
        excerpt,truncated = prefix(record["definition"])
        alias,alias_truncated = None,False
        if reason=="alias": alias,alias_truncated = prefix(next(x for x in record.get("aliases",()) if normalize(x)==normalize(query)))
        return dict(id=record["@id"],label=record["label"],category_ids=self.category_ids(record,groups),
                    definition_excerpt=excerpt,excerpt_truncated=truncated,module_id=record["module"],module_version=self.module_version(view,record),
                    lifecycle=record["lifecycle"],fact_kind=record["fact_kind"],match_reason=reason,matched_alias=alias,
                    matched_alias_truncated=alias_truncated,source_state=sources.freshness(sources.references(view,record["@id"])))

    def node(self,record,groups):
        return dict(id=record["@id"],label=record["label"],kind=record["kind"],category_ids=self.category_ids(record,groups),lifecycle=record["lifecycle"],fact_kind=record["fact_kind"])

    def scope(self,operation,params,view,policy):
        result = {k:v for k,v in params.items() if k!="cursor"}
        if operation=="search":
            q = query_text(params["query"]) if params["query"].strip() else None
            result.update(query=q,normalized_query=normalize(q) if q is not None else None,category=None if params["category"] in (None,"all") else params["category"])
            need(params["sort"] == ("label" if q is None else "relevance"))
            need(result["category"] is None or result["category"] in {c["id"] for c in self.categories(view)[0]})
        if operation in ("search","relationships","neighborhood"):
            result["lifecycles"] = sorted(params["lifecycles"],key=LIFECYCLES.index)
            result["fact_kinds"] = sorted(params["fact_kinds"],key=FACTS.index)
            need(params["limit"] <= policy["page_items"])
        if operation in ("relationships","neighborhood"):
            result["predicate_ids"] = sorted(params["predicate_ids"])
            need(all(p in view.project.by_id and view.project.by_id[p]["kind"]=="predicate" for p in result["predicate_ids"]))
        if operation=="neighborhood": need(params["node_limit"]<=min(policy["display_nodes"],policy["visited_nodes"]))
        return result

    def _cursor_base(self,view,operation,scope,policy,session,sort):
        return dict(v=1,service_instance=self.instance,session_scope=session,project_id=view.project.project_id,root_scope=view.root_scope_id,
                    snapshot=view.snapshot_id,operation=operation,scope_sha256=sha(compact(dict(code_epoch=view.code_epoch,
                    effective_policy_sha256=sha(canonical_bytes(policy)),operation=operation,scope=scope))),sort=sort)

    def decode_cursor(self,token,base,policy,session_expires):
        if token is None: return None
        need(type(token) is str and len(token)<=2048 and re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",token),"cursor_invalid")
        try:
            payload,mac = token.split(".")
            raw = base64.urlsafe_b64decode(payload+"="*((-len(payload))%4))
            sig = base64.urlsafe_b64decode(mac+"="*((-len(mac))%4))
            need(self.b64(raw)==payload and self.b64(sig)==mac,"cursor_invalid")
            need(hmac.compare_digest(sig,hmac.digest(self.secret,raw,"sha256")),"cursor_invalid")
            data = strict_json(raw)
            need(validate(data,"CursorPayload",self.schema) and compact(data)==raw,"cursor_invalid")
        except (ValueError,TypeError,UnicodeError) as exc:
            if isinstance(exc,ReaderError): raise
            raise ReaderError("cursor_invalid") from None
        need(all(data[k]==v for k,v in base.items()),"cursor_scope_changed")
        now=self.now()
        need(data["issued"]<=now and data["expires"]>data["issued"] and data["expires"]-data["issued"]<=1000*policy["cursor_seconds"] and data["expires"]<=session_expires,"cursor_invalid")
        need(now<data["expires"],"cursor_expired")
        return data["last_key"]

    @staticmethod
    def b64(raw): return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    def encode_cursor(self,base,key,policy,session_expires,issued):
        expires=min(issued+policy["cursor_seconds"]*1000,session_expires)
        need(issued<expires,"session_expired")
        raw=compact(dict(base,last_key=key,issued=issued,expires=expires))
        token=self.b64(raw)+"."+self.b64(hmac.digest(self.secret,raw,"sha256"))
        need(len(token)<=2048,"resource_limit")
        return token

    def envelope(self,view,operation,request,session,scope,policy):
        return dict(schema_version=1,request_id=request["request_id"],operation=operation,code_epoch=view.code_epoch,
                    service_instance=self.instance,session_scope=session,project=dict(id=view.project.project_id,namespace=view.project.namespace,root_scope_id=view.root_scope_id),
                    snapshot=view.snapshot_id,status="ok",scope=scope,data=None,page=dict(returned=0,next_cursor=None,has_more=False,total=None),
                    limits=dict(items=scope.get("limit",policy["page_items"]),bytes=policy["response_bytes"],visited_nodes=scope.get("node_limit",policy["visited_nodes"]),seconds=policy["request_seconds"]),
                    coverage=dict(complete=True,reasons=[],filter_exclusions=None,visited_nodes=None,returned_nodes=None,returned_edges=None),diagnostics=[],error=None)

    @staticmethod
    def add_diagnostic(response,code,ident=None):
        item=dict(code=code,message=DIAGNOSTICS[code],record_id=ident)
        if item in response["diagnostics"]: return
        if len(response["diagnostics"])<4: response["diagnostics"].append(item)
        else: response["diagnostics"][-1]=dict(code="diagnostics_omitted",message=DIAGNOSTICS["diagnostics_omitted"],record_id=None)

    def finish(self,response):
        reasons=response["coverage"]["reasons"]
        response["coverage"]["reasons"]=[r for r in REASONS if r in reasons]
        if not response["coverage"]["complete"]:
            self.add_diagnostic(response,"results_incomplete")
            if response["status"]!="source_changed": response["status"]="incomplete"
        elif response["page"]["returned"]==0 and response["page"]["has_more"] is False:
            if response["status"] not in ("source_changed","ambiguous"): response["status"]="empty"
        need(len(compact(response))<=response["limits"]["bytes"],"resource_limit")
        need(validate(response,response["operation"].title()+"Response",self.schema),"internal_error")
        self.tick()
        return response

    def read(self,operation,request,*,session_scope,session_expires_ms,deadline=None):
        """Authenticated fixed dispatch. Caller serializes jobs in its one worker."""
        need(operation in OPERATIONS,"endpoint_unavailable")
        need(validate(session_scope,"SessionScope",self.schema) and type(session_expires_ms) is int,"session_invalid")
        need(self.now()<session_expires_ms,"session_expired")
        try:
            raw=compact(request)
            need(len(raw)<=16384,"request_too_large")
            need(validate(request,operation.title()+"Request",self.schema))
            need(request["code_epoch"]==self.store.package.code_epoch,"package_changed")
            self._request_started=self.clock()
            self._deadline=min(deadline if deadline is not None else float("inf"),self._request_started+self.store.limits["request_seconds"])
            if operation=="source":
                # The selected tuple belongs to the displayed immutable snapshot;
                # source-only observations deliberately do not lease a new view.
                view=next((v for v in (self.store.current,self.store.retiring) if v is not None and v.snapshot_id==request["snapshot"]),None)
                need(view is not None,"snapshot_changed")
                return self._read(view,operation,request,session_scope,session_expires_ms,len(raw))
            expected=request["snapshot"]
            if operation=="context" and request["params"]["refresh"]: expected=None
            with self.store.lease(expected_snapshot=expected,deadline=self._deadline) as view:
                return self._read(view,operation,request,session_scope,session_expires_ms,len(raw))
        except self.store.error_type as exc:
            raise ReaderError(exc.code) from None
        except sources.SourceError as exc:
            raise ReaderError(exc.code) from None
        except (UnicodeError,RecursionError,OverflowError):
            raise ReaderError("invalid_request") from None

    def _read(self,view,operation,request,session,session_expires,size):
        policy=self.policy(view);self._deadline=min(self._deadline,self._request_started+policy["request_seconds"])
        need(size<=policy["request_bytes"],"request_too_large")
        scope=self.scope(operation,request["params"],view,policy)
        response=self.envelope(view,operation,request,session,scope,policy)
        if operation=="context": return self.context(view,response,policy)
        sort=scope["sort"] if operation=="search" else "relation_id" if operation in ("relationships","neighborhood") else "source_offset" if operation=="source" else "section_order"
        base=self._cursor_base(view,operation,scope,policy,session,sort)
        last=self.decode_cursor(request["params"]["cursor"],base,policy,session_expires)
        token=lambda key:self.encode_cursor(base,key,policy,session_expires,self.now())
        if operation=="search": return self.search(view,response,policy,last,token)
        if operation in ("relationships","neighborhood"): return self.graph(view,response,policy,last,token)
        if operation=="entry": return self.entry(view,response,policy,last,token)
        return self.source(view,response,policy,last,token)

    def context(self,view,response,policy):
        groups,omitted=self.categories(view)
        project=view.project.config["project"]
        starting=[self.summary(view,view.project.by_id[i],groups) for i in (view.presentation or {}).get("starting_ids",())]
        need(all(validate(x,"Summary",self.schema) for x in starting),"resource_limit")
        response["data"]=dict(project=dict(id=view.project.project_id,name=project["name"],purpose=project["purpose"],namespace=view.project.namespace),
            root_scope_id=view.root_scope_id,local_additions="present" if any(r["kind"]!="binding" and r["module"]=="project" for r in view.project.records) else "absent",
            service=dict(identity="sys4ai-project-knowledge-explorer",instance=self.instance,code_epoch=view.code_epoch,build_id=self.build_id,schema_sha256=self.schema_sha256),
            categories=[dict(id=c["id"],label=c["label"]) for c in groups],starting_points=starting,process_ids=[x["id"] for x in (view.presentation or {}).get("process_views",())],
            filters=dict(lifecycles=list(LIFECYCLES),fact_kinds=list(FACTS)),capabilities=dict(search=True,entry=True,relationships=True,neighborhood=True,source=True,processes=True,authoring=False,semantic_search=False),
            resource_policy=policy,effective_policy_sha256=sha(canonical_bytes(policy)))
        response["page"]["returned"]=1
        if omitted: response["coverage"].update(complete=False,reasons=["field_limit"])
        need(validate(response["data"],"ContextData",self.schema),"resource_limit")
        return self.finish(response)

    def page_response(self,template,data,returned,more,key,token,reasons=(),*,total=None,nodes=None,edges=None):
        r=copy.deepcopy(template)
        r["data"]=data
        r["page"].update(returned=returned,has_more=more,next_cursor=token(key) if more and key is not None else None,total=total)
        all_reasons=set(r["coverage"]["reasons"])|set(reasons)
        if more:
            # Size the actual legal stopping envelope now. A prefix shorter
            # than its item ceiling needs its byte/visited stopping reason too;
            # adding that metadata after packing can invalidate a tight page.
            if returned >= r["limits"]["items"]: all_reasons.add("item_limit")
            elif "visited_limit" not in all_reasons: all_reasons.add("byte_limit")
        r["coverage"].update(complete=not all_reasons,reasons=[x for x in REASONS if x in all_reasons])
        if nodes is not None: r["coverage"].update(visited_nodes=nodes,returned_nodes=nodes,returned_edges=edges)
        if "item_omitted" in all_reasons: self.add_diagnostic(r,"item_omitted")
        return self.finish(r)

    def fits(self,*args,**kwargs):
        try: return self.page_response(*args,**kwargs)
        except ReaderError as exc:
            if exc.code!="resource_limit": raise
            return None

    def stop_page(self, response, reason):
        response["coverage"]["reasons"].append(reason)
        try:
            return self.finish(response)
        except ReaderError as exc:
            if exc.code != "resource_limit" or response["page"]["total"] is None:
                raise
            # A scoped total is optional; identity, items, coverage and the real
            # cursor are not. Reclaim only this count when a final graph stop
            # reason needs a few additional envelope bytes.
            response["page"]["total"] = None
            return self.finish(response)

    def search(self,view,response,policy,last,token):
        scope=response["scope"];groups,_=self.categories(view)
        category=next((c for c in groups if c["id"]==scope["category"]),None)
        rows,excluded=[],0
        need(len(view.project.records)<=policy["scan_candidates"],"resource_limit")
        for record in view.project.records:
            self.tick()
            if record["kind"]=="binding": continue
            if record["lifecycle"] not in scope["lifecycles"] or record["fact_kind"] not in scope["fact_kinds"] or (category and not self.in_category(record,category)):
                excluded+=1;continue
            if scope["query"] is None:
                key=dict(kind="label",label_sha256=sha(normalize(record["label"]).encode()),id=record["@id"])
                rows.append(((normalize(record["label"]),record["@id"]),record,"browse",key))
            else:
                reason=match(record,scope["query"])
                if reason:
                    need(reason[1]<=100000,"resource_limit")
                    rows.append(((reason[0],-reason[1],record["@id"]),record,reason[2],dict(kind="rank",**{"class":reason[0]},score=reason[1],id=record["@id"])))
        rows.sort(key=lambda x:x[0]);response["coverage"]["filter_exclusions"]=excluded
        if scope["query"] is not None and len(rows)>1 and rows[0][0][0] in (1,2) and rows[0][0][:2]==rows[1][0][:2]: response["status"]="ambiguous"
        start=0
        if last is not None:
            positions=[i for i,row in enumerate(rows) if row[3]==last]
            need(len(positions)==1,"cursor_invalid");start=positions[0]+1
        total=dict(value=len(rows),scope="filtered_query",exact=True)
        items,reasons,best=[],set(),None
        for index in range(start,len(rows)):
            self.tick();_,record,reason,key=rows[index];more=index+1<len(rows)
            entry=self.summary(view,record,groups,reason,scope["query"])
            item=dict(kind="entry",entry=entry)
            fixed=not validate(entry,"Summary",self.schema)
            item_reasons=set()
            if fixed:
                section="label" if not validate(record["label"],"Label",self.schema) else "details"
                item=marker(record["@id"],"entry","field_limit",section);item_reasons={"field_limit","item_omitted"}
            candidate=self.fits(response,dict(items=items+[item]),len(items)+1,more,key,token,reasons|item_reasons,total=total)
            if candidate is None and not fixed:
                empty=self.fits(response,dict(items=[item]),1,more,key,token,(),total=total)
                if empty is None:
                    item=marker(record["@id"],"entry","byte_limit","header");item_reasons={"byte_limit","item_omitted"}
                    candidate=self.fits(response,dict(items=items+[item]),len(items)+1,more,key,token,reasons|item_reasons,total=total)
            if candidate is None:
                need(best is not None,"resource_limit")
                return self.stop_page(best,"byte_limit")
            items.append(item);reasons|=item_reasons;best=candidate
            if len(items)==scope["limit"]: return best
        return best or self.page_response(response,dict(items=[]),0,False,None,token,total=total)

    def graph(self,view,response,policy,last,token):
        scope=response["scope"];by=view.project.by_id;ident=scope["id"]
        need(ident in by,"identity_unavailable")
        groups,_=self.categories(view)
        ids=set()
        if scope["direction"] in ("outgoing","both"): ids.update(view.outgoing.get(ident,()))
        if scope["direction"] in ("incoming","both"): ids.update(view.incoming.get(ident,()))
        need(len(ids)<=policy["incident_candidates"],"resource_limit")
        rows=[]
        for rid in sorted(ids):
            self.tick();r=by[rid]
            if r["lifecycle"] in scope["lifecycles"] and r["fact_kind"] in scope["fact_kinds"] and (not scope["predicate_ids"] or r["predicate"] in scope["predicate_ids"]): rows.append(r)
        response["coverage"]["filter_exclusions"]=len(ids)-len(rows)
        start=0
        if last is not None:
            positions=[i for i,r in enumerate(rows) if last==dict(kind="relation",id=r["@id"])]
            need(len(positions)==1,"cursor_invalid");start=positions[0]+1
        cap=scope.get("node_limit",policy["visited_nodes"])
        focus={}
        if response["operation"]=="neighborhood":
            node=self.node(by[ident],groups)
            if validate(node,"Node",self.schema): focus[ident]=node
        def data(items,nodes):
            return {("focus" if response["operation"]=="neighborhood" else "id"):ident,"direction":scope["direction"],"nodes":list(nodes.values()),"items":items}
        total=dict(value=len(rows),scope="incident_relations",exact=True)
        items,nodes,reasons,best=[],dict(focus),set(),None
        for index in range(start,len(rows)):
            self.tick();record=rows[index];key=dict(kind="relation",id=record["@id"]);more=index+1<len(rows)
            refs=sources.references(view,record["@id"])
            edge=dict(id=record["@id"],subject=record["subject"],predicate=record["predicate"],object=record["object"],predicate_label=by[record["predicate"]]["label"],
                      lifecycle=record["lifecycle"],fact_kind=record["fact_kind"],qualifiers=thaw(record.get("qualifiers")),source_references=refs[:policy["page_items"]],source_count=len(refs),sources_complete=len(refs)<=policy["page_items"])
            endpoints={i:self.node(by[i],groups) for i in (record["subject"],record["object"])}
            combined={**nodes,**endpoints};empty_nodes={**focus,**endpoints};item=dict(kind="edge",edge=edge);item_reasons=set()
            unsafe_number=not safe_wire_numbers(edge["qualifiers"])
            field_bad=unsafe_number or not validate(edge,"Edge",self.schema) or any(not validate(x,"Node",self.schema) for x in endpoints.values())
            if field_bad or len(empty_nodes)>cap:
                reason="field_limit" if field_bad else "visited_limit"
                item=marker(record["@id"],"relation",reason,"qualifiers" if unsafe_number else "details");combined=dict(nodes);item_reasons={reason,"item_omitted"}
            candidate=None if len(combined)>cap else self.fits(response,data(items+[item],combined),len(items)+1,more,key,token,reasons|item_reasons,total=total,nodes=len(combined),edges=sum(x["kind"]=="edge" for x in items+[item]))
            if candidate is None and item["kind"]=="edge":
                empty=self.fits(response,data([item],empty_nodes),1,more,key,token,(),total=total,nodes=len(empty_nodes),edges=1)
                if empty is None:
                    item=marker(record["@id"],"relation","byte_limit","qualifiers" if "qualifiers" in record else "details")
                    combined=dict(nodes);item_reasons={"byte_limit","item_omitted"}
                    candidate=self.fits(response,data(items+[item],combined),len(items)+1,more,key,token,reasons|item_reasons,total=total,nodes=len(combined),edges=sum(x["kind"]=="edge" for x in items))
            if candidate is None:
                need(best is not None,"resource_limit")
                return self.stop_page(best,"visited_limit" if len(combined)>cap else "byte_limit")
            items.append(item);nodes=combined;reasons|=item_reasons;best=candidate
            if len(items)==scope["limit"]: return best
        return best or self.page_response(response,data([],focus),0,False,None,token,total=total,nodes=len(focus),edges=0)

    def available_sections(self,view,record):
        available={"header","label","definition","details"}
        available.update(s for s in ("aliases","scope_note","examples","non_examples","qualifiers") if s in record)
        if sources.references(view,record["@id"]): available.add("sources")
        if any(x["id"]==record["@id"] for x in (view.presentation or {}).get("process_views",())): available.add("process")
        return [x for x in SECTIONS if x in available]

    def entry(self,view,response,policy,last,token):
        scope=response["scope"];ident=scope["id"];section=scope["section"]
        need(ident in view.project.by_id,"identity_unavailable")
        record=view.project.by_id[ident]
        data=dict(id=ident,section=section,header=None,chunks=[],references=[],process=None,process_items=[])
        if section=="header":
            need(last is None,"cursor_invalid")
            label,shortened=prefix(record["label"]);definition,shortdef=prefix(record["definition"])
            data["header"]=dict(id=ident,label=label,label_truncated=shortened,definition_excerpt=definition,excerpt_truncated=shortdef,
                kind=record["kind"],lifecycle=record["lifecycle"],fact_kind=record["fact_kind"],module_id=record["module"],module_version=self.module_version(view,record),
                available_sections=self.available_sections(view,record),source_state=sources.freshness(sources.references(view,ident)))
            need(validate(data["header"],"Header",self.schema),"resource_limit")
            return self.page_response(response,data,1,False,None,token)
        if section=="sources":
            refs=sources.references(view,ident);start=0
            if last is not None:
                need(last==section_key("sources","source_references",index=last.get("item_index"),part="references") and type(last["item_index"]) is int and last["item_index"]<len(refs),"cursor_invalid")
                start=last["item_index"]+1
            best=None
            for i in range(start,len(refs)):
                self.tick();candidate=copy.deepcopy(data);candidate["references"]=data["references"]+[refs[i]]
                result=self.fits(response,candidate,len(candidate["references"]),i+1<len(refs),section_key("sources","source_references",index=i,part="references"),token,total=dict(value=len(refs),scope="section_items",exact=True))
                if result is None:
                    need(best is not None,"resource_limit");return self.stop_page(best,"byte_limit")
                data=candidate;best=result
                if len(data["references"])==policy["page_items"]:return best
            return best or self.page_response(response,data,0,False,None,token,total=dict(value=len(refs),scope="section_items",exact=True))
        if section=="process":
            data["process"],streams=self.process_streams(view,record,response)
            return self.stream_page(response,data,"process_items",streams,policy,last,token)
        streams=[]
        if section in record or section=="details":
            value=thaw(record) if section=="details" else thaw(record[section])
            if section=="details": value.update(module_version=self.module_version(view,record),canonical_location=view.project.locations.get(ident))
            if type(value) is str:
                values=[(None,value,"plain")]
            elif type(value) is list and value and all(type(x) is str and x for x in value):
                values=[(i,x,"plain") for i,x in enumerate(value)]
            else: values=[(None,canonical_bytes(value).decode(),"canonical_json")]
            for index,text,encoding in values:
                if text:
                    key=section_key(section,"text",field=section,index=index)
                    streams.append(dict(key=key,text=text,encoding=encoding,kind="chunk"))
        return self.stream_page(response,data,"chunks",streams,policy,last,token)

    def stream_page(self,response,data,array,streams,policy,last,token):
        # Each stream has a stable key; an offset advances only after a nonempty
        # exact Unicode substring or a complete support-ID prefix is serialized.
        start,offset=0,0
        if last is not None:
            matches=[i for i,s in enumerate(streams) if {**s["key"],"offset":last["offset"]}==last]
            need(len(matches)==1,"cursor_invalid");start=matches[0];offset=last["offset"]
            value=streams[start].get("text",streams[start].get("values"))
            length=len(value.encode()) if type(value) is str else len(value)
            need(0<=offset<=length,"cursor_invalid")
            if offset==length: start+=1;offset=0
        best=None;count=0;source_bytes_returned=0
        for index in range(start,len(streams)):
            stream=streams[index];value=stream.get("text",stream.get("values"));is_text=type(value) is str
            if is_text:
                try: remaining=value.encode()[offset:].decode()
                except UnicodeError: raise ReaderError("cursor_invalid") from None
            else: remaining=value[offset:]
            first=True
            while remaining or (first and not is_text and not value):
                self.tick();first=False
                maximum=min(len(remaining),policy["source_excerpt_bytes"] if is_text else policy["page_items"])
                if is_text:
                    byte_cap = policy["source_excerpt_bytes"]
                    if response["operation"] == "source": byte_cap -= source_bytes_returned
                    while len(remaining[:maximum].encode()) > byte_cap: maximum -= 1
                    if maximum == 0:
                        need(best is not None,"resource_limit")
                        return self.stop_page(best,"byte_limit")
                low,high=1 if remaining else 0,maximum;chosen=None
                # First try the complete maximum: finishing a stream may remove
                # its cursor, so fit is not monotonic at the final substring.
                try_maximum = True
                while low<=high:
                    take = maximum if try_maximum else (low+high)//2
                    try_maximum = False
                    part=remaining[:take]
                    after=offset+(len(part.encode()) if is_text else len(part))
                    more_field=take<len(remaining);more=more_field or index+1<len(streams)
                    key={**stream["key"],"offset":after}
                    if stream["kind"]=="chunk":
                        item=dict(field=key["field"],item_index=key["item_index"],offset=offset,text=part,encoding=stream["encoding"],more_in_field=more_field)
                    elif stream["kind"]=="step":
                        item=dict(kind="ordered_step",ordinal=key["item_index"],reference_id=stream["reference_id"],offset=offset,text=part,more_in_step=more_field)
                    else:
                        item=dict(kind="field",item_index=key["item_index"],part=key["part"],name=key["field"],relation_ids=part if key["part"]=="relations" else [],
                                  reference_ids=part if key["part"]=="references" else [],text=part if is_text else None,offset=offset,more_in_field=more_field)
                    candidate=copy.deepcopy(data);candidate[array]=data[array]+[item]
                    result=self.fits(response,candidate,count+1,more,key,token)
                    if result is not None: chosen=(take,after,candidate,result);low=take+1
                    else: high=take-1
                if chosen is None:
                    need(best is not None,"resource_limit");return self.stop_page(best,"byte_limit")
                take,offset,data,best=chosen;count+=1
                if is_text: source_bytes_returned += len(remaining[:take].encode())
                remaining=remaining[take:]
                if count==policy["page_items"]:return best
                if not remaining:break
            offset=0
        return best or self.page_response(response,data,0,False,None,token)

    def source(self,view,response,policy,last,token):
        scope=response["scope"];ref=sources.resolve(view,scope["owner_id"],scope["reference_id"])
        current,observation,extraction=sources.observe(self.store,view,ref,deadline=self._deadline)
        if last is not None: need(last["observed_sha256"]==observation["sha256"],"source_observation_changed")
        data=dict(reference=current,observation=observation,extraction=extraction.wire(),chunks=[])
        if observation["state"]=="stale":
            response["status"]="source_changed";self.add_diagnostic(response,"source_changed",scope["owner_id"])
        if not extraction.supported:self.add_diagnostic(response,"source_excerpt",scope["owner_id"])
        streams=[]
        if extraction.text:
            streams=[dict(key=section_key("sources","text",field="source",observed=observation["sha256"]),text=extraction.text,encoding=extraction.encoding,kind="chunk")]
        return self.stream_page(response,data,"chunks",streams,policy,last,token)

    def process_streams(self,view,record,response):
        mapping=next((p for p in (view.presentation or {}).get("process_views",()) if p["id"]==record["@id"]),None)
        if mapping is None:return dict(order_state="missing",ordered_reference_id=None,observed_source_sha256=None),[]
        streams=[];cache={}
        def field(name,index,part,value,observed=None):
            if part=="text" and not value:return
            streams.append(dict(key=section_key("process","process_fields",field=name,index=index,part=part,observed=observed),
                                kind="field",**({"text":value} if part=="text" else {"values":value})))
        field("purpose",0,"text",record["definition"])
        if "scope_note" in record:field("scope",0,"text",record["scope_note"])
        for name in FIELDS:
            index=0;seen=set()
            for selector in mapping["field_relations"].get(name,()):
                values=[r["@id"] for r in self.selected_relations(view,record["@id"],selector) if r["@id"] not in seen]
                seen.update(values);field(name,index,"relations",values);index+=1
            seen=set()
            for selector in mapping["field_sources"].get(name,()):
                identity=(selector["owner_id"],selector["reference_id"],selector["extract_locator"])
                if identity in seen:continue
                seen.add(identity)
                ref=sources.resolve(view,selector["owner_id"],selector["reference_id"])
                field(name,index,"references",[ref["reference_id"]])
                raw=self.source_bytes(view,ref,cache)
                if raw is None:self.add_diagnostic(response,"source_unavailable",ref["owner_id"])
                elif ref["source_state"]=="stale":self.add_diagnostic(response,"source_changed",ref["owner_id"])
                else:
                    extraction=sources.extract(raw,selector["extract_locator"] or ref["locator"])
                    if extraction.supported:field(name,index,"text",extraction.text,ref["observed_sha256"])
                    else:self.add_diagnostic(response,"source_excerpt",ref["owner_id"])
                index+=1
        ordered=mapping["ordered_source"]
        meta=dict(order_state="missing",ordered_reference_id=None,observed_source_sha256=None)
        if ordered is not None:
            ref=sources.resolve(view,ordered["owner_id"],ordered["reference_id"])
            meta.update(ordered_reference_id=ref["reference_id"],observed_source_sha256=ref["observed_sha256"])
            raw=self.source_bytes(view,ref,cache)
            if raw is None:meta["order_state"]="unavailable";self.add_diagnostic(response,"source_unavailable",ref["owner_id"])
            elif ref["source_state"]=="stale":meta["order_state"]="stale";self.add_diagnostic(response,"source_changed",ref["owner_id"])
            else:
                parent=sources.extract(raw,ref["locator"]);steps=[];previous=-1
                for step in ordered["steps"]:
                    ext=sources.extract(raw,step["locator"])
                    explicit=re.match(r"^\s*"+str(step["number"])+r"[.)]\s+\S",ext.text)
                    if not sources.contained(parent,ext) or ext.span is None or ext.span[0]<previous or not explicit:break
                    previous=ext.span[1];steps.append((step["number"],ext.text))
                meta["order_state"]="recorded" if len(steps)==len(ordered["steps"]) else "partial"
                if meta["order_state"]=="recorded":
                    for ordinal,text in steps:
                        streams.append(dict(key=section_key("process","process_steps",index=ordinal,observed=ref["observed_sha256"]),kind="step",text=text,reference_id=ref["reference_id"]))
        if meta["order_state"]!="recorded":self.add_diagnostic(response,"ordering_unavailable",record["@id"])
        return meta,streams
