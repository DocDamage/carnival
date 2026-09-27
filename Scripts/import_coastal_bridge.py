"""Import the user-supplied coastal environment without replacing project settings."""
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/MansionConnection'
BACKUP = OUT / 'Backups'
BACKUP.mkdir(parents=True, exist_ok=True)
archive = ROOT / 'Assets/CoastalBridge.zip'
project = ROOT / 'CarnivalGame.uproject'
config = ROOT / 'Config/DefaultEngine.ini'
main_map = ROOT / 'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
for path in [project, config, main_map]:
    dest = BACKUP / (path.name + '.before_mansion')
    if not dest.exists():
        shutil.copy2(path, dest)
report = {'archive': str(archive), 'files': [], 'bytes': 0}
content = (ROOT / 'Content').resolve()
prefix = 'CoastalBridge/Content/'
with zipfile.ZipFile(archive) as z:
    for info in z.infolist():
        if info.is_dir() or not info.filename.startswith(prefix):
            continue
        relative = Path(info.filename[len(prefix):])
        if relative.parts[0] not in ('RailBridge', 'StarterContent'):
            continue
        dest = (content / relative).resolve()
        if not dest.is_relative_to(content):
            raise ValueError('Archive entry escapes Content: ' + info.filename)
        if dest.exists():
            raise FileExistsError('Refusing to overwrite existing asset: ' + str(dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        with z.open(info) as src, dest.open('wb') as dst:
            shutil.copyfileobj(src, dst, length=1024*1024)
        report['files'].append(str(relative))
        report['bytes'] += info.file_size
        if len(report['files']) % 300 == 0:
            print('Imported', len(report['files']), 'files', flush=True)
settings = json.loads(project.read_text(encoding='utf-8'))
plugins = settings.setdefault('Plugins', [])
for name in ['Water', 'WaterExtras', 'Landmass', 'HDRIBackdrop']:
    existing = next((p for p in plugins if p['Name'] == name), None)
    if existing is None:
        plugins.append({'Name': name, 'Enabled': True})
    else:
        existing['Enabled'] = True
project.write_text(json.dumps(settings, indent='\t') + '\n', encoding='utf-8')
text = config.read_text(encoding='utf-8')
if 'Name="WaterBodyCollision"' not in text:
    text += '\n[/Script/Engine.CollisionProfile]\n+Profiles=(Name="WaterBodyCollision",CollisionEnabled=QueryOnly,bCanModify=False,ObjectTypeName="WorldStatic",CustomResponses=((Channel="WorldDynamic",Response=ECR_Overlap),(Channel="Pawn",Response=ECR_Overlap),(Channel="Visibility",Response=ECR_Ignore),(Channel="Camera",Response=ECR_Ignore),(Channel="PhysicsBody",Response=ECR_Overlap),(Channel="Vehicle",Response=ECR_Overlap),(Channel="Destructible",Response=ECR_Overlap)),HelpMessage="Water overlap for the coastal wetlands")\n'
config.write_text(text, encoding='utf-8')
(OUT / 'Coastal_Import.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('Imported', len(report['files']), 'files;', round(report['bytes']/1024**3, 2), 'GiB', flush=True)
