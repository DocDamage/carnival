"""Back up and correct night ambient lighting and post-process glare in authored lighting levels."""
import datetime
import hashlib
import json
import shutil
import traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/PresentationAcceptance/NightLightingRepair_20260930'
OUT.mkdir(parents=True, exist_ok=True)
BACKUP = OUT / 'Backups' / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
BACKUP.mkdir(parents=True, exist_ok=False)
REPORT = {'success': False, 'errors': [], 'levels': [], 'main_map_modified': False,
          'limits': 'Lighting configuration repair. Fresh populated rendered review must prove readability, shadows, glare and region transitions.'}

try:
    for leaf in ('Lv_LightingNight', 'Lv_LightingNightSnow'):
        package = '/Game/Creepwood_Carnival_Meshingun/Environment/Map/' + leaf
        file = ROOT / 'Content' / Path(package.removeprefix('/Game/')).with_suffix('.umap')
        shutil.copy2(file, BACKUP / file.name)
        row = {'package': package, 'backup': str(BACKUP / file.name),
               'sha256_before': hashlib.sha256(file.read_bytes()).hexdigest(), 'changes': []}
        REPORT['levels'].append(row)
        assert hashlib.sha256((BACKUP / file.name).read_bytes()).hexdigest() == row['sha256_before']
        assert unreal.EditorLoadingAndSavingUtils.load_map(package)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        lights = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SkyLight)
        assert len(lights) == 1, 'Expected one skylight in ' + package
        actor = lights[0]
        component = actor.get_component_by_class(unreal.SkyLightComponent)
        row['skylight_before'] = {'actor': actor.get_name(), 'affects_world': component.get_editor_property('affects_world'),
                                  'intensity': component.get_editor_property('intensity'),
                                  'mobility': str(component.get_editor_property('mobility'))}
        actor.modify(); component.modify()
        component.set_editor_property('affects_world', True)
        component.set_intensity(1.0)
        row['changes'].append('Enable existing sky ambient light with intensity 1.0')
        volumes = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume)
        assert len(volumes) == 1, 'Expected one post-process volume in ' + package
        volume = volumes[0]
        assert volume.get_editor_property('unbound')
        settings = volume.get_editor_property('settings')
        row['post_process_before'] = {name: settings.get_editor_property(name) for name in
                                     ('bloom_intensity', 'scene_fringe_intensity', 'auto_exposure_bias',
                                      'auto_exposure_min_brightness', 'auto_exposure_max_brightness')}
        volume.modify()
        settings.set_editor_property('override_bloom_intensity', True)
        settings.set_editor_property('bloom_intensity', 0.2)
        settings.set_editor_property('override_scene_fringe_intensity', True)
        settings.set_editor_property('scene_fringe_intensity', 0.0)
        volume.set_editor_property('settings', settings)
        row['changes'].append('Reduce bloom to 0.2 and remove chromatic edge fringe; preserve exposure')
        assert component.get_editor_property('affects_world')
        assert abs(component.get_editor_property('intensity') - 1.0) < 1e-5
        after = volume.get_editor_property('settings')
        for name in ('auto_exposure_bias', 'auto_exposure_min_brightness', 'auto_exposure_max_brightness'):
            assert after.get_editor_property(name) == row['post_process_before'][name]
        assert unreal.EditorLoadingAndSavingUtils.save_map(world, package)
        row['sha256_after'] = hashlib.sha256(file.read_bytes()).hexdigest()
    REPORT['success'] = True
except Exception:
    REPORT['errors'].append(traceback.format_exc())
    raise
finally:
    (OUT / 'index.json').write_text(json.dumps(REPORT, indent=2))
