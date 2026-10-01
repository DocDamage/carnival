"""Native-equivalent focus check for the records desk: trace to target pivot+40, ignoring the target."""
import json,math,sys,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();sys.path.insert(0,str(ROOT/'Scripts'))
from industrial_hospital_route_config import MAIN_MAP,HOSPITAL_YAW,hospital_level_transform,rotate_xy
OUT=ROOT/'Saved/CampaignAcceptance/HospitalRecordsDeskTopFocus_20260930';OUT.mkdir(parents=True,exist_ok=False)
R={'success':False,'errors':[],'assets_saved':False,'candidates':[]}
def wp(p):
 o=hospital_level_transform();x,y=rotate_xy(p,HOSPITAL_YAW);return unreal.Vector(o[0]+x,o[1]+y,o[2]+p[2])
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
name=lambda h:h[9].get_actor_label() if h and h[9] else ''
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP)
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 desk=next(a for a in EA.get_all_level_actors() if a.get_actor_label()=='BP_Desk_01c9' and 'L_IndustrialHospitalSetDress' in a.get_path_name())
 o,e=desk.get_actor_bounds(False)
 # Station sits on the desk-top centre; native focus traces to its location+40 ignoring only the station.
 pivot=unreal.Vector(o.x,o.y,o.z+e.z)
 R.update(station_world_cm=list(pivot.to_tuple()),desk_bounds_origin=list(o.to_tuple()),desk_bounds_extent=list(e.to_tuple()))
 c=json.loads((ROOT/'Saved/IndustrialHospital/Hospital_Room_Connectivity.json').read_text())
 nodes=c['components'][c['entrance_component']]['nodes']
 for node in sorted(nodes,key=lambda n:math.dist(n,(1760,1190)))[:25]:
  f=t(unreal.SystemLibrary.line_trace_single(world,wp((*node,150)),wp((*node,0)),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
  if not f or f[7].z<.707:continue
  center=f[5]+unreal.Vector(0,0,98)
  cap=t(unreal.SystemLibrary.capsule_trace_single(world,center,center+unreal.Vector(0,0,.1),42,96,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
  los=t(unreal.SystemLibrary.line_trace_single(world,center+unreal.Vector(0,0,50),pivot+unreal.Vector(0,0,40),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
  R['candidates'].append({'node':node,'approach_world_cm':list(center.to_tuple()),'distance_to_pivot_cm':(center-pivot).length(),
   'capsule_blocker':name(cap) if cap else None,'capsule_clear':not cap,'focus_blocker':name(los) if los else None,'focus_clear':not los})
 R['success']=any(x['capsule_clear'] and x['focus_clear'] for x in R['candidates'])
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=2))
