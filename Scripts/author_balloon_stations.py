"""Create reachable ground stations for the ten project-owned sightseeing balloons.

Requires CarnivalBalloonFlightComponent. Surveys the existing Carnival campus,
tests the complete basket/canopy flight volume, and collision-checks an on-foot
connection to an existing Carnival attendant or PlayerStart. Sky locations are
never accepted as boarding locations. Vendor Blueprints are preserved.

Set CARNIVAL_BALLOON_SURVEY_ONLY=1 for a read-only survey. Every written package
is backed up first. Saved survey routes still require actual player/camera PIE.
"""
import hashlib
import json
import math
import os
import shutil
from datetime import datetime
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/RideDevelopment'
MAP='/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
BP='/Game/Carnival/Rides/BP_HotAirBalloon_Carnival'
SURVEY_ONLY=os.environ.get('CARNIVAL_BALLOON_SURVEY_ONLY')=='1'
REPAIR_INDEX=os.environ.get('CARNIVAL_BALLOON_REPAIR_INDEX','')
previous_stations=None
if REPAIR_INDEX:
    REPAIR_INDEX=int(REPAIR_INDEX)
    previous=json.loads((OUT/'Balloon_Stations.json').read_text())
    assert previous.get('success') and len(previous['stations'])==10
    assert 0<=REPAIR_INDEX<10
    previous_stations=previous['stations']
FLIGHT_HEIGHT=1200.
BACKUP=OUT/('BeforeBalloonStations_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
REPORT={'survey_only':SURVEY_ONLY,'backup':str(BACKUP),'stations':[],'rejections':{},'errors':[],
        'native_flight_height_cm':FLIGHT_HEIGHT,'player_walk_acceptance':'pending','rendered_acceptance':'pending'}
REPORT['repair_index']=REPAIR_INDEX if previous_stations else None
REPORT['flight_collision_objects']='WorldStatic, WorldDynamic and PhysicsBody, matching production flight sweeps'
EAL=unreal.EditorAssetLibrary
ACTORS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
DATA=unreal.SubobjectDataBlueprintFunctionLibrary

def save():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'Balloon_Stations.json').write_text(json.dumps(REPORT,indent=2))

def backup(package):
    package=package.split('.')[0]
    assert package.startswith('/Game/')
    for extension in ('.umap','.uasset','.uexp','.ubulk'):
        relative=package.removeprefix('/Game/')+extension
        src=ROOT/'Content'/relative; dst=BACKUP/relative
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)

def reject(reason):
    REPORT['rejections'][reason]=REPORT['rejections'].get(reason,0)+1

def hit(result): return result.to_tuple() if result else None

world=unreal.EditorLoadingAndSavingUtils.load_map(MAP)
assert world
actors=list(ACTORS.get_all_level_actors())
balloons=sorted([a for a in actors if a.get_class().get_name()=='BP_HotAirBalloon_Carnival_C'],key=lambda a:a.get_name())
assert balloons,'No project-owned balloon instances found'
def survey_ignored(current_actors,current_balloons):
    # Reauthoring must sample the underlying campus, not last run's raised deck.
    # Refresh after Blueprint compilation, which can reconstruct the ride actors.
    return [a for a in current_actors if isinstance(a,unreal.Pawn)
            or a.get_actor_label().startswith('BalloonStation_')]+current_balloons

ignored=survey_ignored(actors,balloons)
curve=unreal.load_asset('/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/Structure/C_HotairBalloonFloat')
if curve:
    REPORT['vendor_curve_samples']={str(t):list(curve.get_vector_value(t).to_tuple()) for t in (0,.25,.5,1,2,5,10,20,30,60)}
    try: REPORT['vendor_curve_time_range']=list(curve.get_time_range())
    except Exception as exc: REPORT['vendor_curve_range_error']=repr(exc)

