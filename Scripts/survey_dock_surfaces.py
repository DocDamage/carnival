import json,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
out={}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 lv=a.get_level().get_outermost().get_name().split('/')[-1]
 if 'Docks' not in lv:continue
 l=a.get_actor_label()
 if any(w in l for w in ('Pile','Lantern','LocalLantern','Light','Boat','Hovercraft','Campaign','Skiff','Buoy','Mooring')):continue
 o,e=a.get_actor_bounds(False);r=a.get_actor_rotation()
 out.setdefault(lv,[]).append({'label':l,'top':round(o.z+e.z),'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'yaw':round(r.yaw,1),'pitch':round(r.pitch,2),'roll':round(r.roll,2)})
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\DockSurfaces.json','w').write(json.dumps(out,indent=1))
