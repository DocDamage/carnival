"""Read actual motorcycle/rider assets and inspect their saved contact setup.

Uses an unsaved empty editor world. Does not modify or save licensed assets.
"""
import json
from pathlib import Path
import unreal

OUT = Path(r'F:\Carnival\Saved\DirtBike')
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
bike = actors.spawn_actor_from_class(unreal.load_class(None,
    '/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle.BP_CarnivalMotorcycle_C'), unreal.Vector())
rider = actors.spawn_actor_from_class(unreal.load_class(None,
    '/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter.BP_CarnivalPlayerCharacter_C'), unreal.Vector(0, 200, 100))


def path(obj):
    return obj.get_path_name() if obj else None


def components(actor):
    result = []
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        entry = {'name': component.get_name(), 'class': component.get_class().get_name(),
                 'relative_transform': str(component.get_relative_transform()),
                 'collision': str(component.get_collision_enabled()),
                 'bounds': str(unreal.SystemLibrary.get_component_bounds(component))}
        if isinstance(component, unreal.SkeletalMeshComponent):
            mesh = component.get_editor_property('skeletal_mesh_asset')
            physics = component.get_editor_property('physics_asset_override') or (mesh.get_editor_property('physics_asset') if mesh else None)
            entry.update(mesh=path(mesh),
                         physics_asset=path(physics),
                         animation_mode=str(component.get_animation_mode()),
                         anim_class=path(component.get_editor_property('anim_class')),
                         sockets=[str(name) for name in component.get_all_socket_names()])
        result.append(entry)
    return result


report = {'bike': components(bike), 'rider': components(rider),
          'seat_socket': str(bike.driver_seat_socket_name),
          'seat_exists': bike.bike_mesh.does_socket_exist(bike.driver_seat_socket_name),
          'seat_transform': str(bike.bike_mesh.get_socket_transform(bike.driver_seat_socket_name)),
          'montages': {name: path(rider.get_editor_property(name)) for name in
                       ('mount_left_montage', 'mount_right_montage', 'dismount_left_montage',
                        'dismount_right_montage', 'riding_idle_montage')},
          'clips': []}
for name in ('AS_Idle_Riding', 'AS_Mount_Left', 'AS_Mount_Right', 'AS_Dismount_Left', 'AS_Dismount_Right'):
    clip = unreal.load_asset('/Game/Carnival/Vehicles/Motorcycle/Animations/' + name)
    if not clip:
        report['clips'].append({'name': name, 'missing': True})
        continue
    options = unreal.AnimPoseEvaluationOptions()
    length = clip.get_editor_property('sequence_length')
    samples = []
    for when in (0., length * .5, max(0., length - .001)):
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(clip, when, options)
        samples.append({'time': when, 'bones': {bone: str(pose.get_bone_pose(bone, unreal.AnimPoseSpaces.WORLD))
                        for bone in ('root', 'pelvis', 'hand_l', 'hand_r', 'foot_l', 'foot_r')}})
    report['clips'].append({'name': name, 'skeleton': path(clip.get_editor_property('skeleton')),
                            'length': length, 'samples': samples})
# Exercise the saved root geometry, not a stand-in collision fixture on the bike.
wall = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(500, 0, 200))
wall.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
wall.set_actor_scale3d(unreal.Vector(.2, 6, 6))
wall.static_mesh_component.set_collision_profile_name('BlockAll')
bike.set_actor_location(unreal.Vector(0, 0, 0), False, True)
result = bike.set_actor_location(unreal.Vector(1000, 0, 0), True, False)
report['barrier_sweep'] = {'wall_x': 500, 'requested_x': 1000,
                          'final_location': bike.get_actor_location().to_tuple(),
                          'sweep_result': str(result),
                          'stopped_before_wall': bike.get_actor_location().x < 500}
(OUT / 'Presentation_Inspection.json').write_text(json.dumps(report, indent=2))
unreal.log('MOTORCYCLE_PRESENTATION_INSPECTION_COMPLETE')
