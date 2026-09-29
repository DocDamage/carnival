"""Import the baked complete bike and assign its body/wheel templates locally."""
import datetime
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
SOURCE = ROOT / 'Content/Carnival/Vehicles/Motorcycle/Assembled/Source'
DEST = '/Game/Carnival/Vehicles/Motorcycle/Assembled'
OUT = ROOT / 'Saved/DirtBike'
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads((SOURCE / 'Assembly_Manifest.json').read_text())
backup = OUT / ('AssemblyBackup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
EAL = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def preserve(path):
    relative = path.removeprefix('/Game/') + '.uasset'
    source = ROOT / 'Content' / relative
    if source.exists():
        target = backup / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def import_part(name, skeletal):
    path = DEST + '/' + name
    preserve(path)
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', str(SOURCE / (name + '.fbx')))
    task.set_editor_property('destination_path', DEST)
    task.set_editor_property('destination_name', name)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)
    task.set_editor_property('factory', unreal.FbxFactory())
    options = unreal.FbxImportUI()
    kind = unreal.FBXImportType.FBXIT_SKELETAL_MESH if skeletal else unreal.FBXImportType.FBXIT_STATIC_MESH
    for key, value in {'automated_import_should_detect_type': False, 'mesh_type_to_import': kind,
                       'import_as_skeletal': skeletal, 'import_mesh': True, 'import_animations': False,
                       'import_materials': False, 'import_textures': False, 'create_physics_asset': False}.items():
        options.set_editor_property(key, value)
    task.set_editor_property('options', options)
    tools.import_asset_tasks([task])
    asset = unreal.load_asset(path)
    assert asset, (path, task.get_editor_property('imported_object_paths'))
    property_name = 'materials' if skeletal else 'static_materials'
    materials = asset.get_editor_property(property_name)
    for slot in materials:
        name = str(slot.get_editor_property('imported_material_slot_name'))
        material = unreal.load_asset('/Game/Carnival/Vehicles/Motorcycle/Mesh/' + name)
        assert material, name
        slot.set_editor_property('material_interface', material)
    asset.set_editor_property(property_name, materials)
    if skeletal:
        skeleton = asset.get_editor_property('skeleton')
        assert skeleton, 'Body skeleton was not generated'
        assert EAL.save_loaded_asset(skeleton, False)
    assert EAL.save_loaded_asset(asset, False)
    return asset


body = import_part(manifest['body']['name'], True)
wheels = {}
for part in manifest['parts']:
    if 'wheel_radius_cm' in part:
        wheels['FrontWheel' if 'FrontWheel' in part['name'] else 'RearWheel'] = (import_part(part['name'], False), part)
physics_path = DEST + '/PA_CarnivalBike_Assembly'
preserve(physics_path)
physics = unreal.CarnivalVehicleAuthoring.create_body_collision(body, physics_path, 32., 80.)
assert physics, 'Expected a single rigid root bone in normalized body export'
assert EAL.save_loaded_asset(physics, False)
body.set_editor_property('physics_asset', physics)
assert unreal.CarnivalVehicleAuthoring.set_attachment_socket(body, 'DriverSeat', 'root',
    unreal.Vector(0,0,96 + manifest['floor_shift_cm']))
assert EAL.save_loaded_asset(body, False)
bp_path = '/Game/Carnival/Vehicles/Motorcycle/Blueprints/BP_CarnivalMotorcycle'
preserve(bp_path)
blueprint = unreal.load_asset(bp_path)
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
library = unreal.SubobjectDataBlueprintFunctionLibrary
assigned = []
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    component = library.get_associated_object(library.get_data(handle))
    if not component:
        continue
    name = component.get_name()
    if name == 'BikeMesh':
        component.set_editor_property('skeletal_mesh_asset', body)
        assigned.append(name)
    elif name in wheels:
        mesh, record = wheels[name]
        component.set_editor_property('static_mesh', mesh)
        component.set_editor_property('relative_location', unreal.Vector(*record['location_ue_cm']))
        assigned.append(name)
assert set(assigned) == {'BikeMesh', 'FrontWheel', 'RearWheel'}, assigned
unreal.get_default_object(blueprint.generated_class()).set_editor_property('wheel_radius',
    wheels['RearWheel'][1]['wheel_radius_cm'])
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
assert EAL.save_loaded_asset(blueprint, False)
(OUT / 'Assembly_Import.json').write_text(json.dumps({
    'saved': True, 'body': body.get_path_name(), 'physics': physics.get_path_name(),
    'assigned': assigned, 'backup': str(backup), 'manifest': manifest}, indent=2))
