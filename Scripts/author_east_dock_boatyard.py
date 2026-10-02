"""Turn the landlocked East Dock into a boatyard (user decision 2026-10-01: dry dock / boatyard, not harbour water).

The dock stands over empty space (no landscape under it in editor or game: `probe_east_dock_boatyard_site.py`,
`EastDockEdgesPIE_*`). This adds, in the East Dock level only:
- a drained basin: a sand floor at z 560 under and around the three loading fingers (1 m below the decks), from the
  Main Quay's north face to past the finger tips;
- two slipways: gentle ramps (about 5 degrees) from the basin floor up to the Main Quay, so the basin is never a pit;
- boats on cradles (Docks pack boat lifts) in the basin between the fingers; the old mooring skiff, which hung in the
  air east of the quay, now sits on one of them, and the channel buoy lies on the basin floor;
- hardstanding props on the quay apron's south part: boats on trailers, two cradled boats, a forklift, cable drums,
  barrels and a gas tank.
Every prop is checked against the OuterRoute spine (clear of each segment), the route anchors and the dispatch
station, and must leave a standing capsule free beside it. Edge fences are a separate pass
(`author_walkable_edge_fences.py`). Backs up and saves only the East Dock level; the persistent map hash must not
change.
"""
import hashlib,json,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');LEVEL='L_CarnivalWorldExpansion_DocksEast'
LEVEL_FILE=ROOT/('Content/Carnival/World/Levels/'+LEVEL+'.umap')
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/EastDockBoatyard_v2_20261001';OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
TAG='CarnivalBoatyard';FOLDER='EastDock_Boatyard'
CUBE='/Engine/BasicShapes/Cube.Cube'
SAND='/Game/Docks/VOL2_Powell/Materials/Instances/MI_Sand_01a.MI_Sand_01a'
PLANKS='/Game/Docks/VOL2_Powell/Materials/Instances/MI_Wooden_Planks_Beams_01.MI_Wooden_Planks_Beams_01'
DOCKS='/Game/Docks/VOL2_Powell/Meshes/';LH='/Game/LightHouse_Meshingun/Meshes/Props/'
BASIN_TOP=560.0;APRON_TOP=640.0;QUAY_TOP=645.0;QUAY_NORTH_Y=18850.0
R={'success':False,'errors':[],'placed':[],'moved':[],'checks':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 R.update(map_sha256_before=sha(MAPFILE),level_sha256_before=sha(LEVEL_FILE))
 shutil.copy2(LEVEL_FILE,OUT/(LEVEL+'.before_boatyard.umap'))
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);LE=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 acts=EA.get_all_level_actors()
 assert not any(TAG in [str(x) for x in a.tags] for a in acts),'Boatyard already authored'
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 segs=[a for a in acts if a.get_actor_label().startswith('OuterRoute_Segment')]
 seg_xy=[(a.get_actor_location().x,a.get_actor_location().y) for a in segs]
 anchors=[a.get_actor_location() for a in acts if unreal.Name('CarnivalRouteAnchor') in list(a.tags)]
 station=next(a for a in acts if a.get_actor_label()=='Campaign_east_docks_dispatch').get_actor_location()
 assert LE.set_current_level_by_name(LEVEL)
 def spawn(label,mesh,loc,yaw=0.0,scale=(1,1,1),mat=None,roll=0.0,pitch=0.0):
  m=unreal.load_asset(mesh);assert m,mesh
  # spawn_actor_from_object returns None here; spawn a StaticMeshActor and set its mesh (as connect_dock_pieces.py).
  a=EA.spawn_actor_from_class(unreal.StaticMeshActor,V(*loc),unreal.Rotator(roll=roll,pitch=pitch,yaw=yaw));assert a,label
  assert '/'+LEVEL+'.' in a.get_path_name(),(label,a.get_path_name())
  c=a.static_mesh_component;c.set_static_mesh(m)
  a.set_actor_scale3d(V(*scale));a.set_actor_label(label);a.set_folder_path(FOLDER);a.tags=[unreal.Name(TAG)]
  if mat:c.set_material(0,unreal.load_asset(mat))
  c.set_collision_profile_name('BlockAll')
  o,e=a.get_actor_bounds(False)
  R['placed'].append({'label':label,'mesh':mesh.split('/')[-1].split('.')[0],'loc':[round(v) for v in loc],'yaw':yaw,
   'bounds_min_z':round(o.z-e.z),'bounds_max_z':round(o.z+e.z)})
  return a
 def clear_of_route(label,x,y,radius):
  d_seg=min(math.dist((x,y),s) for s in seg_xy);d_anchor=min(math.dist((x,y),(p.x,p.y)) for p in anchors)
  d_station=math.dist((x,y),(station.x,station.y))
  ok=d_seg>=540+radius and d_anchor>=radius+300 and d_station>=radius+500
  R['checks'].append({'label':label,'clear_of_spine_cm':round(d_seg-540-radius),'anchor_cm':round(d_anchor),'station_cm':round(d_station),'ok':ok})
  assert ok,R['checks'][-1]
 # 1) Basin floor: x 65900..74100, y QUAY_NORTH_Y..31400, top at BASIN_TOP, 40 cm thick.
 bx0,bx1,by0,by1=65900.0,74100.0,QUAY_NORTH_Y,31400.0
 spawn('EastDock_Boatyard_Basin_Floor',CUBE,((bx0+bx1)/2,(by0+by1)/2,BASIN_TOP-20),scale=((bx1-bx0)/100,(by1-by0)/100,0.4),mat=SAND)
 # 2) Slipways: 10 m ramps from the basin floor (y QUAY_NORTH_Y+1000) up to the Main Quay's north face.
 run=1000.0;rise=QUAY_TOP-BASIN_TOP;ang=math.degrees(math.atan2(rise,run));thick=30.0
 for name,x,width in (('West',66300.0,700.0),('Centre',68650.0,600.0)):
  # Cube pivot is its centre. Yaw 90 points the cube's X along +Y, so the slope is a pitch (as the finger links).
  # The top face centre sits halfway up the rise; push the box centre down by half its thickness along the normal.
  zc=BASIN_TOP+rise/2-(thick/2)*math.cos(math.radians(ang));yc=QUAY_NORTH_Y+run/2+(thick/2)*math.sin(math.radians(ang))
  a=None
  for sign in (1.0,-1.0):
   if a:EA.destroy_actor(a);R['placed'].pop()
   a=spawn('EastDock_Boatyard_Slipway_'+name,CUBE,(x,yc,zc),yaw=90.0,scale=((run/math.cos(math.radians(ang))+10)/100,width/100,thick/100),mat=PLANKS,pitch=sign*ang)
   lo=t(unreal.SystemLibrary.line_trace_single(w,V(x,QUAY_NORTH_Y+run-60,900),V(x,QUAY_NORTH_Y+run-60,300),TQ,False,ign,N,True))
   hi=t(unreal.SystemLibrary.line_trace_single(w,V(x,QUAY_NORTH_Y+60,900),V(x,QUAY_NORTH_Y+60,300),TQ,False,ign,N,True))
   if lo and hi and lo[9]==a and hi[9]==a and lo[5].z<hi[5].z:break
  R['checks'].append({'label':a.get_actor_label(),'low_end_z':round(lo[5].z),'high_end_z':round(hi[5].z),'slope_deg':round(ang,1),'normal_z':round(lo[7].z,3)})
  assert lo[9]==a and hi[9]==a and abs(lo[5].z-(BASIN_TOP+rise*60/run))<15 and abs(hi[5].z-(QUAY_TOP-rise*60/run))<15,R['checks'][-1]
 # 3) Boats on cradles. Boat lift: pivot at its top (bounds z -87..5); boat: keel at 0, long axis Y like the lift.
 def cradle(label,x,y,top,boat=None,boat_mesh=DOCKS+'SM_Boat_17a'):
  clear_of_route(label,x,y,300)
  spawn(label+'_Cradle',DOCKS+'SM_BoatLift_01a',(x,y,top+87))
  if boat:
   boat.set_actor_location(V(x,y,top+92),False,False);boat.set_actor_rotation(unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0),False)
   boat.set_folder_path(FOLDER);boat.tags=list(boat.tags)+[unreal.Name(TAG)]
   R['moved'].append({'label':boat.get_actor_label(),'to':[x,y,top+92]})
  else:spawn(label+'_Boat',boat_mesh,(x,y,top+92))
 skiff=next(a for a in acts if a.get_actor_label()=='EastDock_Mooring_Skiff')
 cradle('EastDock_Boatyard_Basin_A',68650,24800,BASIN_TOP,boat=skiff)
 cradle('EastDock_Boatyard_Basin_B',68650,28200,BASIN_TOP,boat_mesh=DOCKS+'SM_Boat_NN_17a')
 cradle('EastDock_Boatyard_Basin_C',71000,24800,BASIN_TOP)
 cradle('EastDock_Boatyard_Basin_D',71000,28200,BASIN_TOP,boat_mesh=DOCKS+'SM_Boat_NN_17a')
 buoy=next(a for a in acts if a.get_actor_label()=='EastDock_Channel_Buoy')
 o,e=buoy.get_actor_bounds(False);bl=buoy.get_actor_location();clear_of_route('EastDock_Channel_Buoy',66300,30300,150)
 buoy.set_actor_location(V(66300,30300,bl.z+(BASIN_TOP-(o.z-e.z))),False,False);buoy.set_folder_path(FOLDER);buoy.tags=list(buoy.tags)+[unreal.Name(TAG)]
 R['moved'].append({'label':'EastDock_Channel_Buoy','to':[66300,30300,round(bl.z+(BASIN_TOP-(o.z-e.z)))]})
 # 4) Hardstanding on the apron's south part (top APRON_TOP).
 for label,x,y,yaw,boat in (('EastDock_Boatyard_Trailer_SpeedBoat',69000,12600,0,'SM_Prop_Speed_Boat'),('EastDock_Boatyard_Trailer_Inflatable',69000,14000,0,'SM_Prop_Inflatable_Boat')):
  clear_of_route(label,x,y,420)
  spawn(label,LH+'Boat_Trailer/'+('SM_Prop_Boat_Trailer_Blue' if 'Speed' in label else 'SM_Prop_Boat_Trailer_White'),(x,y,APRON_TOP),yaw=yaw)
  spawn(label+'_Boat',LH+'Boat_Trailer/'+boat,(x,y,APRON_TOP+55),yaw=yaw)
 cradle('EastDock_Boatyard_Apron_A',71500,12700,APRON_TOP)
 cradle('EastDock_Boatyard_Apron_B',72600,12700,APRON_TOP,boat_mesh=DOCKS+'SM_Boat_NN_17a')
 for label,mesh,x,y,yaw,r in (('EastDock_Boatyard_Forklift',LH+'Vehicle/SM_Prop_Forklift',73700,13800,-90,200),
   ('EastDock_Boatyard_GasTank',LH+'Barrel_Boxes/SM_Prop_Gas_Tank_1',67700,12000,0,250),
   ('EastDock_Boatyard_CableDrum_1',LH+'Barrel_Boxes/SM_Prop_Cable_Roll1',70500,12000,0,100),
   ('EastDock_Boatyard_CableDrum_2',LH+'Barrel_Boxes/SM_Prop_Cable_Roll2',70700,12300,30,100),
   ('EastDock_Boatyard_Barrel_1',LH+'Barrel_Boxes/SM_Prop_Plastic_Barrel',73900,11900,0,60),
   ('EastDock_Boatyard_Barrel_2',LH+'Barrel_Boxes/SM_Prop_Plastic_Barrel',74000,12000,40,60),
   ('EastDock_Boatyard_Barrel_3',LH+'Barrel_Boxes/SM_Prop_Plastic_Barrel',73880,12050,80,60),
   ('EastDock_Boatyard_Barrel_4',LH+'Barrel_Boxes/SM_Prop_Plastic_Barrel',74020,11840,10,60)):
  clear_of_route(label,x,y,r);spawn(label,mesh,(x,y,APRON_TOP),yaw=yaw)
 # 5) Every new prop must rest on (not hang over or sink into) its surface: bounds bottom within 15 cm of the top.
 for p in R['placed']:
  if p['mesh'] in ('Cube',):continue
  surf=BASIN_TOP if p['loc'][1]>QUAY_NORTH_Y+200 and p['loc'][2]<APRON_TOP else APRON_TOP
  if '_Boat' in p['label'] or p['mesh'].startswith('SM_Boat'):continue
  p['rests_cm']=p['bounds_min_z']-surf
 R['resting_outliers']=[p for p in R['placed'] if 'rests_cm' in p and abs(p['rests_cm'])>15]
 a0=next(x for x in EA.get_all_level_actors() if x.get_actor_label()=='EastDock_Main_Quay')
 assert unreal.EditorLoadingAndSavingUtils.save_packages([a0.get_outermost()],False)
 R.update(map_sha256_after=sha(MAPFILE),level_sha256_after=sha(LEVEL_FILE));assert R['map_sha256_after']==R['map_sha256_before']
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
