"""Find supported, unobstructed approaches to reviewed physical hospital clues."""
import hashlib,json,math,sys,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();sys.path.insert(0,str(ROOT/'Scripts'))
from industrial_hospital_route_config import MAIN_MAP,HOSPITAL_YAW,hospital_level_transform,rotate_xy
OUT=ROOT/'Saved/CampaignAcceptance/HospitalStationApproachesDiagnosed_20260930';OUT.mkdir(parents=True,exist_ok=False)
REPORT={'success':False,'errors':[],'assets_saved':False,'stations':[],
 'limits':'Editor floor, capsule and sight-line preflight. Does not establish actual character focus, walking/return or rendered station readability.'}
def wp(p):
 o=hospital_level_transform();x,y=rotate_xy(p,HOSPITAL_YAW)
 return unreal.Vector(o[0]+x,o[1]+y,o[2]+p[2])
def actor_name(h):
 a=h[9] if h and len(h)>9 else None
 return a.get_actor_label() if a else ''
def hit(v):
 data=v.to_tuple() if v else None
 return data if data and data[0] else None
try:
 f=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap';before=hashlib.sha256(f.read_bytes()).hexdigest()
 world=unreal.EditorLoadingAndSavingUtils.load_map(MAIN_MAP);assert world
 c=json.loads((ROOT/'Saved/IndustrialHospital/Hospital_Room_Connectivity.json').read_text())
 nodes=c['components'][c['entrance_component']]['nodes']
 proposals=[('hospital_reception','Visiting pass',(5550,-39,225),250,'BP_InfoBoard_03a'),
  ('hospital_ward',"Eli's account",(9700,-3544,215),350,'BP_InfoBoard_03a7'),
  ('hospital_records','Utility chart',(1760,1190,170),250,'BP_Desk_01c9')]
 for id,label,local,radius,furnishing in proposals:
  p=wp(local);found=None;rejected=[]
  for node in sorted(nodes,key=lambda n:math.dist(n,local[:2])):
   if math.dist(node,local[:2])>radius:break
   floor=hit(unreal.SystemLibrary.line_trace_single(world,wp((*node,150)),wp((*node,0)),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
   if not floor or floor[7].z<.707:rejected.append({'node':node,'reason':'no_walkable_floor'});continue
   center=floor[5]+unreal.Vector(0,0,98)
   if (center-p).length()>radius:rejected.append({'node':node,'reason':'outside_radius','distance_cm':(center-p).length()});continue
   blocked=hit(unreal.SystemLibrary.capsule_trace_single(world,center,center+unreal.Vector(0,0,.1),42,96,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
   if blocked:rejected.append({'node':node,'reason':'capsule_blocked','by':actor_name(blocked)});continue
   los=hit(unreal.SystemLibrary.line_trace_single(world,center+unreal.Vector(0,0,50),p+unreal.Vector(0,0,40),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True))
   # The sight line ends on the clue itself; a hit on that furnishing, or
   # within a few cm of the endpoint, is the clue being seen, not an occluder.
   if los and not (furnishing in actor_name(los) or (los[4]-(p+unreal.Vector(0,0,40))).length()<25):
    rejected.append({'node':node,'reason':'sight_line_blocked','by':actor_name(los)});continue
   found={'station':id,'label':label,'clue_local_cm':local,'clue_world_cm':list(p.to_tuple()),
    'interaction_radius_cm':radius,'furnishing':furnishing,'approach_local_node':node,
    'approach_world_cm':list(center.to_tuple()),'capsule_clear':True,'sight_line_clear':True,
    'sight_line_terminates_on':actor_name(los) if los else None,'rejected_nearer_nodes':rejected}
   break
  if not found:REPORT['stations'].append({'station':id,'rejected_nodes':rejected})
  assert found,'No clear approach to '+id
  REPORT['stations'].append(found)
 REPORT['map_sha256_before']=before;REPORT['map_sha256_after']=hashlib.sha256(f.read_bytes()).hexdigest();assert REPORT['map_sha256_after']==before
 REPORT['success']=True
except Exception:REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
