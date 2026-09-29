# Carnival World Expansion — Asset Audit

Updated 2026-09-29. The expansion maps and the main-world sublevel references have been authored in the active Unreal Engine 5.8.3 project. The asset inventory and map inspection are recorded here; rendered visual review and full Reference Viewer dependency review remain incomplete.

## Selected source packs

| Area | Source and format | Active project root | Selected content and intended use | Dependencies and limits |
|---|---|---|---|---|
| Docks North and East | F:\Carnival\Assets\Untitled24493581f5aeV1\data\Content\Docks\VOL2_Powell. Unreal content; 398 files, about 5.67 GB. | /Game/Docks/VOL2_Powell | One shared library serves both separately authored levels. Used assets include /Meshes/SM_Pier_Pillar_01a, /Meshes/SM_Mooring_post_NN_01h, /Meshes/SM_Boat_17a, /Meshes/SM_Boat_NN_17a, /Blueprints/BP_Lamp_01a, /Materials/Instances/MI_Wooden_Planks_Beams_01, and /Materials/Instances/MI_Sand_01a. | Source maps include Demonstration, LIGHTING_DAY, LIGHTING_NIGHT, and Overview. Layouts use selected structures and dressing rather than replacing Carnival's lighting or player setup. Runtime collision and player-height visual review are still pending. |
| Prison | F:\Carnival\Assets\HauntedPrison.zip. Unreal project archive; 481 extracted files, about 5.09 GB. The source descriptor declared UE 5.0 and the Water plugin. | /Game/HAUNTED_PRISON | Authored from the supplied L_Overview environment and selected prison assets. It is the surface junction for North Docks, East Docks, the Lab spur, and the stair to Sewers. | No external actor/object packages were listed in the extracted archive. Two oversized BasicShape Plane showcase backdrops in the authored Prison level had collision disabled while their visuals were retained; this avoids blocking the Lab route and Prison approach. No source-pack map or mesh was overwritten. |
| Research Lab | F:\Carnival\Assets\SciFiCredfa74d82e8f2V1\data\Content\SciFiWorld. Unreal content; 455 files, about 0.96 GB. | /Game/SciFiWorld | The authored Lab A/B rooms use the ResearchRoomA and ResearchRoomB room content, including source lab Blueprints such as BP_LabHoloProjector01, BP_LabFridge01_1, BP_LabCapsule01, and BP_BaseDoor where selected. | Supplied room geometry is reused. Door behavior and complete in-game collision traversal have not been verified. The route to Prison is a distinct surface spur. |
| Sewers | F:\Carnival\Assets\ModularSb35746afa6c6V1\data\Content\Sewer. Unreal content; 508 files, about 3.36 GB, plus 40 external actor and 6 external object files. | /Game/Sewer | The authored sewer corridor is based on L_Sewers_Corridor. Modular brick, concrete arch, and beam pieces provide the corridor treatment. | External actor/object files were copied with the pack. The passage to Atlantis is a separate sealed interior route. Water behavior and return traversal have not been validated in PIE. |
| Atlantis Ruins | F:\Carnival\Assets\AtlantisRuins_37Assets_2022.3.7.unitypackage. Unity package; inventory contained 758 Unity paths, including base FBX meshes and duplicate render-pipeline variants. | /Game/Atlantis_Ruins/Meshes | Selected base meshes were converted through FBX import, including SM_Arch_00, SM_Column_00, SM_Column_02, rock variants, coral/seaweed dressing, and SM_Statue_00. | Unity prefabs/materials were not migrated. Imported FBX meshes have collision according to Atlantis_Import.json. Recorded dimensions include the arch at approximately 84 x 320 x 194 cm, a column at 136 x 136 x 599 cm, and the statue at 230 x 367 x 541 cm. Materials were rebuilt/imported for Unreal; final appearance is not yet visually accepted. |
| Shipwreck | F:\Carnival\Assets\UnderwaterShip.zip. Unreal project archive; 769 extracted files, about 1.36 GB. Source descriptor declared UE 5.0 and MovieRenderPipeline. | /Game/UnderwaterShip | The authored region uses UnderwaterShip_Showcase_Exterior and its Ship, SetDressing_Interior, and SetDressing_Exterior sublevels as the terminal destination beyond Atlantis. | MovieRenderPipeline was not enabled for this project. Water/oxygen mechanics were not added. The room and hull movement modes still need player traversal review. |

## Additional assets sourced from the user's G drive

The user authorized searching and copying useful content from G:\3d assets. Selected assets are the aged industrial electrical switchboard and the Gothic painting collection:

- Source: G:\3d assets\Modular_Industrial_Electrical_Switchboard_-_Game-Ready_Puzzle_Asset-154f1b86\fbx\source_extracted\FalllEctricBox.fbx
- Project-side source copy: Saved/WorldExpansion/ExternalSource/IndustrialSwitchboard
- Imported mesh: /Game/Carnival/WorldExpansion/IndustrialSwitchboard/SM_IndustrialSwitchboard
- Dimensions: approximately 200 x 30.7 x 200 cm.
- Imported material slots: Dark_Steel_001, Red_velvet_001, Metal_Galvanized_Steel_Grime_001, Yellow_painted_damaged_metal_001, Glass_001, and Scuffed_Copper_001.
- Associated source maps: BasecColor.png, boody_glossiness.png, metalic.png, Normal.png, and RO.png.
- Intended use: a focal utility prop in Lab B.

