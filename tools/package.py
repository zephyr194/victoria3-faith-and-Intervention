"""Build launcher-importable archives; target version is metadata, not certification."""
from pathlib import Path
import argparse
import json
import zipfile
ROOT = Path(__file__).resolve().parents[1]
def package(version):
    mod_version=json.loads((ROOT/'mod/.metadata/metadata.json').read_text())['version']
    target = ROOT/'dist'/f'faith-and-intervention-{mod_version}-vic3-{version}.zip'
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT/'mod').rglob('*')):
            if not path.is_file(): continue
            rel = path.relative_to(ROOT/'mod')
            data = path.read_bytes()
            if str(rel) == 'descriptor.mod': data = data.replace(b'1.13.*', f'{version}.*'.encode())
            if str(rel) == '.metadata/metadata.json':
                meta = json.loads(data); meta['supported_game_version'] = f'{version}.*'
                data = json.dumps(meta,ensure_ascii=False,indent=2).encode()
            archive.writestr('faith_and_intervention/'+str(rel),data)
        descriptor = (ROOT/'mod/descriptor.mod').read_text().replace('1.13.*',f'{version}.*')
        archive.writestr('faith_and_intervention.mod', descriptor+'path="mod/faith_and_intervention"\n')
        for name in ('README.md','DESIGN.md','docs/TESTING.md','docs/COMPATIBILITY.md','docs/HOLY_SITES.md'):
            archive.write(ROOT/name,'faith_and_intervention_docs/'+name)
    return target
if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--game-version',choices=('1.13','1.14'),default='1.13')
    print(package(parser.parse_args().game_version))