def ground(x,y):
    data=hit(unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,3500),unreal.Vector(x,y,-2000),
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignored,unreal.DrawDebugTrace.NONE,True))
    if not data or not data[0] or data[7].z<.8: return None
    if data[9] and any(token in data[9].get_name().lower() for token in ('water','ocean','river')): return None
    # Campus ground, not a roof, attraction platform, or raised scenery surface.
    if data[5].z>700: return None
    return data[5]

def capsule_clear(start,end):
    data=hit(unreal.SystemLibrary.capsule_trace_single(world,start,end,42,94,
        unreal.TraceTypeQuery.ECC_VISIBILITY,False,ignored,unreal.DrawDebugTrace.NONE,True))
    return not data or not data[0]

seeds=[]
for actor in actors:
    point=actor.get_actor_location()
    if math.hypot(point.x,point.y)>18000: continue
    if isinstance(actor,unreal.CarnivalRideAttendant) and actor.get_editor_property('ride') not in balloons:
        ride=actor.get_editor_property('ride')
        if not ride: continue
        outward=point-ride.get_actor_location(); outward.z=0
        point+=outward.normal()*180
    elif not isinstance(actor,unreal.PlayerStart): continue
    floor=ground(point.x,point.y)
    if floor:
        center=floor+unreal.Vector(0,0,97)
        if capsule_clear(center,center+unreal.Vector(0,0,.1)):
            seeds.append((actor.get_path_name(),floor))
assert seeds,'No grounded Carnival access seeds found'
REPORT['access_seeds']=[{'actor':name,'foot_cm':list(point.to_tuple())} for name,point in seeds]

def survey_route(start,finish,destination_center):
    path_points=[start,finish]
    try:
        path=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,start,finish)
        if path and path.is_valid() and not path.is_partial():
            points=list(path.get_editor_property('path_points'))
            if len(points)>1: path_points=points
    except Exception as exc:
        REPORT.setdefault('navigation_api_note',repr(exc))
    sampled=[]
    for a,b in zip(path_points,path_points[1:]):
        steps=max(1,int(math.ceil(math.hypot(a.x-b.x,a.y-b.y)/90)))
        for index in range(steps+1):
            alpha=index/steps
            floor=ground(a.x+(b.x-a.x)*alpha,a.y+(b.y-a.y)*alpha)
            if not floor: return None
            # The destination balloon is also ignored by the world trace, so
            # explicitly exclude its future grounded basket footprint. A route
            # from a west-side seed to the east queue must go around the basket.
            if math.hypot(floor.x-destination_center[0],floor.y-destination_center[1])<425: return None
            # Previously planned baskets are still at their original sky poses
            # during survey. Account for their future ground footprint as well.
            if any(math.hypot(floor.x-c['center_cm'][0],floor.y-c['center_cm'][1])<425 for c in chosen): return None
            center=floor+unreal.Vector(0,0,97)
            if sampled:
                last=unreal.Vector(*sampled[-1])
                if abs(floor.z-last.z)>38 or not capsule_clear(last+unreal.Vector(0,0,97),center): return None
            elif not capsule_clear(center,center+unreal.Vector(0,0,.1)): return None
            sampled.append(list(floor.to_tuple()))
    return sampled

