"""Build a fresh isolated wardrobe composition; never edit the live collection."""
import hashlib,json,os,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
KIND=os.environ['CARNIVAL_BODY_OWNERSHIP_KIND'];assert KIND in ('Mixed','Parts')
OUT=ROOT/'Saved/CharacterRepairs/DeanBodyOwnershipBuild_20260930'/KIND;OUT.mkdir(parents=True,exist_ok=True)
FOLDER='/Game/Carnival/Crowd/BodySurfaceProof/Dean'+KIND
PACKAGE=FOLDER+'/DA_Dean'+KIND;INSTANCE=FOLDER+'/MHI_Dean'+KIND
assert not (ROOT/'Content'/(PACKAGE.removeprefix('/Game/')+'.uasset')).exists(),'Refuse to replace a prior proof'
REPORT={'success':False,'errors':[],'kind':KIND,'phase':'loading','new_packages':[],
 'limits':'Isolated Dean roster and wardrobe composition proof; does not change live crowd, density or runtime configuration. Build and geometry metadata require rendered actor/GPU validation.'}
def save():(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
def path(o):return o.get_path_name() if o else None
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def meshes(prefix):return {path(m):unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(m)
 for m in unreal.ObjectIterator(unreal.SkeletalMesh) if path(m).startswith(prefix)}
save()
try:
 assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 source=unreal.load_asset('/Game/Carnival/Crowd/Collections/DA_CarnivalCrowd_G1_FINAL2');assert source
 prefix=source.get_path_name()+':'
 files=[ROOT/'Content/Carnival/Crowd/Collections/DA_CarnivalCrowd_G1_FINAL2.uasset',ROOT/'Content/Carnival/MetaHumans/Dean.uasset',
 ROOT/'Content/Outfits/TshirtVariants/WI_OA_TshirtLngSlv.uasset',ROOT/'Content/Outfits/SlimJeansVariants/WI_OA_Jeans_slm.uasset',ROOT/'Content/Outfits/CasualSneakers/WI_OA_CasualSneakers.uasset']
 skeleton=source.get_editor_property('Pipeline').get_editor_property('EditorPipeline').get_editor_property('TargetSkeleton')
 skeleton_package=path(skeleton).split('.')[0]
 if skeleton_package.startswith('/Game/'):
  file=ROOT/'Content'/(skeleton_package.removeprefix('/Game/')+'.uasset')
  if file not in files:files.append(file)
 REPORT['source_hashes_before']={str(p):digest(p) for p in files}
 REPORT['source_meshes_before']=meshes(prefix)
 REPORT['source_slots']=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_collection_slots(source))
 unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(),'metahuman.crowd.DebugBodyMergeSlotOwnership 1')
 REPORT['phase']='building';save()
 selected=unreal.load_asset('/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean');assert selected
 collection,error=unreal.CarnivalCrowdMaterialEditorLibrary.build_body_ownership_proof(source,selected,PACKAGE,KIND=='Mixed')
 assert collection and not error,error
 REPORT['proof_slots']=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_collection_slots(collection))
 REPORT['phase']='binding_reviewed_skin';save()
 skin=json.loads((ROOT/'Saved/CharacterRepairs/DeanSkinSavedProof_20260930/index.json').read_text());assert skin['success']
 textures={}
 for row in skin['assets_saved']:
  assert digest(row['file'])==row['sha256'];textures[row['parameter']]=unreal.load_asset(row['asset']);assert textures[row['parameter']]
 ml=unreal.MaterialEditingLibrary;targets=[]
 for m in list(unreal.ObjectIterator(unreal.MaterialInstanceConstant)):
  if not path(m).startswith(collection.get_path_name()+':') or not m.get_name().startswith(('MI_Face_Dean_','MI_FaceCombo_Dean_')):continue
  for name,texture in textures.items():
   ml.set_material_instance_texture_parameter_value(m,name,texture)
   assert ml.get_material_instance_texture_parameter_value(m,name)==texture
  ml.set_material_instance_static_switch_parameter_value(m,'Use Baked Material',True);assert ml.get_material_instance_static_switch_parameter_value(m,'Use Baked Material')
  ml.update_material_instance(m);targets.append(path(m))
 assert targets,'No generated Dean head materials to bind';REPORT['reviewed_head_materials']=targets
 dean=unreal.load_asset('/Game/Carnival/MetaHumans/Dean');assert dean
 instance,error=unreal.CarnivalCrowdEditorLibrary.create_crowd_instance_asset(collection,dean,INSTANCE);assert instance and not error,error
 count,error=unreal.CarnivalCrowdMaterialEditorLibrary.select_body_ownership_proof_clothes(instance);assert count==3 and not error,(count,error)
 actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'DeanOwnershipProbe',unreal.Vector(),unreal.Rotator());assert actor and not error,error
 REPORT['components']=[]
 for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
  mesh=comp.get_editor_property('skeletal_mesh_asset')
  if mesh:REPORT['components'].append({'name':comp.get_name(),'initial_visibility':comp.is_visible(),'materials':[path(comp.get_material(i)) for i in range(comp.get_num_materials())],
    'geometry':json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_loaded_mesh_sections(mesh))})
 REPORT['source_meshes_after']=meshes(prefix);assert REPORT['source_meshes_before']==REPORT['source_meshes_after'],'Source loaded mesh structure changed'
 REPORT['phase']='saving_new_proofs';save()
 for obj in (collection,instance):
  assert path(obj).startswith(FOLDER+'/');assert unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False)
  file=ROOT/'Content'/(path(obj).split('.')[0].removeprefix('/Game/')+'.uasset');REPORT['new_packages'].append({'asset':path(obj),'file':str(file),'sha256':digest(file)})
 REPORT['source_hashes_after']={str(p):digest(p) for p in files};assert REPORT['source_hashes_before']==REPORT['source_hashes_after']
 for image in (ROOT/'Saved').glob('SlotOwnership_DA_Dean'+KIND+'*.png'):shutil.copy2(image,OUT/image.name)
 REPORT.update(success=True,phase='complete',collection=path(collection),instance=path(instance))
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:save()
