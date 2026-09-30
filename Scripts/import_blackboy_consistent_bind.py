"""Import the verified consistent-bind candidate beside the original child assets."""
import hashlib,json,math
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
BASE='/Game/Carnival/Characters/Children/BlackBoy/Diagnostics/ConsistentBind'
REPORT={'success':False,'limits':'Candidate mesh/material binding only; requires fresh retarget and rendered review before production promotion.'}
prepared=json.loads((OUT/'BlackBoy_Consistent_Bind_FBX.json').read_text());assert prepared['success']
file=Path(prepared['prepared_fbx']);assert hashlib.sha256(file.read_bytes()).hexdigest()==prepared['prepared_sha256']
eal=unreal.EditorAssetLibrary;path=BASE+'/SK_BlackBoy_ConsistentBind'
mesh=unreal.load_asset(path) if eal.does_asset_exist(path) else None
if not mesh:
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 unreal.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
 options=unreal.FbxImportUI();options.automated_import_should_detect_type=False
 options.import_as_skeletal=True;options.import_mesh=True;options.import_animations=False
 options.import_materials=False;options.import_textures=False;options.create_physics_asset=True
 options.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH
 data=options.skeletal_mesh_import_data
 for key,value in [('convert_scene',True),('convert_scene_unit',True),('force_front_x_axis',False),('import_morph_targets',True),('update_skeleton_reference_pose',False),('use_t0_as_ref_pose',False)]:data.set_editor_property(key,value)
 task=unreal.AssetImportTask();task.filename=str(file);task.destination_path=BASE;task.destination_name=path.rsplit('/',1)[-1]
 task.automated=True;task.save=True;task.replace_existing=False;task.options=options
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);mesh=unreal.load_asset(path)
 assert mesh
 assert eal.save_directory(BASE,only_if_is_dirty=False,recursive=True)
 eal.set_metadata_tag(mesh,'CarnivalConsistentBindSourceSHA',prepared['prepared_sha256'])
else:assert eal.get_metadata_tag(mesh,'CarnivalConsistentBindSourceSHA')==prepared['prepared_sha256']
assert isinstance(mesh,unreal.SkeletalMesh)
old=json.loads((OUT/'BlackBoy_Unreal_Import.json').read_text());original=unreal.load_asset(old['mesh'])
assert mesh.skeleton!=original.skeleton
assert set(str(n) for n in mesh.skeleton.get_reference_pose().get_bone_names())==set(old['bones'])
original_slots={str(s.material_slot_name):s.material_interface for s in original.materials}
slots=list(mesh.materials);assert {str(s.material_slot_name) for s in slots}==original_slots.keys()
for slot in slots:slot.material_interface=original_slots[str(slot.material_slot_name)];assert slot.material_interface
mesh.modify();mesh.set_editor_property('materials',slots);assert eal.save_loaded_asset(mesh)
assert eal.save_loaded_asset(mesh.skeleton)
physics=mesh.get_editor_property('physics_asset');assert physics,'Missing saved physics dependency; run repair_blackboy_physics_dependency.py'
assert eal.save_loaded_asset(physics)
physics_path=physics.get_path_name().split('.')[0]
assert (ROOT/'Content'/(physics_path.removeprefix('/Game/')+'.uasset')).exists()
bounds=mesh.get_imported_bounds();origin=bounds.origin;extent=bounds.box_extent
assert 100<extent.z*2<210
REPORT.update(success=True,mesh=mesh.get_path_name(),skeleton=mesh.skeleton.get_path_name(),folder=BASE,
 bone_count=len(old['bones']),material_slot_count=len(slots),prepared_sha256=prepared['prepared_sha256'],
 mesh_bounds_cm={'minimum':(origin-extent).to_tuple(),'maximum':(origin+extent).to_tuple(),'height':extent.z*2})
(OUT/'BlackBoy_ConsistentBind_Import.json').write_text(json.dumps(REPORT,indent=2))
