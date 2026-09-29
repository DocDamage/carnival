"""Extract the base-pipeline Atlantis FBX meshes for Unreal import.

The original Unity package is read-only. Render-pipeline duplicates, Unity
prefabs, shaders, and materials are deliberately excluded.
"""
import json
import tarfile
from pathlib import Path

ROOT = Path(r"F:\Carnival")
ARCHIVE = ROOT / "Assets/AtlantisRuins_37Assets_2022.3.7.unitypackage"
OUTPUT = ROOT / "Saved/WorldExpansion/Atlantis_FBX"
REPORT = ROOT / "Saved/WorldExpansion/Atlantis_FBX_Extraction.json"
WHITELIST = {
    "SM_Arch_00.fbx", "SM_Column_00.fbx", "SM_Column_02.fbx",
    "SM_Column_Upperpart_00.fbx", "SM_Column_Upperpart_01.fbx",
    "SM_Column_Lowerpart_02.fbx", "SM_Rocks_Large_02.fbx",
    "SM_Rocks_Large_06.fbx", "SM_Rocks_Large_07.fbx",
    "SM_Rocks_Medium_00.fbx", "SM_Rocks_Medium_01.fbx",
    "SM_Rock_00.fbx", "SM_Rock_02.fbx", "SM_Rock_03.fbx",
    "SM_Rock_04.fbx", "SM_Statue_00.fbx", "SM_Coral_00.fbx",
    "SM_Coral_05.fbx", "SM_Seaweed_00.fbx", "SM_Seaweed_03.fbx",
    "SM_Sticks_Small_10.fbx",
}


def main():
    paths = {}
    with tarfile.open(ARCHIVE, "r:*") as package:
        for member in package:
            if member.name.endswith("/pathname"):
                stream = package.extractfile(member)
                if stream is None:
                    continue
                path = stream.read().decode("utf-8", "replace").strip().replace("\\", "/")
                if path.startswith("Assets/Atlantis_Ruins/Meshes/") and Path(path).name in WHITELIST:
                    paths[Path(path).name] = member.name.rsplit("/", 1)[0]
        missing = sorted(WHITELIST - set(paths))
        if missing:
            raise RuntimeError("Missing base Atlantis FBX sources: " + ", ".join(missing))
        OUTPUT.mkdir(parents=True, exist_ok=True)
        extracted = []
        for name, guid in sorted(paths.items()):
            member = package.extractfile(guid + "/asset")
            if member is None:
                raise RuntimeError("Missing payload for " + name)
            target = OUTPUT / name
            with target.open("wb") as output:
                output.write(member.read())
            extracted.append({"name": name, "guid": guid, "bytes": target.stat().st_size})
    result = {"source": str(ARCHIVE), "destination": str(OUTPUT), "count": len(extracted),
              "files": extracted, "excluded": ["BuiltIn/URP duplicates", "Unity prefabs/materials/shaders"]}
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
