import json,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
acts=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
wells={}
for a in acts:
 l=a.get_actor_label()
 if l.startswith(('SM_Ladder_0','SM_Ladder_Floor')) and 'Hospital' in a.get_level().get_outermost().get_name():
  o,e=a.get_actor_bounds(False);key='well_1' if o.x<98000 else 'well_2'
  w=wells.setdefault(key,[1e9,1e9,1e9,-1e9,-1e9,-1e9])
  for i,(c,x) in enumerate(zip(o.to_tuple(),e.to_tuple())):w[i]=min(w[i],c-x);w[i+3]=max(w[i+3],c+x)
out={}
for k,w in wells.items():
 rows=[]
 for a in acts:
  l=a.get_actor_label();lv=a.get_level().get_outermost().get_name().split('/')[-1]
  if 'Hospital' not in lv or l.startswith(('SM_Ladder','SM_Banister','Wall_','SM_wall','SM_Wall','BO_wall','BO_floor','SM_Floor','BP_Ceiling','SM_Ceiling','SM_Arch')):continue
  comps=a.get_components_by_class(unreal.PrimitiveComponent)
  if not any(str(c.get_collision_enabled())!='CollisionEnabled.NO_COLLISION' for c in comps):continue
  o,e=a.get_actor_bounds(False)
  if e.length()>3000:continue
  if all(o.to_tuple()[i]+e.to_tuple()[i]>=w[i] and o.to_tuple()[i]-e.to_tuple()[i]<=w[i+3] for i in range(3)):
   rows.append({'label':l,'level':lv,'class':a.get_class().get_name(),'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]})
 out[k]={'bounds':[round(v) for v in w],'props':rows}
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\StairwellClutter.json','w').write(json.dumps(out,indent=1))
