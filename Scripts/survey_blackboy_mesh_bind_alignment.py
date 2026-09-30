"""Read actual IKRig mesh bind transforms against source and two idle clips."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');OUT=ROOT/'Saved/CharacterAcceptance/ChildSources'
REPORT={'success':False,'rigs':[],'errors':[]}
BASE='/Game/Carnival/Characters/Children/BlackBoy'
census=json.loads((OUT/'Child_Animation_Source_Census.json').read_text())
source=next(a['path'] for a in census['animations'] if a['name']=='MM_Idle')
children=json.loads((OUT/'Child_Guest_Blueprints.json').read_text())['children']
target=next(c['mesh'] for c in children if c['identity']=='BlackBoy')
try:
 for label,rig_path,mesh_path,clips,bones in [
  ('Manny',BASE+'/Retarget/IK_Source_Manny','/Game/PlayMusicAnim/Demo/Mannequins/Meshes/SKM_Manny',[source],
   ['pelvis','spine_05','clavicle_l','upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r']),
  ('BlackBoy',BASE+'/Retarget/IK_BlackBoy',target,[BASE+'/Animations/Child_Manny_MM_Idle',BASE+'/Diagnostics/Comparison_MM_Idle_ReferenceAlignment'],
   ['Pelvis','Spine02','L_Clavicle','L_Upperarm','L_Forearm','L_Hand','L_UpperarmTwist01','L_UpperarmTwist02','R_Clavicle','R_Upperarm','R_Forearm','R_Hand'])]:
  ctrl=unreal.IKRigController.get_controller(unreal.load_asset(rig_path));mesh=unreal.load_asset(mesh_path)
  options=unreal.AnimPoseEvaluationOptions();options.optional_skeletal_mesh=mesh;options.should_retarget=True
  row={'identity':label,'mesh':mesh_path,'bind':{},'clips':[]}
  def transform(tx):return {'translation':tx.translation.to_tuple(),'rotation':tx.rotation.to_tuple()}
  for bone in bones:row['bind'][bone]=transform(ctrl.get_ref_pose_transform_of_bone(bone))
  for path in clips:
   clip=unreal.load_asset(path);assert clip
   pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(clip,clip.get_editor_property('sequence_length')*.4,options)
   row['clips'].append({'asset':path,'bones':{bone:transform(pose.get_bone_pose(bone,unreal.AnimPoseSpaces.WORLD)) for bone in bones}})
  REPORT['rigs'].append(row)
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc())
(OUT/'BlackBoy_MeshBind_Alignment_Survey.json').write_text(json.dumps(REPORT,indent=2))
