"""Finish terrain grading, clear the driveway, and keep the original packs intact."""
import sys,json,time,traceback
import unreal
sys.path.insert(0,r'F:\Carnival\Scripts')
from mansion_route_config import *
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.EditorLoadingAndSavingUtils.load_map(MANSION)
report={'driveway_changes':[]}
for a in list(eas.get_all_level_actors()):
    if a.get_actor_label()=='SM_StoneFence117':
        report['driveway_changes'].append('Opened the existing driveway by removing its blocking fence panel.');eas.destroy_actor(a)
    elif a.get_actor_label()=='SM_WoodenBeam12' and a.get_actor_location().x<0:
        a.modify();a.get_editor_property('root_component').modify()
        a.set_actor_location(a.get_actor_location()+unreal.Vector(320,0,0),False,True)
        report['driveway_changes'].append('Moved the loose wooden beam to the side of the drive.')
    if a.get_actor_label().startswith('MansionGrounds_'):
        for comp in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            comp.modify();comp.set_cull_distances(16000,24000)
assert unreal.EditorLoadingAndSavingUtils.save_map(world,MANSION)
world=unreal.EditorLoadingAndSavingUtils.load_map(COAST)
land=next(a for a in eas.get_all_level_actors() if isinstance(a,unreal.Landscape))
west=SECTIONS[0]['points'][:-1]+[p for p in SECTIONS[1]['points'] if p[0]<-12900]
east=[p for p in SECTIONS[1]['points'] if p[0]>6500]+SECTIONS[2]['points']
for points in [west,east]:
    assert unreal.CarnivalWorldEditorLibrary.grade_landscape_route(land,[unreal.Vector(p[0],p[1],p[2]-22) for p in points],420,1400)
report['cleared_foliage_instances']=0
route=[unreal.Vector(*p) for section in SECTIONS for p in section['points']]
for a in eas.get_all_level_actors():
    if isinstance(a,unreal.InstancedFoliageActor):report['cleared_foliage_instances']+=unreal.CarnivalWorldEditorLibrary.clear_foliage_from_route(a,route,430)
state={'deadline':time.monotonic()+20,'busy':False}
def tick(dt):
    if state['busy'] or time.monotonic()<state['deadline']:return
    state['busy']=True
    try:
        for a in eas.get_all_level_actors():
            if a.get_actor_label()=='Wetland_Trail_Reeds':
                a.modify()
                for comp in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                    comp.modify();comp.set_cull_distances(16000,24000)
                    transforms=[comp.get_instance_transform(i,world_space=True) for i in range(comp.get_instance_count())]
                    zs=unreal.CarnivalWorldEditorLibrary.sample_landscape_heights(land,[t.translation for t in transforms])
                    for i,(t,z) in enumerate(zip(transforms,zs)):
                        p=t.translation;p.z=z-2;t.translation=p
                        comp.update_instance_transform(i,t,world_space=True,mark_render_state_dirty=True,teleport=True)
        assert unreal.EditorLoadingAndSavingUtils.save_map(world,COAST)
        report['success']=True
    except Exception:report['error']=traceback.format_exc()
    (OUT/'Route_Refinement.json').write_text(json.dumps(report,indent=2))
    unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
