"""Extract only the selected hospital facade and audio source files."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import json

ROOT = Path(r"F:\Carnival")
OUT = ROOT / "Saved/IndustrialHospital/Source"
FACADE_OUT = OUT / "Facade_1M_6x8K"
AUDIO_OUT = OUT / "Audio"
FACADE_ARCHIVE = ROOT / "Assets/High facade of the factory with exit gates/export.zip"
AUDIO_ARCHIVE = ROOT / "Assets/Abandoned Toy Factory.zip"
FACADE_PREFIX = "FBX_1_mln_6x8K/"

def safe_extract(zf, member, destination):
    relative = PurePosixPath(member)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe archive path: {member}")
    target = destination.joinpath(*relative.parts)
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite source extract: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(member) as source, target.open("wb") as output:
        while True:
            block = source.read(1024 * 1024)
            if not block:
                break
            output.write(block)
    return target

extracted = []
with ZipFile(FACADE_ARCHIVE) as zf:
    members = [entry.filename for entry in zf.infolist()
               if not entry.is_dir() and entry.filename.startswith(FACADE_PREFIX)
               and entry.filename.lower().endswith((".fbx", ".jpg", ".jpeg"))]
    if not any(name.lower().endswith(".fbx") for name in members):
        raise FileNotFoundError("Selected 1M polygon facade FBX is missing")
    for member in members:
        extracted.append(str(safe_extract(zf, member, FACADE_OUT)))

with ZipFile(AUDIO_ARCHIVE) as zf:
    members = [entry.filename for entry in zf.infolist()
               if not entry.is_dir() and entry.filename.lower().endswith(".mp3")]
    for member in members:
        extracted.append(str(safe_extract(zf, member, AUDIO_OUT)))

report = {
    "facade_source": str(FACADE_ARCHIVE),
    "facade_variant": "FBX_1_mln_6x8K (1M polygons, six 8K UV tiles)",
    "audio_source": str(AUDIO_ARCHIVE),
    "files": extracted,
}
(OUT / "Source_Extraction.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"Extracted {len(extracted)} source files to {OUT}", flush=True)
