# Carnival World Expansion — IDE / LLM Implementation Handoff

**Revision:** 1.1 — includes the requirement that both dock locations use the same asset pack.  
**Prepared:** September 28, 2026.  
**Target:** The existing Unreal Engine carnival project; project target is Unreal Engine 5.8.3 on Windows. Verify the actual local project and installed engine before editing. Do not migrate the project to a different engine version without approval.  
**Asset source:** `F:\Carnival\Assets`  
**Status of this document:** Implementation instructions, not a report of completed work. The local asset folders, package names, project files, and current level have not been inspected while preparing this handoff.

> **Primary instruction to the implementing LLM:** Expand the existing playable world using the user's existing assets. Add Docks (North), Prison, Research Lab, Docks (East), Sewers, Atlantis Ruins, and Shipwreck. Both docks must reference the same source asset pack, but have separately authored layouts. Preserve the existing carnival, wetlands, coastal train bridge, mansion grounds, and mansion interior. Follow the connection graph below. Inspect the actual assets and current world, author the new areas in Unreal, and verify traversal; do not stop at a proposal, import manifest, or placement script that has never been run.

## 1. Scope and authority

### Required additions

There are **seven separate locations using six asset categories**:

| Location | Role in the world | Required connections |
|---|---|---|
| Docks (North) | Coastal area between Mansion and Prison | Mansion; Prison |
| Prison | Major surface location and entrance to the deeper route | Docks (North); Docks (East); Research Lab; Sewers |
| Research Lab | Side destination reached from Prison | Prison |
| Docks (East) | Second coastal area between Prison and Hospital | Prison; Hospital |
| Sewers | First major deeper/interior region | Prison; Atlantis Ruins |
| Atlantis Ruins | Ancient complex beyond the sewer system | Sewers; Shipwreck |
| Shipwreck | Terminal destination beyond Atlantis Ruins | Atlantis Ruins |

**The two docks use ONE asset pack.** They are two places in the world, not two purchases, two unrelated visual styles, or two imported copies of the same content library.

The current task is environment integration and traversable layout. It does not authorize a replacement game framework, new combat systems, questlines, crowds, boat simulation, or mandatory swimming/oxygen mechanics. Reuse existing systems when the layout needs them.

### Requirement versus suggested composition

The locations, asset-source directory, shared docks pack, and world connections are requirements. The room sequences, pier shapes, landmark placement, and dressing suggestions below are proposed implementation directions. Adapt those details to the actual packs and existing terrain without changing the required connections.

Preserve the user's latest local work. The user has previously stated that the local carnival-to-mansion expansion is ahead of GitHub. Do not treat an older remote checkout as more authoritative than the current local project.

The illustrated map is a spatial reference, not a surveyed terrain plan. Its decorative kilometer scale, island boundary, building sizes, compass orientation, and painted background structures are not approved engineering dimensions or additional locations. Do not reproduce invented titles or background settlements as new requirements.

## 2. Protect the existing project

Begin by identifying the active `.uproject`, main gameplay map, player pawn, engine installation, and existing world-management approach. `F:\Carnival\Assets` is an asset-source directory; it is not proof that the project file is `F:\Carnival\Carnival.uproject`.

The existing route to preserve is:

```text
Carnival <-> Wetlands <-> Coastal Train Bridge
         <-> Mansion Grounds <-> Mansion Interior
```

The wetlands are part of the established carnival-to-bridge approach even though they were not drawn as a separate circle in the rough overview.

Before changing the level, record the current map path, relevant actor/container names, existing exits, and screenshots. Inspect source-control status or make a safe local backup using the project's established process. Do not discard uncommitted work, reset the repository, force a checkout, overwrite the current map with a pack's demonstration map, or automatically publish anything.

Keep the existing carnival rides, player setup, lighting, atmosphere, landscape, water system, mansion placement, and working transitions intact unless a narrowly scoped integration change is necessary. Document those changes. Fit the new expansion to the existing mansion-side exit rather than moving the completed world to resemble the illustration.

If the live project contains an approved route that conflicts with this handoff, report the exact conflict. Do not silently delete existing work or invent a new canonical layout.

