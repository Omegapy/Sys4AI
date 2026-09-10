"""Actual pinned worker fixtures; authored files remain disposable."""
from pathlib import Path
import shutil
import sys
import unittest
from support import make_project,write_json,record,add_records,project_id,core_id,standards_environment
from ontology_core import canonical_bytes,sha256,read_json


def environment():
    candidate = standards_environment()
    if candidate is None:
        raise unittest.SkipTest('Optional standards acceptance is unselected; select an existing certified runtime with SYS4AI_STANDARDS_PYTHON.')
    return candidate


def make_advanced(path):
    root=make_project(path)
    shutil.copytree(environment(),root/'.venv-ontology-standards',symlinks=True,ignore=shutil.ignore_patterns('wheels','__pycache__','*.pyc'))
    write_json(root/'ontology-advanced.yaml',{'schema_version':1,'profiles':{'standards':{'enabled':True,'python':'.venv-ontology-standards/bin/python'},'inference':{'enabled':True}},'extensions':[],'limits':{}})
    return root


def statement(root,local,subject,predicate,obj):
    return {'id':project_id(local),'subject':subject,'predicate':predicate,'object':obj,'sources':record('x')['sources']}


def extension(root,axioms=(),annotations=(),negatives=()):
    value={'schema_version':1,'id':project_id('extension'),'version':'1.0.0','project_id':'example','axioms':list(axioms),'annotations':list(annotations),'negative_assertions':list(negatives)}
    path='ONTOLOGY/extensions/semantics.json'; write_json(root/path,value)
    cfg=read_json(root/'ontology-advanced.yaml'); cfg['extensions']=[{'path':path,'sha256':sha256(root/path)}]; write_json(root/'ontology-advanced.yaml',cfg)
    return value


def wiki(root):
    records=[record('GeneratedWikiPage',kind='concept',type_name='OntologyConcept'),record('wiki',type_name='OntologyConcept',**{'@type':[project_id('GeneratedWikiPage')]}),
       record('wiki-subtype',kind='relation',type_name='Relationship',subject=project_id('GeneratedWikiPage'),predicate=core_id('subtypeOf'),object=core_id('Artifact'))]
    add_records(root,records)
    return records
