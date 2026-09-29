"""Plot exported ride surfaces in Unreal centimeters, retaining mesh evidence."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'Saved/RideDevelopment/SeatGeometry'
manifest = json.loads((OUT / 'index.json').read_text())
summary = []
for row in manifest['meshes']:
    vertices, faces = [], []
    for line in Path(row['obj']).read_text().splitlines():
        if line.startswith('v '):
            x, z, y = map(float, line.split()[1:4])
            vertices.append((x,y,z))
        elif line.startswith('f '): faces.append([int(v.split('/')[0])-1 for v in line.split()[1:4]])
    v = np.array(vertices); tri = v[np.array(faces)]
    # Unreal's clockwise front faces use the opposite cross product from OBJ.
    normal = -np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0])
    area = np.linalg.norm(normal, axis=1)/2
    normal /= np.maximum(2*area[:,None], 1.e-9)
    center = tri.mean(axis=1)
    surface = (normal[:,2] > .9) & (area > 5)
    heights = {}
    for z, weight in zip(center[surface,2], area[surface]):
        key = str(round(float(z)/5)*5)
        heights[key] = heights.get(key, 0)+float(weight)
    levels = sorted(heights.items(), key=lambda item: -item[1])[:18]
    output = Image.new('RGB',(1600,600),'#eeeeee'); draw=ImageDraw.Draw(output)
    for panel, axes in enumerate(((0,1,2),(0,2,1),(1,2,0))):
        a,b,depth = axes
        lo=v[:,(a,b)].min(axis=0); hi=v[:,(a,b)].max(axis=0)
        scale=min(460/max(hi[0]-lo[0],1),490/max(hi[1]-lo[1],1))
        projected=(tri[:,:,(a,b)]-(lo+hi)/2)*scale
        projected[:,:,0]+=panel*530+265; projected[:,:,1]=300-projected[:,:,1]
        for index in np.argsort(center[:,depth]):
            shade=int(130+80*abs(normal[index,depth]))
            fill=(180,60,50) if surface[index] else (shade,shade,shade)
            draw.polygon([tuple(p) for p in projected[index]],fill=fill)
        draw.text((panel*530+12,10),f"{Path(row['obj']).stem}: {'XYZ'[a]}/{'XYZ'[b]} (cm)",fill='black')
        draw.text((panel*530+12,555),f"min {lo.round(1)}; max {hi.round(1)}",fill='black')
        draw.text((panel*530+12,575),'Red: upward surface triangles',fill='black')
    output.save(OUT/(Path(row['obj']).stem+'_surfaces.png'))
    summary.append({'mesh':row['mesh'],'top_surface_height_bins_by_area':levels,
                    'triangles':len(tri),'bounds':[v.min(axis=0).tolist(),v.max(axis=0).tolist()]})
(OUT/'surface_analysis.json').write_text(json.dumps(summary,indent=2))
