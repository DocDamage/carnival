"""Recover a generated but unsaved physics dependency using the verified FBX.

Import a separate owned recovery mesh with the existing corrected skeleton.
Keep production geometry/animations intact; explicitly save generated packages.
"""
import datetime,hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
BASE='/Game/Carnival/Characters/Children/BlackBoy/Diagnostics/ConsistentBind'
REPORT={'success':False,'errors':[],'limits':'Saved physics dependency recovery only; no ragdoll or ride-seat fitting claim.'}
eal=unreal.EditorAssetLibrary
try:
 prepared=json.loads((OUT/'BlackBoy_Consistent_Bind_FBX.json').read_text());assert prepared['success']
 file=Path(prepared['prepared_fbx']);assert hashlib.sha256(file.read_bytes()).hexdigest()==prepared['prepared_sha256']
 mesh=unreal.load_asset(BASE+'/SK_BlackBoy_ConsistentBind');assert mesh
 original=ROOT/'Content'/(BASE.removeprefix('/Game/')+'/SK_BlackBoy_ConsistentBind.uasset')
 backup=OUT/'Backups'/('PhysicsRecovery_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))/original.name
 backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,backup)
 recovery=BASE+'/PhysicsRecovery/SK_BlackBoy_PhysicsRecovery'
 restored=unreal.load_asset(recovery) if eal.does_asset_exist(recovery) else None
 if restored and not restored.get_editor_property('physics_asset'):
  recovery=BASE+'/PhysicsRecovery/SK_BlackBoy_PhysicsRecovery_Durable'
  restored=unreal.load_asset(recovery) if eal.does_asset_exist(recovery) else None
 if not restored:
  world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
  unreal.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
  options=unreal.FbxImportUI();options.automated_import_should_detect_type=False
  options.import_as_skeletal=True;options.import_mesh=True;options.import_animations=False
  options.import_materials=False;options.import_textures=False;options.create_physics_asset=True
  options.skeleton=mesh.skeleton;options.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
  for key,value in [('convert_scene',True),('convert_scene_unit',True),('force_front_x_axis',False),('import_morph_targets',True),('update_skeleton_reference_pose',False),('use_t0_as_ref_pose',False)]:options.skeletal_mesh_import_data.set_editor_property(key,value)
  task=unreal.AssetImportTask();task.filename=str(file);task.destination_path=recovery.rsplit('/',1)[0]
  task.destination_name=recovery.rsplit('/',1)[1];task.automated=True;task.save=True;task.replace_existing=False;task.options=options
  unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);restored=unreal.load_asset(recovery)
 assert restored and restored.skeleton==mesh.skeleton
 physics=restored.get_editor_property('physics_asset');assert physics
 physics.modify()
 assert eal.save_loaded_asset(physics)
 assert eal.save_directory(BASE+'/PhysicsRecovery',only_if_is_dirty=False,recursive=True)
 path=physics.get_path_name().split('.')[0]
 physics_file=ROOT/'Content'/(path.removeprefix('/Game/')+'.uasset');assert physics_file.exists()
 mesh.modify();mesh.set_editor_property('physics_asset',physics);assert eal.save_loaded_asset(mesh)
 assert mesh.get_editor_property('physics_asset')==physics
 REPORT.update(success=True,mesh=mesh.get_path_name(),physics_asset=physics.get_path_name(),
               physics_file=str(physics_file),backup=str(backup),physics_sha256=hashlib.sha256(physics_file.read_bytes()).hexdigest())
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'BlackBoy_Physics_Dependency_Repair.json').write_text(json.dumps(REPORT,indent=2))
