import json,math,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
acts=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if 'Hospital' in a.get_level().get_outermost().get_name()]
rooms={'room_A':(95685,130876,643),'room_B':(99379,129948,643),'room_C':(97007,124012,643)}
out={}
for k,c in rooms.items():
 rows=[]
 for a in acts:
  l=a.get_actor_label();ll=l.lower()
  if not any(w in ll for w in ('door','gate','grid','bars','board','plank','barric')):continue
  o,e=a.get_actor_bounds(False)
  d=math.dist((o.x,o.y),c[:2])
  if d<1200 and o.z-e.z<c[2]+250 and o.z+e.z>c[2]:
   comps=a.get_components_by_class(unreal.PrimitiveComponent)
   coll=any(str(x.get_collision_enabled())!='CollisionEnabled.NO_COLLISION' for x in comps)
   rows.append({'label':l,'class':a.get_class().get_name(),'dist':round(d),'origin':[round(v) for v in o.to_tuple()],'extent':[round(v) for v in e.to_tuple()],'collision':coll})
 out[k]=sorted(rows,key=lambda r:r['dist'])
open(r'F:\Carnival\Saved\WorldExpansion\Reachability\SealedHospitalRooms.json','w').write(json.dumps(out,indent=1))
