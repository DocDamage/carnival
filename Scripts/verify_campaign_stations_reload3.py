"""Fresh-load check of every saved campaign station actor and prop; no saves."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
SRC=ROOT/'Saved/CampaignAcceptance/CampaignStationsAuthored3_20260930/index.json'
R={'success':False,'errors':[],'assets_saved':False,'stations':[]}
try:
 authored=json.loads(SRC.read_text());assert authored['success']
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 actors={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
 for p in authored['placed']:
  for a in p['actors']:
   st=actors[a['label']]
   assert p['level'] in st.get_path_name(),a['label']
   assert str(st.get_editor_property('campaign_station_id'))==p['station'] and st.get_editor_property('campaign_action')==a['action'],a['label']
   assert abs(st.get_editor_property('interaction_radius')-a['radius'])<.01,a['label']
   prop=actors.get(a['label']+'_Prop')
   R['stations'].append({'label':a['label'],'location':list(st.get_actor_location().to_tuple()),
    'prop':prop.static_mesh_component.static_mesh.get_path_name() if prop else None,
    'prop_collision':str(prop.static_mesh_component.get_collision_profile_name()) if prop else None})
 R['success']=len(R['stations'])==sum(len(p['actors']) for p in authored['placed'])
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(SRC.parent/'Reload.json').write_text(json.dumps(R,indent=1))