## 3. Inspect `F:\Carnival\Assets` before placement

Treat the source directory as read-only. Inventory its subfolders and archives, then inspect relevant content rather than selecting assets from filenames alone. Do not invent pack names or assume an exterior building mesh includes playable rooms.

Identify the intended docks pack once and reuse it for both dock areas. Locate the prison, research lab, sewer, Atlantis/ancient ruins, and shipwreck content. Search sensible naming variations when necessary, but visually verify candidate content in Unreal or its supplied preview/sample scene.

Create `Docs/WorldExpansion/ASSET_AUDIT.md` with these fields for each selected pack:

| Field | Required evidence |
|---|---|
| Source | Exact local directory/archive and observed pack name |
| Format | Unreal project/content, plugin content, source meshes, textures, or other observed format |
| Existing import | Whether the content is already present in the active project; actual package root |
| Chosen assets | Exact Unreal object/package paths after verified import |
| Dependencies | Materials, textures, Blueprints, required plugins, and relevant content references |
| Geometry | Scale, pivots, modular dimensions, exterior/interior capability, collision condition |
| Reusable assemblies | Useful supplied rooms, buildings, piers, or demonstration-map sections |
| Limitations | Missing dependencies, unsupported interiors, broken collision, or compatibility problems |
| Intended use | Which location and which structural role use each asset group |

Do not generate a giant catalog of unrelated assets before making progress. Fully inspect the packs needed for this expansion and flag genuinely ambiguous selections.

### Import and dependency handling

Reuse assets already imported into the project. For assets inside another Unreal project, use an appropriate dependency-aware migration workflow rather than dragging isolated `.uasset` files between arbitrary folders. Epic's Migrate tool copies selected assets and their dependencies into the destination project's `Content` directory; review its asset report and overwrite conflicts. [UE-1]

Inspect references using Unreal's Reference Viewer or the project's existing audit tooling. The Reference Viewer exposes asset dependencies and referencers; use those results to check the imported content and the docks' shared sources. Expand any filtered/truncated dependency view before treating it as a complete audit. [UE-2]

Preserve vendor folder structures when that protects existing references. Store project-specific layouts and material variants separately. Do not move or rename an already working imported pack merely to match an example folder tree.

Extract archives into a controlled staging area when needed. Preserve the original archives and source assets. Do not enable unrelated plugins, overwrite global project settings from a sample project, or bulk-import every supplied example map into the live world.

If several plausible packs remain after inspection, ask only which candidate is intended, showing their actual names/previews. Do not substitute a purchase recommendation for inspecting the provided assets.

## 4. Exact world connection graph

### Standard outer route — single lines in the sketch

```text
Carnival
  <-> Coastal Train Bridge
  <-> Mansion
  <-> Docks (North)
  <-> Prison
  <-> Docks (East)
  <-> Hospital
  <-> Slums
  <-> Carnival
```

This is a closed outer loop. The existing wetlands and mansion approach remain embedded in their established portion of that route.

### Standard side branch — single line

```text
Prison <-> Research Lab
```

### Deeper/interior branch — double lines

```text
Prison <=> Sewers <=> Atlantis Ruins <=> Shipwreck
```

A double line means a transition farther inside or deeper into the connected environment. It is not a second surface road, two unrelated paths, or a requirement for teleportation. Express it through an interior passage, basement descent, utility tunnel, cavern, or suitable existing traversal system.

Treat the new routes as reversible for this environment pass unless the current project already has an approved restriction. Do not introduce mandatory keys, one-way drops, boss locks, or equipment requirements just to connect the environments.

### Connection register

