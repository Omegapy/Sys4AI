"""Evidence routing and lifecycle proposals; existing owners alone publish."""
from copy import deepcopy
from curator_policy import digest, exact, require, sha


def decision(finding):
    exact(finding, ('memory', 'ontology', 'supported', 'conflicting', 'new_knowledge', 'stale_products', 'sources'))
    require(all(type(finding[k]) is bool for k in ('memory','ontology','supported','conflicting','new_knowledge')),
            'knowledge_decision', 'Knowledge decisions require explicit booleans.')
    for source in finding['sources']: exact(source, ('path','sha256')); sha(source['sha256'])
    if not finding['supported'] or finding['conflicting']:
        return {'state':'held','decision':'neither','routes':[],'reason':'unsupported_or_conflicting_evidence','canonical_writes':0}
    products = finding['stale_products']
    require(type(products) is list and all(x in ('memory','ontology') for x in products), 'product_owner', 'Only declared owner products are supported.')
    if not finding['new_knowledge']:
        return {'state':'proposed' if products else 'idle','decision':'neither',
                'routes':[x+'.maintenance' for x in sorted(set(products))],'reason':'derived_only','canonical_writes':0}
    require(finding['sources'], 'knowledge_evidence', 'New assertions need exact supporting sources.')
    selected=[k for k in ('memory','ontology') if finding[k]]
    return {'state':'proposed' if selected else 'idle','decision':'both' if len(selected)==2 else selected[0] if selected else 'neither',
            'routes':[x+'.publish' for x in selected],'reason':'review_exact_owner_payloads','canonical_writes':0}


def semantic_rebind(previous, successor, review):
    """A hash refresh alone cannot certify the applicability of a historical claim."""
    exact(review, ('before_sha256','after_sha256','meaning_preserved','applicability','evidence'))
    require(review['before_sha256']==digest(previous) and review['after_sha256']==digest(successor), 'rebind_changed', 'Review must name exact old and new source records.')
    require(review['meaning_preserved'] is True and type(review['applicability']) is str and review['applicability'].strip()
            and type(review['evidence']) is list and review['evidence'], 'semantic_review', 'Applicable meaning and source comparison must be reviewed.')
    for ref in review['evidence']: exact(ref, ('path','sha256')); sha(ref['sha256'])
    return {'state':'proposed','original_sha256':digest(previous),'successor':deepcopy(successor),
            'review':deepcopy(review),'route':'existing_owner_lifecycle','canonical_writes':0}


def ontology_transition(lifecycle_owner, record, state, *, reason, replacement=None):
    """The caller supplies the already pinned actual ontology lifecycle module."""
    candidate=lifecycle_owner.transition(record,state,reason=reason,replacement=replacement)
    require(not lifecycle_owner.validate_transition([record],[candidate]), 'lifecycle_invalid', 'Existing ontology owner rejected the transition.')
    return candidate
