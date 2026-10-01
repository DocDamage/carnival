"""Inspect real generator output and baked lanes without beginning play or saving."""
import json, math, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT/'Saved/CrowdAcceptance/SpawnPositionSurvey_20260930.json'
REPORT = {'success': False, 'errors': [], 'assets_modified': False, 'entities_spawned': False}
try:
    assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    spawners = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MassSpawner)
    REPORT['spawners'] = []
    for spawner in spawners:
        generators = []
        for row in spawner.get_editor_property('spawn_data_generators'):
            instance = row.get_editor_property('generator_instance')
            values = {}
            for key in ('min_gap', 'max_gap'):
                try: values[key] = instance.get_editor_property(key)
                except Exception: pass
            generators.append({'class': instance.get_class().get_name(), **values})
        REPORT['spawners'].append({'actor': spawner.get_path_name(), 'count': spawner.get_count(), 'generators': generators})
    REPORT['lanes'] = list(unreal.CarnivalCrowdEditorLibrary.describe_crowd_lanes(world))
    REPORT['runs'] = []
    for run in range(3):
        positions, error = unreal.CarnivalCrowdEditorLibrary.preview_crowd_spawn_locations(world)
        assert not error, error
        positions = [list(p.to_tuple()) for p in positions]
        distances = [math.dist(a[:2], b[:2]) for i, a in enumerate(positions) for b in positions[i+1:]]
        REPORT['runs'].append({'positions': positions, 'count': len(positions),
            'unique_positions': len(set(tuple(p) for p in positions)),
            'coincident_pairs': sum(d < .01 for d in distances),
            'pairs_below_80cm': sum(d < 80 for d in distances),
            'minimum_distance_cm': min(distances) if distances else None})
    REPORT['success'] = True
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    OUT.write_text(json.dumps(REPORT, indent=2))