| ID | Endpoint A | Endpoint B | Type | Work in this pass |
|---|---|---|---|---|
| R01 | Carnival | Coastal Train Bridge | Standard | Preserve existing wetlands route |
| R02 | Coastal Train Bridge | Mansion | Standard | Preserve existing approach and grounds |
| R03 | Mansion | Docks (North) | Standard | Author a continuous extension from the existing exit |
| R04 | Docks (North) | Prison | Standard | Author coastal/service approach |
| R05 | Prison | Docks (East) | Standard | Author separate east-side surface connection |
| R06 | Docks (East) | Hospital | Standard | Connect to the actual hospital or reserve its future endpoint |
| R07 | Hospital | Slums | Standard | Preserve if present; outside new-region scope otherwise |
| R08 | Slums | Carnival | Standard | Preserve if present; outside new-region scope otherwise |
| R09 | Prison | Research Lab | Standard | Author a short surface side route |
| R10 | Prison | Sewers | Deeper/interior | Author basement/service access and descent |
| R11 | Sewers | Atlantis Ruins | Deeper/interior | Author industrial-to-ancient transition |
| R12 | Atlantis Ruins | Shipwreck | Deeper/interior | Author deeper passage to the wreck environment |

The Hospital and Slums are context from the map, not newly requested asset integrations. Inspect whether they exist. Do not claim the entire outer loop is playable when they are absent. In that case, finish the East Docks approach toward the planned Hospital connection and mark that endpoint honestly as reserved/incomplete.

**Do not add unrequested world-level shortcuts:** no Docks-to-Sewers entrance, Lab-to-Atlantis passage, Lab-to-East-Docks bypass, or surface entrance from either dock directly to the Shipwreck. Local room loops and small exploration alcoves are acceptable; new connections between named regions require approval.

## 5. Overall placement rules

Keep the map's broad ordering: Mansion toward the upper-left of the overview, North Docks beyond it along the upper coast, Prison farther right, Research Lab branching to the Prison's right, and East Docks below/right of the Prison toward the Hospital. Sewers, Atlantis Ruins, and Shipwreck form the deeper branch shown toward the center.

These are relationships, not fixed world coordinates. Record actual transforms only after inspecting the current level. Preserve the existing world origin, terrain scale, and completed area placement.

The location circles represent areas, not single props. Each new region needs a recognizable arrival, an understandable internal route, an identifiable focal feature, and its required exit or return path. Do not scatter complete asset packs across empty terrain or place one building per circle with no authored approach.

Use the current player and camera to size paths, doors, stairways, and clearances. Establish connector positions and elevations before detailed dressing. Avoid arbitrary multi-kilometer spacing, extreme mesh scaling, invisible floors, inaccessible entrances, or long empty walks introduced only to match the picture.

Maintain consistent shoreline and water-height relationships between both docks. The underlying world can bend and change elevation, but piers, access ramps, roads, building foundations, and tunnel openings must meet physically. Treat the map's center as a diagram of the deeper branch, not an instruction to place underwater ruins visibly on top of the surface landscape.

## 6. Shared docks pack: implementation contract

**One shared content library; two independently authored locations.**

Both docks must reference the same imported meshes, base materials, textures, and reusable pack components. Importing an identical vendor pack into both `DocksNorth/Assets` and `DocksEast/Assets` is not acceptable.

Give the two locations separate layout ownership. Use separate region maps, containers, or parent assemblies compatible with the current project. Share small assemblies such as a pier section, bollard group, loading shelter, or warehouse module where useful.

Do not make both full dock regions instances of one shared layout asset and then edit that asset expecting only one region to change. Edits to a shared Level Instance propagate to its other instances. Independent region compositions can still reference shared modular assemblies. [UE-3]

Use this distinction to guide the result:

| Aspect | Docks (North) | Docks (East) |
|---|---|---|
| Source content | Same selected docks pack | Same selected docks pack |
| Shape | More compact, irregular waterfront | Longer, more organized quay/yard |
| Main role | Mansion-to-Prison coastal passage | Prison-to-Hospital coastal passage |
| Suggested pier pattern | Bent main pier with smaller side platforms | Longer quay with spaced finger piers or a larger loading platform |
| Dressing emphasis | Smaller grouped cargo, shelters, mooring details | More ordered storage/service spaces using the same available props |
| Wayfinding | Clear far-side route toward the Prison | Clear inland/coastal continuation toward the Hospital |
| Variation | Local composition and existing material variants | Different arrangement, lighting placement, and existing material variants |

These are composition suggestions, not requirements for missing cranes, containers, boats, or warehouses. If the pack does not contain an asset type, adapt with suitable assets that are actually available. Keep both docks visually related.

