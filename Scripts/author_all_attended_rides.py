"""Incrementally author attended rides from measured mesh-local seat anchors.

Run export_ride_seat_geometry.py and author Config/RideSeatCalibration.json first.
Existing calibrated seats are preserved. Vendor Blueprint assets are never edited;
vendor instances are converted to project-owned children in their original level.
Every touched package is copied to a timestamped backup before saving.
Unsupported driving attractions remain explicit blockers, never become shows.
"""
import hashlib
import json
import math
import os
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir())
OUT = PROJECT / 'Saved/RideDevelopment'
BACKUP = OUT / ('BeforeAllAttended_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
MAP = '/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival'
FOLDER = '/Game/Carnival/Rides/Attended'
CALIBRATION = PROJECT / 'Config/RideSeatCalibration.json'
SELECTED = set(filter(None, os.environ.get('CARNIVAL_RIDE_FAMILIES', '').split(',')))
EAL = unreal.EditorAssetLibrary
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
DATA = unreal.SubobjectDataBlueprintFunctionLibrary
REPORT = {'saved_packages': [], 'rides': [], 'errors': [], 'backup': str(BACKUP),
          'runtime_acceptance': 'not_run', 'vendor_blueprints_modified': False}
AUTHORED_CLASSES = {}
calibration = json.loads(CALIBRATION.read_text()) if CALIBRATION.exists() else {'meshes': {}}
# Fit the saved seated clip's pelvis to a seat surface plus 10 cm of hip
# thickness. This is measurable initial authoring; full skinned fit is reviewed
# separately in rendered acceptance and can override per-mesh offsets later.
player_class = unreal.load_class(None, '/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C')
player_defaults = unreal.get_default_object(player_class)
clip = player_defaults.get_editor_property('ride_seated_animation')
pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(clip, .5, unreal.AnimPoseEvaluationOptions())
pelvis = pose.get_bone_pose('pelvis', unreal.AnimPoseSpaces.WORLD)
local_pelvis = unreal.MathLibrary.transform_location(player_defaults.get_editor_property('mesh').get_relative_transform(), pelvis.translation)
SEATED_OFFSET = [-local_pelvis.x, -local_pelvis.y, 10-local_pelvis.z]
REPORT['seated_pose_fit'] = {'clip': clip.get_path_name(), 'pelvis_relative_to_capsule_cm': list(local_pelvis.to_tuple()),
                           'offset_cm': SEATED_OFFSET, 'skinned_visual_acceptance': 'pending'}


def backup(package):
    package = package.split('.')[0]
    if not package.startswith('/Game/'):
        raise ValueError('Only project content may be authored: ' + package)
    for ext in ('.uasset', '.umap', '.uexp', '.ubulk'):
        rel = package.removeprefix('/Game/') + ext
        source = PROJECT / 'Content' / rel
        destination = BACKUP / rel
        if source.exists() and not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def family(actor):
    name = actor.get_class().get_name().lower()
    for token, result in [('ferriswheel', 'FerrisWheel'), ('carousel', 'Carousel'),
                          ('pirateship', 'PirateShip'), ('swing_', 'Swing'),
                          ('teapot', 'Teapot'), ('flyingbobs', 'FlyingBobs'),
                          ('balloontower', 'BalloonTower'), ('clown', 'ClownRide'),
                          ('hotairballoon', 'HotAirBalloon'), ('circus_', 'Circus'),
                          ('hauntedhouse', 'HauntedHouse'), ('bumpercars', 'BumperCars')]:
        if token in name: return result
    return None


def objects(bp):
    return [(h, DATA.get_associated_object(DATA.get_data(h)))
            for h in SDS.k2_gather_subobject_data_for_blueprint(bp)]


def add_component(bp, parent, cls, name):
    handle, failure = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent, cls, bp))
    obj = DATA.get_associated_object(DATA.get_data(handle))
    if not obj: raise RuntimeError(str(failure))
    SDS.rename_subobject(handle=handle, new_name=unreal.Text(name))
    return obj