# Bounded campus search. It deliberately excludes original balloon XY positions
# tens of thousands of centimeters outside the actual Carnival attractions.
candidates=[(x,y) for x in range(-15500,15501,750) for y in range(-11000,11001,750)]
candidates.sort(key=lambda p:min(math.hypot(p[0]-s.x,p[1]-s.y) for _,s in seeds))
chosen=[s for i,s in enumerate(previous_stations) if i!=REPAIR_INDEX] if previous_stations else []
for x,y in candidates:
    if len(chosen)>=len(balloons): break
    if previous_stations and [x,y]==previous_stations[REPAIR_INDEX]['center_cm'][:2]:
        reject('previous_runtime_obstructed_site'); continue
    if any(math.hypot(x-c['center_cm'][0],y-c['center_cm'][1])<2500 for c in chosen): continue
    if any(math.hypot(x-p[0],y-p[1])<425 for c in chosen for p in c['walk_route_foot_cm']):
        reject('blocks_previously_planned_walk_route'); continue
    floors=[ground(x+dx,y+dy) for dx,dy in ((0,0),(-500,-500),(-500,500),(500,-500),(500,500),
                                          (-250,0),(250,0),(0,-250),(0,250),(650,0))]
    if any(p is None for p in floors): reject('missing_ground'); continue
    heights=[p.z for p in floors]
    if max(heights)-min(heights)>16: reject('uneven_ground'); continue
    floor_z=max(heights)+26
    # The support floor is mesh-local Z=-646.1. Its bottom hull is -667.4.
    # Align floor 26 cm above highest surveyed ground: hull clears the ground.
    pivot_z=floor_z+646.1
    blocked=False
    for local_center,half in ((unreal.Vector(0,0,(-667.43-350)/2),unreal.Vector(250,250,(667.43-350)/2)),
                              (unreal.Vector(1.63,32.36,(-350+1806.6)/2),unreal.Vector(958.3,963.2,(1806.6+350)/2))):
        start=unreal.Vector(x,y,pivot_z)+local_center
        data=hit(unreal.SystemLibrary.box_trace_single_for_objects(world,start,start+unreal.Vector(0,0,FLIGHT_HEIGHT),half,
            unreal.Rotator(),[unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1,unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2,
                unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY4],False,ignored,unreal.DrawDebugTrace.NONE,True))
        if data and data[0]: blocked=True; break
    if blocked: reject('flight_volume_blocked'); continue
    approach=floors[-1]
    nearest=sorted(seeds,key=lambda s:unreal.Vector.distance(s[1],approach))[:4]
    route=None
    for seed_name,seed in nearest:
        if unreal.Vector.distance(seed,approach)>12000: continue
        route=survey_route(seed,approach,(x,y))
        if route: break
    if not route: reject('no_clear_campus_walk_route'); continue
    chosen.append({'center_cm':[x,y,floor_z],'actor_pivot_cm':[x,y,pivot_z],
                   'approach_ground_cm':list(approach.to_tuple()),'access_seed':seed_name,
                   'walk_route_foot_cm':route,'ground_height_range_cm':[min(heights),max(heights)],
                   'flight_volume_clear':True})
    REPORT['surveyed_candidates']=len(chosen); save()

if previous_stations and len(chosen)==len(balloons):
    replacement=chosen[-1]
    chosen=list(previous_stations)
    chosen[REPAIR_INDEX]=replacement
REPORT['stations']=chosen
if len(chosen)<len(balloons):
    REPORT['errors'].append(f'Only {len(chosen)} of {len(balloons)} safe campus stations found; no assets or map changed')
    save(); raise RuntimeError(REPORT['errors'][-1])
if SURVEY_ONLY:
    save(); unreal.SystemLibrary.quit_editor()