Avoid shared-master material edits that unintentionally change both locations. Prefer project-owned material instances or existing supported per-instance variation for local differences. Record intentional shared changes.

## 7. Area-by-area asset layout

### 7.1 Docks (North): coastal transition beyond the Mansion

**Position:** Between Mansion and Prison on the surface route, beyond the existing mansion grounds. Preserve the mansion's established composition and use an appropriate existing or newly authored perimeter exit.

**Suggested route:**

```text
Mansion grounds exit
  -> coastal approach
  -> small arrival/storage yard
  -> waterfront quay and pier area
  -> far-side service path
  -> Prison approach
```

Put the principal walkable quay along the shoreline. Piers extend from it into the water; any warehouses, sheds, fencing, or larger storage structures belong primarily on its landward side. Keep the main through-route distinguishable from optional dead-end platforms.

Use a compact, slightly irregular composition: one primary pier, a bend or change of frontage, and a few smaller platforms if the pack supports them. Let the arrival reveal the waterfront rather than placing the player immediately against the back of a warehouse.

Cluster ropes, crates, barrels, mooring hardware, and similar verified props around meaningful activities and edges. Preserve clear circulation. Put a recognizable pack-supported landmark near the far-side route so the Prison exit is easy to identify without a floating waypoint.

The final section should shift toward a more controlled institutional approach through fencing, road alignment, retaining walls, or existing terrain. Do not abruptly butt mansion landscaping against prison geometry with no transition space.

**Completion test:** The current player can travel from the mansion grounds through the dock area to the Prison approach and back, without teleportation, blocked collision, missing floor segments, or an accidental shortcut to the deeper branch.

### 7.2 Prison: surface junction and deeper-route entrance

**Position:** Beyond North Docks, inland from the coast sufficiently to support coherent grounds, foundations, and service access. It should read as the dominant institutional structure in this part of the world.

Arrange four distinct connection points: arrival from North Docks; surface departure toward East Docks; a side approach to the Research Lab; and an interior/basement entrance to Sewers. Make them physically distinct and understandable, not four doors opening onto the same unlabelled corner.

**Suggested structure:**

```text
North Docks approach
  -> perimeter gate / forecourt
  -> prison grounds and intake
  -> main interior circulation / cell-block area
  -> maintenance access
  -> basement / utility corridor
  -> Sewers

Prison grounds -> side service route -> Research Lab
Prison grounds -> separate coastal/service exit -> Docks (East)
```

Use the pack's strongest prison silhouette for the exterior focal building. Place walls, fencing, towers, gates, and secondary service structures around an understandable compound footprint. Put entrances where the actual interior can support them.

Keep the East Docks continuation on the surface. It can traverse the compound's outer circulation without forcing the player into the basement. Position the lab spur to read as an attached coastal/institutional service destination, not the next required stop on the outer loop.

For the deeper branch, create a deliberate sequence from occupied-scale architecture to maintenance space: public/intake area, cell/service circulation, utility stair, basement, then sewer access. Use the actual pack's rooms and modular dimensions; do not promise a complete cell-block interior from an exterior-only mesh.

Provide a readable, reversible descent. Ladders and lifts may be used only when the project already supports and verifies their traversal; otherwise use compatible stairs or ramps. Avoid creating a shaft the player can enter but cannot leave.

**Completion test:** All four required region connections are identifiable. The surface route remains separate from the deeper route, and the player can reach the sewer threshold through actual playable space.

### 7.3 Research Lab: a Prison side destination

**Position:** A short side branch to the right/east side of the Prison in the overview. Connect it by an ordinary service road, walkway, or coastal path, not a double-line deep tunnel.

**Suggested structure:**

```text
Prison side exit
  -> service approach / small exterior apron
  -> lab entrance
  -> entry or control space
  -> principal research room
  -> supporting utility / storage spaces where supported
  -> return along the Prison connection
```

Keep the facility smaller and more self-contained than the Prison. Use the pack's main laboratory building or strongest reusable assembly as its anchor. Place equipment in functional clusters rather than lining every wall with identical props.

Build a sensible transition between the exterior and interior. Put working floor space around research stations, machinery, and storage, and keep doorways clear. Use the actual asset style rather than inventing a futuristic visual language that clashes with the supplied lab.