def author_blueprint(actor, ride_id):
    class_path = actor.get_class().get_path_name()
    if class_path in AUTHORED_CLASSES:
        bp, mode, count = AUTHORED_CLASSES[class_path]
        return bp, mode, [], count
    original_package = class_path.split('.')[0]
    if original_package.startswith('/Game/Carnival/'):
        path = original_package
        bp = unreal.load_asset(path)
    else:
        name = 'BP_Attended_' + actor.get_class().get_name().removesuffix('_C').removeprefix('BP_')
        path = FOLDER + '/' + name
        bp = unreal.load_asset(path) if EAL.does_asset_exist(path) else None
        if not bp:
            factory = unreal.BlueprintFactory()
            factory.set_editor_property('parent_class', actor.get_class())
            bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, unreal.Blueprint, factory)
    assert bp, class_path
    backup(path)
    items = objects(bp)
    root = next(h for h, obj in items if DATA.is_actor(DATA.get_data(h)))
    controller = next((obj for _, obj in items if isinstance(obj, unreal.CarnivalRideControllerComponent)), None)
    if not controller:
        controller = add_component(bp, root, unreal.CarnivalRideControllerComponent, 'CarnivalRideController')
    controller.set_editor_property('ride_id', ride_id)
    controller.set_editor_property('auto_detect_phase', False)
    queue = next((obj for _, obj in items if isinstance(obj, unreal.CarnivalRideQueueComponent)), None)
    if not queue:
        queue = add_component(bp, root, unreal.CarnivalRideQueueComponent, 'CarnivalRideQueue')
    queue.set_editor_property('ride_id', ride_id)
    mode = ('SHOW' if ride_id == 'Circus' else 'WALKTHROUGH' if ride_id == 'HauntedHouse' else 'SEATED_RIDE')
    operation = next((obj for _, obj in items if isinstance(obj, unreal.CarnivalRideOperationComponent)), None)
    if not operation:
        operation = add_component(bp, root, unreal.CarnivalRideOperationComponent, 'CarnivalRideOperation')
    operation.set_editor_property('experience', getattr(unreal.CarnivalRideExperience, mode))
    existing_ids = {str(obj.get_editor_property('seat_id')) for _, obj in items
                    if isinstance(obj, unreal.CarnivalRideSeatComponent)}
    added = []
    for handle, component in items:
        if not isinstance(component, unreal.StaticMeshComponent): continue
        mesh = component.get_editor_property('static_mesh')
        if not mesh: continue
        layout = calibration['meshes'].get(mesh.get_path_name())
        if not layout: continue
        if not layout.get('geometry_reviewed'):
            raise RuntimeError('Unreviewed mesh calibration: ' + mesh.get_path_name())
        name = component.get_name().removesuffix('_GEN_VARIABLE')
        for index, anchor in enumerate(layout['anchors']):
            seat_id = name + '_' + str(index)
            if seat_id in existing_ids: continue
            seat = add_component(bp, handle, unreal.CarnivalRideSeatComponent, 'Seat_' + seat_id)
            seat.set_editor_property('seat_id', seat_id)
            seat.set_editor_property('standing_passenger', layout.get('standing_passenger', False))
            seat.set_editor_property('relative_location', unreal.Vector(*anchor['location']))
            seat.set_editor_property('relative_rotation', unreal.Rotator(yaw=anchor['yaw']))
            offset = layout.get('passenger_offset', [0,0,96] if layout.get('standing_passenger') else SEATED_OFFSET)
            seat.set_editor_property('passenger_offset', unreal.Transform(location=unreal.Vector(*offset)))
            existing_ids.add(seat_id)
            added.append(seat_id)
    # Anchors follow mesh-scaled positions, but passenger fitting offsets are
    # centimeters for a full-size person rather than inherited mesh scale.
    for _, component in objects(bp):
        if isinstance(component, unreal.CarnivalRideSeatComponent) and component.get_name().startswith('Seat_'):
            component.set_absolute(False,False,True)
            component.set_editor_property('relative_scale3d',unreal.Vector(1,1,1))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert EAL.save_loaded_asset(bp, False), path
    REPORT['saved_packages'].append(path)
    AUTHORED_CLASSES[class_path] = (bp, mode, len(existing_ids))
    AUTHORED_CLASSES[bp.generated_class().get_path_name()] = (bp, mode, len(existing_ids))
    return bp, mode, added, len(existing_ids)


