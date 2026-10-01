"""Read exact material objects observed in the saved populated review; never save assets."""
import json, traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/LiveCrowdMaterialBindings_20260930'
OUT.mkdir(parents=True,exist_ok=True)
runtime=json.loads((ROOT/'Saved/PresentationAcceptance/PopulatedCarnivalNightBounce_20260930/index.json').read_text())
ML=unreal.MaterialEditingLibrary
REPORT={'success':False,'errors':[],'assets_modified':False,'materials':[], 'temporary_instances_assembled':[],
        'source_report':'PopulatedCarnivalNightBounce_20260930',
        'limits':'Read-only effective parameter/parent inspection of observed material objects. Does not establish shader resource validity or intended section mapping, and makes no appearance correction.'}

def path(obj): return obj.get_path_name() if obj else None

try:
    assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
    paths=[]
    # Face, eyes, clothes, skin and hair from real collection-one components.
    for component in runtime['live_components'][:16]:
        for key in component['materials']:
            if key and key not in paths: paths.append(key)
    for key in paths:
        if key.startswith('/Game/Carnival/Crowd/Instances/'):
            instance_path=key.split(':')[0]
            if instance_path not in REPORT['temporary_instances_assembled']:
                instance=unreal.load_object(None,instance_path)
                assert isinstance(instance,unreal.MetaHumanInstance),instance_path
                actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(
                    instance,'MaterialBindingProbe_'+str(len(REPORT['temporary_instances_assembled'])),
                    unreal.Vector(),unreal.Rotator())
                assert actor and not error,error
                REPORT['temporary_instances_assembled'].append(instance_path)
        asset=unreal.load_object(None,key)
        assert isinstance(asset,unreal.MaterialInterface),key
        row={'path':key,'class':asset.get_class().get_name(),'parent_chain':[], 'textures':[], 'vectors':[]}
        REPORT['materials'].append(row)
        parent=asset
        while parent:
            row['parent_chain'].append(path(parent))
            if isinstance(parent,unreal.Material): break
            parent=parent.get_editor_property('parent')
        for name in ML.get_texture_parameter_names(asset):
            if isinstance(asset,unreal.MaterialInstanceDynamic): texture=asset.get_texture_parameter_value(name)
            elif isinstance(asset,unreal.MaterialInstanceConstant): texture=ML.get_material_instance_texture_parameter_value(asset,name)
            else: texture=ML.get_material_default_texture_parameter_value(asset,name)
            row['textures'].append({'name':str(name),'texture':path(texture),
                'class':texture.get_class().get_name() if texture else None})
        for name in ML.get_vector_parameter_names(asset):
            if isinstance(asset,unreal.MaterialInstanceDynamic): colour=asset.get_vector_parameter_value(name)
            elif isinstance(asset,unreal.MaterialInstanceConstant): colour=ML.get_material_instance_vector_parameter_value(asset,name)
            else: colour=ML.get_material_default_vector_parameter_value(asset,name)
            row['vectors'].append({'name':str(name),'value':list(colour.to_tuple())})
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc()); raise
finally:
    (OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
