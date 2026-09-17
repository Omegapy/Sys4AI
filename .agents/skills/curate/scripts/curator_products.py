"""Ordered owner obligations; successful canonical writes do not imply readiness."""
from copy import deepcopy
from curator_policy import digest, exact, require, sha

ORDER = {'canonical':0,'recertify':1,'memory.reindex':2,'ontology.compile':2,'ontology.wiki':3,'ontology.semantic':4,'ontology.memory':5}


def plan(products, snapshot):
    sha(snapshot); require(type(products) is list and len(products)<=100, 'product_limit', 'Select bounded product obligations.')
    ids=set(); result=[]
    for product in products:
        exact(product, ('id','route','required','enabled','present','current','input_sha256','dependencies'))
        require(product['id'] not in ids and product['route'] in ORDER, 'product_identity', 'Unknown or duplicate product.');ids.add(product['id'])
        require(all(type(product[k]) is bool for k in ('required','enabled','present','current')), 'product_selection', 'Product selection must be explicit.')
        sha(product['input_sha256']);require(type(product['dependencies']) is list, 'product_dependencies', 'Select exact prerequisites.')
        state='current' if product['enabled'] and product['present'] and product['current'] else 'pending' if product['enabled'] or product['required'] else 'disabled'
        result.append({**deepcopy(product),'state':state,'receipt':None})
    require(all(set(p['dependencies'])<=ids and p['id'] not in p['dependencies'] for p in result), 'product_dependencies', 'Product prerequisite is missing or self-referential.')
    for product in result:
        predecessors={p['id'] for p in result if p['enabled'] and ORDER[p['route']] < ORDER[product['route']]}
        product['dependencies']=sorted(set(product['dependencies']) | predecessors)
    ordered=[];remaining=result[:]
    while remaining:
        ready=[p for p in remaining if set(p['dependencies'])<={x['id'] for x in ordered}]
        require(ready,'product_cycle','Product dependency cycle.')
        chosen=min(ready,key=lambda p:(ORDER[p['route']],p['id']))
        if chosen['enabled'] and any(p['id'] in chosen['dependencies'] and p['state']=='pending' for p in ordered): chosen['state']='pending'
        ordered.append(chosen);remaining.remove(chosen)
    return {'snapshot':snapshot,'products':ordered,'state':'pending' if any(p['state']=='pending' for p in ordered) else 'current'}


def next_operation(value, *, current_snapshot, inputs):
    require(value['snapshot']==current_snapshot, 'products_stale', 'Documentation/integration changed the final source snapshot.')
    complete={p['id'] for p in value['products'] if p['state'] in ('current','complete')}
    for product in value['products']:
        require(inputs.get(product['id'])==product['input_sha256'], 'product_inputs_changed', 'Product input digest changed.')
        if product['state']!='pending':continue
        if not product['enabled']:return {'state':'held','item':product['id'],'reason':'required_product_disabled'}
        if not set(product['dependencies'])<=complete:return {'state':'held','item':product['id'],'reason':'prerequisite_pending'}
        return {'state':'selected','item':product['id'],'route':product['route'],'input_sha256':product['input_sha256']}
    return {'state':'current','item':None}


def observe(value, item, *, input_sha256, receipt, outcome):
    """Outcome is the owning Broker's inspected result, not a top-level ready flag."""
    require(outcome in ('completed','partial','failed','unavailable','aborted','reconciled_pending'), 'product_outcome', 'Expected an inspected owner outcome.')
    candidate=deepcopy(value); selected=next((p for p in candidate['products'] if p['id']==item),None)
    require(selected is not None and selected['enabled'] and selected['input_sha256']==input_sha256, 'product_changed', 'Product identity/input/selection changed.')
    exact(receipt, ('path','sha256'));sha(receipt['sha256'])
    if selected['state']=='complete' and outcome=='completed' and selected['receipt']==receipt: return candidate
    expected=next_operation(candidate,current_snapshot=candidate['snapshot'],inputs={p['id']:p['input_sha256'] for p in candidate['products']})
    require(expected['state']=='selected' and expected['item']==item,'product_order','Observe only the current selected owner operation after its prerequisites.')
    selected['receipt']=deepcopy(receipt);selected['state']='complete' if outcome=='completed' else 'pending'
    candidate['state']='pending' if any(p['state']=='pending' for p in candidate['products']) else 'current'
    return candidate
