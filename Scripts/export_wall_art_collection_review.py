"""Export representative collection textures from the scratch project."""
import json
from pathlib import Path
import unreal
root=Path(r'F:\Carnival\Saved\WorldExpansion\AssetCompatProbe')
out=root/'CollectionPreviews'
out.mkdir(parents=True,exist_ok=True)
rows=json.loads((root/'Collection_Review_Manifest.json').read_text())
for row in rows:
    asset=unreal.load_asset(row['asset'])
    row['loaded']=bool(asset)
    if not asset: continue
    destination=out/(row['volume']+'_'+row['texture']+'.tga')
    task=unreal.AssetExportTask()
    task.object=asset
    task.filename=str(destination)
    task.automated=True
    task.prompt=False
    task.replace_identical=True
    task.exporter=unreal.TextureExporterTGA()
    row['exported']=bool(unreal.Exporter.run_asset_export_task(task))
    row['preview']=str(destination)
(root/'Collection_Review_Exports.json').write_text(json.dumps(rows,indent=2))
unreal.SystemLibrary.quit_editor()
