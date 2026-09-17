import copy
from hashlib import sha256
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from curator_classification import classify_target, validate_map
from curator_policy import PolicyError


class ClassificationTests(unittest.TestCase):
    def entry(self, path, kind='documentation', owner='project'):
        raw=b'Facts start.\nFacts end.\nInstructions start.\nInstructions end.\n'
        entry={'id':'stable','path':path,'pattern':False,'sha256':sha256(raw).hexdigest(),
            'class':kind,'owner':owner,'generator':None,'sources':[],'sections':[],'interfaces':[]}
        return entry,raw

    def classify(self, entry, raw, ranges=None, path=None):
        path=path or entry['path']
        return classify_target({'schema_version':1,'entries':[entry]},
            {'id':entry['id'],'path':path,'sha256':sha256(raw).hexdigest()},
            ranges or [[0,len(raw)]],{path:raw})

    def test_nested_instructions_and_runtime_controls_keep_floor(self):
        for path in ('AGENTS.md','docs/AGENTS.md','.codex/config.toml','pkg/.codex/config.toml',
                     'docs/SOUL.md','Roles/example/ROLE.md','x/.agents/skills/a/SKILL.md',
                     'document-ownership.json','x/curator_policy.py','x/curator_confinement.py'):
            entry,raw=self.entry(path)
            self.assertEqual(self.classify(entry,raw)['class'],'governance',path)

    def test_distinct_generated_and_history_routes(self):
        entry,raw=self.entry('ONTOLOGY/WIKI/index.md','generated','ontology')
        entry.update(generator='ontology.wiki',sources=['ONTOLOGY/modules/a.jsonld'])
        self.assertEqual(self.classify(entry,raw)['route'],'ontology.wiki')
        entry,raw=self.entry('Tasks/t/responses/response.md','historical','task')
        self.assertEqual(self.classify(entry,raw)['route'],'task.response-correction')

    def test_readme_sections_and_crossing_patch(self):
        entry,raw=self.entry('README.md')
        start=b'Instructions start.'; end=b'Instructions end.'
        low=raw.index(start); high=raw.index(end)+len(end)
        entry['sections']=[{'id':'instructions','start':start.decode(),'end':end.decode(),
            'sha256':sha256(raw[low:high]).hexdigest(),'class':'governance','owner':'project','protected':True}]
        self.assertEqual(self.classify(entry,raw,[[0,5]])['class'],'documentation')
        self.assertEqual(self.classify(entry,raw,[[low,high]])['class'],'governance')
        self.assertEqual(self.classify(entry,raw)['code'],'mixed_patch')
        self.assertEqual(self.classify(entry,raw,[[0,5],[low,high]])['code'],'mixed_patch')

    def test_stable_identity_rename_stale_unbound_and_bad_anchor(self):
        entry,raw=self.entry('README.md')
        self.assertEqual(self.classify(entry,raw,path='renamed.txt')['code'],'rename_unbound')
        entry['sha256']=None
        self.assertEqual(self.classify(entry,raw)['code'],'source_changed')
        entry['sha256']=sha256(raw).hexdigest()
        entry['sections']=[{'id':'missing','start':'missing','end':'absent','sha256':'0'*64,
            'class':'documentation','owner':'project','protected':False}]
        self.assertEqual(self.classify(entry,raw)['code'],'anchor_ambiguous')

    def test_alias_and_duplicate_identity_hold(self):
        entry,raw=self.entry('README.md'); other=copy.deepcopy(entry);other['id']='other';other['path']='readme.md'
        with self.assertRaises(PolicyError):validate_map({'schema_version':1,'entries':[entry,other]})
        other['path']='different.md';other['id']=entry['id']
        with self.assertRaises(PolicyError):validate_map({'schema_version':1,'entries':[entry,other]})



    def test_malformed_complete_map_class_and_owner_hold(self):
        entry,raw=self.entry('README.md')
        for field in ('class','owner'):
            for bad in ({},[]):
                candidate=copy.deepcopy(entry);candidate[field]=bad
                self.assertEqual(self.classify(candidate,raw)['state'],'held')
        for field in ('class','owner'):
            candidate=copy.deepcopy(entry)
            section={'id':'facts','start':'Facts start.','end':'Facts end.',
                'sha256':sha256(raw[:raw.index(b'Facts end.')+len(b'Facts end.')]).hexdigest(),
                'class':'documentation','owner':'project','protected':False}
            section[field]={};candidate['sections']=[section]
            self.assertEqual(self.classify(candidate,raw)['state'],'held')

if __name__ == '__main__':unittest.main()
