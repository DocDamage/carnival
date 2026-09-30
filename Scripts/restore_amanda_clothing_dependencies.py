"""Restore exact local licensed files at hard-reference paths missing in PIE.

Only copies dependencies observed in the live log from Amanda's existing
relocated source tree. Refuses conflicting destinations; preserves sources.
Fresh asset loading must still verify graph and transitive dependencies.
"""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterRepairs'
SOURCE_PREFIX='Carnival/MetaHumans/Additional/Amanda/AmandaBlack/'
PACKAGE_PREFIX='/Game/Fab/MetaHuman/OA_Crewneckt/'
manifest=json.loads((OUT/'CrowdLiveMissingDependencies_20260930.json').read_text())
report={'success':False,'copies':[],'source_files_modified':False,
 'limits':'Exact local source dependency copies only; fresh reload/transitive dependencies/material compilation and crowd appearance remain required.'}
paths=sorted({r['missing'] for r in manifest['missing_dependencies']})
for package in paths:
 assert package.startswith(PACKAGE_PREFIX),package
 relative=package.removeprefix('/Game/')
 source=ROOT/'Content'/(SOURCE_PREFIX+relative+'.uasset')
 assert source.exists(),source
 for extension in ('.uasset','.uexp','.ubulk'):
  origin=source.with_suffix(extension)
  if not origin.exists():continue
  destination=ROOT/'Content'/(relative+extension)
  source_sha=hashlib.sha256(origin.read_bytes()).hexdigest()
  if destination.exists():
   assert hashlib.sha256(destination.read_bytes()).hexdigest()==source_sha,'Conflicting pre-existing asset '+str(destination)
   action='already_identical'
  else:
   destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin,destination);action='copied'
  assert hashlib.sha256(destination.read_bytes()).hexdigest()==source_sha
  assert hashlib.sha256(origin.read_bytes()).hexdigest()==source_sha
  report['copies'].append({'package':package,'source':str(origin),'destination':str(destination),'sha256':source_sha,'action':action})
report['success']=True
(OUT/'AmandaClothingDependencyCopies_20260930.json').write_text(json.dumps(report,indent=2))
print('Restored exact source dependency files:',len(report['copies']))
