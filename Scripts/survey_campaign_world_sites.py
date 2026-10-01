"""Read the connected world and probe draft hospital stations without saving."""
import hashlib,json,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CampaignAcceptance'/os.environ.get('CARNIVAL_CAMPAIGN_SURVEY','ConnectedWorldSites_20260930')
OUT.mkdir(parents=True,exist_ok=False)
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
REPORT={'success':False,'errors':[],'assets_saved':False,'map':MAP,'levels':[],'landmarks':[],'hospital_candidates':[],
 'limits':'Loaded editor actors and collision-probed draft approaches only. Room designation, production placement, runtime focus and complete travel/return remain required.'}
def vec(v):return list(v.to_tuple())
try:
 before=hashlib.sha256(MAPFILE.read_bytes()).hexdigest()
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAP);assert world
 for level in unreal.EditorLevelUtils.get_levels(world):REPORT['levels'].append(level.get_path_name())
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 REPORT['loaded_actor_count']=len(actors)
 # Record fixed interfaces and landmarks, not thousands of unrelated set-dressing objects.
 for actor in actors:
  label=actor.get_actor_label()
  if isinstance(actor,unreal.CarnivalMissionInteractionActor) or any(word in label.lower() for word in ('hospital','dock','laboratory','prison','lighthouse','noticeboard')):
   origin,extent=actor.get_actor_bounds(False)
   REPORT['landmarks'].append({'label':label,'path':actor.get_path_name(),'class':actor.get_class().get_name(),
    'location_cm':vec(actor.get_actor_location()),'bounds_origin_cm':vec(origin),'bounds_extent_cm':vec(extent)})
 routes=json.loads((ROOT/'Saved/IndustrialHospital/Hospital_Candidate_Routes.json').read_text())
 draft=[('hospital_reception',next(iter(routes['routes'].values()))['candidate_floor_points_cm'][0]),
  ('hospital_ward',routes['routes']['hospital_corridor_west']['candidate_floor_points_cm'][-1]),
  ('hospital_records',routes['routes']['hospital_corridor_east']['candidate_floor_points_cm'][-1])]
 for station,point in draft:
  floor=unreal.Vector(*point)
  hit=unreal.SystemLibrary.line_trace_single(world,floor+unreal.Vector(0,0,180),floor-unreal.Vector(0,0,120),
   unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
  data=hit.to_tuple() if hit else None
  row={'station':station,'candidate_from_prior_route_cm':point,'floor_hit':bool(data and data[0])}
  if row['floor_hit']:
   location=data[5];center=location+unreal.Vector(0,0,98)
   clearance=unreal.SystemLibrary.capsule_trace_single(world,center,center+unreal.Vector(0,0,.1),42,96,
    unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
   c=clearance.to_tuple() if clearance else None
   row.update(floor_cm=vec(location),approach_cm=vec(center),capsule_clear=not bool(c and c[0]))
  REPORT['hospital_candidates'].append(row)
 REPORT['map_sha256_before']=before;REPORT['map_sha256_after']=hashlib.sha256(MAPFILE.read_bytes()).hexdigest()
 assert REPORT['map_sha256_after']==before
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
