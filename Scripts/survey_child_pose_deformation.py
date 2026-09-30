"""Read-only bind/animated rotations, alignment offsets and material bindings."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
REPORT={'success':False,'meshes':[],'retargeters':[],'errors':[]}
census=json.loads((OUT/'Child_Animation_Source_Census.json').read_text())
try:
 for child in census['children']:
  mesh=unreal.load_asset(child['mesh']);ref=mesh.skeleton.get_reference_pose()
  options=unreal.AnimPoseEvaluationOptions();options.optional_skeletal_mesh=mesh
  options.should_retarget=True;options.incorporate_root_motion_into_pose=True
  clip=unreal.load_asset('/Game/Carnival/Characters/Children/'+child['identity']+'/Animations/Child_Manny_MM_Idle')
  animated=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,clip.get_editor_property('sequence_length')*.4,options)
  bones=[]
  for n in ref.get_bone_names():
   name=str(n)
   if not any(x in name.lower() for x in ('arm','clavicle','ribs','eye')):continue
   row={'bone':name}
   for label,pose in [('reference',ref),('idle',animated)]:
    tx=pose.get_bone_pose(n,unreal.AnimPoseSpaces.LOCAL)
    row[label]={'translation':tx.translation.to_tuple(),'rotation':tx.rotation.to_tuple(),'scale':tx.scale3d.to_tuple()}
   bones.append(row)
  materials=[]
  for slot in mesh.materials:
   if not any(x in str(slot.material_slot_name).lower() for x in ('eye','skin','shirt','top')):continue
   asset=slot.material_interface;chain=[asset.get_path_name()];root=asset
   while isinstance(root,unreal.MaterialInstance):
    root=root.get_editor_property('parent');chain.append(root.get_path_name())
   mel=unreal.MaterialEditingLibrary
   params=[]
   for name in mel.get_texture_parameter_names(asset):
    tx=mel.get_material_instance_texture_parameter_value(asset,name) if isinstance(asset,unreal.MaterialInstance) else mel.get_material_default_texture_parameter_value(root,name)
    params.append({'name':str(name),'texture':tx.get_path_name() if tx else None})
   materials.append({'slot':str(slot.material_slot_name),'chain':chain,'textures':params,
    'blend_mode':str(root.get_editor_property('blend_mode')),'shading_model':str(root.get_editor_property('shading_model'))})
  REPORT['meshes'].append({'identity':child['identity'],'bones':bones,'materials':materials})
  for group in ('Manny','RamsterZ','SeatedSource'):
   asset=unreal.load_asset('/Game/Carnival/Characters/Children/'+child['identity']+'/Retarget/RTG_'+group+'_To_'+child['identity'])
   ctrl=unreal.IKRetargeterController.get_controller(asset)
   offsets=[]
   for row in bones:
    offset=ctrl.get_rotation_offset_for_retarget_pose_bone(row['bone'],unreal.RetargetSourceOrTarget.TARGET)
    offsets.append({'bone':row['bone'],'rotation':offset.to_tuple()})
   REPORT['retargeters'].append({'identity':child['identity'],'group':group,'offsets':offsets})
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'Child_Pose_Deformation_Survey.json').write_text(json.dumps(REPORT,indent=2))
