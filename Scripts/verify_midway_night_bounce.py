"""Read both saved lighting levels in a fresh process without saving."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/PresentationAcceptance/NightBounceRepair_20260930'
original=json.loads((OUT/'index.json').read_text())
REPORT={'success':False,'errors':[],'levels':[],'assets_modified':False}
for row in original['levels']:
    assert unreal.EditorLoadingAndSavingUtils.load_map(row['package'])
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    skies=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SkyLight)
    assert len(skies)==1
    component=skies[0].get_component_by_class(unreal.SkyLightComponent)
    colour=list(component.get_editor_property('lower_hemisphere_color').to_tuple())
    assert all(abs(a-b)<1e-5 for a,b in zip(colour,(0.12,0.16,0.22,1)))
    assert component.get_editor_property('lower_hemisphere_is_black')
    assert component.get_editor_property('intensity')==row['after']['intensity']
    REPORT['levels'].append({'package':row['package'],'lower_hemisphere_color':colour})
REPORT['success']=True
(OUT/'Reload.json').write_text(json.dumps(REPORT,indent=2))
