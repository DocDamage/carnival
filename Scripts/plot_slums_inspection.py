"""Plot source-building bounds against the proposed street, from saved evidence."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(r"F:\Carnival\Saved\IndustrialHospital")
maps = json.loads((OUT / "Map_Inspection.json").read_text())
source = next(m for m in maps if m["asset_path"].endswith("L_DemoScene"))
image = Image.new("RGB", (1200, 1600), "#18222c")
draw = ImageDraw.Draw(image)

def screen(x, y):
    return (50 + (x + 21000) * .083, 50 + y * .09)

for actor in source["actors"]:
    bounds = actor.get("bounds")
    mesh = (actor.get("mesh") or "").lower()
    if not bounds or not any(s in mesh for s in ("house", "ground", "stair", "handrail")):
        continue
    x, y, z = bounds["center"]
    ex, ey, ez = bounds["extent"]
    if not (-21000 < x < -8000 and -500 < y < 16500) or ex > 8000 or ey > 8000:
        continue
    kind = "house" if "house" in mesh else "other"
    color = "#94a5b5" if kind == "house" else "#465b69"
    draw.rectangle((*screen(x-ex, y-ey), *screen(x+ex, y+ey)), outline=color, width=2)
    if kind == "house":
        draw.text(screen(x-ex, y), actor["label"], fill="#becad2")
for x in range(-20000, -8000, 1000):
    draw.text(screen(x, 0), str(x), fill="white")
for y in range(0, 16500, 1000):
    draw.text(screen(-21000, y), str(y), fill="white")
draw.line((*screen(-12000, 0), *screen(-12000, 16000)), fill="#ff4444", width=4)
for x in (-12450, -11550):
    draw.line((*screen(x, 0), *screen(x, 16000)), fill="#a14444", width=2)
image.save(OUT / "Slums_Source_Streetplan.png")
