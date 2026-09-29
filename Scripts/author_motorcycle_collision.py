"""Save real body collision for the local imported motorcycle mesh."""
import datetime
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/DirtBike'
OUT.mkdir(parents=True, exist_ok=True)
mesh_path = '/Game/Carnival/Vehicles/Motorcycle/Mesh/SK_rsg_LastGuns_bike_01'
asset_path = '/Game/Carnival/Vehicles/Motorcycle/Mesh/PA_CarnivalBikeBody'
mesh = unreal.load_asset(mesh_path)
assert mesh
source = ROOT / 'Content' / (mesh_path.removeprefix('/Game/') + '.uasset')
backup = OUT / ('BodyCollisionBackup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
backup.mkdir()
shutil.copy2(source, backup / source.name)
physics_file = ROOT / 'Content' / (asset_path.removeprefix('/Game/') + '.uasset')
if physics_file.exists():
    shutil.copy2(physics_file, backup / physics_file.name)
asset = unreal.CarnivalVehicleAuthoring.create_body_collision(mesh, asset_path)
assert asset, 'Single-bone local collision authoring failed'
assert unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
mesh.set_editor_property('physics_asset', asset)
assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
(OUT / 'Body_Collision_Setup.json').write_text(json.dumps({
    'mesh': mesh_path, 'physics_asset': asset.get_path_name(), 'backup': str(backup),
    'saved': True, 'scope': 'body collision only; wheels and rider presentation remain separate'}, indent=2))
