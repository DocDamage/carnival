import json
from pathlib import Path
import unreal
out=Path(r'F:\Carnival\Saved\WorldExpansion\Connection_Repair_Geometry.json')
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival')
rows=[]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    label=a.get_actor_label(); path=a.get_path_name()
    if not (label in ('Cube2','Cube3','Landscape2','SM_Sails_Torn') or ('Connections_Layout' in path and any(x in label for x in ('StairCeiling','AtlantisToShipwreck')))): continue
    center,extent=a.get_actor_bounds(False,True)
    row={'path':path,'name':a.get_name(),'label':label,'class':a.get_class().get_name(),'location':a.get_actor_location().to_tuple(),'scale':a.get_actor_scale3d().to_tuple(),'rotation':str(a.get_actor_rotation()),'center':center.to_tuple(),'extent':extent.to_tuple()}
    if label=='Landscape2':
        row['api']=[n for n in dir(a) if any(x in n for x in ('weight','layer','landscape','material'))]
        row['transform']=str(a.get_actor_transform())
    if 'Sails' in label:
        row['components']=[{'name':c.get_name(),'class':c.get_class().get_name(),'physics':c.is_simulating_physics(),'collision':str(c.get_collision_enabled()),'asset':str(c.get_editor_property('physics_asset_override')) if isinstance(c,unreal.SkeletalMeshComponent) else ''} for c in a.get_components_by_class(unreal.PrimitiveComponent)]
    rows.append(row)
out.write_text(json.dumps(rows,indent=2))
unreal.SystemLibrary.quit_editor()
