"""Creates a predictable Carnival content hierarchy in the current Unreal project."""
import unreal

folders = [
    "/Game/Carnival",
    "/Game/Carnival/AI",
    "/Game/Carnival/AI/StateTrees",
    "/Game/Carnival/Animations",
    "/Game/Carnival/Animations/Rides",
    "/Game/Carnival/Blueprints",
    "/Game/Carnival/Blueprints/Guests",
    "/Game/Carnival/Blueprints/Rides",
    "/Game/Carnival/Crowd",
    "/Game/Carnival/Crowd/Collections",
    "/Game/Carnival/Crowd/Instances",
    "/Game/Carnival/Crowd/Mass",
    "/Game/Carnival/MetaHumans",
    "/Game/Carnival/Maps",
]

for path in folders:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        unreal.log(f"CarnivalKit: created {path}")

unreal.log("CarnivalKit: folder preparation complete")
