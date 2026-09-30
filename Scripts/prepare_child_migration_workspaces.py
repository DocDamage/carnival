"""Clone immutable supplied child projects into disposable migration workspaces."""
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
manifest=json.loads((OUT/'SourceManifest.json').read_text())
workspaces=[]
for row in manifest['sources']:
    if not row.get('staged_project'):
        continue
    source=Path(row['staged_project']).parent
    destination=OUT/'MigrationWorkspace'/row['identity']
    # An existing workspace may contain engine-renamed assets: never reset it.
    if not destination.exists():
        shutil.copytree(source,destination)
    project=destination/Path(row['staged_project']).name
    data=json.loads(project.read_text(encoding='utf-8-sig'))
    for name in ('PythonScriptPlugin','EditorScriptingUtilities'):
        if not any(p['Name']==name for p in data.get('Plugins',[])):
            data.setdefault('Plugins',[]).append({'Name':name,'Enabled':True})
    project.write_text(json.dumps(data,indent=2))
    workspaces.append({'identity':row['identity'],'source':str(source),'project':str(project)})
(OUT/'MigrationWorkspaces.json').write_text(json.dumps({'workspaces':workspaces},indent=2))
print(json.dumps(workspaces,indent=2))