Coastal research dressing is appropriate if supplied by the assets, but this handoff does not approve a separate seaport district, a named research organization, or a new story premise. The required area name is **Research Lab**.

Do not create a second world-level exit to Sewers, Atlantis, or East Docks. This is a branch that returns to Prison. Small internal loops are fine.

**Completion test:** The player reaches and explores the supported lab space from the Prison and returns. An exterior-only facade must not be reported as a completed playable laboratory interior.

### 7.4 Docks (East): second waterfront, same pack

**Position:** Below/right of the Prison in the overview, between Prison and Hospital on the outer route.

**Suggested route:**

```text
Prison surface exit
  -> service road / waterfront arrival
  -> organized quay and loading/storage area
  -> longer shoreline circulation
  -> Hospital-side departure
```

Use the same dock assets already imported for North Docks. Build a different silhouette and internal plan: a longer waterfront, more deliberate parallel circulation, and larger but clearly separated storage groups where the assets support them.

Place the main quay along the water and arrange piers or loading platforms outward from that frontage. Keep larger buildings landward, with a believable service lane between storage and the waterfront. Do not copy North Docks wholesale and merely rotate it.

Use a different arrangement of the same landmark assets, not a different asset pack. A supplied shed, crane, boat, or loading platform can serve a different compositional role here; none of those objects is assumed to exist before inspection.

The Prison arrival and Hospital departure must be at clearly different ends/sides of the location. Do not route the Hospital connection through a dead-end pier, a warehouse wall, or the Research Lab.

If the Hospital is not yet built, leave a named, physically coherent future connection at the edge of the finished dock route. Mark its incomplete status in the development report and use an appropriate temporary boundary rather than presenting empty terrain as a completed hospital approach.

**Completion test:** The second dock is visibly distinct at player level and in an overhead view, both regions reference the same shared source pack, and the Prison-to-Hospital-side route is coherent.

### 7.5 Sewers: industrial passage below the Prison

**Position:** The first deeper region, entered through the Prison's utility/basement route. Its endpoint leads into Atlantis Ruins, not back to a dock.

**Suggested route:**

```text
Prison basement connection
  -> utility descent / access corridor
  -> main sewer channel
  -> junction or pump chamber
  -> older or damaged section
  -> breach into ancient stone / cavern
  -> Atlantis Ruins entrance
```

Align the first modules with the actual prison outlet before building the wider network. Maintain floor heights, pipe junctions, wall thickness, and believable connections between repeated pieces.

Vary the main route with bends, one or more wider chambers, and deliberate landmark placement. Do not build an unnecessarily large maze or a single visually repetitive straight tube. Keep side branches limited and make the intended route legible through architecture, lighting, and changes in materials.

Where water channels exist, provide supported walkways, ledges, bridges, or the project's verified movement solution. Do not make decorative sewer water a mandatory swimming section by accident.

At the far end, transition gradually from modern utilities to damaged masonry, exposed rock, and ancient structures. Create a physical breach or passage linking the packs. Do not terminate one environment at an unhidden seam and begin the next several meters away.

**Completion test:** Prison-to-Atlantis travel works in both directions, with no disconnected tunnel ends, impassable grates, incorrect collision, exposed void, or unsupported traversal requirement.

### 7.6 Atlantis Ruins: a distinct ancient complex

**Position:** Beyond the Sewers on the deeper branch. Treat the center-of-map placement as a connectivity cue; this should not become an unexplained surface monument between the exterior regions.

**Suggested route:**

```text
Sewer breach
  -> ancient threshold / arrival overlook
  -> ruined courtyard or chamber
  -> principal architectural focal area
  -> deeper side of the complex
  -> passage toward Shipwreck
```

Use the strongest recognizable ancient assets as the area's organizing structure. Establish a focal plaza, chamber, temple front, or equivalent supported by the pack. Frame it with columns, walls, terraces, or ruins rather than scattering decorative fragments uniformly.

Arrange the sewer arrival to reveal the environment's scale and change in character. Put the Shipwreck connection deeper within or beyond the main complex, so the player actually traverses Atlantis before reaching the next destination.

