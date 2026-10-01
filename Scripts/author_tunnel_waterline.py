"""Make the sewer-tunnel water boundary visible: a translucent, two-sided, unlit teal sheet across the
Sewer -> Atlantis passage at x = -21000, where Water_Flooded_AtlantisShipwreck begins. No collision.
Creates /Game/Carnival/World/Materials/Water/M_CarnivalWaterline and saves only that material and the
connectors level (backed up); the persistent map hash is checked unchanged."""
import hashlib,json,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(r'F:\Carnival');CONN='L_CarnivalWorldExpansion_Connections_Layout'
CONN_FILE=ROOT/('Content/Carnival/World/Levels/'+CONN+'.umap')
MAPFILE=ROOT/'Content/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.umap'
OUT=ROOT/'Saved/WorldExpansion/TunnelWaterline_20261001';OUT.mkdir(parents=True,exist_ok=False)
PKG='/Game/Carnival/World/Materials/Water';MAT='M_CarnivalWaterline'
ML=unreal.MaterialEditingLibrary;V=unreal.Vector
R={'success':False,'errors':[]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 shutil.copy2(CONN_FILE,OUT/(CONN+'.before_waterline.umap'));R['map_sha256_before']=sha(MAPFILE)
 assert not unreal.EditorAssetLibrary.does_asset_exist(PKG+'/'+MAT)
 m=unreal.AssetToolsHelpers.get_asset_tools().create_asset(MAT,PKG,unreal.Material,unreal.MaterialFactoryNew())
 m.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
 m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
 m.set_editor_property('two_sided',True)
 col=ML.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-400,0);col.set_editor_property('constant',unreal.LinearColor(0.03,0.22,0.26,1))
 fres=ML.create_material_expression(m,unreal.MaterialExpressionFresnel,-400,200)
 op=ML.create_material_expression(m,unreal.MaterialExpressionLinearInterpolate,-200,200)
 op.set_editor_property('const_a',0.35);op.set_editor_property('const_b',0.7)
 assert ML.connect_material_expressions(fres,'',op,'Alpha')
 assert ML.connect_material_property(col,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 assert ML.connect_material_property(op,'',unreal.MaterialProperty.MP_OPACITY)
 ML.recompile_material(m);unreal.EditorAssetLibrary.save_asset(PKG+'/'+MAT,False)
 world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival');assert world
 EA=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 assert not [a for a in EA.get_all_level_actors() if a.get_actor_label()=='SewerToAtlantis_Waterline']
 assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name(CONN)
 # Plane faces +Z; pitch 90 stands it up facing -X. Tunnel: walkway y -10933..-9721, floor -1800, ceiling -1340.
 a=EA.spawn_actor_from_class(unreal.StaticMeshActor,V(-21000,-10327,-1570),unreal.Rotator(roll=0.0,pitch=90.0,yaw=0.0))
 assert '/'+CONN+'.' in a.get_path_name()
 a.set_actor_label('SewerToAtlantis_Waterline')
 c=a.static_mesh_component;c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'))
 c.set_material(0,m);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property('cast_shadow',False)
 a.set_actor_scale3d(V(4.8,13.0,1.0))
 assert unreal.EditorLoadingAndSavingUtils.save_packages([a.get_outermost()],False)
 R['map_sha256_after']=sha(MAPFILE);assert R['map_sha256_after']==R['map_sha256_before']
 o,e=a.get_actor_bounds(False);R['bounds']=[list(o.to_tuple()),list(e.to_tuple())]
 R['success']=True
except Exception:R['errors'].append(traceback.format_exc())
finally:(OUT/'index.json').write_text(json.dumps(R,indent=1,default=str))
