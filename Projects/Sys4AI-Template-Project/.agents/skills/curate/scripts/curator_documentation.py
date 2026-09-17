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


def check_local_links(root, documents):
    """Read selected Markdown links and report exact local path/casing findings."""
    from pathlib import Path
    import os
    import re
    from urllib.parse import unquote,urlsplit
    from curator_integration import read_exact,content_hash
    require(type(documents) is list and len(documents)<=50,'documentation_scope','Select at most 50 documents.')
    root=Path(root).resolve(strict=True);findings=[];sources=[];total=0
    for name in documents:
        raw=read_exact(root,name);total+=len(raw)
        require(total<=8000000,'documentation_scope','Selected document bytes exceed the bounded review.')
        sources.append({'path':name,'sha256':content_hash(raw)})
        for match in re.finditer(r'\[[^\]\n]*\]\(([^)\n]+)\)',raw.decode('utf-8')):
            value=match.group(1).strip();value=value[1:value.index('>')] if value.startswith('<') and '>' in value else value.split()[0] if value else ''
            if not value:continue
            parsed=urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path:continue
            target=(root/name).parent/unquote(parsed.path)
            target=Path(os.path.normpath(target))
            if not target.is_relative_to(root):
                findings.append({'document':name,'target':value,'code':'outside_selected_project'});continue
            current=root;corrected=[];code=None
            for part in target.relative_to(root).parts:
                if not current.is_dir():code='missing_link';break
                names=[entry.name for entry in current.iterdir()]
                if part in names:chosen=part
                else:
                    matches=[entry for entry in names if entry.casefold()==part.casefold()]
                    if len(matches)!=1:code='missing_link';break
                    chosen=matches[0];code='path_casing'
                corrected.append(chosen);current=current/chosen
            if code:findings.append({'document':name,'target':value,'code':code,'actual_path':'/'.join(corrected) if code=='path_casing' else None})
    return {'state':'current' if not findings else 'findings','findings':findings,'sources':sources,
            'canonical_writes':0,'model_calls':0,'scope':'Selected local Markdown paths; semantic descriptions still require source comparison.'}