Place rubble, broken columns, vegetation, and water details around the main architecture while retaining a readable route. Local exploration alcoves or a small returning loop can add depth without creating new world-level connections.

Preserve the drowned/ancient visual identity suggested by the map, but separate visual water treatment from playable movement requirements. The source material does not establish whether fully underwater swimming already exists. Follow the water and traversal decision in Section 8 rather than inventing it.

**Completion test:** Atlantis reads as a coherent place, has a supported entrance from Sewers and exit toward Shipwreck, and does not rely on imaginary interior space or an unimplemented swimming system.

### 7.7 Shipwreck: the endpoint beyond Atlantis

**Position:** Beyond the deeper exit from Atlantis Ruins. It is reached from Atlantis, not from either surface dock.

**Suggested route:**

```text
Atlantis deeper exit
  -> connecting cavern / submerged or enclosed passage
  -> wreck reveal and approach
  -> accessible wreck opening or exploration area
  -> terminal landmark
  -> return toward Atlantis
```

Place the wreck as the main focal object in a coherent basin, cavern, or underwater space supported by the selected assets and movement system. Avoid placing it on an arbitrary surface hillside just because its diagram bubble appears beneath Atlantis.

Orient the most suitable opening or approach toward the incoming route. Arrange the hull, bow/stern, masts, and major debris to create a readable silhouette and a believable resting position. Support visible contact with seabed, rock, or surrounding structures.

A modest grounded tilt can improve composition only when it remains compatible with collision and traversal. Do not rotate a complete vessel so severely that its usable spaces become impossible to navigate, or accidentally turn a static wreck into a physics vessel.

Inspect whether the pack provides enterable decks, a hold, or only an exterior shell. A playable approach is required. Additional interior exploration should use verified geometry; do not report a static exterior model as a completed enterable ship. If a required passage cannot be made with the available assets, record that specific gap.

Use debris and environmental detail to guide the player to the endpoint without blocking the return. This pass does not add a secret surface exit, working boat, or one-way escape sequence.

**Completion test:** The player reaches the wreck from Atlantis and returns using the supported route. Any limits on interior exploration are documented accurately.

## 8. Depth, water, and movement decisions

The intended spatial progression is:

```text
Surface world
  -> Prison interior / maintenance space
  -> Sewers
  -> Atlantis Ruins
  -> Shipwreck environment
```

Express increasing enclosure and depth without imposing arbitrary numerical elevations. Fit the geometry to the existing terrain, water system, and available modular pieces. Every change in floor level needs an actual supported connection.

Before committing Atlantis and Shipwreck elevations, inspect whether swimming/diving, underwater camera treatment, water entry/exit, and relevant collision already work in this project. Their existence in another user project is not evidence that they exist here.

If compatible swimming is already implemented, use and test it. If it is absent, do not silently invent underwater walking, oxygen meters, or a new movement framework. Continue asset inspection and nondependent environment work, then report the specific choice required: a dry/semi-flooded traversable interpretation or a separately scoped underwater-traversal implementation. Treat fully underwater gameplay as unverified until that choice and its implementation are resolved.

Do not allow the outdoor ocean surface, water collision, or global post-process effects to unintentionally pass through sealed prison basements and interior chambers. Preserve existing water behavior outside the new region. Check transitions at player-camera height, not only in an overhead editor view.

## 9. Unreal organization and authoring

Work within the project's actual level, streaming, interaction, and save conventions. Do not convert a working world to World Partition solely because this task expands the map. World Partition provides source-driven spatial streaming, but adopting or configuring it remains a project decision, not a consequence of drawing more region nodes. [UE-4]

Where appropriate, reuse Level Instances for modular assemblies. They are authoring tools, not a complete automatic streaming strategy outside a World Partition main world. Test the actual runtime loading behavior used by this project. [UE-3]

A suggested ownership structure for **new project-authored content**, adapted to existing conventions, is:

```text
WorldExpansion/
  DocksNorth/
  Prison/
  ResearchLab/
  DocksEast/
  Sewers/
  AtlantisRuins/
  Shipwreck/
  SharedAssemblies/
  SharedVariants/
```

