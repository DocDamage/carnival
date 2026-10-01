import json,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
out=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if a.get_name()=='StaticMeshActor_2432' or a.get_actor_label().startswith('Campaign_slums'):
  o,e=a.get_actor_bounds(False);out.append({'name':a.get_name(),'label':a.get_actor_label(),'level':a.get_level().get_outermost().get_name(),'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
open(r'F:\Carnival\Saved\WorldExpansion\Actor2432.json','w').write(json.dumps(out,indent=1))
