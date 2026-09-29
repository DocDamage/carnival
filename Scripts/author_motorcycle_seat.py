"""Add a real driver attachment socket to the assembled bike's normalized root."""
import datetime
import json
import shutil
from pathlib import Path
import unreal

ROOT = Path(r'F:\Carnival')
OUT = ROOT / 'Saved/DirtBike'
path = '/Game/Carnival/Vehicles/Motorcycle/Assembled/SK_CarnivalBike_Body'
mesh = unreal.load_asset(path)
assert mesh
manifest = json.loads((ROOT / 'Content/Carnival/Vehicles/Motorcycle/Assembled/Source/Assembly_Manifest.json').read_text())
backup = OUT / ('SeatBackup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.uasset')
shutil.copy2(ROOT / 'Content' / (path.removeprefix('/Game/') + '.uasset'), backup)
# Character mesh origin is 96 cm below its capsule centre. The riding clip
# is authored with its root at the bike ground origin; preserve that basis.
socket = unreal.CarnivalVehicleAuthoring.set_attachment_socket(mesh, 'DriverSeat', 'root',
    unreal.Vector(0,0,96 + manifest['floor_shift_cm']))
assert socket
assert unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
(OUT / 'Seat_Setup.json').write_text(json.dumps({'mesh':path,'backup':str(backup),
    'socket':'DriverSeat','location':socket.get_editor_property('relative_location').to_tuple(),
    'scope':'root attachment; hand/foot pose contacts and transitions still require fitting'},indent=2))
