# Haunted mansion and coastal connection

Open the existing **LV_Carnival** map and press Play. Leave through the main gate and follow the **Haunted Mansion / Via Wetlands** signs. The gravel trail joins the old railroad crossing, passes through the coastal wetlands, and reaches the mansion driveway. Both new areas load with Carnival; travel does not switch maps.

The route is approximately **1,028 metres**. At the game's normal movement speed of 450 cm/s, the on-foot test took **3 minutes 50 seconds**. Holding the slower walk modifier increases that time. The gravel surface is 4.6 metres wide and the timber crossing is 2.8 metres wide. The driveway entrance is open for motorcycle access.

## Where to edit

| Item | Unreal asset |
|---|---|
| Main world | `/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival` |
| Wetlands, railroad bridge, connecting trail, signs | `/Game/Carnival/World/Levels/L_CoastalMansionApproach` |
| Mansion, interior, and nearby grounds | `/Game/Carnival/World/Levels/L_HauntedMansionConnected` |
| Generated trail and crossing meshes | `/Game/Carnival/World/Meshes` |

Use the **Levels** window in LV_Carnival to select the coastal or mansion sublevel before editing. They are Always Loaded sublevels with saved transforms. Keep their transforms together with the route when relocating either area.

The mansion centre is approximately **X -69966, Y -85850, Z 500 cm**, yaw **325 degrees**. The Carnival trail starts near **X -5727, Y -6312, Z 102 cm**. In the coastal sublevel, the new actors are grouped under **Connected Route / Surface**, **Wayfinding**, and **Vegetation**. Mansion foliage is under **Mansion / Grounds / Foliage**.

The existing mansion interior and nearby grounds were retained. Its outer demo landscape was replaced by a matching height stamp in the coastal terrain. A blocking fence panel was removed at the driveway, and a loose beam was moved to the side. The original mansion and coastal demo maps remain available separately.

## Authoring and verification

The editable Blender source is `Saved/MansionConnection/Source/Mansion_Coastal_Route.blend`; its exported FBXs are in the adjacent `FBX` folder. Route coordinates and dimensions are in `Scripts/mansion_route_config.py`.

The generation sequence is:

1. `build_mansion_route_meshes.py` in Blender.
2. `prepare_mansion_connected_level.py` in the Unreal Python commandlet.
3. `setup_mansion_coastal_connection.py` in the rendered Unreal editor.
4. `refine_mansion_route.py` in the rendered editor, to finish terrain, vegetation clearance, and driveway details.
5. `verify_mansion_connection.py`, `playtest_mansion_route.py`, and `capture_mansion_connection.py` to check saved geometry, real movement, and rendering.

The native editor helpers in `CarnivalWorldEditorLibrary` support terrain grading, height transfer, and persistent mesh instancing. They are editor-only. Regeneration replaces the generated sublevels, so preserve later manual edits before rebuilding.

Reports and previews are in `Saved/MansionConnection`. `Route_Validation.json` records floor and capsule clearance; `Route_Playtest.json` records travel with the actual player and motorcycle pawns. The playtest teleports each pawn to the route entrance once, then traverses it using movement inputs. It does not save changes to the game maps. Run Unreal validation jobs one at a time to avoid excessive memory use.

The motorcycle's ground-slope calculation was corrected so an upward floor normal keeps the bike upright. Redundant shadow casting was disabled on 32 cinematic fill lights named `forcam`; the lights still illuminate the Carnival. Copies of the affected lighting maps are in the backup folder.

## Source assets and recovery

`Assets/CoastalBridge.zip` supplied the environment. Its assets retain their `/Game/RailBridge` and `/Game/StarterContent` paths. Water, WaterExtras, Landmass, and HDRIBackdrop plugins are enabled, and the WaterBodyCollision profile is configured in the project.

`Saved/MansionConnection/Backups` contains the main Carnival map, project descriptor, and engine configuration from before this integration, plus lighting-map backups. The source maps `/Game/RailBridge/Maps/testmap` and `/Game/Mansion/Levels/LV_Haunted_Mansion` were copied into the connected sublevels and preserved.

The source coastal pack emits existing spline-construction warnings while loading in Unreal 5.8. They are recorded in the engine logs. The connection adds scenery and travel; mansion encounters and mission scripting can be placed in its connected sublevel next.

## GitHub contents

The public repository contains the authoring scripts, native helpers, documentation, and generated road meshes. Following the repository's existing exclusions for licensed packs, the imported coastal assets, copied mansion/coastal maps, doll model, and retargeted pack animations remain local. A fresh checkout requires your licensed source assets and the generation sequence above. The saved Blender file, backups, screenshots, and validation logs live in `Saved` and are also local.

At this checkpoint the on-foot traversal passed. The motorcycle traversal and final rendered previews are still being verified; they are not recorded as passing checks.
