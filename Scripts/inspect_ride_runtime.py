"""Read the ride control API and existing character assets without changing them."""
import json
from pathlib import Path
import unreal

out = Path(r'F:\Carnival\Saved\RideDevelopment')
out.mkdir(parents=True, exist_ok=True)
report = {'rides': [], 'characters': [], 'meshes': []}
paths = list(unreal.EditorAssetLibrary.list_assets('/Game/Carnival/Rides', recursive=False))
paths += [
    '/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/BP_FerrisWheel_Ride_01a',
    '/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/BP_Carousel_Ride_01a',
]
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for path in paths:
    bp = unreal.load_asset(path)
    if not bp or not hasattr(bp, 'generated_class'):
        continue
    actor = actors.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0, 0, 0))
    data = {'path': path, 'api': [n for n in dir(actor) if any(s in n.lower() for s in ['ride', 'start', 'stop', 'state', 'speed', 'rotat', 'animation'])], 'components': []}
    data['control_functions'] = list(unreal.CarnivalRideOperationComponent.describe_ride_controls(actor))
    for component in actor.get_components_by_class(unreal.ActorComponent):
        item = {'name': component.get_name(), 'class': component.get_class().get_name()}
        if isinstance(component, unreal.SceneComponent):
            item['position'] = list(component.get_world_location().to_tuple())
            item['rotation'] = list(component.get_world_rotation().to_tuple())
            item['parent'] = component.get_attach_parent().get_name() if component.get_attach_parent() else None
        if isinstance(component, unreal.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            if mesh: item['mesh'] = mesh.get_path_name()
        if isinstance(component, unreal.RotatingMovementComponent):
            item['rate'] = str(component.get_editor_property('rotation_rate'))
        data['components'].append(item)
    for name in data['api']:
        try:
            value = getattr(actor, name)
            if not callable(value): data[name] = str(value)
        except Exception:
            pass
    report['rides'].append(data)
    actors.destroy_actor(actor)
for path in ['/Game/Carnival/Blueprints/Guests/BP_CarnivalGuest', '/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter']:
    bp = unreal.load_asset(path)
    if bp:
        actor = actors.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0,0,0))
        meshes = []
        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = component.get_skeletal_mesh_asset()
            meshes.append({'component': component.get_name(), 'mesh': mesh.get_path_name() if mesh else None})
        report['characters'].append({'path': path, 'meshes': meshes})
        actors.destroy_actor(actor)
registry = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ['/Game/Carnival/MetaHumans', '/Game/Carnival/Crowd', '/Game/FreeAnimationLibrary/Demo/Characters', '/Game/RamsterZ_FreeAnims_Volume1', '/Game/Carnival/Character/Animations']:
    for asset in registry.get_assets_by_path(root, recursive=True):
        if str(asset.asset_class_path.asset_name) in ['SkeletalMesh', 'AnimSequence']:
            report['meshes'].append(str(asset.package_name))
(out / 'Ride_Runtime_Inspection.json').write_text(json.dumps(report, indent=2))
unreal.log('Ride inspection saved: ' + str(out))
