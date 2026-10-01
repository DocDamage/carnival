"""Author swimming water (ACarnivalWaterVolume) into the always-loaded connectors level.

1. River: the WaterBodyRiver is a 1 km wide sheet at z -240 along its spline; its water shows wherever the
   landscape lies below -240. 50 m cells inside the band whose landscape dips below the surface get a box from
   the local riverbed (-200 cm) up to the surface; cells are merged along X into runs.
2. Dry override: a non-water volume (higher priority) over the prison stair, Sewers and sewer tunnel, so no
   river cell can flood those underground spaces.
3. Atlantis + Shipwreck: one flooded volume (highest priority) from partway along the sewer tunnel through both
   interiors, with a solid surface lid at -500 and the underwater look.
Backs up and saves only the connectors level; the persistent map hash is checked unchanged."""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');CONN='L_CarnivalWorldExpansion_Connections_Layout'
CONN_FILE=ROOT/('Content/Carnival/World/Levels/'+CONN+'.umap')
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/WaterVolumes_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
SURF=-240.0;CELL=5000.0;HALF_BAND=50000.0
DRY=((-30500,-18500),(-25500,-9000),(-3000,1500))
FLOOD=((-21000,-4000),(-15000,-6200),(-2500,-500))
R={'success':False,'errors':[],'river_boxes':[],'dry':None,'flood':None,'wet_cells':0,'wet_cells_in_dry':0}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 shutil.copy2(CONN_FILE,OUT/(CONN+'.before_water.umap'));R['map_sha256_before']=sha(MAPFILE)
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);acts=EA.get_all_level_actors()
 old=[a for a in acts if a.get_class().get_name()=='CarnivalWaterVolume'];assert not old,'water volumes already authored'
 river=next(a for a in acts if a.get_actor_label()=='WaterBodyRiver')
 sp=river.get_component_by_class(unreal.SplineComponent);NPTS=sp.get_number_of_spline_points()
 pts=[sp.get_location_at_spline_point(i,unreal.SplineCoordinateSpace.WORLD) for i in range(NPTS)]
 def ground_min(x0,y0):
  zs=[]
  for fx in (0.1,0.5,0.9):
   for fy in (0.1,0.5,0.9):
    x,y=x0+CELL*fx,y0+CELL*fy
    for h in unreal.SystemLibrary.line_trace_multi(w,V(x,y,4000),V(x,y,-6000),TQ,True,[river],N,True) or []:
     t=h.to_tuple();a=t[9]
     if a and 'Landscape' in a.get_class().get_name():zs.append(t[5].z);break
  return min(zs) if zs else None
 def in_band(x,y):
  key=sp.find_input_key_closest_to_world_location(V(x,y,SURF))
  if key<=0.001 or key>=NPTS-1-0.001:return False
  c=sp.get_location_at_spline_input_key(key,unreal.SplineCoordinateSpace.WORLD)
  return math.hypot(c.x-x,c.y-y)<=HALF_BAND
 inside=lambda b,x,y:b[0][0]<=x<=b[0][1] and b[1][0]<=y<=b[1][1]
 xs=[p.x for p in pts];ys=[p.y for p in pts]
 X0=math.floor((min(xs)-HALF_BAND)/CELL)*CELL;X1=max(xs)+HALF_BAND;Y0=math.floor((min(ys)-HALF_BAND)/CELL)*CELL;Y1=max(ys)+HALF_BAND
 rows={}
 y=Y0
 while y<Y1:
  x=X0
  while x<X1:
   cx,cy=x+CELL/2,y+CELL/2
   if in_band(cx,cy):
    g=ground_min(x,y)
    if g is not None and g<SURF-10:
     R['wet_cells']+=1
     if inside(DRY,cx,cy):R['wet_cells_in_dry']+=1
     rows.setdefault(y,[]).append((x,g))
   x+=CELL
  y+=CELL
 # Merge contiguous wet cells along X.
 runs=[]
 for yy,cells in rows.items():
  cells.sort();cur=None
  for x,g in cells:
   if cur and abs(x-cur['x1'])<1:cur['x1']=x+CELL;cur['g']=min(cur['g'],g)
   else:
    cur={'y':yy,'x0':x,'x1':x+CELL,'g':g};runs.append(cur)
 lvl_actor=next(a for a in acts if '/'+CONN+'.' in a.get_path_name())
 assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name(CONN)
 def spawn(label,lo,hi,water,priority,lid=False,fog=None,color=None):
  c=V((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,(lo[2]+hi[2])/2)
  a=EA.spawn_actor_from_class(unreal.CarnivalWaterVolume,c,unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0))
  assert '/'+CONN+'.' in a.get_path_name(),a.get_path_name()
  a.set_actor_label(label)
  a.set_editor_property('water_extent',V((hi[0]-lo[0])/2,(hi[1]-lo[1])/2,(hi[2]-lo[2])/2))
  a.set_editor_property('water_volume',water)
  a.set_editor_property('priority',priority)
  a.set_editor_property('solid_surface',lid)
  if fog is not None:a.set_editor_property('underwater_fog_per_metre',fog)
  if color is not None:a.set_editor_property('underwater_fog_color',unreal.LinearColor(*color))
  a.rerun_construction_scripts() if hasattr(a,'rerun_construction_scripts') else None
  return a
 for i,r in enumerate(runs):
  bottom=max(-2500.0,r['g']-200.0)
  spawn('Water_River_%03d'%i,(r['x0'],r['y'],bottom),(r['x1'],r['y']+CELL,SURF),True,10,fog=0.09,color=(0.02,0.07,0.06,1))
  R['river_boxes'].append({'x':[r['x0'],r['x1']],'y':r['y'],'bottom':round(bottom)})
 spawn('Water_DryOverride_SewersAndStair',(DRY[0][0],DRY[1][0],DRY[2][0]),(DRY[0][1],DRY[1][1],DRY[2][1]),False,20)
 R['dry']=DRY
 spawn('Water_Flooded_AtlantisShipwreck',(FLOOD[0][0],FLOOD[1][0],FLOOD[2][0]),(FLOOD[0][1],FLOOD[1][1],FLOOD[2][1]),True,30,lid=True,fog=0.06,color=(0.01,0.07,0.1,1))
 R['flood']=FLOOD
 assert unreal.EditorLoadingAndSavingUtils.save_packages([lvl_actor.get_outermost()],False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 R['river_box_count']=len(runs);R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