else:
    backup(MAP); backup(BP)
    bp=unreal.load_asset(BP)
    items=[(h,DATA.get_associated_object(DATA.get_data(h))) for h in SDS.k2_gather_subobject_data_for_blueprint(bp)]
    flight=next((obj for _,obj in items if isinstance(obj,unreal.CarnivalBalloonFlightComponent)),None)
    if not flight:
        parent=next(h for h,_ in items if DATA.is_actor(DATA.get_data(h)))
        new_handle,error=SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent,unreal.CarnivalBalloonFlightComponent,bp))
        flight=DATA.get_associated_object(DATA.get_data(new_handle))
        assert flight,str(error)
        SDS.rename_subobject(handle=new_handle,new_name=unreal.Text('CarnivalBalloonFlight'))
    flight.set_editor_property('flight_height',FLIGHT_HEIGHT)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert EAL.save_loaded_asset(bp,False)
    actors=list(ACTORS.get_all_level_actors())
    balloons=sorted([a for a in actors if a.get_class().get_name()=='BP_HotAirBalloon_Carnival_C'],key=lambda a:a.get_name())
    ignored=survey_ignored(actors,balloons)
    staff_bp=unreal.load_asset('/Game/Carnival/Rides/BP_RideAttendant')
    cube=unreal.load_asset('/Engine/BasicShapes/Cube')
    assert unreal.EditorLevelLibrary.set_current_level_by_name(MAP.rsplit('/',1)[-1])
    by_label={a.get_actor_label():a for a in actors}
    def block(label,position,scale):
        actor=by_label.get(label)
        if not actor:
            actor=ACTORS.spawn_actor_from_class(unreal.StaticMeshActor,position)
            actor.set_actor_label(label); by_label[label]=actor
        actor.static_mesh_component.set_static_mesh(cube)
        actor.static_mesh_component.set_collision_profile_name('BlockAll')
        actor.set_actor_location(position,False,True)
        actor.set_actor_scale3d(scale)
        return actor
    for index,(balloon,station) in enumerate(zip(balloons,chosen)):
        if previous_stations and index!=REPAIR_INDEX: continue
        station['ride']=balloon.get_path_name()
        station['original_transform']=str(balloon.get_actor_transform())
        balloon.set_actor_scale3d(unreal.Vector(1,1,1))
        balloon.set_actor_rotation(unreal.Rotator(),True)
        balloon.set_actor_location(unreal.Vector(*station['actor_pivot_cm']),False,True)
        x,y,z=station['center_cm']
        prefix='BalloonStation_'+str(index)
        # Ring deck has a 520 cm center opening: the basket's swept hull stays
        # clear of the deck while the staff and waiting player have real support.
        for suffix,offset,scale in [('East',(380,0),(2.4,10)),('West',(-380,0),(2.4,10)),
                                    ('North',(0,380),(5.2,2.4)),('South',(0,-380),(5.2,2.4))]:
            block(prefix+'_Deck_'+suffix,unreal.Vector(x+offset[0],y+offset[1],z-13),unreal.Vector(scale[0],scale[1],.26))
        staff=next((a for a in ACTORS.get_all_level_actors() if isinstance(a,unreal.CarnivalRideAttendant)
                    and a.get_editor_property('ride')==balloon),None)
        if not staff:
            staff=ACTORS.spawn_actor_from_class(staff_bp.generated_class(),unreal.Vector(x+380,y,z+92),unreal.Rotator(yaw=180))
            staff.set_actor_label(prefix+'_Attendant')
        staff.set_actor_location(unreal.Vector(x+380,y,z+92),False,True)
        staff.set_editor_property('ride',balloon)
        staff.set_editor_property('ride_name',unreal.Text('HotAirBalloon'))
        staff.set_editor_property('experience',unreal.CarnivalRideExperience.SEATED_RIDE)
        identifier='HotAirBalloon_'+hashlib.sha1(balloon.get_path_name().encode()).hexdigest()[:10]
        balloon.get_component_by_class(unreal.CarnivalRideControllerComponent).set_editor_property('ride_id',identifier)
        balloon.get_component_by_class(unreal.CarnivalRideQueueComponent).set_editor_property('ride_id',identifier)
        station['attendant']=staff.get_path_name()
        station['queue_id']=identifier
        station['queue_points']=[]
        # The first marker is the surveyed public approach, within 350 cm of staff.
        for point_index,distance in enumerate((650,770,890)):
            p=ground(x+distance,y)
            if not p: break
            center=p+unreal.Vector(0,0,97)
            if not capsule_clear(center,center+unreal.Vector(0,0,.1)): break
            label=prefix+'_Queue_'+str(point_index)
            marker=by_label.get(label)
            if not marker:
                marker=ACTORS.spawn_actor_from_class(unreal.CarnivalQueuePoint,center)
                marker.set_actor_label(label)
            marker.set_actor_location(center,False,True)
            marker.set_editor_property('ride_id',identifier)
            marker.set_editor_property('queue_index',point_index)
            station['queue_points'].append(marker.get_path_name())
        save()
    assert unreal.EditorLevelLibrary.save_current_level()
    REPORT['saved_packages']=[BP,MAP]
    REPORT['success']=True
    save(); unreal.SystemLibrary.quit_editor()
