import json,unreal
out={}
bp=unreal.load_asset('/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter')
cdo=unreal.get_default_object(bp.generated_class());mesh=cdo.get_editor_property('mesh')
out['mesh']=mesh.get_editor_property('skeletal_mesh_asset').get_path_name() if mesh.get_editor_property('skeletal_mesh_asset') else None
ac=mesh.get_editor_property('anim_class');out['anim_class']=ac.get_path_name() if ac else None
AR=unreal.AssetRegistryHelpers.get_asset_registry()
for p in ('/Game/FreeAnimationLibrary/Animations/Swim/anim_SwimIdle','/Game/FreeAnimationLibrary/Animations/Swim/anim_Swim_Surface_Fwd'):
 refs=AR.get_referencers(p,unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True)) or []
 out['referencers:'+p.split('/')[-1]]=[str(r) for r in refs]
 a=unreal.load_asset(p);out['skeleton:'+p.split('/')[-1]]=a.get_editor_property('skeleton').get_path_name() if a else None
open(r'F:\Carnival\Saved\CharacterRepairs\SwimSetup_20261001.json','w').write(json.dumps(out,indent=1))
