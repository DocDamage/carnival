"""Remove the measured duplicate Ferris Blueprint node, preserving all seats."""
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/RideDevelopment'
BACKUP=OUT/('BeforeDuplicateSeatRepair_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
REPORT={'success':False,'removed':[],'saved_packages':[],'backup':str(BACKUP),'vendor_blueprints_modified':False,
        'repair_scope':'Exact duplicate project Ferris SCS node'}
assert unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def targets():
    return [a for a in actors.get_all_level_actors() if a.get_class().get_path_name().startswith(
        '/Game/Carnival/Rides/Attended/BP_Attended_FerrisWheel_')]

def snapshot(actor):
    seats=[s for s in actor.get_components_by_class(unreal.CarnivalRideSeatComponent)
           if s.get_name().startswith('Seat_')]
    assert len(seats)==160
    return {s.get_name():{'id':str(s.seat_id),'parent':s.get_attach_parent().get_name(),
        'translation':list(s.get_relative_transform().translation.to_tuple()),
        'rotation':list(s.get_relative_transform().rotation.to_tuple()),
        'scale':list(s.get_relative_transform().scale3d.to_tuple())} for s in seats}

before={a.get_path_name():snapshot(a) for a in targets()}
assert len(before)==3
packages=set()
for actor in targets():
    packages.add(actor.get_level().get_path_name().split('.')[0])
    packages.add(actor.get_class().get_path_name().split('.')[0])
for package in sorted(packages):
    extension='.uasset' if '/Rides/' in package else '.umap'
    relative=package.removeprefix('/Game/')+extension
    source=ROOT/'Content'/relative; target=BACKUP/relative
    target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
for package in sorted(p for p in packages if '/Rides/' in p):
    bp=unreal.load_asset(package)
    removed=unreal.CarnivalRouteEditorLibrary.repair_duplicate_ferris_seat_blueprint(bp)
    assert removed==1, 'Exact measured duplicate was not removed: '+package+' result '+str(removed)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
    REPORT['removed'].append({'blueprint':package,'node':'CarnivalRideSeat','retained_seats':160})
    REPORT['saved_packages'].append(package)
for actor in targets():
    seats=list(actor.get_components_by_class(unreal.CarnivalRideSeatComponent))
    assert len(seats)==160 and len({str(s.seat_id) for s in seats})==160
    assert snapshot(actor)==before[actor.get_path_name()], 'Calibrated geometry changed'
    assert all(s.get_name()!='CarnivalRideSeat' for s in seats)
    REPORT.setdefault('construction_after',{})[actor.get_path_name()]=list(
        unreal.CarnivalRouteEditorLibrary.describe_ride_seat_construction(actor))
for package in sorted(p for p in packages if '/Rides/' not in p):
    assert unreal.EditorLevelLibrary.set_current_level_by_name(package.rsplit('/',1)[-1])
    assert unreal.EditorLevelLibrary.save_current_level()
    REPORT['saved_packages'].append(package)
REPORT['success']=True
(OUT/'DuplicateFerrisSeatRepair.json').write_text(json.dumps(REPORT,indent=2))
unreal.SystemLibrary.quit_editor()
