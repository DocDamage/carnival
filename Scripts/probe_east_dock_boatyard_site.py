"""Read-only: site survey for turning the East Dock into a boatyard.

- Actors in the East Dock level and the East Dock pieces of the connectors level: label, mesh, bounds.
- Bounds (size) of the candidate boatyard meshes.
- A 4 m grid over the dock area: ground top z, actor, normal, and whether a standing capsule fits (open ground),
  plus the nearest route anchor / spine segment, so props can be kept off the walking lines.
"""
import json,math,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\EastDockBoatyardSite_20261001.json')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
MESHES=['/Game/Docks/VOL2_Powell/Meshes/SM_BoatLift_01a','/Game/Docks/VOL2_Powell/Meshes/SM_BoatLift_01b',
 '/Game/Docks/VOL2_Powell/Meshes/SM_Boat_17a','/Game/Docks/VOL2_Powell/Meshes/SM_Boat_NN_14d','/Game/Docks/VOL2_Powell/Meshes/SM_Boat_NN_17a',
 '/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Boat_Trailer_Blue','/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Boat_Trailer_White',
 '/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Speed_Boat','/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Inflatable_Boat',
 '/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Cargo_Ship','/Game/LightHouse_Meshingun/Meshes/Props/Vehicle/SM_Prop_Forklift',
 '/Game/LightHouse_Meshingun/Meshes/Props/Barrel_Boxes/SM_Prop_Plastic_Barrel','/Game/LightHouse_Meshingun/Meshes/Props/Barrel_Boxes/SM_Prop_Cable_Roll1',
 '/Game/LightHouse_Meshingun/Meshes/Props/Barrel_Boxes/SM_Prop_Gas_Tank_1','/Game/Docks/VOL2_Powell/Meshes/SM_Support_Beam_A',
 '/Game/Docks/VOL2_Powell/Meshes/SM_Wood_Piles_NN_01e','/Game/Docks/VOL2_Powell/Meshes/SM_Old_Buoys_NN_01a']
R={'success':False,'errors':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 R['meshes']={}
 for p in MESHES:
  m=unreal.load_asset(p)
  if not m:R['meshes'][p]=None;continue
  b=m.get_bounding_box();R['meshes'][p.split('/')[-1]]={'min':[round(v) for v in b.min.to_tuple()],'max':[round(v) for v in b.max.to_tuple()],
   'collision':bool(m.get_editor_property('body_setup')) }
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 dock=[];lo=[1e9,1e9];hi=[-1e9,-1e9]
 for a in acts:
  lv=a.get_level().get_outermost().get_name().split('/')[-1];lab=a.get_actor_label()
  if lv=='L_CarnivalWorldExpansion_DocksEast' or lab.startswith('EastDock'):
   o,e=a.get_actor_bounds(False)
   if e.x>30000:continue
   c=a.get_component_by_class(unreal.StaticMeshComponent);sm=c.static_mesh.get_name() if c and c.static_mesh else ''
   dock.append([lab,lv,sm,[round(v) for v in o.to_tuple()],[round(v) for v in e.to_tuple()],round(a.get_actor_rotation().yaw)])
   lo=[min(lo[0],o.x-e.x),min(lo[1],o.y-e.y)];hi=[max(hi[0],o.x+e.x),max(hi[1],o.y+e.y)]
 R['dock_actors']=sorted(dock,key=lambda r:r[0]);R['dock_bbox']=[round(v) for v in lo+hi]
 anchors=[a.get_actor_location() for a in acts if unreal.Name('CarnivalRouteAnchor') in list(a.tags)]
 spine=[a for a in acts if a.get_actor_label().startswith(('OuterRoute','Route_OuterRoute','Spine'))]
 R['spine_count']=len(spine)
 pad=4000;x0,y0,x1,y1=lo[0]-pad,lo[1]-pad,hi[0]+pad,hi[1]+pad;S=400
 grid=[];x=x0
 while x<=x1:
  y=y0
  while y<=y1:
   h=t(unreal.SystemLibrary.line_trace_single(w,V(x,y,5000),V(x,y,-3000),TQ,False,ign,N,True))
   if h:
    c=h[5]+V(0,0,98);clear=not t(unreal.SystemLibrary.capsule_trace_single(w,c,c+V(0,0,.1),42,96,TQ,False,ign,N,True))
    da=min((math.dist((x,y),(p.x,p.y)) for p in anchors),default=None)
    grid.append([round(x),round(y),round(h[5].z),h[9].get_actor_label() if h[9] else '',round(h[7].z,2),clear,round(da) if da else None])
   y+=S
  x+=S
 R['grid_step']=S;R['grid']=grid
 R['anchors_near']=[[round(v) for v in p.to_tuple()] for p in anchors if x0<=p.x<=x1 and y0<=p.y<=y1]
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
