"""Check complete source/converted clips on actual assembled body/outfit meshes; save no assets."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=ROOT/'Saved/CharacterRepairs/DeanConvertedAnimationNeutralReference_20260930';OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'index.json').exists(),'Preserve existing agreement evidence'
REPORT={'success':False,'errors':[],'assets_saved':False,'samples_per_clip':65,'tolerance_cm':.1,'rotation_tolerance_degrees':.1,'comparisons':[],
 'limits':'Complete duration, every raw body/outfit mesh bone, native GetAnimationPose evaluation. No GPU rendered/face postprocess/cloth simulation/all-character/continuous gameplay acceptance.'}
def path(o):return o.get_path_name() if o else None
files=[ROOT/'Content'/p for p in ('Carnival/Crowd/ClothingFamilies/G1Parts/DA_CarnivalCrowd_G1_Parts.uasset',
 'Carnival/Crowd/ClothingFamilies/G1Parts/Instances/MHI_Dean.uasset',
 'Town/Demo/Characters/Mannequins/Animations/Manny/MM_Idle.uasset',
 'Town/Demo/Characters/Mannequins/Animations/Manny/MM_Walk_InPlace.uasset','Town/Demo/Characters/Mannequins/Meshes/SK_Mannequin.uasset')]
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
try:
 REPORT['hashes_before']=hashes();assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
 instance=unreal.load_asset('/Game/Carnival/Crowd/ClothingFamilies/G1Parts/Instances/MHI_Dean');assert instance
 actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'AgreementDean',unreal.Vector(),unreal.Rotator());assert actor and not error,error
 meshes=[c.get_editor_property('skeletal_mesh_asset') for c in actor.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='Body' or c.get_name().startswith('Outfit')]
 assert len(meshes)==4 and all(meshes)
 collection=path(instance.get_meta_human_collection());keep=[]
 for name,source_name in (('Idle','MM_Idle'),('Walk','MM_Walk_InPlace')):
  source=unreal.load_asset('/Game/Town/Demo/Characters/Mannequins/Animations/Manny/'+source_name)
  baked=unreal.load_object(None,collection+':AS_'+name);assert source and baked
  converted,error=unreal.CarnivalCrowdMaterialEditorLibrary.make_animation_space_conversion_proof(baked,source);assert converted and not error,error
  keep += [converted,converted.get_skeleton()]
  for mesh in meshes:
   baseline,error=unreal.CarnivalCrowdMaterialEditorLibrary.describe_animation_pose_agreement(mesh,source,baked,65);assert not error,error
   result,error=unreal.CarnivalCrowdMaterialEditorLibrary.describe_animation_pose_agreement(mesh,source,converted,65);assert not error,error
   normalized,error=unreal.CarnivalCrowdMaterialEditorLibrary.describe_animation_pose_agreement(mesh,source,converted,65,normalize_unanimated_source_bones=True);assert not error,error
   row={'animation':name,'baseline':json.loads(baseline),'converted_raw_reference':json.loads(result),'converted':json.loads(normalized)};REPORT['comparisons'].append(row)
   (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
 REPORT['hashes_after']=hashes();assert REPORT['hashes_before']==REPORT['hashes_after'];REPORT['success']=True
 violations=[r['converted'] for r in REPORT['comparisons'] if r['converted']['maximum_bone_position_error_cm']>REPORT['tolerance_cm'] or r['converted']['maximum_bone_rotation_error_degrees']>REPORT['rotation_tolerance_degrees']]
 assert not violations,'Full-bone agreement failed on '+str(len(violations))+' comparisons'
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:
 REPORT['hashes_after']=hashes();REPORT['success']=not REPORT['errors'] and REPORT.get('hashes_before')==REPORT['hashes_after']
 (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
