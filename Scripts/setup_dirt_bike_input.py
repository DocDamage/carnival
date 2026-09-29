"""Add rear-brake and rider-balance inputs without rebuilding other mappings."""
import datetime
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/DirtBike'
OUT.mkdir(parents=True, exist_ok=True)
BACKUP = OUT / ('InputBackup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
INPUT = '/Game/Carnival/Input'


def backup(path):
    relative = path.removeprefix('/Game/') + '.uasset'
    source = ROOT / 'Content' / relative
    if source.exists():
        dest = BACKUP / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def action(name, kind):
    path = INPUT + '/' + name
    backup(path)
    result = unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(
        name, INPUT, unreal.InputAction, unreal.DataAssetFactory())
    assert result, path
    result.set_editor_property('value_type', kind)
    assert EAL.save_loaded_asset(result, False)
    return result


context_path = INPUT + '/IMC_CarnivalMotorcycle'
controller_path = '/Game/Carnival/Blueprints/BP_CarnivalPlayerController'
backup(context_path)
backup(controller_path)
context = unreal.load_asset(context_path)
assert context
rear_brake = action('IA_Handbrake', unreal.InputActionValueType.BOOLEAN)
balance = action('IA_RiderBalance', unreal.InputActionValueType.AXIS1D)
brake_reverse = action('IA_BrakeReverse', unreal.InputActionValueType.AXIS1D)
data = context.get_editor_property('default_key_mappings')
mappings = [m for m in data.mappings if m.action not in (rear_brake, balance, brake_reverse)
            and m.key.export_text() != 'Gamepad_LeftTriggerAxis']
for target, name, flip, dead_zone in [
    (brake_reverse, 'Gamepad_LeftTriggerAxis', False, True),
    (rear_brake, 'Gamepad_RightShoulder', False, False),
    (rear_brake, 'LeftAlt', False, False),
    (balance, 'Gamepad_LeftY', True, True),
    (balance, 'LeftShift', False, False),
    (balance, 'LeftControl', True, False),
]:
    key = unreal.Key()
    key.import_text(name)
    mapping = unreal.EnhancedActionKeyMapping()
    mapping.set_editor_property('action', target)
    mapping.set_editor_property('key', key)
    modifiers = []
    if dead_zone:
        modifier = unreal.InputModifierDeadZone(outer=context)
        modifier.set_editor_property('lower_threshold', .18)
        modifier.set_editor_property('upper_threshold', .95)
        modifiers.append(modifier)
    if flip:
        modifier = unreal.InputModifierNegate(outer=context)
        modifier.set_editor_property('x', True)
        modifier.set_editor_property('y', False)
        modifier.set_editor_property('z', False)
        modifiers.append(modifier)
    mapping.set_editor_property('modifiers', modifiers)
    mappings.append(mapping)
data.set_editor_property('mappings', mappings)
context.set_editor_property('default_key_mappings', data)
assert EAL.save_loaded_asset(context, False)
blueprint = unreal.load_asset(controller_path)
controller = unreal.get_default_object(blueprint.generated_class())
controller.set_editor_property('handbrake_action', rear_brake)
controller.set_editor_property('rider_balance_action', balance)
controller.set_editor_property('brake_reverse_action', brake_reverse)
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
assert EAL.save_loaded_asset(blueprint, False)
report = {
    'success': True,
    'backup': str(BACKUP),
    'mappings': [{'action': m.action.get_name(), 'key': m.key.export_text(),
                  'modifiers': [o.get_class().get_name() for o in m.modifiers]}
                 for m in context.get_editor_property('default_key_mappings').mappings],
    'controller': {name: controller.get_editor_property(name).get_path_name()
                   for name in ('handbrake_action', 'rider_balance_action', 'brake_reverse_action')},
}
(OUT / 'Input_Setup.json').write_text(json.dumps(report, indent=2))
unreal.log('DIRT_BIKE_INPUT_SETUP_COMPLETE')
