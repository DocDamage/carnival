"""Incremental ride/controller setup. Keeps existing gameplay and vendor assets.

Run after compiling: run_doll_tool.py unreal Scripts/setup_attended_rides.py
Licensed animation files stay in their existing local pack directories.
"""
import json
import shutil
from pathlib import Path
import unreal

OUT = Path(r'F:\Carnival\Saved\RideDevelopment')
OUT.mkdir(parents=True, exist_ok=True)
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
INPUT = '/Game/Carnival/Input'

def backup(path):
    relative = path.removeprefix('/Game/')
    for extension in ('.uasset', '.umap'):
        source = Path(r'F:\Carnival\Content') / (relative + extension)
        dest = OUT / 'BeforeAttendedRides' / (relative + extension)
        if source.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)

def action(name, axis=unreal.InputActionValueType.BOOLEAN):
    path = INPUT + '/' + name
    asset = unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(name, INPUT, unreal.InputAction, unreal.DataAssetFactory())
    assert asset, path
    asset.set_editor_property('value_type', axis)
    EAL.save_loaded_asset(asset)
    return asset

def key(name):
    result = unreal.Key()
    result.import_text(name)
    return result

def deadzone():
    modifier = unreal.InputModifierDeadZone(outer=context)
    modifier.set_editor_property('type', unreal.DeadZoneType.RADIAL)
    modifier.set_editor_property('lower_threshold', .18)
    modifier.set_editor_property('upper_threshold', .95)
    return modifier

def map_input(context, input_action, name, modifiers=()):
    assert input_action, name
    data = context.get_editor_property('default_key_mappings')
    mappings = [m for m in data.mappings if m.key.export_text() not in ('None', '') and not (m.action == input_action and m.key.export_text() == name)]
    mapping = unreal.EnhancedActionKeyMapping()
    mapping.set_editor_property('action', input_action)
    mapping.set_editor_property('key', key(name))
    mapping.set_editor_property('modifiers', list(modifiers))
    mappings.append(mapping)
    data.set_editor_property('mappings', mappings)
    context.set_editor_property('default_key_mappings', data)

def negate(x=True, y=False):
    m = unreal.InputModifierNegate(outer=context)
    m.set_editor_property('x', x)
    m.set_editor_property('y', y)
    m.set_editor_property('z', False)
    return m

def swizzle():
    m = unreal.InputModifierSwizzleAxis(outer=context)
    m.set_editor_property('order', unreal.InputAxisSwizzle.YXZ)
    return m

