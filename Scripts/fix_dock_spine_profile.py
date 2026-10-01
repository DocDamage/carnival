"""Continuous-profile version of the dock/spine levelling (replaces fix_dock_spine_levels*.py).

Restores the connectors level from the pre-levelling backup, then defines the spine's target top as
a function of arc length: flush (+2 cm) on dock decks, elsewhere min(original, nearest deck knot +
6-degree grade). Each affected slab takes its start/end heights from that profile, so adjacent slab
ends meet. The East Dock decks raised to 640 by the earlier pass are kept. Saves only the connectors
level (backed up).
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');CONN='L_CarnivalWorldExpansion_Connections_Layout'
CONN_FILE=ROOT/('Content/Carnival/World/Levels/'+CONN+'.umap')
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
PRE=ROOT/'Saved/WorldExpansion/DockSpineLevels_20261001'/(CONN+'.before_dock_levels.umap')
OUT=ROOT/'Saved/WorldExpansion/DockSpineProfile_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
HALF_T=22.5;GRADE=math.tan(math.radians(6.0));DOCK=('NorthDock_','EastDock_')
REGIONS=((-66000,-44000,-66000,-38000),(58000,80000,8000,32000))
R={'success':False,'errors':[],'segments':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 shutil.copy2(CONN_FILE,OUT/(CONN+'.before_profile.umap'))
 shutil.copy2(PRE,CONN_FILE);R['restored_from']=str(PRE);R['map_sha256_before']=sha(MAPFILE)
 src=(ROOT/'Scripts/playtest_world_expansion_walk_routes.py').read_text()
 ns={};exec(compile(src[:src.index('lab=resample(')],'spine','exec'),ns);path=ns['outer']
 arc=[0.0]
 for i in range(1,len(path)):arc.append(arc[-1]+math.dist(path[i-1][:2],path[i][:2]))
 def along(x,y):
  i=min(range(len(path)),key=lambda k:math.dist(path[k][:2],(x,y)))
  # refine with projection onto neighbouring polyline segments
  best=(math.dist(path[i][:2],(x,y)),arc[i])
  for j in (i-1,i):
   if 0<=j<len(path)-1:
    ax,ay=path[j][:2];bx,by=path[j+1][:2];dx,dy=bx-ax,by-ay;L2=dx*dx+dy*dy or 1
    u=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/L2));px,py=ax+u*dx,ay+u*dy
    d=math.dist((px,py),(x,y))
    if d<best[0]:best=(d,arc[j]+u*math.sqrt(L2))
  return best[1]
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 segs=[a for a in EA.get_all_level_actors() if a.get_actor_label()=='OuterRoute_Segment']
 inreg=lambda c:any(x0<c.x<x1 and y0<c.y<y1 for x0,x1,y0,y1 in REGIONS)
 rows=[]
 for a in segs:
  c=a.get_actor_location()
  if not inreg(c):continue
  f=a.get_actor_forward_vector();L=a.get_actor_scale3d().x*100;rot=a.get_actor_rotation()
  e1=(c.x-f.x*L/2,c.y-f.y*L/2);e2=(c.x+f.x*L/2,c.y+f.y*L/2)
  s1,s2=along(*e1),along(*e2);flip=s1>s2
  if flip:e1,e2,s1,s2=e2,e1,s2,s1
  top_c=c.z+HALF_T;slope_orig=math.tan(math.radians(rot.pitch))*(-1 if flip else 1)
  z1,z2=top_c-slope_orig*L/2,top_c+slope_orig*L/2
  hits=[]
  for fx,fy in ((0,0),(.8,.8),(.8,-.8),(-.8,.8),(-.8,-.8)):
   r=a.get_actor_right_vector();hy=a.get_actor_scale3d().y*50
   p=(c.x+f.x*L/2*fx+r.x*hy*fy,c.y+f.y*L/2*fx+r.y*hy*fy)
   h=t(unreal.SystemLibrary.line_trace_single(world,V(p[0],p[1],c.z+300),V(p[0],p[1],c.z-400),TQ,False,segs,N,True))
   if h:hits.append((h[9].get_actor_label() if h[9] else '',h[5].z))
  docks=[z for l,z in hits if l.startswith(DOCK)]
  rows.append({'a':a,'s1':s1,'s2':s2,'z1':z1,'z2':z2,'L':L,'flip':flip,'dock':max(docks)+2 if len(docks)>=3 else None,'rot':rot,'c':c})
 knots=[(r['s1'],r['dock']) for r in rows if r['dock'] is not None]+[(r['s2'],r['dock']) for r in rows if r['dock'] is not None]
 def target(s,orig,dock):
  if dock is not None:return dock
  lim=min((z+GRADE*abs(s-ks) for ks,z in knots),default=orig)
  return min(orig,lim)
 for r in rows:
  t1,t2=target(r['s1'],r['z1'],r['dock']),target(r['s2'],r['z2'],r['dock'])
  if abs(t1-r['z1'])<1 and abs(t2-r['z2'])<1:continue
  a=r['a'];c=r['c'];slope=(t2-t1)/r['L'];pitch=math.degrees(math.atan(slope))*(-1 if r['flip'] else 1)
  a.modify();a.set_actor_location(V(c.x,c.y,(t1+t2)/2-HALF_T),False,True)
  a.set_actor_rotation(unreal.Rotator(roll=r['rot'].roll,pitch=pitch,yaw=r['rot'].yaw),True)
  R['segments'].append({'name':a.get_name(),'along_m':[round(r['s1']/100,1),round(r['s2']/100,1)],'old':[round(r['z1']),round(r['z2'])],'new':[round(t1),round(t2)],'dock':r['dock'] is not None,'pitch':round(pitch,2)})
 x=next(a for a in EA.get_all_level_actors() if '/'+CONN+'.' in a.get_path_name())
 assert unreal.EditorLoadingAndSavingUtils.save_packages([x.get_outermost()],False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
