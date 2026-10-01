"""Fresh-load check of the saved hospital campaign station actors; no saves."""
import json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
SRC=ROOT/'Saved/CampaignAcceptance/HospitalStationsAuthoredDeskTop_20260930/index.json'
R={'success':False,'errors':[],'assets_saved':False,'stations':[]}
try:
 authored=json.loads(SRC.read_text());assert authored['success']
 unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 actors={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
  if isinstance(a,unreal.CarnivalMissionInteractionActor) and 'L_IndustrialHospitalSetDress' in a.get_path_name()}
 for s in authored['stations']:
  a=actors[s['label']];t=a.get_editor_property('interaction_target_actor')
  r={'label':s['label'],'station_id':str(a.get_editor_property('campaign_station_id')),
   'interaction':str(a.get_editor_property('interaction')),'radius_cm':a.get_editor_property('interaction_radius'),
   'target':t.get_actor_label() if t else s['label'],'location':list(a.get_actor_location().to_tuple())}
  assert r['station_id']==s['station'] and r['radius_cm']==s['radius_cm'] and r['target']==s['target'],json.dumps(r)
  assert 'CAMPAIGN_STATION' in r['interaction'],r['interaction']
  R['stations'].append(r)
 R['success']=len(R['stations'])==3
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(SRC.parent/'Reload.json').write_text(json.dumps(R,indent=2))
