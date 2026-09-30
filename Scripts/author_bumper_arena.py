"""Author project-owned drivable bumper cars around the saved vendor arena.

Run only after the native bumper classes build. Keeps vendor blueprints/meshes
unchanged, backs up map and project child, and reports geometric acceptance.
"""
import hashlib
import json
import math
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT/'Saved/RideDevelopment'
BACKUP = OUT/('BeforeBumperArena_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
MAP = '/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
BP_PATH = '/Game/Carnival/Rides/Attended/BP_Attended_BumperArena'
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
DATA = unreal.SubobjectDataBlueprintFunctionLibrary
AL = unreal.EditorAssetLibrary
REPORT = {'cars': [], 'saved_packages': [], 'errors': [], 'backup': str(BACKUP),
          'vendor_assets_modified': False, 'runtime_acceptance': 'not_run',
          'seat_visual_fit': 'Initial geometry placement; rendered fit requires verification'}


def backup(package):
    assert package.startswith('/Game/')
    for extension in ('.uasset', '.umap', '.uexp', '.ubulk'):
        relative = package[len('/Game/'):] + extension
        source = ROOT/'Content'/relative
        if source.exists():
            destination = BACKUP/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def components(bp):
    return [(handle, DATA.get_associated_object(DATA.get_data(handle)))
            for handle in SDS.k2_gather_subobject_data_for_blueprint(bp)]


def ensure_component(bp, cls, name):
    items = components(bp)
    existing = next((obj for _, obj in items if isinstance(obj, cls)), None)
    if existing:
        return existing
    root = next(handle for handle, _ in items if DATA.is_actor(DATA.get_data(handle)))
    handle, failure = SDS.add_new_subobject(unreal.AddNewSubobjectParams(root, cls, bp))
    obj = DATA.get_associated_object(DATA.get_data(handle))
    assert obj, str(failure)
    SDS.rename_subobject(handle=handle, new_name=unreal.Text(name))
    return obj


def transform_point(transform, point):
    return unreal.MathLibrary.transform_location(transform, point)


def clear_capsule(world, point, ignore):
    hit = unreal.SystemLibrary.capsule_trace_single(world, point, point+unreal.Vector(0,0,.1),
        42, 96, unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, unreal.DrawDebugTrace.NONE, True)
    return not hit or not hit.to_tuple()[0]


def ground_point(world, point, height=98, ignore=None):
    hit = unreal.SystemLibrary.line_trace_single(world, point+unreal.Vector(0,0,250), point-unreal.Vector(0,0,500),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore or [], unreal.DrawDebugTrace.NONE, True)
    data = hit.to_tuple() if hit else None
    return data[5]+unreal.Vector(0,0,height) if data and data[0] and data[7].z>.7 else None


def shown(component):
    # SceneComponent visibility is a per-component flag; parenting does not
    # combine these flags. SetVisibility only propagates when explicitly asked.
    return component.is_visible() and not component.get_editor_property('hidden_in_game')


try:
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    assert world
    ride = next((actor for actor in ACTORS.get_all_level_actors()
                 if 'bumper' in actor.get_class().get_name().lower() and not isinstance(actor, unreal.CarnivalBumperCar)), None)
    assert ride, 'Placed vendor arena not found'
    original_path = ride.get_path_name()
    level_package = ride.get_level().get_path_name().split('.')[0]
    backup(level_package); backup(BP_PATH)
    bp = unreal.load_asset(BP_PATH) if AL.does_asset_exist(BP_PATH) else None
    if not bp:
        factory = unreal.BlueprintFactory(); factory.set_editor_property('parent_class', ride.get_class())
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(BP_PATH.rsplit('/',1)[1], BP_PATH.rsplit('/',1)[0], unreal.Blueprint, factory)
    assert bp
    controller_template = ensure_component(bp, unreal.CarnivalRideControllerComponent, 'CarnivalRideController')
    controller_template.set_editor_property('auto_detect_phase', False)
    ensure_component(bp, unreal.CarnivalRideQueueComponent, 'CarnivalRideQueue')
    ensure_component(bp, unreal.CarnivalBumperArenaComponent, 'BumperArena')
    operation_template = ensure_component(bp, unreal.CarnivalRideOperationComponent, 'CarnivalRideOperation')
    operation_template.set_editor_property('experience', unreal.CarnivalRideExperience.DRIVING_ARENA)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert AL.save_loaded_asset(bp)
    REPORT['saved_packages'].append(BP_PATH)
    ride = next(actor for actor in ACTORS.get_all_level_actors() if actor.get_path_name()==original_path)
    if ride.get_class()!=bp.generated_class():
        converted = ACTORS.convert_actors([ride], bp.generated_class(), '/Game/Carnival/Rides/Converted')
        assert len(converted)==1
        ride=converted[0]
    ride.set_actor_label('Bumper Cars - Staffed Driving Arena')
    assert unreal.EditorLevelLibrary.set_current_level_by_name(level_package.rsplit('/',1)[1])
    arena = ride.get_component_by_class(unreal.CarnivalBumperArenaComponent)
    mesh_components = list(ride.get_components_by_class(unreal.StaticMeshComponent))
    REPORT['mesh_components']=[{'name':component.get_name(),
        'mesh':component.get_editor_property('static_mesh').get_path_name() if component.get_editor_property('static_mesh') else None,
        'visible':component.is_visible(),'hidden_in_game':bool(component.get_editor_property('hidden_in_game')),
        'transform':str(component.get_world_transform())} for component in mesh_components]
    platform = next(component for component in mesh_components if 'bumpercarplatform' in component.get_name().lower())
    box = platform.get_editor_property('static_mesh').get_bounding_box()
    platform_transform = platform.get_world_transform()
    inverse = unreal.MathLibrary.invert_transform(ride.get_actor_transform())
    corners = [transform_point(inverse, transform_point(platform_transform, unreal.Vector(x,y,z)))
               for x in (box.min.x,box.max.x) for y in (box.min.y,box.max.y) for z in (box.min.z,box.max.z)]
    low = unreal.Vector(min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners))
    high = unreal.Vector(max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners))
    # These are BlueprintReadWrite runtime properties. Editor property setters
    # invoke PostEditChange and reconstruct the entire placed Blueprint, making
    # all cached component references TRASH objects. Direct assignment keeps the
    # component identity stable; SaveCurrentLevel below saves the current level
    # explicitly, including these serialized values.
    arena.local_center = (low+high)*.5
    arena.half_extent = unreal.Vector2D((high.x-low.x)*.5-30, (high.y-low.y)*.5-30)
    assert arena == ride.get_component_by_class(unreal.CarnivalBumperArenaComponent)
    assert not platform.get_name().startswith('TRASH_'), 'Platform was reconstructed while configuring arena'
    REPORT['platform']={'component':platform.get_name(),'mesh':platform.get_editor_property('static_mesh').get_path_name(),
                        'transform':str(platform_transform),'arena_local_low':list(low.to_tuple()),'arena_local_high':list(high.to_tuple())}
    existing = list(arena.get_editor_property('cars'))
    cars = [car for car in existing if car]
    source_cars = [component for component in mesh_components
                   if component.get_editor_property('static_mesh') and
                   component.get_name().lower().startswith('sm_bumpercar')
                   and not any(word in component.get_name().lower() for word in ('entrance','platform','text'))]
    REPORT['source_car_candidates']=[]
    for component in source_cars:
        mesh=component.get_editor_property('static_mesh')
        box=mesh.get_bounding_box()
        hierarchy=[]
        parent=component.get_attach_parent()
        while parent:
            hierarchy.append({'name':parent.get_name(),'visible':parent.is_visible(),
                              'hidden_in_game':bool(parent.get_editor_property('hidden_in_game'))})
            parent=parent.get_attach_parent()
        REPORT['source_car_candidates'].append({'name':component.get_name(),'mesh':mesh.get_path_name(),
            'visible':component.is_visible(),'hidden_in_game':bool(component.get_editor_property('hidden_in_game')),
            'transform':str(component.get_world_transform()),'bounds_min':list(box.min.to_tuple()),
            'bounds_max':list(box.max.to_tuple()),'parents':hierarchy,
            'materials':[component.get_material(slot).get_path_name() if component.get_material(slot) else None
                         for slot in range(component.get_num_materials())]})
    visible_sources = [component for component in source_cars if shown(component)]
    REPORT['source_components']=[component.get_name() for component in visible_sources]
    if not cars:
        for index, component in enumerate(visible_sources):
            mesh = component.get_editor_property('static_mesh')
            original = component.get_world_transform()
            bounds = mesh.get_bounding_box()
            scale = original.scale3d
            hull_x=max(40.,(bounds.max.x-bounds.min.x)*abs(scale.x)*.5)
            hull_y=max(40.,(bounds.max.y-bounds.min.y)*abs(scale.y)*.5)
            hull_radius=math.hypot(hull_x,hull_y)
            # Keep the visual transform exactly, but use a low chassis collision
            # hull; antenna/pole height must not determine the bumper hull height.
            center = transform_point(original, (bounds.min+bounds.max)*.5)
            bottom = min(transform_point(original, unreal.Vector(x,y,bounds.min.z)).z
                         for x in (bounds.min.x,bounds.max.x) for y in (bounds.min.y,bounds.max.y))
            location = unreal.Vector(center.x,center.y,bottom+36)
            if not arena.contains_car_location(location, hull_radius):
                REPORT['cars'].append({'source':component.get_name(),'skipped':'Outside measured platform bounds'})
                continue
            car = ACTORS.spawn_actor_from_class(unreal.CarnivalBumperCar, location, component.get_world_rotation())
            assert car and car.get_level()==ride.get_level()
            car.set_actor_label('BumperDriver_'+str(index))
            visual = car.get_editor_property('car_mesh')
            car.get_editor_property('hull').set_box_extent(unreal.Vector(hull_x,hull_y,35),True)
            visual.set_mobility(unreal.ComponentMobility.MOVABLE)
            visual.set_static_mesh(mesh)
            visual.set_world_transform(original,False,True)
            for slot in range(component.get_num_materials()): visual.set_material(slot,component.get_material(slot))
            car.arena = arena
            cars.append(car)
            REPORT['cars'].append({'source':component.get_name(),'car':car.get_path_name(),'mesh':mesh.get_path_name(),
                                   'location':list(location.to_tuple()),'hull_half_extent_cm':[hull_x,hull_y,35]})
    assert cars, 'No visible source cars lie on the measured arena platform'
    arena.replaced_display_car_components = [unreal.Name(component.get_name()) for component in source_cars]
    REPORT['replaced_display_car_components'] = [component.get_name() for component in source_cars]
    for component in source_cars:
        component.set_visibility(False, True)
        component.set_hidden_in_game(True, True)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    arena.cars = cars
    instance_id='BumperCars_'+hashlib.sha1(ride.get_path_name().encode()).hexdigest()[:10]
    ride.get_component_by_class(unreal.CarnivalRideControllerComponent).ride_id = instance_id
    ride.get_component_by_class(unreal.CarnivalRideQueueComponent).ride_id = instance_id
    # Select supported ground with a clear player-to-driver capsule path. This
    # provides a real boarding bay instead of teleporting through arena fences.
    bay = None
    entrance = next((component for component in mesh_components if 'bumpercarentrance' in component.get_name().lower()),platform)
    cars.sort(key=lambda car:unreal.Vector.distance(car.get_actor_location(),entrance.get_world_location()))
    for car in cars:
        for distance in (180,260,340):
            for index in range(16):
                angle = index*math.tau/16
                candidate = ground_point(world,car.get_actor_location()+unreal.Vector(math.cos(angle)*distance,math.sin(angle)*distance,0),ignore=[car])
                if not candidate or not clear_capsule(world,candidate,[]): continue
                seat = car.get_editor_property('driver_seat').get_passenger_world_transform().translation
                hit = unreal.SystemLibrary.capsule_trace_single(world,candidate,seat,42,96,
                    unreal.TraceTypeQuery.ECC_VISIBILITY,False,[car],unreal.DrawDebugTrace.NONE,True)
                if hit and hit.to_tuple()[0]: continue
                staff_position = ground_point(world,candidate+unreal.Vector(-math.sin(angle)*130,math.cos(angle)*130,0),height=92,ignore=[car])
                if not staff_position or not clear_capsule(world,staff_position+unreal.Vector(0,0,6),[]): continue
                bay=(candidate,staff_position,car); break
            if bay: break
        if bay: break
    assert bay, 'No capsule-clear supported boarding bay; map was not saved'
    approach,staff_position,boarding_car=bay
    staff=next((actor for actor in ACTORS.get_all_level_actors() if isinstance(actor,unreal.CarnivalRideAttendant)
                and actor.get_editor_property('ride')==ride),None)
    if not staff:
        staff_class=unreal.load_asset('/Game/Carnival/Rides/BP_RideAttendant').generated_class()
        staff=ACTORS.spawn_actor_from_class(staff_class,staff_position,unreal.MathLibrary.find_look_at_rotation(staff_position,boarding_car.get_actor_location()))
    staff.ride = ride
    staff.ride_name = unreal.Text('BumperCars')
    staff.experience = unreal.CarnivalRideExperience.DRIVING_ARENA
    marker=next((actor for actor in ACTORS.get_all_level_actors() if isinstance(actor,unreal.CarnivalQueuePoint)
                 and str(actor.get_editor_property('ride_id'))==instance_id),None)
    if not marker:
        marker=ACTORS.spawn_actor_from_class(unreal.CarnivalQueuePoint,approach)
        marker.ride_id = instance_id
        marker.queue_index = 0
    REPORT.update(ride=ride.get_path_name(),attendant=staff.get_path_name(),queue=marker.get_path_name(),
                  approach=list(approach.to_tuple()),boarding_car=boarding_car.get_path_name(),
                  arena_center=list(arena.get_editor_property('local_center').to_tuple()),
                  arena_half_extent=str(arena.get_editor_property('half_extent')))
    assert unreal.EditorLevelLibrary.save_current_level()
    REPORT['saved_packages'].append(level_package)
except Exception:
    REPORT['errors'].append(traceback.format_exc())
finally:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'BumperArena_Authoring.json').write_text(json.dumps(REPORT,indent=2))
    unreal.log('BUMPER_ARENA_AUTHORING '+json.dumps(REPORT))
    unreal.SystemLibrary.quit_editor()
