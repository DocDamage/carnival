"""Enlarge the low landing for a full hovercraft turn and author its shore course.

Preserve the boat-facing edge and floor height. The old landing made the craft
approach the ramp transversely while its hull straddled the sloping side face.
The new southern turning area lets it line up with the ramp instead.
"""
import hashlib
import json
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(r'F:\Carnival')
NAME = 'L_CarnivalWorldExpansion_DocksNorth_Layout'
LEVEL = ROOT / ('Content/Carnival/World/Levels/' + NAME + '.umap')
MAIN = ROOT / 'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
CONNECT = ROOT / 'Content/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout.umap'
OUT = ROOT / 'Saved/WorldExpansion/WaterVehicleAcceptance/HovercraftShoreAccess_20261029'
BACKUP = Path(r'D:\CarnivalBackups\hovercraft_shore_access_20261029')
OUT.mkdir(parents=True, exist_ok=False)
BACKUP.mkdir(parents=True, exist_ok=False)
V = unreal.Vector
R = {'success': False, 'errors': []}
PATH = [(-57000, -52000, 735), (-57000, -48100, 735), (-50300, -48100, 735),
        (-50300, -54500, 735), (-50300, -55000, 735), (-50300, -57200, -110),
        (-50300, -57650, -110), (-49700, -57650, -110),
        (-49700, -58500, -140), (-47700, -58500, -140)]
ROUTE = PATH[1:] + list(reversed(PATH[:-1]))
DESCRIPTIONS = ['Reach the main-pier bend.', 'Follow the quay to the side pier.',
    'Follow the side pier south.', 'Line up with the shore ramp.', 'Descend the ramp.',
    'Enter the turning area.', 'Turn toward the river.', 'Leave the landing for the river.',
    'Reach the river marker.', 'Return west toward the landing.', 'Approach the turning area.',
    'Line up with the ramp.', 'Reach the ramp foot.', 'Climb the ramp.',
    'Follow the side pier north.', 'Reach the quay.', 'Return to the main pier.', 'Return to the start.']


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


try:
    assert len(ROUTE) == len(DESCRIPTIONS)
    R['before'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT)}
    for target in (OUT / (NAME + '.before.umap'), BACKUP / (NAME + '.before.umap')):
        shutil.copy2(LEVEL, target)
        assert sha(target) == R['before'][LEVEL.name]
    world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    assert world
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    deck = next(a for a in actors if a.get_actor_label() == 'Boat_NorthDock_Inflatable_BoardingDeck_1')
    assert '/' + NAME + '.' in deck.get_path_name()
    R['landing_before'] = {'location_cm': deck.get_actor_location().to_tuple(), 'scale': deck.get_actor_scale3d().to_tuple()}
    deck.modify()
    assert deck.set_actor_location(V(-50050, -57500, -227.5), False, True)
    deck.set_actor_scale3d(V(17, 10, .35))
    center, extent = deck.get_actor_bounds(False)
    assert abs(center.z + extent.z + 210) < .01
    assert abs(center.x + extent.x + 49200) < .01, 'Boat-facing edge must stay fixed'
    R['landing_after'] = {'location_cm': deck.get_actor_location().to_tuple(), 'scale': deck.get_actor_scale3d().to_tuple(),
                           'top_z_cm': center.z + extent.z, 'boat_edge_x_cm': center.x + extent.x}
    activity = next(a for a in actors if a.get_actor_label() == 'Hovercraft_NorthDock_Handling_HandlingActivity')
    assert '/' + NAME + '.' in activity.get_path_name()
    activity.modify()
    checkpoints = []
    for point, description in zip(ROUTE, DESCRIPTIONS):
        cp = unreal.CarnivalActivityCheckpoint()
        cp.set_editor_property('location', V(*point))
        cp.set_editor_property('radius', 200.)
        cp.set_editor_property('description', description)
        checkpoints.append(cp)
    activity.set_editor_property('checkpoints', checkpoints)
    activity.set_editor_property('target_score', len(checkpoints) * 100)
    activity.set_editor_property('time_limit', 240.)
    activity.set_editor_property('gold_time', 100.)
    activity.set_editor_property('silver_time', 150.)
    activity.set_editor_property('bronze_time', 220.)
    activity.set_editor_property('description', 'Board the hovercraft, follow the quays and ramp to the river marker, then return to the starting pier.')
    R.update(route_cm=ROUTE, checkpoint_descriptions=DESCRIPTIONS, checkpoints=len(checkpoints))
    assert unreal.EditorLoadingAndSavingUtils.save_packages([deck.get_outermost()], False)
    R['after'] = {p.name: sha(p) for p in (LEVEL, MAIN, CONNECT)}
    for p in (MAIN, CONNECT):
        assert R['after'][p.name] == R['before'][p.name]
    shutil.copy2(LEVEL, BACKUP / LEVEL.name)
    assert sha(BACKUP / LEVEL.name) == R['after'][LEVEL.name]
    R.update(success=True, external_backup=str(BACKUP))
except Exception:
    R['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'index.json').write_text(json.dumps(R, indent=2))
