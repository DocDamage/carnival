"""Read-only: where is the visible water at the docks / coast (river water body surface, spline extent), and what
water rendering/collision settings it has. No saves."""
import json,traceback,unreal
V=unreal.Vector;R={'errors':[],'points':[],'spline':[],'props':{}}
PTS={'north_berth':(-49000,-58200),'north_open':(-52000,-60000),'north_end_platform_side':(-55800,-44500),'east_water':(70000,10000),'east_fingers_gap':(69000,20500),'east_beyond':(70000,33000),'coast_mansion':(-60000,-80000),'wetland1':(-12000,-20000)}
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 river=next(a for a in acts if a.get_actor_label()=='WaterBodyRiver')
 wc=river.get_water_body_component() if hasattr(river,'get_water_body_component') else river.get_component_by_class(unreal.WaterBodyComponent)
 for k in ('generate_collisions','collision_profile_name','affects_landscape','water_material','physical_material','overlap_material_priority','channel_depth','fixed_water_depth'):
  try:R['props'][k]=str(wc.get_editor_property(k))[:160]
  except Exception as e:R['props'][k]='n/a'
 sp=river.get_component_by_class(unreal.SplineComponent)
 n=sp.get_number_of_spline_points();R['spline_points']=n
 for i in range(0,n,max(1,n//60)):
  p=sp.get_location_at_spline_point(i,unreal.SplineCoordinateSpace.WORLD);R['spline'].append([round(p.x),round(p.y),round(p.z)])
 for name,(x,y) in PTS.items():
  rec={'name':name,'xy':[x,y]}
  try:
   key=sp.find_input_key_closest_to_world_location(V(x,y,0));cp=sp.get_location_at_spline_input_key(key,unreal.SplineCoordinateSpace.WORLD)
   rec['nearest_spline']=[round(cp.x),round(cp.y),round(cp.z)];rec['dist_to_spline_m']=round(((cp.x-x)**2+(cp.y-y)**2)**.5/100,1)
  except Exception as e:rec['spline_err']=str(e)[:100]
  try:
   r=wc.get_water_surface_info_at_location(V(x,y,0),True);rec['surface']=str(r)[:300]
  except Exception as e:rec['surface_err']=str(e)[:150]
  hs=unreal.SystemLibrary.line_trace_multi(w,V(x,y,3000),V(x,y,-3000),unreal.TraceTypeQuery.ECC_VISIBILITY,True,[],unreal.DrawDebugTrace.NONE,True) or []
  rec['hits']=[(h.to_tuple()[9].get_actor_label() if h.to_tuple()[9] else '?',round(h.to_tuple()[5].z)) for h in hs][:4]
  R['points'].append(rec)
except Exception:R['errors'].append(traceback.format_exc())
open(r'F:\Carnival\Saved\WorldExpansion\WaterSurfaces_20261001.json','w').write(json.dumps(R,indent=1))