look = action('IA_LookStick', unreal.InputActionValueType.AXIS2D)
interact = action('IA_RideOperate')
cancel = action('IA_RideCancel')
for context_name in ('IMC_CarnivalPlayer', 'IMC_CarnivalMotorcycle'):
    path = INPUT + '/' + context_name
    backup(path)
    context = unreal.load_asset(path)
    assert context, path
    foot = context_name.endswith('Player')
    mount = unreal.load_asset(INPUT + '/IA_InteractMount')
    # E becomes contextual operation; F remains the enter/exit control in both modes.
    context.unmap_key(mount, key('E'))
    map_input(context, mount, 'F')
    map_input(context, mount, 'Gamepad_FaceButton_Top')
    map_input(context, unreal.load_asset(INPUT + '/IA_Look'), 'Mouse2D', [negate(False, True)])
    flip_y = unreal.InputModifierNegate(outer=context)
    flip_y.set_editor_property('x', False)
    flip_y.set_editor_property('y', True)
    flip_y.set_editor_property('z', False)
    map_input(context, look, 'Gamepad_Right2D', [deadzone(), flip_y])
    map_input(context, unreal.load_asset(INPUT + '/IA_SettingsMenu'), 'Gamepad_Special_Right')
    if foot:
        move = unreal.load_asset(INPUT + '/IA_Move')
        for name, modifiers in [('W',[swizzle()]), ('S',[negate(),swizzle()]), ('A',[negate()]), ('D',[])]:
            map_input(context, move, name, modifiers)
        keyboard = {'IA_JumpVault':'SpaceBar','IA_Sprint':'LeftShift','IA_Crouch':'C','IA_Prone':'Z',
                    'IA_WeaponSlot1':'One','IA_WeaponSlot2':'Two','IA_WeaponSlot3':'Three','IA_WeaponSlot0':'Four',
                    'IA_ToggleBuild':'B','IA_SecondaryAction':'RightMouseButton','IA_RotatePiece':'R','IA_CyclePieceNext':'MouseScrollUp',
                    'IA_CyclePiecePrev':'MouseScrollDown','IA_CycleCategory':'T'}
        for name, button in keyboard.items():
            map_input(context, unreal.load_asset(INPUT + '/' + name), button)
        map_input(context, unreal.load_asset(INPUT + '/IA_Move'), 'Gamepad_Left2D', [deadzone()])
        for name, button in [('IA_Sprint', 'Gamepad_FaceButton_Bottom'), ('IA_JumpVault', 'Gamepad_FaceButton_Left'), ('IA_Crouch', 'Gamepad_LeftThumbstick')]:
            map_input(context, unreal.load_asset(INPUT + '/' + name), button)
        for button in ('E', 'Gamepad_DPad_Right'):
            map_input(context, interact, button)
        for button in ('BackSpace', 'Gamepad_FaceButton_Right'):
            map_input(context, cancel, button)
    else:
        for name, button, mods in [('IA_Throttle','W',[]),('IA_Throttle','S',[negate()]),('IA_Steer','D',[]),('IA_Steer','A',[negate()]),('IA_Brake','SpaceBar',[])]:
            map_input(context, unreal.load_asset(INPUT + '/' + name), button, mods)
        for name, button in [('IA_Throttle','Gamepad_RightTriggerAxis'), ('IA_Brake','Gamepad_LeftTriggerAxis'), ('IA_Steer','Gamepad_LeftX')]:
            map_input(context, unreal.load_asset(INPUT + '/' + name), button, [deadzone()])
    map_input(context, unreal.load_asset(INPUT + '/IA_Attack'), 'LeftMouseButton')
    for button in ('M','Tab'):
        map_input(context, unreal.load_asset(INPUT + '/IA_SettingsMenu'), button)
    EAL.save_loaded_asset(context, False)

path = '/Game/Carnival/Blueprints/BP_CarnivalPlayerController'
backup(path)
controller_bp = unreal.load_asset(path)
controller = unreal.get_default_object(controller_bp.generated_class())
controller.set_editor_property('look_stick_action', look)
controller.set_editor_property('context_interact_action', interact)
controller.set_editor_property('cancel_action', cancel)
controller.set_editor_property('bPlayStationPrompts', True)
unreal.BlueprintEditorLibrary.compile_blueprint(controller_bp)
EAL.save_loaded_asset(controller_bp, False)

# Inspect candidate existing clips before selecting a seated pose or staff mesh.
report = {'mappings': {}, 'animations': []}
for name in ('IMC_CarnivalPlayer', 'IMC_CarnivalMotorcycle'):
    context = unreal.load_asset(INPUT + '/' + name)
    report['mappings'][name] = [
        {'action': m.action.get_name(), 'key': m.key.export_text(), 'modifiers': [o.get_class().get_name() for o in m.modifiers]}
        for m in context.get_editor_property('default_key_mappings').get_editor_property('mappings')]
for path in [
    '/Game/FreeAnimationLibrary/Animations/Idle/anim_Idle',
    '/Game/FreeAnimationLibrary/Animations/Interaction/anim_PushButton_R',
    *['/Game/FreeAnimationLibrary/Animations/Update_2/Chair/AS_Sit_0' + str(i) for i in range(1,5)],
]:
    clip = unreal.load_asset(path)
    assert clip, path
    options = unreal.AnimPoseEvaluationOptions()
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(clip, .5, options)
    report['animations'].append({'path': path, 'skeleton': clip.get_editor_property('skeleton').get_path_name(), 'duration': clip.get_editor_property('sequence_length'),
                                'pelvis': str(pose.get_bone_pose('pelvis', unreal.AnimPoseSpaces.WORLD)),
                                'head': str(pose.get_bone_pose('head', unreal.AnimPoseSpaces.WORLD))})
(OUT / 'Controller_Setup.json').write_text(json.dumps(report, indent=2))
unreal.log('ATTENDED_RIDE_INPUT_SETUP_COMPLETE')
