"""Read-only inputs for the spine edge fences and the East Dock boatyard.

- Railing/fence candidate meshes: bounds, collision (simple shapes / complex-as-simple).
- Materials on the East Dock slabs and a spine segment.
- Every OuterRoute_Segment: transform, mesh extent (length along forward, width along right), and for each side
  whether there is ground within 60 m below a point 1 m beyond the edge (void side), plus nearby non-spine walkable
  surfaces at deck height beside that edge (junctions that a fence must leave open).
"""
import json,math,traceback
from pathlib import Path
import unreal
OUT=Path(r'F:\Carnival\Saved\WorldExpansion\FenceYardInputs_20261001.json')
V=unreal.Vector;TQ=unreal.TraceTypeQuery.ECC_VISIBILITY;N=unreal.DrawDebugTrace.NONE
CANDIDATES=['/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_A','/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_B','/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_C',
 '/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_D','/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_E','/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_F',
 '/Game/Docks/VOL2_Powell/Meshes/SM_Pier_Railing_G','/Game/Docks/VOL2_Powell/Meshes/SM_Plank_Railing_Small','/Game/Docks/VOL2_Powell/Meshes/SM_Fence_Dune_NN_01b',
 '/Game/Docks/VOL2_Powell/Meshes/SM_Fence_Dune_NN_01d','/Game/Docks/VOL2_Powell/Meshes/SM_Fishing_Fence_NN_01g','/Game/Docks/VOL2_Powell/Meshes/SM_Fishing_Fence_NN_01m']
R={'success':False,'errors':[]}
def t(h):
 d=h.to_tuple() if h else None;return d if d and d[0] else None
try:
 R['meshes']={}
 for p in CANDIDATES:
  m=unreal.load_asset(p)
  if not m:continue
  b=m.get_bounding_box();bs=m.get_editor_property('body_setup')
  agg=bs.get_editor_property('agg_geom') if bs else None
  shapes={k:len(agg.get_editor_property(k)) for k in ('box_elems','convex_elems','sphere_elems','sphyl_elems')} if agg else None
  R['meshes'][p.split('/')[-1]]={'min':[round(v) for v in b.min.to_tuple()],'max':[round(v) for v in b.max.to_tuple()],'shapes':shapes,
   'trace_flag':str(bs.get_editor_property('collision_trace_flag')) if bs else None}
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert w
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 ign=[a for a in acts if a.get_actor_label().startswith('SM_Landscape_Far_01a')]
 def mats(a):
  c=a.get_component_by_class(unreal.StaticMeshComponent)
  return [m.get_path_name() if m else None for m in c.get_materials()] if c else None
 for lab in ('EastDock_Quay_Approach','EastDock_Main_Quay','EastDock_Loading_Finger','EastDock_Finger_Link_Centre','EastDock_Through_Walk'):
  a=next(x for x in acts if x.get_actor_label()==lab);c=a.get_component_by_class(unreal.StaticMeshComponent)
  R.setdefault('dock_slabs',{})[lab]={'materials':mats(a),'mesh':c.static_mesh.get_path_name(),'scale':list(a.get_actor_scale3d().to_tuple()),
   'profile':str(c.get_collision_profile_name()),'location':list(a.get_actor_location().to_tuple())}
 segs=[a for a in acts if a.get_actor_label().startswith('OuterRoute_Segment')]
 R['spine_material']=mats(segs[0]);c0=segs[0].get_component_by_class(unreal.StaticMeshComponent)
 R['spine_mesh']=c0.static_mesh.get_path_name();R['spine_profile']=str(c0.get_collision_profile_name())
 mb=c0.static_mesh.get_bounding_box();R['spine_mesh_bounds']=[list(mb.min.to_tuple()),list(mb.max.to_tuple())]
 rows=[]
 for a in segs:
  c=a.get_component_by_class(unreal.StaticMeshComponent);b=c.static_mesh.get_bounding_box();s=a.get_actor_scale3d()
  L=(b.max.x-b.min.x)*s.x;W=(b.max.y-b.min.y)*s.y;H=(b.max.z-b.min.z)*s.z
  o=a.get_actor_location();f=a.get_actor_forward_vector();r=a.get_actor_right_vector();rot=a.get_actor_rotation()
  ctr=o+f*((b.max.x+b.min.x)/2*s.x)+r*((b.max.y+b.min.y)/2*s.y)+V(0,0,(b.max.z+b.min.z)/2*s.z)
  top=ctr.z+H/2*math.cos(math.radians(rot.pitch))
  sides={}
  for name,sg in (('left',-1),('right',1)):
   void=0;junction=[]
   for k in (-0.4,0,0.4):
    p=ctr+f*(k*L)+r*(sg*(W/2+100))
    h=t(unreal.SystemLibrary.line_trace_single(w,V(p.x,p.y,top+150),V(p.x,p.y,top-6000),TQ,False,ign+[a],N,True))
    if not h:void+=1
    elif h[5].z>top-80:junction.append(h[9].get_actor_label() if h[9] else '')
   sides[name]={'void_samples':void,'junction':sorted(set(junction))}
  rows.append({'path':a.get_path_name(),'ctr':[round(v,1) for v in ctr.to_tuple()],'yaw':round(rot.yaw,2),'pitch':round(rot.pitch,2),'roll':round(rot.roll,2),
   'L':round(L),'W':round(W),'H':round(H),'top':round(top),'sides':sides})
 R['segments']=rows
 R['void_side_count']=sum(1 for x in rows for s in x['sides'].values() if s['void_samples']>=2)
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:OUT.write_text(json.dumps(R,indent=1))
