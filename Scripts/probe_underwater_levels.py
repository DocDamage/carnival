"""Read-only: how the Atlantis / Shipwreck levels are set up (volumes, fog, post-process, lights, water/caustic materials)."""
import collections,json,unreal
w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
R=collections.defaultdict(lambda:{'classes':collections.Counter(),'volumes':[],'materials':collections.Counter()})
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 lv=a.get_level().get_outermost().get_name().split('/')[-1]
 if not any(k in lv for k in ('Atlantis','Shipwreck','Underwater','Ship')):continue
 c=a.get_class().get_name();R[lv]['classes'][c]+=1
 if 'Volume' in c or 'Fog' in c or 'PostProcess' in c or 'Water' in c:
  o,e=a.get_actor_bounds(False);d={'label':a.get_actor_label(),'class':c,'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()]}
  if c=='PostProcessVolume':
   try:d['unbound']=a.get_editor_property('unbound');s=a.get_editor_property('settings');d['mat']=[str(x.object.get_name()) for x in s.weighted_blendables.array if x.object]
   except Exception as ex:d['err']=str(ex)[:80]
  if 'PhysicsVolume' in c:d['water']=a.get_editor_property('water_volume')
  R[lv]['volumes'].append(d)
 for m in a.get_components_by_class(unreal.MeshComponent):
  try:
   for i in range(m.get_num_materials()):
    x=m.get_material(i)
    if x and any(k in x.get_name().lower() for k in ('water','caustic','under','sea','bubble','godray','sand')):R[lv]['materials'][x.get_name()]+=1
  except Exception:pass
out={k:{'classes':dict(v['classes'].most_common(25)),'volumes':v['volumes'],'materials':dict(v['materials'].most_common(15))} for k,v in R.items()}
open(r'F:\Carnival\Saved\WorldExpansion\UnderwaterLevels_20261001.json','w').write(json.dumps(out,indent=1))
