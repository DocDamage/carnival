"""Back up and save only owned meshes with measured unstable derived keys.

Does not change authored geometry, clothing choices or source archives.
Fresh reload must prove that repeated rebuild warnings are reduced.
"""
import datetime,hashlib,json,re,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterRepairs'
LOG=ROOT/'Saved/PresentationAcceptance/PopulatedCarnival/index_engine.log'
REPORT={'success':False,'saved':[],'errors':[],
 'limits':'Backed-up current-editor mesh build saves only; fresh reload and runtime/cook acceptance remain required.'}
backup=OUT/('BeforeObservedMeshBuildSave_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
eal=unreal.EditorAssetLibrary
try:
 paths=sorted(set(re.findall(r'Skeletal mesh \[(.*?)\]: The derived data key is different after the build',LOG.read_text(errors='replace'))))
 assert paths,'No measured mesh rebuilds in completed populated report log'
 entry=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 for command in ('Editor.AsyncAssetCompilationMaxConcurrency 1','Editor.AsyncSkinnedAssetCompilationMaxConcurrency 1','Editor.AsyncAssetCompilationMaxMemoryUsage 4'):
  unreal.SystemLibrary.execute_console_command(entry,command)
 for path in paths:
  package=path.split('.')[0]
  assert package.startswith(('/Game/Outfits/','/Game/Carnival/')),package
  file=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset');assert file.exists()
  copies=[]
  for extension in ('.uasset','.uexp','.ubulk'):
   origin=file.with_suffix(extension)
   if not origin.exists():continue
   target=backup/origin.relative_to(ROOT/'Content');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin,target)
   copies.append({'backup':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
  asset=unreal.load_asset(package);assert asset
  assert isinstance(asset,unreal.SkeletalMesh),'Unexpected measured package type '+package
  material_slots=[(str(s.material_slot_name),s.material_interface.get_path_name() if s.material_interface else None) for s in asset.materials]
  skeleton=asset.skeleton.get_path_name() if asset.skeleton else None
  assert eal.save_loaded_asset(asset,only_if_is_dirty=False),package
  assert [(str(s.material_slot_name),s.material_interface.get_path_name() if s.material_interface else None) for s in asset.materials]==material_slots
  assert (asset.skeleton.get_path_name() if asset.skeleton else None)==skeleton
  REPORT['saved'].append({'package':package,'backups':copies,'skeleton':skeleton,
      'material_slot_count':len(material_slots),'after_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'ObservedCrowdMeshBuildSave_20260930.json').write_text(json.dumps(REPORT,indent=2))
