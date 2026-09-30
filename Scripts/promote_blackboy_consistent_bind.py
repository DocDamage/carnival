"""Use the checked bind correction for the existing owned child guest class.

Preserve original mesh/skeleton/clips and back up Blueprint/manifest. Seating,
full gait and face material acceptance remain open, as recorded by the preview.
"""
import datetime,json,shutil
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
preview=json.loads((ROOT/'Saved/CharacterAcceptance/ChildPreview/BlackBoyConsistentBind/index.json').read_text())
assert preview['capture_success'] and preview['engine_exit_code']==0
assert all(preview['visual_review']['poses'][pose]['success'] for pose in ('Reference','Idle','Walk'))
candidate=json.loads((OUT/'BlackBoy_ConsistentBind_Import.json').read_text());assert candidate['success']
guest=json.loads((OUT/'BlackBoy_ConsistentBind_Guest.json').read_text());assert guest['success']
row=guest['children'][0];assert row['identity']=='BlackBoy'
REPORT={'success':False,'limits':'Working guest body/idle correction only. Full gait, eye closeups, roaming, clothing across all motion and ride seat fitting remain open.'}
path='/Game/Carnival/Characters/Children/BlackBoy/BP_ChildGuest_BlackBoy'
eal=unreal.EditorAssetLibrary;blueprint=unreal.load_asset(path)
assert eal.get_metadata_tag(blueprint,'CarnivalChildIdentity')=='BlackBoy'
backup=OUT/'Backups'/('ConsistentBindPromotion_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
source_report=OUT/'Child_Guest_Blueprints.json'
original_manifest=json.loads(source_report.read_text());assert original_manifest['success']
override_file=OUT/'Child_Rig_Overrides.json'
files=[ROOT/'Content'/(path.removeprefix('/Game/')+'.uasset'),source_report]
if override_file.exists():files.append(override_file)
for file in files:
 destination=backup/file.name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,destination)
mesh=unreal.load_asset(row['mesh']);idle=unreal.load_asset(row['idle'])
assert idle.get_editor_property('skeleton')==mesh.skeleton
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem);data=unreal.SubobjectDataBlueprintFunctionLibrary
components={}
for handle in sds.k2_gather_subobject_data_for_blueprint(blueprint):
 obj=data.get_associated_object(data.get_data(handle))
 if isinstance(obj,unreal.SkeletalMeshComponent):components['mesh']=obj
 elif isinstance(obj,unreal.CapsuleComponent):components['capsule']=obj
body=components['mesh'];body.modify();body.set_skeletal_mesh_asset(mesh)
body.set_relative_location(unreal.Vector(*row['mesh_relative_location_cm']),False,False)
body.override_animation_data(idle,True,True,0,1)
capsule=components['capsule'];capsule.modify();capsule.set_capsule_size(row['capsule_radius_cm'],row['capsule_half_height_cm'],False)
eal.set_metadata_tag(blueprint,'CarnivalChildRigRevision','ConsistentBind_20260929')
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint);assert eal.save_loaded_asset(blueprint)
cdo=unreal.get_default_object(blueprint.generated_class())
assert cdo.get_editor_property('mesh').get_editor_property('skeletal_mesh_asset')==mesh
actual=dict(row,blueprint=path,**{'class':blueprint.generated_class().get_path_name()})
original_manifest['children']=[actual if c['identity']=='BlackBoy' else c for c in original_manifest['children']]
source_report.write_text(json.dumps(original_manifest,indent=2))
overrides=json.loads(override_file.read_text()) if override_file.exists() else {}
overrides['BlackBoy']={'mesh':candidate['mesh'],'mesh_bounds_cm':candidate['mesh_bounds_cm'],
 'folder':candidate['folder'],'animation_folder':candidate['folder']+'/Animations',
 'revision':'ConsistentBind_20260929','acceptance_limits':REPORT['limits']}
override_file.write_text(json.dumps(overrides,indent=2))
REPORT.update(success=True,blueprint=path,mesh=row['mesh'],idle=row['idle'],backup=str(backup),rig_overrides=str(override_file),original_assets_retained=True)
(OUT/'BlackBoy_ConsistentBind_Promotion.json').write_text(json.dumps(REPORT,indent=2))
