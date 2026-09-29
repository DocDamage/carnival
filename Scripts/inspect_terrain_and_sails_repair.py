"""Read-only inspection for terrain portal and Shipwreck root-physics repair."""
import json
from pathlib import Path
import unreal
report={'object_factory_api':[n for n in dir(unreal) if 'object' in n.lower() and any(s in n.lower() for s in ('new','construct'))], 'material_api':[n for n in dir(unreal.MaterialEditingLibrary) if 'input' in n or 'connect' in n]}
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Carnival/World/Levels/L_CoastalMansionApproach')
for a in eas.get_all_level_actors():
    if a.get_actor_label()!='Landscape2': continue
    material=a.get_editor_property('landscape_material'); chain=[]
    while material:
        row={'path':material.get_path_name(),'class':material.get_class().get_name()}; chain.append(row)
        if isinstance(material,unreal.Material):
            row['blend_mode']=str(material.get_editor_property('blend_mode'))
            row['use_material_attributes']=material.get_editor_property('use_material_attributes')
            break
        material=material.get_editor_property('parent')
    report['landscape']={'material_chain':chain,'hole_material':str(a.get_editor_property('landscape_hole_material')),'layers':[str(x) for x in a.get_edit_layers_bp()]}
    try: report['landscape']['weightmap_examples']=[str(t) for c in a.get_components_by_class(unreal.LandscapeComponent)[:2] for t in c.get_editor_property('weightmap_textures')]
    except Exception as e: report['landscape']['weightmap_error']=str(e)
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck')
for a in eas.get_all_level_actors():
    if a.get_actor_label()!='SM_Sails_Torn': continue
    c=a.get_component_by_class(unreal.SkeletalMeshComponent)
    mesh=c.get_skinned_asset(); asset=c.get_editor_property('physics_asset_override') or mesh.get_editor_property('physics_asset')
    report['sails']={'actor':a.get_path_name(),'mesh':mesh.get_path_name(),'physics_asset':asset.get_path_name() if asset else None,'bones':[str(c.get_bone_name(i)) for i in range(c.get_num_bones())]}
    try:
        report['sails']['bodies']=[{'bone':str(b.get_editor_property('bone_name')),'name':b.get_name()} for b in asset.get_editor_property('skeletal_body_setups')]
    except Exception as e: report['sails']['body_error']=str(e)
Path(r'F:\Carnival\Saved\WorldExpansion\Terrain_Sails_Repair_Inspection.json').write_text(json.dumps(report,indent=2))
unreal.SystemLibrary.quit_editor()
