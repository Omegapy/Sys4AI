"""Prepare a disposable tooling fixture from explicitly selected reviewed dependencies.

Example: .venv/bin/python -B prepare_fixture.py --dependencies /private/tmp/reviewed/node_modules --target /private/tmp/explorer-tools-recheck
The target must not exist. No dependency download, hooks, service or browser runs.
"""
from pathlib import Path
import argparse
import shutil

p=argparse.ArgumentParser()
p.add_argument('--dependencies',type=Path,required=True)
p.add_argument('--target',type=Path,required=True)
args=p.parse_args()
repo=Path(__file__).resolve().parents[3]
target=args.target.absolute()
if target.exists() or target.is_symlink() or not target.is_relative_to(Path('/private/tmp')) or target.parent.resolve()!=target.parent:
    p.error('Choose an absent target below real /private/tmp without symlink parents.')
root=target/'ontology/explorer';root.mkdir(parents=True)
source=repo/'SKILLS-depo/ontology/explorer'
for name in ['package.json','package-lock.json','THIRD_PARTY_NOTICES.md','vite.config.ts','tsconfig.json','BUILD.md','scripts/package-runtime.mjs']:
    dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,dest)
(root/'src').mkdir()
(root/'src/main.ts').write_text("""import './styles.css';
const output = document.querySelector<HTMLDivElement>('#app');
if (output) output.textContent = import.meta.env.EXPLORER_BUILD_ID + ':' + import.meta.env.EXPLORER_SCHEMA_SHA256;
document.querySelector('#load')?.addEventListener('click', async () => { const { default: cytoscape } = await import('cytoscape'); const graph = cytoscape({ headless: true, elements: [{data:{id:'a'}},{data:{id:'b'}},{data:{id:'r', source:'a',target:'b'}}]}); if (output) output.textContent += ':' + graph.edges().length; graph.destroy(); });
""")
(root/'src/styles.css').write_text('body { font-family: sans-serif; color: #151515; background: #fff; }\n')
(root/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="UTF-8"><title>Tooling fixture</title><script type="module" src="/src/main.ts"></script></head><body><div id="app"></div><button id="load" type="button">Load local graph code</button></body></html>\n')
(root.parent/'scripts').mkdir()
shutil.copyfile(repo/'SKILLS-depo/ontology/scripts/ontology_explorer_assets.py',root.parent/'scripts/ontology_explorer_assets.py')
shutil.copyfile(repo/'ONTOLOGY-depo/schema/explorer-v1.json',root.parent/'schema.json')
shutil.copytree(args.dependencies,root/'node_modules',symlinks=True)
print(root)
