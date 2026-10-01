"""Read-only: WaterBodyRiver spline widths/depths from its water spline metadata."""
import json,traceback,unreal
R={'errors':[]}
try:
 w=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
 river=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='WaterBodyRiver')
 sp=river.get_component_by_class(unreal.SplineComponent)
 R['points']=[[round(v) for v in sp.get_location_at_spline_point(i,unreal.SplineCoordinateSpace.WORLD).to_tuple()] for i in range(sp.get_number_of_spline_points())]
 R['length_m']=round(sp.get_spline_length()/100)
 md=None
 for getter in ('get_water_spline_metadata',):
  for o in (river,river.get_component_by_class(unreal.WaterBodyComponent)):
   if o and hasattr(o,getter):md=getattr(o,getter)();break
 if md is None:
  R['dir_river']=[n for n in dir(river) if 'meta' in n.lower() or 'spline' in n.lower()]
 else:
  for k in ('river_width','depth','water_velocity_scalar','audio_intensity'):
   try:
    c=md.get_editor_property(k);R[k]=[(round(p.get_editor_property('in_val'),2),round(p.get_editor_property('out_val'),1)) for p in c.get_editor_property('points')]
   except Exception as e:R[k+'_err']=str(e)[:200]
 R['components']=[c.get_class().get_name()+':'+c.get_name() for c in river.get_components_by_class(unreal.ActorComponent)][:30]
except Exception:R['errors'].append(traceback.format_exc())
open(r'F:\Carnival\Saved\WorldExpansion\RiverWidth_20261001.json','w').write(json.dumps(R,indent=1))
