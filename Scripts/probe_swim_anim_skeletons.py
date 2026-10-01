"""Read-only: can the FreeAnimationLibrary swim animations play on the player's skeleton? Compares bone
names and reference poses, lists slot names used by the player's AnimBP and any IK retargeters. No saves."""
import json,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\CharacterRepairs\SwimAnimSkeletons_20261001.json')
R={'errors':[]}
AR=unreal.AssetRegistryHelpers.get_asset_registry()
try:
 player=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
 swim=unreal.load_asset('/Game/FreeAnimationLibrary/Animations/Swim/anim_Swim_Surface_Fwd')
 ps=player.skeleton;ss=swim.get_editor_property('skeleton')
 R['player_skeleton']=ps.get_path_name();R['swim_skeleton']=ss.get_path_name()
 def bones(sk_mesh):
  return [str(sk_mesh.get_bone_name(i)) for i in range(sk_mesh.get_num_bones())] if hasattr(sk_mesh,'get_num_bones') else None
 lib=unreal.SkeletalMeshEditorSubsystem if hasattr(unreal,'SkeletalMeshEditorSubsystem') else None
 swim_mesh=unreal.load_asset('/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny') or None
 R['swim_folder_meshes']=[str(a.package_name) for a in AR.get_assets_by_path('/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes',True)]
 # Bone names via the reference skeleton exposed on skeletal meshes.
 def mesh_bones(m):
  try:
   n=m.get_editor_property('skeleton') and None
  except Exception:pass
  out=[]
  try:
   i=0
   while True:
    b=unreal.SkeletalMeshLibrary if False else None
    break
  except Exception:pass
  return out
 R['player_bone_count_api']=hasattr(player,'get_bone_name')
 try:
  R['player_bones']=[str(player.get_bone_name(i)) for i in range(player.get_num_bones())]
 except Exception as e:R['player_bones_err']=str(e)
 for p in R['swim_folder_meshes']:
  m=unreal.load_asset(p)
  if isinstance(m,unreal.SkeletalMesh):
   try:R.setdefault('swim_meshes',{})[p]={'skeleton':m.skeleton.get_path_name(),'bones':[str(m.get_bone_name(i)) for i in range(m.get_num_bones())]}
   except Exception as e:R.setdefault('swim_meshes',{})[p]={'err':str(e)}
 try:R['compatible_skeletons_player']=[s.get_path_name() for s in ps.get_editor_property('compatible_skeletons')]
 except Exception as e:R['compatible_err']=str(e)
 R['retargeters']=[str(a.package_name) for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/IKRig','IKRetargeter'))][:40]
 R['ikrigs']=[str(a.package_name) for a in AR.get_assets_by_class(unreal.TopLevelAssetPath('/Script/IKRig','IKRigDefinition'))][:40]
 abp=unreal.load_asset('/Game/Carnival/Character/Animations/ABP_CarnivalManny')
 R['abp_skeleton']=abp.get_editor_property('target_skeleton').get_path_name() if abp else None
 try:R['slot_groups']=[str(g.get_editor_property('group_name'))+':'+','.join(str(s) for s in g.get_editor_property('slot_names')) for g in ps.get_editor_property('slot_groups')]
 except Exception as e:R['slot_err']=str(e)
 swims=[a for a in AR.get_assets_by_path('/Game/FreeAnimationLibrary/Animations/Swim',True)]
 R['swim_assets']=[(str(a.asset_name),str(a.asset_class_path.asset_name)) for a in swims]
 R['anim_lengths']={str(a.asset_name):round(unreal.load_asset(str(a.package_name)).get_play_length(),2) for a in swims if str(a.asset_class_path.asset_name)=='AnimSequence'}
except Exception:R['errors'].append(traceback.format_exc())
OUT.write_text(json.dumps(R,indent=1))
