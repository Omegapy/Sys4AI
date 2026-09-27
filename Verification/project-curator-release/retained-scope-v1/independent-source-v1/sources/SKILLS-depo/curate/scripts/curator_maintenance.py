"""Scope checks for a selected isolated repair; proposals carry no new authority."""
from fnmatch import fnmatchcase
from curator_policy import digest, exact, require
from curator_classification import relative


def technical(finding, accepted, *, current_target, selected_classes, selected_paths, selected_tools, remaining):
    exact(finding, ('class','paths','tools','cause_established','evidence','definition_of_done'))
    require(finding['class'] in selected_classes and finding['class'] in ('defect','compatibility'), 'repair_class', 'Repair class is not selected.')
    require(type(finding['paths']) is list and bool(finding['paths']) and type(finding['cause_established']) is bool,'repair_scope','Select explicit repair paths and a factual cause status.')
    normalized=[relative(p) for p in selected_paths]
    for original in finding['paths']:
        path=relative(original);require(any(fnmatchcase(path,p) or path==p or path.startswith(p.rstrip('/')+'/') for p in normalized), 'repair_scope', 'Repair path exceeds selected scope.')
    require(set(finding['tools'])<=set(selected_tools), 'repair_tool', 'Repair tool is not selected.')
    require(finding['evidence'] and finding['definition_of_done'], 'repair_evidence', 'A repair needs observable evidence and completion criteria.')
    require(accepted['target_sha256']==current_target and accepted['finding_sha256']==digest(finding), 'repair_stale', 'The accepted implementation target changed.')
    require(all(type(n) is int and n>=0 for n in remaining.values()) and all(k in remaining and type(v) is int and v>=0 and remaining[k]>=v for k,v in accepted['cost'].items()), 'repair_budget', 'Selected repair budget is exhausted.')
    return {'state':'proposed','route':'isolated_technical_repair' if finding['cause_established'] else 'bounded_investigation',
            'finding_sha256':digest(finding),'target_sha256':current_target,'paths':finding['paths'],'canonical_writes':0}
