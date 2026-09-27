"""Use one Carnival sky across the connected world, then capture the result."""
import sys,json
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
world=unreal.EditorLoadingAndSavingUtils.load_map(COAST)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report={'removed_duplicate_skies':[]}
report['removed_train_demo_nodes']=unreal.CarnivalWorldEditorLibrary.clear_connected_level_demo_events(world)
for actor in list(eas.get_all_level_actors()):
    if actor.get_actor_label()=='Wetlands_ViewClarity':eas.destroy_actor(actor);continue
    if actor.get_actor_label()=='SM_SkySphere2':
        report['removed_duplicate_skies'].append(actor.get_actor_label())
        eas.destroy_actor(actor)
clarity=unreal.CarnivalWorldEditorLibrary.create_wetlands_post_process(world,unreal.Vector(10000,-6500,1000),unreal.Vector(58500,42000,25000))
assert clarity
clarity.set_folder_path('Connected Route/Atmosphere')
report['bounded_glare_control']=True
assert unreal.EditorLoadingAndSavingUtils.save_map(world,COAST)
world=unreal.EditorLoadingAndSavingUtils.load_map(CARNIVAL)
# Match the editor preview to the world's existing runtime lighting selection.
report['editor_lighting']={}
for level in unreal.EditorLevelUtils.get_levels(world):
    path=level.get_path_name().split('.')[0]
    name=path.rsplit('/',1)[-1]
    if name in {'Lv_LightingDay','Lv_LightingNight','Lv_LightingNightSnow'}:
        active=name=='Lv_LightingNightSnow'
        unreal.EditorLevelUtils.set_level_visibility(level,active,False)
        report['editor_lighting'][name]=active
assert unreal.EditorLoadingAndSavingUtils.save_map(world,CARNIVAL)
report['success']=True
(OUT/'Atmosphere_Finalization.json').write_text(json.dumps(report,indent=2))
# Audit the persisted terrain before the final viewport captures.
import runpy
runpy.run_path(str(ROOT/'Scripts/verify_mansion_connection.py'))
exec(compile((ROOT/'Scripts/capture_mansion_connection.py').read_text(),str(ROOT/'Scripts/capture_mansion_connection.py'),'exec'))
