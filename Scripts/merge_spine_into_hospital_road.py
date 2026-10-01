"""Merge the outer spine's last stretch onto the hospital road instead of hovering above it.

Segments 1155-1165 lie wholly over SM_IndustrialHospital_Road_0x 30-95 cm above its descending
surface, obstructing road traffic (motorcycle wedge at StaticMeshActor_1163). They are laid flush on
the sampled road surface (+2 cm) and pitched to follow it. Segments 1145-1154 (open ground beneath)
descend linearly from segment 1144's end to segment 1155's start. Only the connectors level is saved.
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_Connections_Layout'
LEVEL_FILE=ROOT/'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/SpineHospitalRoadMerge_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE;HALF_T=22.5
R={'success':False,'errors':[],'segments':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 R.update(level_sha256_before=sha(LEVEL_FILE),map_sha256_before=sha(MAPFILE));shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_road_merge.umap'))
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 allsegs=[a for a in EA.get_all_level_actors() if a.get_actor_label()=='OuterRoute_Segment']
 by={a.get_name():a for a in allsegs}
 def seg(i):return by['StaticMeshActor_%d'%i]
 def ends(a,toward_next):
  """Start/end XY of a segment along the route direction (start toward lower index)."""
  c=a.get_actor_location();f=a.get_actor_forward_vector();L=a.get_actor_scale3d().x*100
  sgn=1 if (f.x*toward_next.x+f.y*toward_next.y)>=0 else -1
  return V(c.x-f.x*L/2*sgn,c.y-f.y*L/2*sgn,0),V(c.x+f.x*L/2*sgn,c.y+f.y*L/2*sgn,0),sgn,L
 def road_z(p,ref):
  h=t(unreal.SystemLibrary.line_trace_single(world,V(p.x,p.y,ref+300),V(p.x,p.y,ref-400),TQ,False,allsegs,N,True))
  assert h and 'IndustrialHospital_Road' in (h[9].get_actor_label() if h[9] else ''),'No hospital road under %s'%p
  return h[5].z
 targets={}
 # Flush segments 1155..1165: follow the road surface.
 for i in range(1155,1166):
  a=seg(i);nxt=seg(i+1) if 'StaticMeshActor_%d'%(i+1) in by else None
  d=(nxt.get_actor_location()-a.get_actor_location()) if nxt else (a.get_actor_location()-seg(i-1).get_actor_location())
  s,e,sgn,L=ends(a,d);c=a.get_actor_location()
  targets[i]=(s,e,road_z(s,c.z)+2,road_z(e,c.z)+2,sgn,L)
 # Ramp 1145..1154 from 1144's end top to 1155's start top.
 a44=seg(1144);s44,e44,_,_=ends(a44,seg(1145).get_actor_location()-a44.get_actor_location())
 top44=a44.get_actor_location().z+HALF_T
 zA,zB=top44,targets[1155][2];pA=e44;pB=targets[1155][0]
 dist=lambda p,q:math.hypot(p.x-q.x,p.y-q.y)
 total=sum(dist(*ends(seg(i),seg(i+1).get_actor_location()-seg(i).get_actor_location())[:2]) for i in range(1145,1155))
 run=0.0
 for i in range(1145,1155):
  a=seg(i);s,e,sgn,L=ends(a,seg(i+1).get_actor_location()-a.get_actor_location())
  z0=zA+(zB-zA)*run/total;run+=dist(s,e);z1=zA+(zB-zA)*run/total
  targets[i]=(s,e,z0,z1,sgn,L)
 for i in sorted(targets):
  a=seg(i);s,e,z0,z1,sgn,L=targets[i];r=a.get_actor_rotation();c=a.get_actor_location()
  pitch=math.degrees(math.atan2(z1-z0,L))*sgn
  a.modify();a.set_actor_location(V(c.x,c.y,(z0+z1)/2-HALF_T),False,True)
  a.set_actor_rotation(unreal.Rotator(roll=r.roll,pitch=pitch,yaw=r.yaw),True)
  R['segments'].append({'name':a.get_name(),'old_center_z':c.z,'old_pitch':r.pitch,'top_start':z0,'top_end':z1,'pitch':pitch})
 assert unreal.EditorLoadingAndSavingUtils.save_packages([seg(1155).get_outermost()],False)
 R.update(level_sha256_after=sha(LEVEL_FILE),map_sha256_after=sha(MAPFILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1))
