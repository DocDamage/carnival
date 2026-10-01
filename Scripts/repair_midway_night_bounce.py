"""Save the rendered moderate lower-hemisphere fill, preserving exposure and other lights."""
import datetime, hashlib, json, shutil, traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/PresentationAcceptance/NightBounceRepair_20260930'
OUT.mkdir(parents=True,exist_ok=True)
BACKUP=OUT/'Backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
BACKUP.mkdir(parents=True,exist_ok=False)
REPORT={'success':False,'errors':[],'levels':[],
        'reference':'NightFillComparisonValidated_20260930/LowerBounceModerate',
        'limits':'Saved lighting adjustment; fresh populated visual review and packaged performance remain required.'}

def state(component):
    return {'source_type':str(component.get_editor_property('source_type')),
        'intensity':component.get_editor_property('intensity'),
        'light_color':list(component.get_editor_property('light_color').to_tuple()),
        'lower_hemisphere_color':list(component.get_editor_property('lower_hemisphere_color').to_tuple()),
        'lower_hemisphere_is_black':component.get_editor_property('lower_hemisphere_is_black'),
        'affects_world':component.get_editor_property('affects_world'),
        'cubemap':component.get_editor_property('cubemap').get_path_name() if component.get_editor_property('cubemap') else None}

try:
    for leaf in ('Lv_LightingNight','Lv_LightingNightSnow'):
        package='/Game/Creepwood_Carnival_Meshingun/Environment/Map/'+leaf
        file=ROOT/'Content'/Path(package.removeprefix('/Game/')).with_suffix('.umap')
        shutil.copy2(file,BACKUP/file.name)
        row={'package':package,'backup':str(BACKUP/file.name),'sha256_before':hashlib.sha256(file.read_bytes()).hexdigest()}
        REPORT['levels'].append(row)
        assert hashlib.sha256((BACKUP/file.name).read_bytes()).hexdigest()==row['sha256_before']
        assert unreal.EditorLoadingAndSavingUtils.load_map(package)
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        skies=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SkyLight)
        assert len(skies)==1
        component=skies[0].get_component_by_class(unreal.SkyLightComponent)
        row['before']=state(component)
        skies[0].modify(); component.modify()
        component.set_editor_property('lower_hemisphere_is_black',True)
        component.set_lower_hemisphere_color(unreal.LinearColor(0.12,0.16,0.22,1.0))
        component.recapture_sky()
        row['after']=state(component)
        for key in row['before']:
            if key not in ('lower_hemisphere_color','lower_hemisphere_is_black'):
                assert row['before'][key]==row['after'][key],key
        assert unreal.EditorLoadingAndSavingUtils.save_map(world,package)
        row['sha256_after']=hashlib.sha256(file.read_bytes()).hexdigest()
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc()); raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
