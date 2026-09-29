"""Read-only PIE Water plugin surface/depth queries with actual body overlap.

GetWaterSurfaceInfoAtLocation calls UE5.8 TryQueryWaterInfoClosestToWorldLocation.
Its success alone is not spatial membership, so a sphere must also overlap the
same WaterBody actor just below the returned surface. Ground clearance uses a
separate collision trace ignoring water. No bounds/name-only water acceptance.
"""
import hashlib,json,os,time,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival'); OUT=ROOT/'Saved/WorldExpansion/WaterVehicleAcceptance'; OUT.mkdir(parents=True,exist_ok=True)
AREA=os.environ.get('CARNIVAL_WATER_DEPTH_AREA','docks')
if AREA not in ('docks','boat_berth'): raise ValueError('Unknown survey area')
survey_path=OUT/'main_PlacementSurvey.json'; previous=json.loads(survey_path.read_text())
report={'success':False,'source_survey_sha256':hashlib.sha256(survey_path.read_bytes()).hexdigest(),'samples':[],'water_bodies':[],'errors':[],
        'limits':'Water plugin nearest-surface query plus actual WaterBody overlap and terrain trace. Placement still needs approach, hull-clearance lane and rendered review.'}
state={'phase':'setup','deadline':time.monotonic()+240,'busy':False}
le=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def save(): (OUT/('DockWaterBerth.json' if AREA=='boat_berth' else 'DockWaterDepth.json')).write_text(json.dumps(report,indent=2))
def tick(delta):
    if state['busy']: return
    state['busy']=True
    try:
        wall=time.monotonic()
        if state['phase']=='exit':
            if wall>state['deadline']: unreal.unregister_slate_post_tick_callback(handle); unreal.SystemLibrary.quit_editor()
            return
        game=unreal.EditorLevelLibrary.get_game_world()
        if not game:
            if wall>state['deadline']: raise RuntimeError('PIE startup timed out')
            return
        if state['phase']=='setup':
            unreal.GameplayStatics.set_game_paused(game,False); state.update(phase='survey',ready=wall+1); return
        if wall<state['ready']: return
        bodies=unreal.GameplayStatics.get_all_actors_of_class(game,unreal.WaterBody)
        report['vehicle_mesh_bounds']=[]
        for path in ('/Game/Mars_Futuristic_Cars/Static_Meshes/SM_rover4_SM','/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Speed_Boat','/Game/LightHouse_Meshingun/Meshes/Props/Boat_Trailer/SM_Prop_Inflatable_Boat'):
            mesh=unreal.load_asset(path)
            box=mesh.get_bounding_box() if mesh else None
            report['vehicle_mesh_bounds'].append({'path':path,'bounds_min_cm':box.min.to_tuple() if box else None,'bounds_max_cm':box.max.to_tuple() if box else None})
        # A 30 m hovercraft candidate lane on the existing 15 m-wide pier.
        # Sample center and hull sides; traces are evidence, not route acceptance.
        report['hover_deck_lane']=[]
        for x in (-57300,-57000,-56700):
            for y in range(-53000,-49499,250):
                trace=unreal.SystemLibrary.line_trace_single(game,unreal.Vector(x,y,1000),unreal.Vector(x,y,400),
                    unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
                h=trace.to_tuple() if trace else None
                report['hover_deck_lane'].append({'xy_cm':[x,y],'floor':{'point_cm':h[5].to_tuple(),'normal':h[7].to_tuple(),'actor':h[9].get_actor_label() if h[9] else None,'initial_overlap':bool(h[1])} if h and h[0] else None})
        report['api_documentation']=unreal.WaterBodyComponent.get_water_surface_info_at_location.__doc__
        if not bodies: raise RuntimeError('No native WaterBody in integrated world')
        for body in bodies: report['water_bodies'].append({'label':body.get_actor_label(),'path':body.get_path_name()})
        points=set()
        for d in previous['docks']:
            for p in d['edge_surveys']: points.add(tuple(p['probe_cm'][:2]))
        if AREA=='boat_berth':
            points=set()
            # Deep basin southeast of the existing SidePier, plus ramp/berth.
            for x in range(-50500,-47999,100):
                for y in range(-59000,-54999,100): points.add((x,y))
        else:
            for x in range(-61000,-44999,1000):
                for y in range(-59000,-42999,1000): points.add((x,y))
            for x in range(64000,76001,1000):
                for y in range(10000,28001,1000): points.add((x,y))
        for x,y in sorted(points):
            for body in bodies:
                component=body.get_water_body_component()
                result=component.get_water_surface_info_at_location(unreal.Vector(x,y,-300),True)
                row={'query_xy_cm':[x,y],'body':body.get_actor_label(),'query_succeeded':result is not None}
                if result:
                    values=list(result)
                    if len(values)==5: row['query_succeeded']=bool(values.pop(0))
                    if len(values)!=4: raise RuntimeError('Unexpected water API result '+str(result))
                    surface,normal,velocity,depth=values
                    row.update(surface_cm=surface.to_tuple(),normal=normal.to_tuple(),velocity_cm_s=velocity.to_tuple(),plugin_depth_cm=depth)
                    overlaps=unreal.SystemLibrary.sphere_overlap_actors(game,unreal.Vector(x,y,surface.z-50),5,
                        [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1],unreal.WaterBody,[])
                    row['same_body_overlap']=body in (overlaps or [])
                    trace=unreal.SystemLibrary.line_trace_single(game,unreal.Vector(x,y,surface.z+100),unreal.Vector(x,y,surface.z-5000),
                        unreal.TraceTypeQuery.ECC_VISIBILITY,False,bodies,unreal.DrawDebugTrace.NONE,True)
                    h=trace.to_tuple() if trace else None
                    row['ground']=None
                    if h and h[0]: row['ground']={'actor':h[9].get_actor_label() if h[9] else None,'point_cm':h[5].to_tuple(),'normal':h[7].to_tuple(),'initial_overlap':bool(h[1]),'depth_below_surface_cm':surface.z-h[5].z}
                report['samples'].append(row)
        report['success']=True; save(); le.editor_request_end_play(); state.update(phase='exit',deadline=wall+3)
    except Exception:
        report['errors'].append(traceback.format_exc()); save(); le.editor_request_end_play(); state.update(phase='exit',deadline=time.monotonic()+3)
    finally: state['busy']=False
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
if not unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'): raise RuntimeError('Main world load failed')
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report['excluded_spawners']=[]
for a in list(eas.get_all_level_actors()):
    if a.get_class().get_name()=='MetaHumanMassSpawner': report['excluded_spawners'].append(a.get_actor_label()); eas.destroy_actor(a)
handle=unreal.register_slate_post_tick_callback(tick); save(); le.editor_request_begin_play()
