"""Preserve translucent materials by disabling Nanite on copied interior components."""
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
BACKUP=ROOT/'Saved/PresentationAcceptance'/('BeforeTranslucentNanite_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
REPORT={'changed':[], 'errors':[], 'saved_packages':[], 'backup':str(BACKUP), 'rendered_acceptance':'pending'}
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
packages=set()
for actor in actors.get_all_level_actors():
    package=actor.get_level().get_path_name().split('.')[0]
    if not package.startswith('/Game/Carnival/World/Levels/'):
        continue
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh=component.get_editor_property('static_mesh')
        if not mesh or not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'):
            continue
        translucent=[]
        for index in range(component.get_num_materials()):
            material=component.get_material(index)
            base=material.get_base_material() if material else None
            if base and base.get_editor_property('blend_mode') not in (unreal.BlendMode.BLEND_OPAQUE,unreal.BlendMode.BLEND_MASKED):
                translucent.append(material.get_path_name())
        if not translucent or component.get_editor_property('disallow_nanite'):
            continue
        if package not in packages:
            source=ROOT/'Content'/(package.removeprefix('/Game/')+'.umap')
            destination=BACKUP/(package.removeprefix('/Game/')+'.umap')
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
            packages.add(package)
        # BlueprintReadWrite assignment avoids reconstructing the entire actor
        # and invalidating its other component references during enumeration.
        actor.modify()
        component.modify()
        component.disallow_nanite=True
        assert component.disallow_nanite
        REPORT['changed'].append({'actor':actor.get_path_name(),'component':component.get_name(),'materials':translucent})
for package in sorted(packages):
    assert unreal.EditorLevelLibrary.set_current_level_by_name(package.rsplit('/',1)[-1])
    assert unreal.EditorLevelLibrary.save_current_level()
    REPORT['saved_packages'].append(package)
output=ROOT/'Saved/PresentationAcceptance/TranslucentNaniteRepair.json'
output.parent.mkdir(parents=True,exist_ok=True)
REPORT['success']=not REPORT['errors']
output.write_text(json.dumps(REPORT,indent=2))
unreal.SystemLibrary.quit_editor()