Keep imported vendor assets at their verified shared package roots. These region folders own arrangements and project-specific additions; they are not instructions to duplicate vendor textures and meshes.

For each connection in the register, record an endpoint on both sides with its region owner, transform, facing direction, floor elevation, clearance, and current status. Use the project's existing marker/tag conventions. Do not build a generalized portal framework solely to store twelve route records.

Use the actual editor, supported editor scripting, or existing project tools to author and save `.umap`, Blueprint, and related assets. Do not fabricate Unreal binary files with plain-text writes. Generated placement scripts must be executed and their results inspected before they count as integrated content.

Keep automation repeatable: identify its own generated actors and update them without duplicating entire environments on each run. Do not delete manually authored content while cleaning up a generated region. Put local source-directory settings in editor/import tooling; the packaged game must not depend on reading `F:\Carnival\Assets` at runtime.

Reuse the project's atmosphere and lighting. Do not paste each pack's separate sun, sky, ocean, exposure, player start, and game mode into the persistent world. Scope local sound, lighting, and visual treatment to the intended region.

## 10. Implementation sequence

### Phase A — Establish the baseline and select assets

Identify the real project and map, inspect existing routes, protect local changes, and produce the focused asset audit. Verify the shared docks source and import one representative usable assembly from each necessary pack before mass placement.

**Gate:** Correct project identified; needed packs mapped to real content; existing work remains intact. Report only genuinely blocking asset or compatibility issues.

### Phase B — Fit the surface expansion

Locate the Mansion exit and establish North Docks, Prison, the lab spur, East Docks, and the Hospital-side endpoint. Use temporary blockout geometry only to test dimensions and connections, then replace it with supplied assets.

**Gate:** Surface approaches are physically coherent at player scale. Hospital/Slums availability is known and documented rather than assumed.

### Phase C — Fit the deeper branch

Anchor the prison maintenance descent, sewer route, ancient transition, Atlantis circulation, and Shipwreck connection. Resolve movement/water dependencies before claiming underwater traversal.

**Gate:** Each intended connection has a viable supported route or an explicitly documented blocker. There are no accidental surface shortcuts.

### Phase D — Author the supplied environments

Build the region layouts described above. Prioritize structure, floors, entrances, routes, and landmarks before small prop dressing. Give the two docks different compositions while keeping their shared-source contract.

**Gate:** All seven requested regions have actual saved authored content, or any incomplete region is clearly named with its exact missing dependency. A collection of imported assets alone does not pass.

### Phase E — Integrate atmosphere and runtime behavior

Connect to existing streaming, water, collision, doors, audio, and save behavior where applicable. Check repeated asset use, material consistency, local visual effects, and loading transitions. Avoid unrelated system rewrites.

**Gate:** The expansion works in the active gameplay map, not just in isolated pack demonstration scenes.

### Phase F — Verify, capture, and report

Run editor validation, actual player traversal, available build/cook checks, and regression checks. Save the final maps and capture evidence. State what passed, failed, or was not run.

**Gate:** Completion claims match observed results. Provide exact modified package/file paths and remaining work.

## 11. Acceptance and verification

| Check | Required result |
|---|---|
| Existing-world regression | Carnival, wetlands, bridge, mansion grounds/interior, player controls, and existing ride behavior remain usable |
| Region presence | Both docks, Prison, Research Lab, Sewers, Atlantis Ruins, and Shipwreck exist as authored areas, not just imported assets |
| Shared docks pack | Both dock regions reference the same verified vendor source assets; no duplicate import library created for the second location |
| Dock differentiation | Overhead and player-height views show materially different layout/composition |
| Surface traversal | Mansion–North Docks–Prison–East Docks connections work in both directions |
| Lab branch | Prison–Research Lab works and does not add an unapproved world shortcut |
| Deeper traversal | Prison–Sewers–Atlantis–Shipwreck works with supported movement, or the exact unresolved movement dependency is reported |
| Collision and scale | No missing floors, impassable intended doors, unusable stairs, severe camera clipping, or forced unsupported jumps |
| Water/depth | Appropriate camera and movement behavior; no ocean leaking into intended dry/sealed spaces |
| Streaming/loading | Required geometry and collision are present before entry; returning to a previous region still works |
| Save/return behavior | Existing persistence/checkpoint systems are not broken; test new region use when supported |
| Hospital endpoint | Connected if the Hospital exists; otherwise visibly and accurately marked as reserved/incomplete |
| Dependency health | No unresolved required materials, textures, Blueprint references, or pack dependencies after reopening the project |
| Performance | Record observed behavior on the available machine and settings; do not invent frame-rate or RTX 3060 validation claims |
| Build evidence | Record the actual editor/build/cook checks performed, with command or procedure, result, and log location |

