"""Read-only PIE survey of real water/hover placements and dock boarding geometry.

Select CARNIVAL_VEHICLE_WORLD=main|lighthouse|mars|castle and run with
run_doll_tool.py playtest. Does not spawn vehicles or save any map.
"""
import hashlib,json,os,time,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion/WaterVehicleAcceptance'; OUT.mkdir(parents=True,exist_ok=True)
WORLDS={'main':'/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival',
        'lighthouse':'/Game/LightHouse_Meshingun/Map/LV_LightHouse','mars':'/Game/Mars_Futuristic_Cars/Maps/Playmap',
        'castle':'/Game/Medieval_Castle/Level/Medieval_Castle_Level'}
key=os.environ.get('CARNIVAL_VEHICLE_WORLD','main'); MAP=WORLDS[key]
report={'success':False,'world':key,'map':MAP,'vehicles':[],'activities':[],'water_candidates':[],
        'docks':[],'errors':[],'limits':'Inventory and runtime collision survey only; water-name/material identification is heuristic. No lifecycle or buoyancy acceptance.',
        'timestamp':time.time(),'saved_map_modified':False}
state={'phase':'setup','deadline':time.monotonic()+240,'busy':False}
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def save(): (OUT/(key+'_PlacementSurvey.json')).write_text(json.dumps(report,indent=2))
def trace(game,p,z_above=500,z_below=1600,ignore=()):
    raw=unreal.SystemLibrary.line_trace_single(game,p+unreal.Vector(0,0,z_above),p-unreal.Vector(0,0,z_below),unreal.TraceTypeQuery.ECC_VISIBILITY,False,list(ignore),unreal.DrawDebugTrace.NONE,True)
    h=raw.to_tuple() if raw else None
    if not h or not h[0]: return None
    return {'actor':h[9].get_actor_label() if h[9] else None,'path':h[9].get_path_name() if h[9] else None,'point_cm':h[5].to_tuple(),'normal':h[7].to_tuple(),'initial_overlap':bool(h[1])}
def bounds(a):
    c,e=a.get_actor_bounds(False,True); return {'center_cm':c.to_tuple(),'extent_cm':e.to_tuple()}
def tick(delta):
    if state['busy']: return
    state['busy']=True
    try:
        if state['phase']=='exit':
            if time.monotonic()>state['deadline']: unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:
            if time.monotonic()>state['deadline']: raise RuntimeError('PIE startup timeout')
            return
        if state['phase']=='setup':
            unreal.GameplayStatics.set_game_paused(game,False); state.update(phase='survey',ready=time.monotonic()+1); return
        if time.monotonic()<state['ready']: return
        actors=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.Actor)
        for a in actors:
            label=a.get_actor_label(); cls=a.get_class().get_name()
            if isinstance(a,(unreal.CarnivalBoat,unreal.CarnivalHovercraft)):
                row={'label':label,'class':cls,'path':a.get_path_name(),'location_cm':a.get_actor_location().to_tuple(),'rotation':str(a.get_actor_rotation()),**bounds(a)}
                row['collision_extent_cm']=a.get_editor_property('collision_box').get_scaled_box_extent().to_tuple()
                row['mount_extent_cm']=a.get_editor_property('mount_trigger').get_scaled_box_extent().to_tuple()
                row['surface_below']=trace(game,a.get_actor_location(),ignore=[a]); report['vehicles'].append(row)
            if isinstance(a,unreal.CarnivalActivityBase):
                cps=[{'location_cm':cp.get_editor_property('location').to_tuple(),'radius_cm':cp.get_editor_property('radius')} for cp in a.get_editor_property('checkpoints')]
                report['activities'].append({'label':label,'path':a.get_path_name(),'location_cm':a.get_actor_location().to_tuple(),'checkpoints':cps})
            water_words=('water','ocean','river','lake')
            materials=[]
            for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                for i in range(comp.get_num_materials()):
                    mat=comp.get_material(i)
                    if mat and any(s in mat.get_path_name().lower() for s in water_words): materials.append(mat.get_path_name())
            if any(s in (label+' '+cls).lower() for s in water_words) or materials:
                report['water_candidates'].append({'label':label,'class':cls,'path':a.get_path_name(),'materials':materials,**bounds(a)})
            if label in ('NorthDock_Main_Pier','NorthDock_Bent_Quay','NorthDock_Side_Pier','NorthDock_Sandy_Arrival','EastDock_Main_Quay','EastDock_Quay_Approach'):
                c,e=a.get_actor_bounds(False,True)
                row={'label':label,'path':a.get_path_name(),**bounds(a),'positive_control':trace(game,c+unreal.Vector(0,0,e.z),z_above=300,z_below=700),'edge_surveys':[]}
                for axis in (0,1):
                    for sign in (-1,1):
                        for offset in (200,500,1200,2500):
                            p=list(c.to_tuple()); p[axis]+=sign*(e.to_tuple()[axis]+offset)
                            row['edge_surveys'].append({'axis':axis,'sign':sign,'offset_cm':offset,'probe_cm':p,'surface_below':trace(game,unreal.Vector(*p),z_above=300,z_below=2200)})
                report['docks'].append(row)
        report['success']=True
        report['vehicle_placement_present']=bool(report['vehicles'])
        report['collision_positive_controls_passed']=all(d['positive_control'] and d['positive_control']['normal'][2]>.7 for d in report['docks']) if report['docks'] else None
        save(); le.editor_request_end_play(); state.update(phase='exit',deadline=time.monotonic()+3)
    except Exception:
        report['errors'].append(traceback.format_exc()); save(); le.editor_request_end_play(); state.update(phase='exit',deadline=time.monotonic()+3)
    finally: state['busy']=False
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world: raise RuntimeError('Cannot load '+MAP)
# Crowd exclusion is temporary and disclosed; this is a geometry survey.
report['excluded_spawners']=[]
for actor in list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()):
    if actor.get_class().get_name()=='MetaHumanMassSpawner':
        report['excluded_spawners'].append(actor.get_actor_label()); unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(actor)
handle=unreal.register_slate_post_tick_callback(tick); save(); le.editor_request_begin_play()
