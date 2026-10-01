import collections,json,unreal
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
by=collections.defaultdict(lambda:{'count':0,'levels':collections.Counter(),'components':collections.defaultdict(list)})
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 if not a.get_actor_label().startswith('BP_Door'):continue
 c=a.get_class().get_name();d=by[c];d['count']+=1;d['levels'][a.get_level().get_outermost().get_name().split('/')[-1]]+=1
 for m in a.get_components_by_class(unreal.StaticMeshComponent):
  r=m.get_editor_property('relative_rotation');o,e=m.bounds.origin if False else (None,None)
  d['components'][m.get_name()].append({'yaw':round(r.yaw,1),'mobility':str(m.get_editor_property('mobility')),'mesh':m.static_mesh.get_name() if m.static_mesh else None,
   'rel_loc':[round(v) for v in m.get_editor_property('relative_location').to_tuple()],'collision':str(m.get_collision_enabled())})
out={}
for c,d in by.items():
 out[c]={'count':d['count'],'levels':dict(d['levels']),'components':{k:{'yaws':sorted({x['yaw'] for x in v}),'mobility':sorted({x['mobility'] for x in v}),'mesh':v[0]['mesh'],'rel_loc':v[0]['rel_loc'],'collision':v[0]['collision']} for k,v in d['components'].items()}}
open(r'F:\Carnival\Saved\WorldExpansion\VendorDoorSurvey_20261001.json','w').write(json.dumps(out,indent=1))
