"""Retarget the FreeAnimationLibrary swim animations (UE5 Manny, demo skeleton) onto the player's skeleton
(Gladiator SK_Mannequin) with the stock Manny->Manny retargeter, into /Game/Carnival/Character/Animations/Swim.
Source assets are untouched; only the new animation packages are saved."""
import json,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\CharacterRepairs\SwimRetarget_20261001');OUT.mkdir(parents=True,exist_ok=False)
DEST='/Game/Carnival/Character/Animations/Swim'
NAMES=['anim_SwimIdle','anim_Swim_Surface_Fwd','anim_Swim_Surface_Left','anim_Swim_Surface_Right']
R={'success':False,'errors':[],'assets':{}}
EAL=unreal.EditorAssetLibrary
try:
 src_mesh=unreal.load_asset('/Game/FreeAnimationLibrary/Demo/Characters/Mannequins/Meshes/SKM_Manny_Simple')
 dst_mesh=unreal.load_asset('/Game/Gladiator_Arena/Demo/StarterContent/Characters/Mannequins/Meshes/SKM_Manny_Simple')
 rtg=unreal.load_asset('/Game/Mansion/Demo/Characters/Mannequins/Rigs/RTG_Mannequin')
 assert src_mesh and dst_mesh and rtg
 R['retargeter_source']=str(rtg.get_editor_property('source_ik_rig_asset') if hasattr(rtg,'get_editor_property') else '')[:200] if False else None
 for n in NAMES:
  if EAL.does_asset_exist(DEST+'/'+n):raise RuntimeError('already exists: '+DEST+'/'+n)
 AR=unreal.AssetRegistryHelpers.get_asset_registry()
 data=[AR.get_asset_by_object_path('/Game/FreeAnimationLibrary/Animations/Swim/%s.%s'%(n,n)) for n in NAMES]
 made=unreal.IKRetargetBatchOperation.duplicate_and_retarget(data,src_mesh,dst_mesh,rtg,search='',replace='',prefix='',suffix='',target_path=DEST,use_source_path=False,include_referenced_assets=False,overwrite_existing_files=False)
 R['made']=[str(a.package_name) for a in made]
 for a in made:
  p=str(a.package_name);base=p.split('/')[-1]
  if not base.startswith('anim_'):continue
  assert p==DEST+'/'+base,p
  asset=unreal.load_asset(DEST+'/'+base)
  R['assets'][base]={'path':DEST+'/'+base,'skeleton':asset.get_editor_property('skeleton').get_path_name(),'length':round(asset.get_play_length(),3)}
  EAL.save_asset(DEST+'/'+base,False)
 assert len(R['assets'])==len(NAMES),R['assets']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
