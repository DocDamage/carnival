"""Read-only provenance of the unexpected constructed Ferris component."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
report={'assets_modified':False,'actors':[],'blueprints':[],'errors':[]}
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data=unreal.SubobjectDataBlueprintFunctionLibrary
paths=set()
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    path=actor.get_class().get_path_name()
    if not path.startswith('/Game/Carnival/Rides/Attended/BP_Attended_FerrisWheel_'): continue
    paths.add(path.split('.')[0])
    row={'actor':actor.get_path_name(),'unexpected':[],
         'native_construction':list(unreal.CarnivalRouteEditorLibrary.describe_ride_seat_construction(actor))}
    for handle in sds.k2_gather_subobject_data_for_instance(actor):
        info=data.get_data(handle); obj=data.get_associated_object(info)
        if not isinstance(obj,unreal.CarnivalRideSeatComponent) or obj.get_name()!='CarnivalRideSeat': continue
        bp=data.get_blueprint(info)
        details={'path':obj.get_path_name(),'can_delete':data.can_delete(info),
            'is_instanced':data.is_instanced_component(info),'is_inherited':data.is_inherited_component(info),
            'is_native':data.is_native_component(info),'blueprint':bp.get_path_name() if bp else None,
            'variable_name':str(data.get_variable_name(info))}
        try: details['creation_method']=str(obj.get_editor_property('creation_method'))
        except Exception as exc: details['creation_method_error']=str(exc)
        if bp:
            template=data.get_object_for_blueprint(info,bp)
            details['template']=template.get_path_name() if template else None
        row['unexpected'].append(details)
    report['actors'].append(row)
seen=set()
for path in sorted(paths):
    while path and path not in seen:
        seen.add(path); bp=unreal.load_asset(path)
        if not isinstance(bp,unreal.Blueprint): break
        seats=[]
        for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
            obj=data.get_associated_object(data.get_data(handle))
            if isinstance(obj,unreal.CarnivalRideSeatComponent):
                seats.append({'name':obj.get_name(),'path':obj.get_path_name(),'seat_id':str(obj.seat_id)})
        row={'blueprint':path,'seats':seats,
             'execution':list(unreal.CarnivalBalloonFlightComponent.describe_blueprint_execution(bp))}
        try:
            templates=bp.get_editor_property('component_templates')
            row['component_templates']=[{'path':o.get_path_name(),'class':o.get_class().get_name()}
                                        for o in templates]
        except Exception as exc: row['component_templates_error']=str(exc)
        report['blueprints'].append(row)
        parent=unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp)
        path=parent.get_path_name().split('.')[0] if parent else None
(ROOT/'Saved/RideDevelopment/FerrisSeatOrigin.json').write_text(json.dumps(report,indent=2))
unreal.SystemLibrary.quit_editor()
