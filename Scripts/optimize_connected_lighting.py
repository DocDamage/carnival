"""Remove redundant cubemap shadows from cinematic fill lights in the Carnival."""
import sys,json,shutil
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
main=unreal.EditorLoadingAndSavingUtils.load_map(CARNIVAL)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report={'changed':[],'point_lights':[]};worlds={}
for actor in eas.get_all_level_actors():
    for comp in actor.get_components_by_class(unreal.PointLightComponent):
        label=actor.get_actor_label()
        world=actor.get_outer().get_outer();path=world.get_path_name().split('.')[0]
        record={'actor':label,'level':path,'cast_shadows':comp.get_editor_property('cast_shadows'),
                'radius':comp.get_editor_property('attenuation_radius')}
        report['point_lights'].append(record)
        if 'forcam' not in label.lower() or not record['cast_shadows']:continue
        source=ROOT/'Content'/(path.removeprefix('/Game/')+'.umap')
        backup=OUT/'Backups'/(source.name+'.before_fill_shadow_optimization')
        if source.exists() and not backup.exists():shutil.copy2(source,backup)
        actor.modify();comp.modify();comp.set_cast_shadows(False)
        worlds[path]=world;report['changed'].append(record)
for path,world in worlds.items():assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
report['success']=True
(OUT/'Lighting_Optimization.json').write_text(json.dumps(report,indent=2))
unreal.log('FILL_SHADOW_OPTIMIZATION '+str(len(report['changed'])))