Test routes in both directions, including turns, transitions, and return journeys after a region has unloaded/reloaded when applicable. Use the gameplay pawn and camera; an editor flythrough does not prove a walkable route.

Capture a world overview, one readable player-height view per new region, a comparison of both docks, and representative views of all three deeper transitions. Screenshots supplement traversal evidence; they do not replace it.

## 12. Required outputs from the implementing LLM

Deliver the actual saved level changes and any minimal integration code/scripts needed to use them. Also provide:

| Output | Contents |
|---|---|
| `Docs/WorldExpansion/ASSET_AUDIT.md` | Real source folders, selected assets, package paths, dependencies, and limitations |
| `Docs/WorldExpansion/LAYOUT_AND_CONNECTIONS.md` | Actual region containers, layout decisions, connection endpoints/transforms, and incomplete endpoints |
| `Docs/WorldExpansion/IMPLEMENTATION_STATUS.md` | Completed work, changes to existing content, remaining work, and blockers |
| `Docs/WorldExpansion/VALIDATION.md` | Tests performed, results, hardware/settings where relevant, logs, and capture locations |
| Project evidence directory | Captured overview, region views, docks comparison, and transition evidence |

Reuse equivalent existing project documentation instead of creating competing status files. Do not overwrite an existing development-status document wholesale; update it with the relevant verified results and link the detailed records.

The final implementation report must name the active project/map, engine version actually used, shared docks pack and package root, all seven region statuses, which routes were traversed, which checks were not run, and the exact remaining blocker or next action.

Do not say “implemented” when only instructions were written. Do not say “tested” when only a script was generated. Do not claim a complete outer loop unless Hospital and Slums connections were actually present and verified.

## 13. Handling blockers without stalling the entire task

Ask a targeted question only when local inspection cannot resolve a material ambiguity: multiple equally plausible intended packs, absent required content, an incompatible pack, or the underwater movement decision described above.

State what was inspected, the exact affected region/connection, and why it blocks that part. Continue independent work where safe. Do not respond to an asset-layout task with only a new planning document when the editor and assets are available.

Do not silently buy replacement assets, pull in unrelated marketplace content, enable a large new system, change the approved graph, or replace finished areas as a workaround.

## 14. Technical references

These references support the Unreal asset-management and authoring notes, not the proposed creative layout. Check behavior against the actual installed engine, especially its exact patch version.

**[UE-1] Epic Games — Migrating Assets:** dependency-aware migration, target `Content` folder, asset report, and overwrite handling.

```text
https://dev.epicgames.com/documentation/en-us/unreal-engine/migrating-assets-in-unreal-engine
```

**[UE-2] Epic Games — Reference Viewer:** dependency/referencer graphs, inspection controls, and asset-audit tools.

```text
https://dev.epicgames.com/documentation/en-us/unreal-engine/reference-viewer-in-unreal-engine
```

**[UE-3] Epic Games — Level Instancing:** reusable assemblies, shared edit propagation, and runtime/streaming considerations.

```text
https://dev.epicgames.com/documentation/en-us/unreal-engine/level-instancing-in-unreal-engine
```

**[UE-4] Epic Games — World Partition:** spatial streaming and integration with world-management features.

```text
https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine
```

---

**Begin with the real project and asset audit, then implement the surface connection from the existing Mansion toward North Docks and Prison. Reuse that same docks pack when building East Docks. Preserve the separate Lab spur and the Prison–Sewers–Atlantis–Shipwreck deeper branch throughout authoring.**
