"""Fresh-process verification of scoped Dean bindings and unchanged loaded mesh/material state."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/DeanCrowdSkinBinding_20260930'
saved=json.loads((OUT/'index.json').read_text());assert saved['success']
REPORT={'success':False,'errors':[],'meshes_verified':0,'materials_verified':0,'bindings':[],'assets_saved':False}
ML=unreal.MaterialEditingLibrary
def path(o): return o.get_path_name() if o else None
def snapshot(m):
    return {'parent':path(m.get_editor_property('parent')),
        'textures':{str(n):path(ML.get_material_instance_texture_parameter_value(m,n)) for n in ML.get_texture_parameter_names(m)},
        'scalars':{str(n):ML.get_material_instance_scalar_parameter_value(m,n) for n in ML.get_scalar_parameter_names(m)},
        'vectors':{str(n):list(ML.get_material_instance_vector_parameter_value(m,n).to_tuple()) for n in ML.get_vector_parameter_names(m)},
        'switches':{str(n):ML.get_material_instance_static_switch_parameter_value(m,n) for n in ML.get_static_switch_parameter_names(m)}}
try:
    file=Path(saved['backups'][0]['original'])
    assert hashlib.sha256(file.read_bytes()).hexdigest()==saved['saved_sha256']
    c=unreal.load_asset(saved['saved_package']);assert c
    prefix=c.get_path_name()+':'
    meshes={path(m):unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(m)
        for m in unreal.ObjectIterator(unreal.SkeletalMesh) if path(m).startswith(prefix)}
    assert meshes==saved['meshes_before'],'Loaded mesh structure differs after fresh reload'
    REPORT['meshes_verified']=len(meshes)
    changes={row['material']:row for row in saved['changes']}
    materials={path(m):m for m in unreal.ObjectIterator(unreal.MaterialInstanceConstant) if path(m).startswith(prefix)}
    assert set(materials)==set(saved['materials_before'])
    for p,m in materials.items():
        expected=json.loads(json.dumps(saved['materials_before'][p]))
        if p in changes:
            expected['textures'].update(changes[p]['textures'])
            expected['switches']['Use Baked Material']=True
            REPORT['bindings'].append({'material':p,'textures':changes[p]['textures']})
        assert snapshot(m)==expected,'Unexpected material state after reload: '+p
        REPORT['materials_verified']+=1
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:
    (OUT/'Reload.json').write_text(json.dumps(REPORT,indent=2))
