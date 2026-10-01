import json,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
out=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 lv=a.get_level().get_outermost().get_name()
 if 'Hospital' in lv and isinstance(a,unreal.BlockingVolume):
  o,e=a.get_actor_bounds(False);out.append({'label':a.get_actor_label(),'level':lv,'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'profile':str(a.get_component_by_class(unreal.BrushComponent).get_collision_profile_name())})
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\HospitalBlockingVolumes.json','w').write(json.dumps(out,indent=1))
