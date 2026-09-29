"""Recover local sampler-repair graph wiring from unchanged vendor originals.

Requires CarnivalMaterialRepairLibrary. Backs up every touched local graph,
restores exact input/output-index/mask connections, recompiles the local master
and refuses to save if the compiler reports errors. No instance reparenting or
vendor mutation is performed.
"""
import hashlib
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/'Saved/CharacterRepairs'
BACKUP=OUT/('BeforeSamplerGraphRecovery_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
PREFIX='/Game/Carnival/Crowd/Materials/SamplerRepair/'
ML=unreal.MaterialEditingLibrary
AL=unreal.EditorAssetLibrary
REPORT={'status':'not_started','backup':str(BACKUP),'backups':[],
        'restored_graphs':[],'compiler_errors':[],'saved_packages':[],'errors':[],
        'vendor_assets_modified':False}


def expressions(asset):
    return (ML.get_material_expressions(asset) if isinstance(asset,unreal.Material)
            else ML.get_material_function_expressions(asset))


def backup(asset):
    package=asset.get_path_name().split('.')[0]
    assert package.startswith(PREFIX), package
    for extension in ('.uasset','.uexp','.ubulk'):
        relative=package[len('/Game/'):] + extension
        source=ROOT/'Content'/relative
        if source.exists():
            destination=BACKUP/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
            REPORT['backups'].append({'file':str(destination),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})


try:
    previous=json.loads((OUT/'CrowdSamplerRepair.json').read_text())
    pairs={}
    for entry in previous['cloned_assets']:
        source=unreal.load_asset(entry['source'])
        if not isinstance(source,(unreal.Material,unreal.MaterialFunction)): continue
        target=unreal.load_asset(entry['local'])
        assert target and target.get_path_name().startswith(PREFIX)
        assert source.get_class()==target.get_class(), entry
        pairs[source.get_path_name()]=(source,target)
    assert len(pairs)==6, f'Expected master plus five copied functions; found {len(pairs)}'
    for source,target in pairs.values(): backup(target)
    done=set()

    def restore(key):
        if key in done: return
        source,target=pairs[key]
        source_nodes={node.get_name():node for node in expressions(source)}
        target_nodes={node.get_name():node for node in expressions(target)}
        assert source_nodes.keys()==target_nodes.keys(), 'Duplicate graph nodes differ: '+key
        for name,node in source_nodes.items():
            if not isinstance(node,unreal.MaterialExpressionMaterialFunctionCall): continue
            child=node.get_editor_property('material_function')
            if not child or child.get_path_name() not in pairs: continue
            child_key=child.get_path_name()
            restore(child_key)
            local_call=target_nodes[name]
            local_child=pairs[child_key][1]
            if local_call.get_editor_property('material_function')!=local_child:
                local_call.set_editor_property('material_function',local_child)
        errors=list(unreal.CarnivalMaterialRepairLibrary.restore_material_graph_connections(source,target))
        assert not errors, json.dumps(errors)
        REPORT['restored_graphs'].append({'source':key,'local':target.get_path_name(),
                                        'expression_count':len(source_nodes)})
        done.add(key)
        if isinstance(target,unreal.MaterialFunction): ML.update_material_function(target)

    for key in pairs: restore(key)
    for source,target in pairs.values():
        if isinstance(target,unreal.Material):
            REPORT['compiler_errors'].extend(list(ML.recompile_material(target)))
    assert not REPORT['compiler_errors'], json.dumps(REPORT['compiler_errors'])
    for source,target in pairs.values():
        assert AL.save_loaded_asset(target,only_if_is_dirty=False), target.get_path_name()
        REPORT['saved_packages'].append(target.get_path_name())
    REPORT['status']='saved_compiled_current_editor_shader_platform_needs_fresh_sm5_cook'
except Exception:
    REPORT['status']='failed'
    REPORT['errors'].append(traceback.format_exc())
finally:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'CrowdSamplerGraphRecovery.json').write_text(json.dumps(REPORT,indent=2))
    unreal.log('CROWD_SAMPLER_GRAPH_RECOVERY '+json.dumps(REPORT))
    unreal.SystemLibrary.quit_editor()