The industrial switchboard source and import records remain inside the project. The packaged game does not read from G:\3d assets.

The Gothic painting set was selected for the old stone Prison towers:

- Source: `G:\3d assets\Medieval3c5a0a999b62V1\Gothic_Props`
- Project-side source copy: `Saved/WorldExpansion/ExternalSource/AdditionalAssets/GothicPaintings` (three framed FBXs and seven 1024x1024 painting textures).
- Imported collection: `/Game/Carnival/WorldExpansion/WallArt/GothicPaintings`
- Imported content: three framed meshes (`SM_GothicFrame_A/B/C`), seven painting textures/material instances (`A` through `G`), and frame/image materials.
- Placement: seven non-colliding framed paintings are in `L_CarnivalWorldExpansion_Prison`, arranged on solid wall panels in `BP_MainTower` and `BP_Tower`; labels run `WorldExpansion_WallArt_Prison_A` through `_G`. See `Saved/WorldExpansion/Gothic_Prison_WallArt_Placement.json`.
- The main Mansion already has 38 placed pictures; the ship interior already contains its own framed painting. The classical Gothic set remains in the Prison, where it matches the stone towers.
- Rendered placement review is still open: the current offscreen capture produced black images, so the saved transforms and wall-panel dimensions confirm placement geometry but do not confirm final in-game appearance.

## User-supplied HorrorPaint collection

The project-side asset library contains 16 HorrorPaint volumes. `HorrorPaintVol48` was checked in an isolated Unreal Engine 5.8.3 project before migration; its meshes, materials, and textures loaded without errors. Only the selected volume's framed picture/photo meshes and their dependencies were migrated. Its sample map was not brought into the active game.

- Source: `F:\Carnival\Assets\HorrorFad61952cf0604V1\data\Content\HorrorPaintVol48`
- Active project root: `/Game/HorrorPaintVol48`
- Imported: 14 picture meshes, 9 photo meshes, and their material/texture dependencies (102 `.uasset` files, about 56 MiB total).
- Placement: six portraits and five framed photos are in `/Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabB`, on three blank 700 x 350 cm room-side panels. Portraits face inward on two panels; small photos face inward on the third. Their collision is disabled. See `Saved/WorldExpansion/HorrorPaintVol48_LabB_WallArt_Placement.json` and `Saved/WorldExpansion/LabB_Wall_Transforms.json`.
- Selected images: pictures 01, 02, 05, 06, 08, and 10; photos 01 through 05. Eight other pictures and four other photos remain imported but unplaced.
- The active map save was verified from mesh bounds, target centers, and wall-face alignment. Rendered in-game appearance has not yet been reviewed. A packaged build made before this placement will not contain the updated Lab B map and needs a recook after map authoring stabilizes.

## Existing world content

Hospital content remains under /Game/Hospital_Meshingun and Slums content under /Game/IndustrialSlums. Their existing branch levels are retained. The Carnival, wetlands, coastal train bridge, mansion, hospital, and slum packs were not replaced by new demonstration maps.

## Import and verification limits

- The two dock layouts reference the same /Game/Docks/VOL2_Powell source library; no second dock content library was imported.
- Region actor-count snapshots are in Saved/WorldExpansion/Map_Content_Inspection.json. That UE 5.8 Python audit could not read the deprecated Level.actors property, so its actor counts are not a dependency report.
- Atlantis dimensions and collision are recorded in Saved/WorldExpansion/Atlantis_Import.json. Root, route, and Prison collision reports are in Saved/WorldExpansion.
- A complete Reference Viewer dependency graph and final rendered per-region captures are not available. Full-scene rendering exceeded the available memory budget during capture; vendor/source pack previews are not treated as evidence of the connected game's appearance.
- The resave, rebuild, forced recooks, and packaged startup checks are recorded in VALIDATION.md. The `PostRebuild` archive reproduced `BP_CarnivalPlayerController` `Bad import index 2818048/89`, but its cook began before the controller was resaved. A forced recook after that resave and the Lab B wall-art save completed 10,096 packages and archived to `I:\Carnival_WorldExpansion_HorrorPaint_FreshRecook_FS\Windows`. Its root `CarnivalGame.exe`, launched with `-dx12`, brought up `LV_Carnival` and ticked for over five minutes with zero bad-import, fatal, or unhandled-exception entries. This clears the serialization crash for this package startup check, but does not count as route traversal. Nine MetaHuman crowd collections still report missing `DefaultInstance` imports, the startup log has 70 invalid material ShaderMaps, and the cook has SM5 crowd shader fallbacks (`X4510`); their visual impact remains unreviewed.
