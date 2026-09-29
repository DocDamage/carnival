"""Draw a diagnostic floor plan from saved source actor bounds, without Unreal."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(r"F:\Carnival\Saved\IndustrialHospital")
maps = json.loads((OUT / "Map_Inspection.json").read_text())
source = next(m for m in maps if m["asset_path"].endswith("LV_Hospital_Main_Architecture"))
image = Image.new("RGB", (1550, 1180), "#17202a")
draw = ImageDraw.Draw(image)

def screen(x, y):
    return (40 + x * .118, 45 + (y + 7300) * .118)

for kind, color in (("floor", "#5d6d7e"), ("wall", "#cbd2d8"), ("door", "#e8a543")):
    for actor in source["actors"]:
        mesh = (actor.get("mesh") or "").lower()
        bounds = actor.get("bounds")
        if kind not in mesh or not bounds:
            continue
        x, y, z = bounds["center"]
        ex, ey, ez = bounds["extent"]
        if z - ez > 250 or z + ez < 80:
            continue
        draw.rectangle((*screen(x-ex, y-ey), *screen(x+ex, y+ey)), fill=color)
        if kind == "door":
            draw.text(screen(x+30, y+40), actor["label"].replace("SM_", "").replace("BP_", ""), fill="#ffcc80")
for x in range(0, 12500, 1000):
    p = screen(x, -7200)
    draw.text(p, str(x), fill="white")
for y in range(-7000, 2000, 1000):
    draw.text(screen(0, y), str(y), fill="white")
for name, x, y in (("Road endpoint", 5000, -1750), ("Door center", 5200, -1775), ("Old camera", 3900, -1750)):
    px, py = screen(x, y)
    draw.ellipse((px-6, py-6, px+6, py+6), fill="#ff3333")
    draw.text((px-15, py-25), name, fill="white")
image.save(OUT / "Hospital_Source_Floorplan.png")
