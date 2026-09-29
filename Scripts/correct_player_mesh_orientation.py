"""Correct a pitch/yaw mix-up in the saved player mesh component only."""
import datetime
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/DirtBike'
path = '/Game/Carnival/Character/Blueprints/BP_CarnivalPlayerCharacter'
source = ROOT / 'Content' / (path.removeprefix('/Game/') + '.uasset')
backup = OUT / ('PlayerOrientationBackup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.uasset')
shutil.copy2(source, backup)
blueprint = unreal.load_asset(path)
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
library = unreal.SubobjectDataBlueprintFunctionLibrary
found = []
for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
    component = library.get_associated_object(library.get_data(handle))
    if component and component.get_name() == 'CharacterMesh0':
        before = component.get_editor_property('relative_rotation').to_tuple()
        component.set_editor_property('relative_rotation', unreal.Rotator(pitch=0, yaw=-90, roll=0))
        found.append({'component':component.get_name(), 'before':before,
                      'after':component.get_editor_property('relative_rotation').to_tuple()})
assert len(found) == 1, found
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
assert unreal.EditorAssetLibrary.save_loaded_asset(blueprint, False)
(OUT / 'Player_Orientation_Correction.json').write_text(json.dumps({'backup':str(backup),'changes':found}, indent=2))
