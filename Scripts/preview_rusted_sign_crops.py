"""Make a visual index of the sign rectangles referenced by the GLB meshes."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(r"F:\Carnival")
inspection = json.loads((root / "Saved/WorldExpansion/Rusted_Signs_Inspection.json").read_text(encoding="utf-8"))
atlas = Image.open(root / "Saved/WorldExpansion/ExternalSource/AdditionalAssets/RustedSigns/Textures/Image_0.png").convert("RGB")
tile_w, tile_h, label_h, cols = 440, 300, 42, 3
rows = (len(inspection["meshes"]) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tile_w, rows * (tile_h + label_h)), "#242424")
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype("arial.ttf", 26)
for index, row in enumerate(inspection["meshes"]):
    u0, v0, u1, v1 = row["uv_bounds"]
    rect = (int(u0 * atlas.width), int((1 - v1) * atlas.height),
            int(u1 * atlas.width), int((1 - v0) * atlas.height))
    crop = atlas.crop(rect)
    crop.thumbnail((tile_w - 12, tile_h - 12))
    x = (index % cols) * tile_w
    y = (index // cols) * (tile_h + label_h)
    sheet.paste(crop, (x + (tile_w - crop.width) // 2, y + (tile_h - crop.height) // 2))
    draw.text((x + 8, y + tile_h + 4), f"{row['name']} | {row['dimensions_cm'][0]:.0f} x {row['dimensions_cm'][2]:.0f} cm",
              fill="white", font=font)
out = root / "Saved/WorldExpansion/Rusted_Sign_PreviewSheet.jpg"
sheet.save(out, quality=92)
print(out)
