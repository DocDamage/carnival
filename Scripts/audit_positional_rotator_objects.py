"""Read-only: actual rotations of objects placed by scripts that used positional unreal.Rotator(0, yaw, 0)."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
R={'success':False,'errors':[],'actors':[],'player_mesh':None}
try:
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  l=a.get_actor_label()
  if l.startswith(('Stunt_','Boat_','Hovercraft_','Mission_Foyer_Eli_Physical_Note')) or isinstance(a,(unreal.CarnivalBoat,unreal.CarnivalHovercraft)):
   r=a.get_actor_rotation();o,e=a.get_actor_bounds(False)
   R['actors'].append({'label':l,'class':a.get_class().get_name(),'level':a.get_level().get_outermost().get_name().split('/')[-1],
    'roll':round(r.roll,2),'pitch':round(r.pitch,2),'yaw':round(r.yaw,2),'location':[round(v) for v in a.get_actor_location().to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
 bp=unreal.load_asset('/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter')
 if bp:
  cdo=unreal.get_default_object(bp.generated_class())
  mesh=cdo.get_editor_property('mesh')
  r=mesh.get_editor_property('relative_rotation')
  R['player_mesh']={'mesh':mesh.get_editor_property('skeletal_mesh_asset').get_path_name() if mesh.get_editor_property('skeletal_mesh_asset') else None,'roll':r.roll,'pitch':r.pitch,'yaw':r.yaw}
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(ROOT/'Saved/CampaignAcceptance/PositionalRotatorAudit_20261001.json').write_text(json.dumps(R,indent=1))
