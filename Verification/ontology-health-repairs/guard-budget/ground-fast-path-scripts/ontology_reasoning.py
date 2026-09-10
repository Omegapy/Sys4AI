"""A deterministic named-resource rule subset, with inspectable finite proofs."""
from ontology_core import OntologyError, canonical_bytes, require, sha256
from ontology_advanced import AXIOMS, RDF, RDFS, OWL
from ontology_derivations import key

PROFILE='finite-profile-v1'
RULES=('scm-eqc1','scm-eqc2','scm-sco','cax-sco','scm-eqp1','scm-eqp2',
       'scm-spo','prp-spo1','prp-inv1','prp-inv2','prp-symp','prp-trp',
       'eq-sym','eq-trans','eq-rep-s','eq-rep-o')


def infer(premises, negatives, goals, context, bound):
    ttype=RDF+'type'; subclass=RDFS+'subClassOf'; subproperty=RDFS+'subPropertyOf'
    same=OWL+'sameAs'; different=OWL+'differentFrom'
    initial=set(); proofs={}; failures=[]
    classes=set(); properties=set()
    for premise in premises:
        triple=premise['triple']
        if not all(isinstance(x,str) for x in triple):
            failures.append({'code':'unsupported_axiom','message':'The finite reasoning profile supports named-resource axioms only.','premise':premise['id']}); continue
        s,p,o=triple
        if p.startswith(OWL) and p not in AXIOMS:
            failures.append({'code':'unsupported_axiom','message':'OWL axiom is outside the finite profile.','premise':premise['id']}); continue
        if p==ttype and o.startswith(OWL) and o not in {OWL+'SymmetricProperty',OWL+'TransitiveProperty',OWL+'ObjectProperty',OWL+'Class',OWL+'NamedIndividual'}:
            failures.append({'code':'unsupported_axiom','message':'OWL class/property expression is outside the finite profile.','premise':premise['id']}); continue
        if not premise.get('approved'):
            failures.append({'code':'unapproved_premise','message':'Draft or unapproved input is not a reasoning premise.','premise':premise['id']}); continue
        t=tuple(triple); initial.add(t)
        proofs.setdefault(t,{'id':key(t),'triple':list(t),'rule':'premise','premises':[],
            'approved':True,'assertion_id':premise['id'],'record_id':premise.get('record_id'),
            'sources':premise['sources'],'input_snapshot_sha256':context['snapshot_sha256']})
        if p in {subclass,OWL+'equivalentClass',OWL+'disjointWith'}: classes.update((s,o))
        if p in {subproperty,OWL+'equivalentProperty',OWL+'inverseOf',OWL+'propertyDisjointWith'}: properties.update((s,o))
        if p==ttype:
            classes.add(o)
            if o in {OWL+'SymmetricProperty',OWL+'TransitiveProperty',OWL+'ObjectProperty',RDF+'Property'}: properties.add(s)
    for s,p,o in initial:
        if p==same and (s in classes|properties or o in classes|properties):
            failures.append({'code':'unsupported_axiom','message':'Identity equality is restricted to approved named individuals.'})
    if failures: return {'status':'unsupported_semantics','complete':False,'trusted':False,'diagnostics':failures,'profile':PROFILE}
    if len(initial)>bound['input_triples']: return {'status':'resource_limit','complete':False,'limit':'input_triples','trusted':False}
    closure=set(initial); limited=None; rounds=0
    def add(triple,rule,support):
        nonlocal limited
        triple=tuple(triple)
        if triple in closure: return
        if len(closure)-len(initial)>=bound['derived_triples']: limited='derived_triples'; return
        if len(proofs)>=bound['proof_nodes']: limited='proof_nodes'; return
        closure.add(triple)
        proofs[triple]={'id':key(triple),'triple':list(triple),'rule':rule,
            'premises':[key(t) for t in support],'input_snapshot_sha256':context['snapshot_sha256']}
    if len(proofs)>bound['proof_nodes']: limited='proof_nodes'
    while not limited:
        if rounds>=bound['rule_rounds']: limited='rule_rounds'; break
        rounds+=1; previous=len(closure); snapshot=sorted(closure)
        by_p={}
        for triple in snapshot: by_p.setdefault(triple[1],[]).append(triple)
        for s,p,o in snapshot:
            t=(s,p,o)
            if p==OWL+'equivalentClass':
                add((s,subclass,o),'scm-eqc1',[t]); add((o,subclass,s),'scm-eqc2',[t])
            if p==OWL+'equivalentProperty':
                add((s,subproperty,o),'scm-eqp1',[t]); add((o,subproperty,s),'scm-eqp2',[t])
            if p in {subclass,subproperty}:
                for a,_,b in by_p.get(p,[]):
                    if o==a: add((s,p,b),'scm-sco' if p==subclass else 'scm-spo',[t,(a,p,b)])
            if p==ttype:
                for a,_,b in by_p.get(subclass,[]):
                    if o==a: add((s,ttype,b),'cax-sco',[t,(a,subclass,b)])
            for a,_,b in by_p.get(subproperty,[]):
                if p==a: add((s,b,o),'prp-spo1',[t,(a,subproperty,b)])
            for a,_,b in by_p.get(OWL+'inverseOf',[]):
                if p==a: add((o,b,s),'prp-inv1',[t,(a,OWL+'inverseOf',b)])
                if p==b: add((o,a,s),'prp-inv2',[t,(a,OWL+'inverseOf',b)])
            sym=(p,ttype,OWL+'SymmetricProperty'); trans=(p,ttype,OWL+'TransitiveProperty')
            if sym in closure: add((o,p,s),'prp-symp',[t,sym])
            if trans in closure:
                for a,_,b in by_p.get(p,[]):
                    if o==a: add((s,p,b),'prp-trp',[t,(a,p,b),trans])
            if p==same:
                add((o,same,s),'eq-sym',[t])
                for a,_,b in by_p.get(same,[]):
                    if o==a: add((s,same,b),'eq-trans',[t,(a,same,b)])
            for a,_,b in by_p.get(same,[]):
                if s==a: add((b,p,o),'eq-rep-s',[t,(a,same,b)])
                if o==a: add((s,p,b),'eq-rep-o',[t,(a,same,b)])
            if limited: break
        if len(closure)==previous: break
    conflicts=[]; affected=set()
    def conflict(kind,ts):
        signature=sha256(canonical_bytes({'kind':kind,'triples':sorted(ts)}))
        if any(c['id']==signature for c in conflicts): return
        conflicts.append({'id':signature,'kind':kind,'triples':[list(t) for t in ts],
                          'proofs':[key(t) for t in ts if t in proofs]})
        for s,p,o in ts: affected.update((s,o))
    for s,p,o in sorted(closure):
        if p==OWL+'disjointWith':
            for a,q,b in sorted(closure):
                if q==ttype and b==s and (a,ttype,o) in closure:
                    conflict('disjoint_types',[(s,p,o),(a,q,b),(a,ttype,o)])
        if p==OWL+'propertyDisjointWith':
            for a,q,b in sorted(closure):
                if q==s and (a,o,b) in closure: conflict('disjoint_properties',[(s,p,o),(a,q,b),(a,o,b)])
        if p==different and ((s,same,o) in closure or (o,same,s) in closure or s==o):
            conflict('inconsistent_identity',[(s,p,o),(s,same,o)] if (s,same,o) in closure else [(s,p,o),(o,same,s)] if (o,same,s) in closure else [(s,p,o)])
    negative_set=set()
    for statement in negatives:
        triple=tuple(statement[k] for k in ('subject','predicate','object'))
        require(all(isinstance(v,str) for v in triple),'unsupported_axiom','Negative assertions require named-resource terms.')
        negative_set.add(triple)
        if triple in closure: conflict('negative_assertion',[triple])
    conclusions=[]
    for goal in goals or []:
        require(isinstance(goal,list) and len(goal)==3 and all(isinstance(x,str) for x in goal),'invalid_goal','A reasoning goal is three named resource IRIs.')
        t=tuple(goal)
        classification='entailed' if t in closure else 'contradicted' if t in negative_set else 'unproven'
        if conflicts and (t[0] in affected or t[2] in affected): classification='inconsistent'
        conclusions.append({'triple':goal,'classification':classification,'proof':key(t) if t in proofs else None,
            'negative_evidence':[n['id'] for n in negatives if [n[k] for k in ('subject','predicate','object')]==goal],
            'trusted':not limited and not conflicts and classification=='entailed'})
    return {'status':'resource_limit' if limited else 'inconsistent' if conflicts else 'ok','complete':not limited,
        'trusted':not limited and not conflicts,'limit':limited,'profile':PROFILE,'rules':list(RULES),'rounds':rounds,
        'inferred':[list(t) for t in sorted(closure-initial)],'conclusions':conclusions,
        'proofs':sorted(proofs.values(),key=lambda p:p['id']),'conflicts':sorted(conflicts,key=lambda c:c['id']),
        'negative_assertions':[dict(n,input_snapshot_sha256=context['snapshot_sha256']) for n in sorted(negatives,key=lambda n:n['id'])],
        'diagnostics':[],'authority':False}
