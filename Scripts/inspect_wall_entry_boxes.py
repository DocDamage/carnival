import json,unreal
out={}
for p in ('/Game/HAUNTED_PRISON/Meshes/Exterior/Moduls/SM_WallEntry','/Game/HAUNTED_PRISON/Meshes/Exterior/Moduls/SM_WallEntryInt'):
 m=unreal.load_asset(p);agg=m.get_editor_property('body_setup').get_editor_property('agg_geom')
 rows=[]
 for b in agg.get_editor_property('box_elems'):
  c=b.get_editor_property('center');r=b.get_editor_property('rotation')
  rows.append({'center':[round(v) for v in c.to_tuple()],'size':[round(b.get_editor_property(k)) for k in ('x','y','z')],'rot':[round(v,1) for v in r.to_tuple()]})
 bb=m.get_bounds();out[p.split('/')[-1]]={'bounds_origin':[round(v) for v in bb.origin.to_tuple()],'bounds_extent':[round(v) for v in bb.box_extent.to_tuple()],'boxes':rows}
open(r'F:\Carnival\Saved\WorldExpansion\PrisonWallEntryBoxes_20261001.json','w').write(json.dumps(out,indent=1))
