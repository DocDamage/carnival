"""Read-only navmesh reachability: build a transient navmesh over a region (unsaved) and query paths
from a route anchor to target points (e.g. areas the grid audit could not reach). Nothing is saved.
Region/targets come from env CARNIVAL_NAV_REGION and the grid audit's unreachable clusters."""
import json,math,os,time,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival')
NAME=os.environ.get('CARNIVAL_NAV_REGION','hospital_fine')
AUDIT=ROOT/'Saved/WorldExpansion/Reachability'/(os.environ.get('CARNIVAL_NAV_AUDIT',NAME+'_v4_20261001'))/'index.json'
OUT=ROOT/'Saved/WorldExpansion/Reachability'/(NAME+os.environ.get('CARNIVAL_NAV_SUFFIX','_navmesh3_20261001'));OUT.mkdir(parents=True,exist_ok=False)
V=unreal.Vector
R={'success':False,'errors':[],'region':NAME,'paths':[]}
audit=json.loads(AUDIT.read_text());spec=audit['spec'];entrance=audit['entrance_cell']
targets=[('unreach_%d'%i,c['centroid'],c['area_m2'],c['floors'][:2]) for i,c in enumerate(audit['unreachable'][:25])]
targets+=[('trap_%d'%i,c['centroid'],c['area_m2'],c['floors'][:2]) for i,c in enumerate(audit.get('traps',[])[:10])]
S={'phase':'build','busy':False,'deadline':time.monotonic()+900,'t0':time.monotonic()}
def save():(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
def finish(e=None):
 if e:R['errors'].append(e)
 R['success']=not R['errors'];save();unreal.unregister_slate_post_tick_callback(h);unreal.SystemLibrary.quit_editor()
try:
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 cx,cy=spec['center'];H=spec['half'];zlo,zhi=spec['z']
 vol=EA.spawn_actor_from_class(unreal.NavMeshBoundsVolume,V(cx,cy,(zlo+zhi)/2),unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0))
 vol.set_actor_scale3d(V(H/100.0,H/100.0,(zhi-zlo)/200.0+1))
 # LV_Carnival ships with navigation disabled (the game uses no AI navigation). Enable it for this
 # unsaved probe only, with a navmesh sized to the player capsule and step.
 world.get_world_settings().set_editor_property('enable_navigation_system',True)
 nm=EA.spawn_actor_from_class(unreal.RecastNavMesh,V(cx,cy,(zlo+zhi)/2),unreal.Rotator(roll=0.0,pitch=0.0,yaw=0.0))
 for k,v in (('agent_radius',42.0),('agent_height',192.0),('agent_max_step_height',45.0),('agent_max_slope',44.0),('cell_size',10.0),('cell_height',10.0)):
  try:nm.set_editor_property(k,v)
  except Exception as e:R.setdefault('navmesh_property_errors',[]).append(k+': '+str(e)[:120])
 unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation')
except Exception:R['errors'].append(traceback.format_exc());save();unreal.SystemLibrary.quit_editor();raise
def tick(_):
 if S['busy']:return
 S['busy']=True
 try:
  now=time.monotonic()
  if now>S['deadline']:raise RuntimeError('timeout '+S['phase'])
  nav=unreal.NavigationSystemV1.get_navigation_system(world)
  if S['phase']=='build':
   if now-S['t0']<10 or (nav and nav.is_navigation_being_built(world)):return
   R['build_seconds']=round(now-S['t0'])
   R['navdata_actors']=[a.get_class().get_name()+':'+a.get_name() for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.NavigationData)] if hasattr(unreal,'NavigationData') else 'n/a'
   st=V(*entrance)+V(0,0,98)
   for lab,end in (('control_1m',st+V(100,0,0)),('control_reception',V(97283,130125,741))):
    p=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,st,end)
    R.setdefault('controls',[]).append({'label':lab,'path':bool(p),'points':len(list(p.path_points)) if p else 0,'partial':p.is_partial() if p else None})
   pr=unreal.NavigationSystemV1.project_point_to_navigation(world,st) if hasattr(unreal.NavigationSystemV1,'project_point_to_navigation') else None
   R['entrance_projected']=list(pr.to_tuple()) if pr else None
   start=V(*entrance)+V(0,0,98)
   for name,c,area,floors in targets:
    end=V(c[0],c[1],c[2]+98)
    p=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,start,end)
    pts=list(p.path_points) if p else []
    ok=bool(p) and not p.is_partial() and len(pts)>0 and (pts[-1]-end).length()<200
    R['paths'].append({'target':name,'centroid':c,'area_m2':area,'floors':floors,'reachable':ok,
     'partial':bool(p.is_partial()) if p else None,'points':len(pts),'end_gap_cm':round((pts[-1]-end).length()) if pts else None,
     'length_m':round(sum((pts[i+1]-pts[i]).length() for i in range(len(pts)-1))/100,1) if len(pts)>1 else 0})
   finish();return
 except Exception:finish(traceback.format_exc())
 finally:S['busy']=False
save();h=unreal.register_slate_post_tick_callback(tick)
