"""Build a contact sheet of the user's Gothic wall-painting textures."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

source = Path(r"G:\3d assets\Medieval3c5a0a999b62V1\Gothic_Props\Textures")
files = sorted(source.glob("T_Props_Painting_*.png"))
tile_w, tile_h, label_h = 500, 340, 48
cols = 3
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tile_w, rows * (tile_h + label_h)), "#282828")
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype("arial.ttf", 28)
for i, path in enumerate(files):
    image = Image.open(path).convert("RGB")
    image.thumbnail((tile_w - 16, tile_h - 16))
    x, y = (i % cols) * tile_w, (i // cols) * (tile_h + label_h)
    sheet.paste(image, (x + (tile_w - image.width) // 2, y + (tile_h - image.height) // 2))
    draw.text((x + 8, y + tile_h + 4), path.stem, fill="white", font=font)
out = Path(r"F:\Carnival\Saved\WorldExpansion\GothicPaintings_PreviewSheet.jpg")
sheet.save(out, quality=94)
print(out)
