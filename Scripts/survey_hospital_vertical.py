import json,collections,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
out=collections.defaultdict(list)
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 lv=a.get_level().get_outermost().get_name().split('/')[-1]
 if 'Hospital' not in lv:continue
 l=a.get_actor_label();ll=l.lower()
 if any(w in ll for w in ('stair','step','ladder','ramp','elevator','lift','hole','hatch')):
  o,e=a.get_actor_bounds(False);out[lv].append({'label':l,'class':a.get_class().get_name(),'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\HospitalVertical.json','w').write(json.dumps(out,indent=1))
