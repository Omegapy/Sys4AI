"""Descriptive updates use exact ownership; generators and history retain owners."""
from curator_classification import classify_target
from curator_policy import exact, require


def route(ownership, identity, ranges, snapshot, change):
    exact(change, ('kind','old_path','new_path','semantic_review'))
    require(change['kind'] in ('content','rename','interface','governance'), 'documentation_change', 'Select a known change kind.')
    classified=classify_target(ownership,identity,ranges,snapshot)
    if classified['state']!='classified':return classified
    if change['kind']=='governance' or classified['class']=='governance':return {**classified,'route':'protected.review','state':'proposed'}
    if classified['class']=='historical':return {**classified,'route':'task.response-correction','state':'proposed','preserve_original':True}
    if classified['class']=='generated':return {**classified,'state':'proposed','edit_generated_output':False}
    if change['kind'] in ('rename','interface'):
        require(change['semantic_review'] is not None and change['semantic_review'].get('source_sha256')==identity['sha256']
                and change['semantic_review'].get('applicable') is True, 'documentation_semantics', 'Rename/interface claims need exact semantic review.')
        require(change['old_path']==identity['path'] and type(change['new_path']) is str, 'documentation_path', 'Bind the actual old and selected new path.')
    return {**classified,'state':'proposed','change_kind':change['kind'],'canonical_writes':0}
