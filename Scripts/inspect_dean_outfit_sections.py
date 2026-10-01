"""Read assembled outfit and source garment sections, mappings and weights; no saves."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/CharacterRepairs/DeanOutfitSectionSurvey_20260930';OUT.mkdir(parents=True,exist_ok=True)
REPORT={'success':False,'errors':[],'assets_saved':False,'meshes':[],'source_hashes':[],
        'limits':'Loaded geometry/mapping/weight metadata only. Runtime-normalized indices do not prove authored slot intent. Garment fit, actual poses and shader/LOD rendering require visual comparisons.'}
def path(o):return o.get_path_name() if o else None
try:
    assert unreal.EditorLoadingAndSavingUtils.load_map('/Engine/Maps/Entry')
    instance=unreal.load_asset('/Game/Carnival/Crowd/Instances/ExpandedFinal2/MHI_Dean');assert instance
    actor,error=unreal.CarnivalCrowdEditorLibrary.place_initialized_meta_human_actor(instance,'DeanOutfitSectionProbe',unreal.Vector(),unreal.Rotator())
    assert actor and not error,error
    meshes={}
    REPORT['components']=[]
    for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        mesh=comp.get_editor_property('skeletal_mesh_asset')
        REPORT['components'].append({'name':comp.get_name(),'mesh':path(mesh),'materials':[path(comp.get_material(i)) for i in range(comp.get_num_materials())],
            'relative_location':list(comp.get_editor_property('relative_location').to_tuple()),
            'relative_scale':list(comp.get_editor_property('relative_scale3d').to_tuple())})
        if mesh:meshes[path(mesh)]=mesh
    sourcebase='/Game/Outfits/TshirtVariants/OA_TshirtLngSlv/Meshes/'
    for name in ['m_med_ovw_CombinedSkelMesh']+['m_med_ovw_TshirtLngSlv_nrm_lod'+str(i)+'_mesh' for i in range(4)]:
        package=sourcebase+name
        sourcefile=ROOT/'Content'/(package.removeprefix('/Game/')+'.uasset')
        before=hashlib.sha256(sourcefile.read_bytes()).hexdigest()
        mesh=unreal.load_asset(package);assert isinstance(mesh,(unreal.SkeletalMesh,unreal.StaticMesh)),(package,type(mesh))
        if isinstance(mesh,unreal.SkeletalMesh):meshes[path(mesh)]=mesh
        else:
            REPORT.setdefault('source_static_meshes',[]).append({'mesh':path(mesh),'lod_count':mesh.get_num_lods(),
                'materials':[{'slot':str(m.get_editor_property('material_slot_name')),'material':path(m.get_editor_property('material_interface'))}
                    for m in mesh.get_editor_property('static_materials')],
                'sections_per_lod':[mesh.get_num_sections(i) for i in range(mesh.get_num_lods())]})
        REPORT['source_hashes'].append({'file':str(sourcefile),'sha256_before':before})
    for key,mesh in meshes.items():
        before=unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(mesh)
        row=json.loads(unreal.CarnivalCrowdMaterialEditorLibrary.describe_loaded_mesh_sections(mesh))
        row['digest_before']=before;row['digest_after']=unreal.CarnivalCrowdMaterialEditorLibrary.get_loaded_mesh_structure_digest(mesh)
        assert row['digest_before']==row['digest_after'],'Read-only description altered loaded mesh '+key
        REPORT['meshes'].append(row)
    for row in REPORT['source_hashes']:
        row['sha256_after']=hashlib.sha256(Path(row['file']).read_bytes()).hexdigest();assert row['sha256_before']==row['sha256_after']
    REPORT['success']=True
except Exception:
    REPORT['errors'].append(traceback.format_exc());raise
finally:(OUT/'index.json').write_text(json.dumps(REPORT,indent=2))
