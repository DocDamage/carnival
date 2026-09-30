"""Read-only SCS seat census for saved project ride Blueprints."""
import collections
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/RideDevelopment/AuthoredSeatIds.json'
source=json.loads((ROOT/'Saved/RideDevelopment/All_Attended_Authoring.json').read_text())
sds=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
data=unreal.SubobjectDataBlueprintFunctionLibrary
report={'assets_modified':False,'blueprints':[]}
for path in sorted(set(p for p in source['saved_packages'] if p.startswith('/Game/Carnival/Rides/'))):
    bp=unreal.load_asset(path)
    if not isinstance(bp,unreal.Blueprint): continue
    seats={}
    for handle in sds.k2_gather_subobject_data_for_blueprint(bp):
        seat=data.get_associated_object(data.get_data(handle))
        if isinstance(seat,unreal.CarnivalRideSeatComponent):
            seats[seat.get_path_name()]={'component':seat.get_name(),'seat_id':str(seat.seat_id),'path':seat.get_path_name()}
    counts=collections.Counter(row['seat_id'] for row in seats.values())
    report['blueprints'].append({'blueprint':path,'seats':list(seats.values()),
        'duplicates':{key:count for key,count in counts.items() if count>1}})
OUT.write_text(json.dumps(report,indent=2))
unreal.log('AUTHORED_SEAT_IDS '+json.dumps({row['blueprint']:row['duplicates'] for row in report['blueprints']}))
unreal.SystemLibrary.quit_editor()
