"""Assemble a review video, pose sheet, source scripts and verified asset ZIP."""
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

OUT = Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile")
QA = Path(r"F:\Carnival\Saved\HauntedDollMobile")
SCRIPTS = Path(r"F:\Carnival\Scripts")
TIMING = json.loads((QA / "Demo_Timing.json").read_text())
validation = json.loads((OUT / "Export_Roundtrip_Validation.json").read_text())
assert validation["status"] == "PASS"
frames = QA / "DemoFrames"
labeled = QA / "LabeledFrames"
labeled.mkdir(exist_ok=True)
font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 25)
small = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
accent = (203, 116, 99)

for shot in TIMING["shots"]:
    for i in range(shot["first_frame"], shot["last_frame"] + 1):
        im = Image.open(frames / f"frame_{i:04d}.png").convert("RGB")
        draw = ImageDraw.Draw(im)
        draw.rectangle((0, 0, im.width, 101), fill=(16, 20, 24))
        draw.text((30, 17), "POSSESSED DOLL  /  CUSTOM MOTION SET", font=small, fill=(161, 172, 181))
        draw.text((29, 44), shot["title"], font=font, fill=(237, 238, 232))
        draw.rectangle((30, 87, 94, 89), fill=accent)
        draw.rectangle((0, 862, im.width, 900), fill=(16, 20, 24))
        draw.text((30, 871), "STIFF + TWITCHY   |   30 FPS   |   BLENDER PREVIEW", font=small, fill=(167, 177, 185))
        length = (i - shot["first_frame"] + 1) / (shot["last_frame"] - shot["first_frame"] + 1)
        draw.rectangle((0, 897, int(im.width * length), 899), fill=accent)
        im.save(labeled / f"frame_{i:04d}.png")

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
video = OUT / "Possessed_Doll_Mobile_Animations.mp4"
subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-framerate", "30",
                "-i", str(labeled / "frame_%04d.png"), "-frames:v", str(TIMING["frames"]),
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", str(video)], check=True)
# Decode the entire final video once; a successful encode alone is insufficient.
subprocess.run([ffmpeg, "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)

sheet = Image.new("RGB", (1200, 1090), (16, 20, 24))
draw = ImageDraw.Draw(sheet)
draw.text((30, 16), "POSSESSED DOLL  /  MOBILE ANIMATION SET", font=font, fill=(236, 237, 232))
draw.text((30, 54), "Original upper body and shoes + reconstructed legs and skirt", font=small, fill=(162, 173, 182))
for i, (frame, title) in enumerate([(25, "POSSESSED IDLE"), (134, "STIFF WALK"), (248, "TWITCHY RUN"),
                                   (332, "HEAD SNAP"), (402, "REACHING SCARE"), (516, "JUMP SCARE")]):
    im = Image.open(frames / f"frame_{frame:04d}.png").convert("RGB")
    im = im.resize((390, 488), Image.Resampling.LANCZOS)
    x, y = 10 + (i % 3) * 400, 89 + (i // 3) * 500
    sheet.paste(im, (x, y))
    draw.rectangle((x, y, x + 390, y + 33), fill=(27, 34, 40))
    draw.text((x + 13, y + 7), title, font=small, fill=(236, 237, 232))
sheet.save(OUT / "Mobile_Animation_Pose_Sheet.jpg", quality=94)

script_dir = OUT / "SourceScripts"
script_dir.mkdir(exist_ok=True)
for name in ["build_mobile_doll_rig.py", "animate_mobile_doll.py", "validate_mobile_doll_rig.py",
             "render_mobile_doll_demo.py", "package_mobile_doll.py"]:
    shutil.copyfile(SCRIPTS / name, script_dir / name)

# Verify that the original and the previously delivered seated package stayed intact.
seated = OUT.parent / "Rigged_Seated"
old_manifest = json.loads((seated / "Package_Manifest.json").read_text())
checked = 0
for name, info in old_manifest.items():
    file = seated / name
    assert hashlib.sha256(file.read_bytes()).hexdigest() == info["sha256"], f"Seated file changed: {name}"
    checked += 1
source_hash = hashlib.sha256((OUT.parent / "possessed_doll.glb").read_bytes()).hexdigest()
assert source_hash == "c2060df6759e0ff3f84106e9ad649058f9b728108b0b7f31d5afd001e8c0bc71"
(OUT / "Preservation_Validation.json").write_text(json.dumps({"source_sha256": source_hash,
    "seated_package_files_verified": checked, "status": "PASS"}, indent=2))

files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.suffix not in [".zip", ".blend1"]
               and p.name != "Package_Manifest.json")
package_manifest = {p.relative_to(OUT).as_posix(): {"bytes": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
(OUT / "Package_Manifest.json").write_text(json.dumps(package_manifest, indent=2))
archive = OUT / "Possessed_Doll_Mobile_Package.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for file in [*files, OUT / "Package_Manifest.json"]:
        z.write(file, file.relative_to(OUT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name, info in package_manifest.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == info["sha256"]
    count = len(z.namelist())
print("MOBILE_PACKAGE_COMPLETE", json.dumps({"archive": str(archive), "bytes": archive.stat().st_size,
      "files": count, "video_seconds": TIMING["frames"] / TIMING["fps"], "preserved_seated_files": checked}))
