import json,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
out=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 c=a.get_class().get_name()
 if 'Volume' in c and ('Physics' in c or 'Water' in c or 'PainCausing' in c) or 'Water' in c:
  o,e=a.get_actor_bounds(False)
  wv=None
  try:wv=a.get_editor_property('water_volume')
  except Exception:pass
  out.append({'label':a.get_actor_label(),'class':c,'level':a.get_level().get_outermost().get_name().split('/')[-1],'water_volume':wv,'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
open(r'F:\Carnival\Saved\CharacterRepairs\WaterVolumes_20261001.json','w').write(json.dumps(out,indent=1))
