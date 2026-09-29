"""Create a review sheet from the photo textures in one HorrorPaint volume."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(r"F:\Carnival\Saved\WorldExpansion\AssetCompatProbe\TexturePreviews")
out = Path(r"F:\Carnival\Saved\WorldExpansion\AssetCompatProbe\HorrorPaintVol48_Photos_ContactSheet.jpg")
files = sorted(root.glob("T_Photo_*_D.tga"))
cell_w, cell_h, header_h, padding = 320, 250, 34, 14
cols, rows = 3, (len(files) + 2) // 3
sheet = Image.new("RGB", (padding + cols * (cell_w + padding), padding + rows * (cell_h + padding)), (27, 28, 32))
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 20)
for index, path in enumerate(files):
    x = padding + (index % cols) * (cell_w + padding)
    y = padding + (index // cols) * (cell_h + padding)
    draw.text((x + 4, y + 2), f"Photo {index+1:02d}", fill=(242, 232, 211), font=font)
    image = Image.open(path).convert("RGB")
    image.thumbnail((cell_w, cell_h - header_h), Image.Resampling.LANCZOS)
    sheet.paste(image, (x + (cell_w - image.width) // 2, y + header_h + (cell_h - header_h - image.height) // 2))
sheet.save(out, quality=92)
print(f"Wrote {out} ({len(files)} textures)")