def clear_staff_position(world, ride):
    origin, extent = ride.get_actor_bounds(False)
    candidates = []
    # Use the mesh bounds only to propose exterior locations. Ground support and
    # two clear capsule positions are required; bounds alone cannot approve one.
    for margin in (150, 300, 500):
        for index in range(24):
            angle = index * math.tau / 24
            candidates.append(unreal.Vector(origin.x + (extent.x + margin) * math.cos(angle),
                                             origin.y + (extent.y + margin) * math.sin(angle),
                                             ride.get_actor_location().z))
    for candidate in candidates:
        hit = unreal.SystemLibrary.line_trace_single(world, candidate + unreal.Vector(0,0,400),
            candidate - unreal.Vector(0,0,1800), unreal.TraceTypeQuery.ECC_VISIBILITY,
            False, [ride], unreal.DrawDebugTrace.NONE, True)
        data = hit.to_tuple() if hit else None
        if not data or not data[0] or data[7].z < .75: continue
        ground = data[5]
        position = unreal.Vector(candidate.x, candidate.y, ground.z + 92)
        direction = unreal.Vector(candidate.x-origin.x, candidate.y-origin.y, 0).normal()
        approach = position + direction * 180
        approach_floor = unreal.SystemLibrary.line_trace_single(world, approach+unreal.Vector(0,0,50),
            approach-unreal.Vector(0,0,150), unreal.TraceTypeQuery.ECC_VISIBILITY,
            False, [ride], unreal.DrawDebugTrace.NONE, True)
        approach_data = approach_floor.to_tuple() if approach_floor else None
        if (not approach_data or not approach_data[0] or approach_data[7].z < .75
                or abs(approach_data[5].z-ground.z)>25): continue
        blocked = False
        for point in (position, approach):
            sweep = unreal.SystemLibrary.capsule_trace_single(world, point, point + unreal.Vector(0,0,.1),
                42, 90, unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
            if sweep and sweep.to_tuple()[0]: blocked = True; break
        if not blocked:
            return position, unreal.MathLibrary.find_look_at_rotation(position, origin), {
                'floor': data[9].get_path_name() if data[9] else None,
                'position': list(position.to_tuple()), 'approach': list(approach.to_tuple())}
    raise RuntimeError('No supported clear staff/player approach found around ride')


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
assert world, MAP
REPORT['manager_settings'] = []
for manager in ACTORS.get_all_level_actors():
    if 'Manager' not in manager.get_class().get_name() or 'Carnival' not in manager.get_class().get_name(): continue
    entry={'actor':manager.get_path_name(),'variables':{},'controls':list(unreal.CarnivalRideOperationComponent.describe_ride_controls(manager))}
    try:
        entry['properties']=list(unreal.CarnivalRideOperationComponent.describe_ride_properties(manager))
        property_name='bEnableControlRideCycles?'
        entry['prior_global_cycle_control']=bool(manager.get_editor_property(property_name))
        package=manager.get_level().get_path_name().split('.')[0]
        backup(package)
        manager.set_editor_property(property_name,False)
        assert not manager.get_editor_property(property_name)
        assert unreal.EditorLevelLibrary.set_current_level_by_name(package.rsplit('/',1)[-1])
        assert unreal.EditorLevelLibrary.save_current_level()
        entry['global_cycle_control']=False
        REPORT['saved_packages'].append(package)
    except Exception as exc:
        entry['inspection_error']=repr(exc)
    REPORT['manager_settings'].append(entry)
staff_bp = unreal.load_asset('/Game/Carnival/Rides/BP_RideAttendant')
assert staff_bp
targets = [(a.get_path_name(), a.get_actor_label(), family(a)) for a in ACTORS.get_all_level_actors()
           if family(a) and (not SELECTED or family(a) in SELECTED)]
for original_path, label, ride_id in targets:
    row = {'original_path': original_path, 'family': ride_id, 'label': label}
    REPORT['rides'].append(row)
    if ride_id == 'BumperCars':
        row['blocker'] = 'Dedicated player driving and arena lifecycle required'
        continue
    try:
        actor = next((a for a in ACTORS.get_all_level_actors() if a.get_path_name() == original_path), None)
        if not actor: raise RuntimeError('Ride instance disappeared after Blueprint compile')
        level_path = actor.get_level().get_path_name().split('.')[0]
        backup(level_path)
        bp, mode, added, seat_count = author_blueprint(actor, ride_id)
        # Compilation can reconstruct instances: resolve the original reference.
        actor = next(a for a in ACTORS.get_all_level_actors() if a.get_path_name() == original_path)
        if actor.get_class() != bp.generated_class():
            original_location = actor.get_actor_location()
            converted = ACTORS.convert_actors([actor], bp.generated_class(), '/Game/Carnival/Rides/Converted')
            # UE's ConvertActors returns selected actors, not the actual
            # conversion result. Hidden lighting levels cannot select their
            # new actor even when DoConvertActors succeeded. Resolve only an
            # exact class/level/label/location match before continuing.
            if not converted:
                converted = [candidate for candidate in unreal.ObjectIterator(unreal.Actor)
                    if candidate.get_class() == bp.generated_class()
                    and candidate.get_level()
                    and candidate.get_level().get_path_name().split('.')[0] == level_path
                    and candidate.get_actor_label() == label
                    and (candidate.get_actor_location()-original_location).length() < .1]
            if len(converted) != 1:
                row['conversion_candidates']=[{'path':candidate.get_path_name(),
                    'label':candidate.get_actor_label(),'location':list(candidate.get_actor_location().to_tuple()),
                    'level':candidate.get_level().get_path_name()}
                    for candidate in unreal.ObjectIterator(unreal.Actor)
                    if candidate.get_class() == bp.generated_class() and candidate.get_level()]
                raise RuntimeError('Ride conversion failed')
            actor = converted[0]
            actor.set_actor_label(label)
        assert actor.get_level().get_path_name().split('.')[0] == level_path, 'Conversion changed level'
        assert unreal.EditorLevelLibrary.set_current_level_by_name(level_path.rsplit('/',1)[-1]), level_path
        row.update({'path': actor.get_path_name(), 'experience': mode, 'added_seats': added, 'seat_count': seat_count})
        staff = next((a for a in ACTORS.get_all_level_actors() if isinstance(a, unreal.CarnivalRideAttendant)
                      and a.get_editor_property('ride') == actor), None)
        if not staff:
            position, rotation, evidence = clear_staff_position(world, actor)
            assert unreal.EditorLevelLibrary.set_current_level_by_name(level_path.rsplit('/',1)[-1]), level_path
            staff = ACTORS.spawn_actor_from_class(staff_bp.generated_class(), position, rotation)
            assert staff and staff.get_level() == actor.get_level()
            staff.set_actor_label('Attendant_' + ride_id + '_' + hashlib.sha1(original_path.encode()).hexdigest()[:8])
            staff.set_editor_property('ride', actor)
            row['placement'] = evidence
        staff.set_editor_property('ride_name', unreal.Text(ride_id))
        staff.set_editor_property('experience', getattr(unreal.CarnivalRideExperience, mode))
        row['attendant'] = staff.get_path_name()
        # Every placed instance owns its queue. Lighting variants and the ten
        # balloons must never discover one another's markers through a shared ID.
        instance_id = ride_id+'_'+hashlib.sha1(actor.get_path_name().encode()).hexdigest()[:10]
        actor.get_component_by_class(unreal.CarnivalRideControllerComponent).set_editor_property('ride_id', instance_id)
        actor.get_component_by_class(unreal.CarnivalRideQueueComponent).set_editor_property('ride_id', instance_id)
        row['queue_id'] = instance_id
        existing_points = [a for a in ACTORS.get_all_level_actors() if isinstance(a,unreal.CarnivalQueuePoint)
                           and str(a.get_editor_property('ride_id')) == instance_id]
        row['queue_markers'] = [a.get_path_name() for a in existing_points]
        if not existing_points:
            outward=staff.get_actor_location()-actor.get_actor_location(); outward.z=0
            outward=outward.normal()
            for index in range(4):
                proposed=staff.get_actor_location()+outward*(220+index*120)
                hit=unreal.SystemLibrary.line_trace_single(world,proposed+unreal.Vector(0,0,80),
                    proposed-unreal.Vector(0,0,180),unreal.TraceTypeQuery.ECC_VISIBILITY,
                    False,[staff],unreal.DrawDebugTrace.NONE,True)
                data=hit.to_tuple() if hit else None
                if not data or not data[0] or data[7].z<.75: break
                position=unreal.Vector(proposed.x,proposed.y,data[5].z+96)
                hit=unreal.SystemLibrary.capsule_trace_single(world,position,position+unreal.Vector(0,0,.1),
                    42,90,unreal.TraceTypeQuery.ECC_VISIBILITY,False,[],unreal.DrawDebugTrace.NONE,True)
                if hit and hit.to_tuple()[0]: break
                marker=ACTORS.spawn_actor_from_class(unreal.CarnivalQueuePoint,position)
                marker.set_actor_label('AttendedQueue_'+instance_id+'_'+str(index))
                marker.set_editor_property('ride_id',instance_id)
                marker.set_editor_property('queue_index',index)
                row['queue_markers'].append(marker.get_path_name())
        if not row['queue_markers']: row['queue_warning']='No clear grounded queue positions near attendant'
        if not seat_count and mode == 'SEATED_RIDE': row['blocker'] = 'No measured passenger seat calibration yet'
        assert unreal.EditorLevelLibrary.set_current_level_by_name(level_path.rsplit('/',1)[-1]), level_path
        assert unreal.EditorLevelLibrary.save_current_level(), level_path
        REPORT['saved_packages'].append(level_path)
    except Exception as exc:
        row['error'] = repr(exc)
        row['traceback'] = traceback.format_exc()
        REPORT['errors'].append({'ride': original_path, 'error': repr(exc)})
        unreal.log_warning('ATTENDED_AUTHORING ' + repr(exc))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'All_Attended_Authoring.json').write_text(json.dumps(REPORT, indent=2))
unreal.log('ATTENDED_AUTHORING_COMPLETE ' + json.dumps({'rides': len(REPORT['rides']), 'errors': REPORT['errors']}))
unreal.SystemLibrary.quit_editor()
