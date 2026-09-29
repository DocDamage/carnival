"""Run the scratch texture export and build compact review sheets."""
import json
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root=Path(r'F:\Carnival')
scratch=root/'Saved/WorldExpansion/AssetCompatProbe'
env=os.environ.copy()
env['UE_SKIP_UBT_SDK_SETUP']='1'
args=[r'C:\Program Files\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe',str(scratch/'AssetCompatProbe.uproject'),
      '-unattended','-nullrhi','-nosplash','-nop4','-run=pythonscript',
      '-script='+str(root/'Scripts/export_wall_art_collection_review.py'),
      '-abslog='+str(scratch/'Collection_Review_Engine.log')]
with (scratch/'Collection_Review_Console.log').open('w') as log:
    result=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
if result.returncode: raise RuntimeError('Scratch export failed; see Collection_Review_Engine.log')
rows=json.loads((scratch/'Collection_Review_Exports.json').read_text())
volumes=sorted(set(row['volume'] for row in rows))
font=ImageFont.truetype(r'C:\Windows\Fonts\segoeui.ttf',18)
sheets=[]
for page in range(0,len(volumes),4):
    sheet=Image.new('RGB',(1150,960),(28,29,32))
    draw=ImageDraw.Draw(sheet)
    for line,volume in enumerate(volumes[page:page+4]):
        items=[row for row in rows if row['volume']==volume]
        draw.text((12,line*240+5),volume,fill='white',font=font)
        for column,row in enumerate(items):
            if not row.get('exported'): continue
            pic=Image.open(row['preview']).convert('RGB')
            pic.thumbnail((215,180))
            x=column*230+(230-pic.width)//2
            y=line*240+32+(180-pic.height)//2
            sheet.paste(pic,(x,y))
            draw.text((column*230+8,line*240+215),row['texture'].replace('T_','').replace('_D',''),fill='white',font=font)
    path=scratch/('Collection_Review_%02d.jpg'%(page//4+1))
    sheet.save(path,quality=92)
    sheets.append(str(path))
print(json.dumps({'exported':sum(bool(r.get('exported')) for r in rows),'textures':len(rows),'sheets':sheets}))
