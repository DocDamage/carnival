"""Visualize measured capsule connectivity; disconnected grid is not a door verdict."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(r'F:\Carnival\Saved\IndustrialHospital')
report = json.loads((OUT / 'Hospital_Room_Connectivity.json').read_text())
image = Image.new('RGB', (1450, 1160), '#16202b')
draw = ImageDraw.Draw(image)


def screen(x, y):
    return 60 + (x - 1000) * .12, 90 + (y + 7200) * .12


palette = ['#c6a96f', '#a19fea', '#ff8181', '#8cc7ed', '#ed93d1']
summary = []
for i, component in enumerate(report['components']):
    color = '#5dddba' if i == report['entrance_component'] else palette[(i + 2) % len(palette)]
    for x, y in component['nodes']:
        px, py = screen(x, y)
        draw.rectangle((px-4, py-4, px+4, py+4), fill=color)
    xs, ys = zip(*component['nodes'])
    summary.append({'index': i, 'nodes': component['count'],
                    'bounds': [min(xs), min(ys), max(xs), max(ys)],
                    'entrance_connected': i == report['entrance_component']})
    if component['count'] >= 20:
        draw.text(screen((min(xs)+max(xs))/2, (min(ys)+max(ys))/2), str(i), fill='white', stroke_width=2, stroke_fill='black')
px, py = screen(*report['entrance_seed'])
draw.ellipse((px-8, py-8, px+8, py+8), outline='white', width=3)
draw.text((35, 22), 'Hospital ground floor: measured 1 m capsule grid. Entrance component = green.', fill='white')
draw.text((35, 43), 'Grid gaps can miss narrow passages. Verify with door probes and real walking.', fill='white')
for x in range(1000, 12001, 1000):
    draw.text(screen(x, -7500), str(x), fill='white')
for y in range(-7000, 1601, 1000):
    draw.text((3, screen(1000, y)[1]), str(y), fill='white')
image.save(OUT / 'Hospital_Room_Connectivity.png')
(OUT / 'Hospital_Room_Component_Summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary[:12], indent=2))
