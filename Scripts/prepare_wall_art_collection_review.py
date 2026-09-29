"""Copy representative textures into the disposable review project, never the game."""
import json
import shutil
from pathlib import Path

root = Path(r'F:\Carnival')
scratch = root/'Saved/WorldExpansion/AssetCompatProbe'
rows = []
for source in sorted((root/'Assets').glob('HorrorFa*/data/Content/HorrorPaintVol*')):
    for name in ('T_Picture_01_D', 'T_Picture_07_D', 'T_Picture_14_D', 'T_Photo_01_D', 'T_Photo_06_D'):
        file = source/'Textures'/(name+'.uasset')
        if not file.exists(): continue
        destination = scratch/'Content'/source.name/'Textures'/file.name
        destination.parent.mkdir(parents=True,exist_ok=True)
        if not destination.exists(): shutil.copy2(file,destination)
        for ext in ('.ubulk','.uexp'):
            if file.with_suffix(ext).exists() and not destination.with_suffix(ext).exists():
                shutil.copy2(file.with_suffix(ext),destination.with_suffix(ext))
        rows.append({'volume':source.name,'texture':name,'asset':'/Game/'+source.name+'/Textures/'+name})
(scratch/'Collection_Review_Manifest.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'collections':len(set(row['volume'] for row in rows)), 'textures':len(rows)}))
