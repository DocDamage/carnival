"""Remove the one-way drops between the outer spine and both docks.

The spine crosses the North and East Docks as a raised slab (top ~672-703) above the dock decks
(580-660), so players can step down onto a dock but not back up. Spine slabs over a dock deck are
laid flush (+2 cm) and their neighbours re-pitched into transitions of at most 6 degrees; the East
Dock's Quay_Approach and Through_Walk are raised to 640 to meet the Main Quay (645). Saves only the
connectors and East Docks levels (backed up). North Dock decks (boat ramp meets them flush) are kept.
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
CONN='L_CarnivalWorldExpansion_Connections_Layout';EAST='L_CarnivalWorldExpansion_DocksEast'
FILES={n:ROOT/('Content/Carnival/World/Levels/'+n+'.umap') for n in (CONN,EAST)}
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/DockSpineLevelsPass2_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
HALF_T=22.5;MAX_GRADE=math.tan(math.radians(6.0));DOCK=('NorthDock_','EastDock_')
R={'success':False,'errors':[],'flush':[],'ramped':[],'raised':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 R['map_sha256_before']=sha(MAPFILE)
 for n,f in FILES.items():R[n+'_before']=sha(f);shutil.copy2(f,OUT/(n+'.before_dock_levels_pass2.umap'))
 # Spine path (same geometry as the walk runner) for ordering segments by arc length.
 src=(ROOT/'Scripts/playtest_world_expansion_walk_routes.py').read_text()
 ns={};exec(compile(src[:src.index('lab=resample(')],'spine','exec'),ns);path=ns['outer']
 arc=[0.0]
 for i in range(1,len(path)):arc.append(arc[-1]+math.dist(path[i-1][:2],path[i][:2]))
 def along(p):
  i=min(range(len(path)),key=lambda k:math.dist(path[k][:2],p))
  return arc[i]
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);acts=EA.get_all_level_actors()
 segs=[a for a in acts if a.get_actor_label()=='OuterRoute_Segment']
 def under(a):
  c=a.get_actor_location();f=a.get_actor_forward_vector();r=a.get_actor_right_vector();hx=a.get_actor_scale3d().x*50;hy=a.get_actor_scale3d().y*50
  hits=[]
  for fx,fy in ((0,0),(.8,.8),(.8,-.8),(-.8,.8),(-.8,-.8)):
   p=V(c.x+f.x*hx*fx+r.x*hy*fy,c.y+f.y*hx*fx+r.y*hy*fy,0)
   h=t(unreal.SystemLibrary.line_trace_single(world,V(p.x,p.y,c.z+300),V(p.x,p.y,c.z-400),TQ,False,segs,N,True))
   if h:hits.append((h[9].get_actor_label() if h[9] else '',h[5].z))
  return hits
 rows=[]
 for a in segs:
  c=a.get_actor_location()
  if not (-66000<c.x<-44000 and -66000<c.y<-38000) and not (58000<c.x<80000 and 8000<c.y<32000):continue
  u=under(a);docks=[z for l,z in u if l.startswith(DOCK)]
  rows.append({'a':a,'s':along((c.x,c.y)),'top':c.z+HALF_T,'dock':max(docks) if len(docks)>=3 else None})
 rows.sort(key=lambda r:r['s'])
 # Targets: flush over decks; others limited by MAX_GRADE from fixed neighbours (two passes), never raised.
 for r in rows:r['target']=r['dock']+2 if r['dock'] is not None else r['top']
 for order in (rows,list(reversed(rows))):
  for i in range(1,len(order)):
   p,q=order[i-1],order[i]
   if q['dock'] is not None:continue
   d=abs(q['s']-p['s']);lim=p['target']+MAX_GRADE*d
   if q['target']>lim:q['target']=lim
 for i,r in enumerate(rows):
  a=r['a'];c=a.get_actor_location();rot=a.get_actor_rotation()
  if abs(r['target']-r['top'])<1:continue
  prv=rows[i-1] if i>0 else r;nxt=rows[i+1] if i+1<len(rows) else r
  ds=(nxt['s']-prv['s']) or 1.0;slope=(nxt['target']-prv['target'])/ds
  f=a.get_actor_forward_vector();dirn=V(path[min(len(path)-1,1)][0],0,0)
  # Forward points along increasing arc length if moving forward increases 'along'.
  sgn=1 if along((c.x+f.x*200,c.y+f.y*200))>=along((c.x,c.y)) else -1
  pitch=math.degrees(math.atan(slope))*sgn
  a.modify();a.set_actor_location(V(c.x,c.y,r['target']-HALF_T),False,True)
  a.set_actor_rotation(unreal.Rotator(roll=rot.roll,pitch=pitch,yaw=rot.yaw),True)
  (R['flush'] if r['dock'] is not None else R['ramped']).append({'name':a.get_name(),'along_m':round(r['s']/100,1),'old_top':round(r['top'],1),'new_top':round(r['target'],1),'pitch':round(pitch,2)})
 for a in acts:
  if a.get_actor_label() in ('EastDock_Quay_Approach','EastDock_Through_Walk'):
   o,e=a.get_actor_bounds(False);top=o.z+e.z;dz=640.0-top
   if dz>0:
    a.modify();a.set_actor_location(a.get_actor_location()+V(0,0,dz),False,True)
    R['raised'].append({'label':a.get_actor_label(),'old_top':round(top,1),'new_top':640.0})
 pk=[]
 for n in (CONN,EAST):
  x=next(a for a in EA.get_all_level_actors() if '/'+n+'.' in a.get_path_name());pk.append(x.get_outermost())
 assert unreal.EditorLoadingAndSavingUtils.save_packages(pk,False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 for n,f in FILES.items():R[n+'_after']=sha(f)
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
