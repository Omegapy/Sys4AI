"""Stable finite proof DAGs; every edge names an earlier exact premise/rule."""
from ontology_core import canonical_bytes, sha256


def key(triple):
    return 'urn:sys4ai:ontology:proof:' + sha256(canonical_bytes(list(triple)))


def verify(proofs):
    by_id={p['id']:p for p in proofs}
    visited=set(); visiting=set()
    def walk(identity):
        if identity in visiting or identity not in by_id: return False
        if identity in visited: return True
        visiting.add(identity)
        value=by_id[identity]
        if not value.get('rule') or (value['rule']=='premise' and not value.get('approved')): return False
        if not all(walk(parent) for parent in value['premises']): return False
        visiting.remove(identity); visited.add(identity); return True
    return all(walk(identity) for identity in sorted(by_id))


def for_conclusion(proofs, triple):
    selected=set(); by_id={p['id']:p for p in proofs}
    def walk(identity):
        if identity in selected: return
        selected.add(identity)
        for parent in by_id[identity]['premises']: walk(parent)
    identity=key(triple)
    if identity in by_id: walk(identity)
    return [by_id[k] for k in sorted(selected)]
