# Carnival World Expansion — Implementation Status

Updated 2026-09-29. Active project: F:\Carnival\CarnivalGame.uproject. Engine: Unreal Engine 5.8.3. Main gameplay map: /Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival.

## Authored region status

| Requested region | Saved content | Status |
|---|---|---|
| Docks North | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksNorth_Layout | Authored with its own compact layout; uses the same /Game/Docks/VOL2_Powell library as Docks East. |
| Prison | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Prison | Authored as the main surface junction. Two blocking showcase-plane collisions were disabled in this authored copy. Seven Gothic framed paintings now dress solid panels in the two tower assemblies. |
| Research Lab | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_LabA and L_CarnivalWorldExpansion_LabB | Two supplied room assemblies authored as a side branch; their door opening alignment is recorded. Lab B now has six portraits and five framed archival photos on three blank wall panels. |
| Docks East | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_DocksEast | Authored as a longer, ordered quay; shares the North Docks source library. |
| Sewers | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Sewers | Authored with the Prison descent and Atlantis passage. |
| Atlantis Ruins | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Atlantis | Authored from selected FBX architecture and dressing; imported collision is present. |
| Shipwreck | /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Shipwreck | Authored from the supplied exterior, ship, and set-dressing levels as the terminal region. |

The persistent Carnival map references nine new Always Loaded levels: the seven named regions, a second Lab room, and the generated connection level. The one linked connector map is /Game/Carnival/World/Levels/L_CarnivalWorldExpansion_Connections_Layout. A stale partial map named L_CarnivalWorldExpansion_Connections is not linked.

The generated outer route uses the Mansion driveway's measured endpoint. It replaces only the prior generated OuterRoute segments in the connector level: 724 old generated segments were removed and 435 regenerated. The Prison collision repair changed only the two showcase planes in the authored Prison level; vendor source content remains unchanged.

User-authorized content from G:\3d assets was copied into project-side source staging and imported: the industrial switchboard in Lab B and the seven-image Gothic painting collection in Prison. Source and import records are listed in ASSET_AUDIT.md.

The user-supplied HorrorPaintVol48 collection was checked in UE 5.8.3, migrated with dependencies to `/Game/HorrorPaintVol48`, and used for the 11 Lab B wall-art placements. The placement report records the saved transforms, bounds, inward-facing rotations, material slots, and disabled collision. The source collection remains intact; unused art stays available in the project library.

The full controller-resave/HorrorPaint recook completed 10,096 packages and archived to `I:\Carnival_WorldExpansion_HorrorPaint_FreshRecook_FS\Windows`. Its manifest includes the Lab B map, controller, and all placed frame meshes. The root `CarnivalGame.exe` launched with `-dx12`, brought up `LV_Carnival`, and ticked for more than five minutes without `Bad import index`, fatal, or unhandled-exception entries. The earlier PostRebuild package that crashed had been cooked before the controller resave. This newer startup clears that serialization failure for the archived package, but it is not route-traversal evidence.

## Runtime completion status

All seven requested areas have saved authored content, but gameplay integration is not accepted as complete until route traversal succeeds. The current expansion route report has only one sample at the Prison start and no player movement, completion phase, or return journey. The fresh packaged main-world launch requested streaming for all nine expansion sublevels, including Prison, but that startup is not a player traversal. Therefore R03–R12 remain unverified for collision, doors, turns, streaming, and return travel.

The existing combined Carnival–wetlands–bridge–Mansion route has earlier documented on-foot and motorcycle traversal evidence in Docs/HAUNTED_MANSION_CONNECTION.md. Its R01/R02 endpoint split was not separately rerun during this expansion pass. The existing Hospital/Slums branch remains connected but has not received new PIE traversal evidence here.

The latest startup still reports missing `DefaultInstance` imports for nine MetaHuman crowd collections and 70 invalid material ShaderMaps. The cook reports SM5 crowd shader fallbacks (`X4510`), and the Shipwreck skeletal-mesh actor reports a missing root physics body. Their visual/gameplay impact is not reviewed.

The latest manifest includes all nine expansion level packages (the seven regions plus the second Lab room and connector layout), `BP_CarnivalPlayerController`, `SM_IndustrialSwitchboard`, the Gothic frame meshes and painting dependencies, and HorrorPaintVol48 frames, materials, and textures.

## Remaining work

- Repair the PIE harness startup so it records player movement, then test outer surface travel, Lab, stair descent/ascent, both tunnels, and return legs with the gameplay pawn/camera.
- Inspect per-region views and both dock layouts at player height; the previous full-scene capture exceeded the available memory budget.
- Review the Gothic Prison and HorrorPaint Lab B wall-art placements in a working in-game view; the attempted offscreen captures were black and did not validate appearance.
- Verify water separation, collision, load/return behavior, and performance in the packaged world.
- Review the packaged MetaHuman `DefaultInstance` imports, invalid material ShaderMaps, SM5 crowd shader fallbacks, and missing Shipwreck root physics body; determine their visible/gameplay impact.
- The wider first-demo queue remains active; controller remapping and physical DualSense testing from the handoff are also still open.
