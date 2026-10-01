"""Read-only: river width from its spline mesh components and the river component's per-key width."""
import json,traceback,unreal
R={'errors':[],'meshes':[],'keys':[]}
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 river=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='WaterBodyRiver')
 for c in river.get_components_by_class(unreal.SplineMeshComponent):
  b=c.static_mesh.get_bounds() if c.static_mesh else None
  R['meshes'].append({'name':c.get_name(),'mesh':c.static_mesh.get_name() if c.static_mesh else None,'start_scale':str(c.get_start_scale()),'end_scale':str(c.get_end_scale()),'mesh_extent':list(b.box_extent.to_tuple()) if b else None,'world_bounds':[list(x.to_tuple()) if hasattr(x,'to_tuple') else x for x in unreal.SystemLibrary.get_component_bounds(c)],'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name())})
 rc=river.get_component_by_class(unreal.WaterBodyRiverComponent)
 R['rc_methods']=[n for n in dir(rc) if 'width' in n.lower() or 'depth' in n.lower()]
 for k in (0.0,0.5,1.0,1.5,2.0):
  rec={'key':k}
  for m in R['rc_methods']:
   if m.startswith('get_') and 'at_spline_input_key' in m:
    try:rec[m]=getattr(rc,m)(k)
    except Exception as e:rec[m]='err '+str(e)[:80]
  R['keys'].append(rec)
except Exception:R['errors'].append(traceback.format_exc())
open(r'F:\Carnival\Saved\WorldExpansion\RiverWidth2_20261001.json','w').write(json.dumps(R,indent=1,default=str))
