# September 30 goal continuation

The full first-demo scope remains active and **incomplete**. The supplied scope
is preserved in `Docs/DEMO_SCOPE_20260930.md`; earlier asset/gameplay evidence
remains in `Docs/COMPLETION_PASS_20260929.md` and the existing playable checklist.
No broad acceptance item is checked merely because native foundations pass.

## Save, pause and presentation checkpoint — 06:40 UTC / 02:40 EDT

Added a three-slot native save subsystem and controller/keyboard pause menu.
Save/load persists stable missing-worker progress and story-item flags, player
transform/view, music-room door states, and authored-palette player construction.
Each slot uses two alternating generations, reload verification, and older-bank
fallback for structurally incompatible writes. Building restoration stages all
pieces before deleting current construction and rejects missing palette meshes,
blocked/unsupported placement or a saved player position inside construction.
Load preflights door pose, player floor and capsule clearance before committing.
Successful load stops motion and refreshes the recovery anchor.

The pause menu exposes resume, slot selection, save, load, investigation retry,
settings and quit. Overwrite/load/retry/quit require deliberate confirmations;
held confirm cannot accept its own newly opened confirmation. Settings returns
to pause without unpausing. Save metadata is refreshed on menu/slot changes,
not read from disk every rendered frame. Controller reconnect retains an open
pause/settings menu. Development help/travel overlays default off; building
controls appear only during building, and vehicle controls appear in context.
Building prompts now use device/remapping-aware action labels and actual grid
size, and display placement feedback.

Latest Editor and Windows game builds both PASS. Final full native suite passes
**36/36**, zero warnings/failures/not-run/in-process tests. This includes
`Carnival.Save.SlotsAndSafeRestore` and `Carnival.Input.SessionMenuNavigation`.
Save coverage includes three slots, disk round trips, camera/story/buildings,
open/closed door state, consumed-clue notification, incompatible-bank fallback,
invalid slots/stages, mid-fall/scare rejection, blocked saved player position,
and transactionally rejected unavailable building meshes. The initial 35/36
failure was a temporary-world map-root validation issue; allowing read-only
map roots (no asset writes) fixes it. Its report/log are preserved separately
under `Saved/SaveAcceptance/Initial_20260930`.

Six production-HUD pause/save/load/quit screenshots PASS capture and have all
been visually inspected at 1280×800, 800×600 and 640×480. Text and selection are
readable without clipping; the production Blueprint inherits help-overlay=false.
The DX12 render process exits 0. This accepts menu readability, not character,
lighting, physical-controller or packaged-game appearance. Evidence:
`Saved/PresentationAcceptance/SessionMenu/index.json` and adjacent PNGs/logs.

Hardware scan and user confirmation establish this PC as the reference:
i5-14600K, approximately 48 GB RAM, RTX 3060 with **12 GiB VRAM**, Windows 11 Pro.
Target is **30 FPS minimum, 60 FPS target**. `Docs/PERFORMANCE_TARGET.md` records
the evidence and initial 1920×1080 benchmark resolution assumption. WMI's GPU
memory value overflows; VRAM was verified with installed NVIDIA `nvidia-smi`.
This scan does not establish frame-rate acceptance.

## Still required

The implemented saves currently require standing on permanent safe ground in
the same loaded persistent world, with no active ride/vehicle/activity/traversal
or scare. Larger inventory/campaign content, equipment, vehicle persistence and
retry baselines, further world state, cross-map loading, packaged relaunch, and
physical controller save/load remain open. See `Docs/SAVE_SYSTEM.md` for limits.
No fresh package was cooked during this checkpoint; older packages do not have
these binaries/content changes.

Continue the entire supplied scope: crowd avoidance/world safety and queueing,
adult/child/player clothing and seat fitting, all ride/vehicle/gameplay/mission
content and travel, remaining presentation/audio, MetaHuman packaged compatibility
and a fresh full cook, populated 1080p performance against the confirmed target,
controller hardware and new-player acceptance, and complete asset/source backup.

## Guest roaming follow-up

Added a runtime Mass StateTree task that requests ordinary lane paths and
continues partial paths. The owned behavior alternates walking and a 1.5-second
pause, chooses outgoing pedestrian lanes, and reverses at disconnected ends.
The config now supplies movement, steering, lane navigation, avoidance/obstacle
grid, orientation and behavior traits. All existing 32 appearance instances,
representation settings, authored maps and the 240-guest spawner are preserved.
Owned config/behavior backups and before/after hashes are recorded in
`Saved/CrowdAcceptance/RoamingAuthoring_20260930.json`.

The full-map NullRHI PIE movement check **PASS**, engine exit 0: all **240/240**
distinct guests retain their entity index/serial, behavior instance and valid
lane across **40.269 game seconds**. Each moves **16.09–56.82 metres** along
sampled positions; **240/240** change lane. No missing entity or implausible
movement step is observed. No guest/player teleport, time dilation, density
reduction or map save is used. Raw per-second samples and per-guest results:
`Saved/CrowdAcceptance/RoamingPIE_20260930/index.json` and adjacent engine log.
All 240 have far/off representation LOD at the normal arrival viewpoint.
This establishes lane-roaming simulation at that viewpoint, not
rendered locomotion/near-view avoidance, world collisions, queueing or FPS.

Spacing inspection at arrival still finds 68 initially and 66 finally sampled
guest pairs closer than 80 cm, with minimum separations 10.36 and 12.89 cm.
Near-view steering/avoidance needs a separate real-viewpoint check; movement
success does not accept crowd spacing. The verification script now supports a
transient near-crowd observer (`CARNIVAL_CROWD_OBSERVER=near`) while keeping the
player and all guests untouched. `Docs/CROWD_ROAMING.md` describes behavior,
authoring, evidence requirements and remaining limits.

Latest Editor and Windows game builds PASS with the new runtime task. The full
native suite is **36/36 PASS**, including **one test with warnings**:
`Carnival.Rides.BalloonGroundStation` reports the imported ride parent reading
and removing index 0 of an empty `announcementsToPlay_temp` array. This warning
also appears in full-map gameplay and remains to fix. Evidence is preserved
under `Saved/CrowdAcceptance/Native_20260930`. These latest results supersede the
earlier clean 36/36 result for current source/content; no warning is hidden.

Rendered crowd review **FAIL** in
`Saved/PresentationAcceptance/PopulatedCarnivalRoaming_20260930`. The DX12 process
exits 0 and produces two valid 1280×800 PNGs, both inspected, but close guests
remain dark silhouettes under bright/glowing foliage. The live near-view pass
also repeatedly logs `Template actor type -1 is not referring to a valid type`.
The report distinguishes successful capture from failed visual acceptance. The
runner now rejects live Mass representation errors even when Unreal exits 0.
The prior populated visual review is preserved separately.

Source inspection identifies an unset `LowResTemplateActor`: the stock MetaHuman
trait requests LowResSpawnedActor at medium LOD, while owned config creation
previously assigned only HighResTemplateActor. New config creation supplies both
from the stock BP_CrowdActor class. `repair_crowd_actor_template.py` backs up and
repairs the existing owned config while checking appearance and LOD parameters
stay intact. The repair is saved, backed up and hash-verified in
`Saved/CrowdAcceptance/ActorTemplateRepair_20260930.json`.

Fresh **near-view simulation PASS**, engine exit 0, **zero Mass representation
errors** after repair. The real observation camera activates 9 high-detail
actors, 15 medium-detail actors and 216 skinned-instance representations. All
**240/240** stable guests move **10.69–56.87 metres** over **40.251 game seconds**;
**238/240** change lanes. No invalid lane, inactive behavior, lost handle or
implausible step is recorded. Evidence:
`Saved/CrowdAcceptance/RoamingNearPIE_20260930/index.json`, with full raw samples
and copied engine log. Only the transient camera moves; the ordinary player
stays at arrival. This NullRHI run verifies live representation modes and
movement, not rendered appearance or animation contacts.

Spacing is still unaccepted: the near-view first/final snapshots show 66/67
pairs closer than 80 cm, minimum separations 13.50/10.07 cm. Further lane/queue
authoring and avoidance tuning must be measured against these preserved
baselines without disguising overlaps through density cuts or test teleports.
Fresh rendered review after the actor repair, silhouette/glare corrections,
physical controller and packaged 1080p performance remain required.

## Announcement, lighting and crowd spawn continuation

The imported ride parent's announcement timer previously selected and removed
index zero when both its reusable announcement source and playback queue were
empty. The saved Blueprint now checks the refilled queue length before sound
selection. An empty queue still resets the timer and chooses the next delay.
Repeated nonempty playback/refill is preserved. `RepairEmptyAnnouncementQueue`
checks the exact parent graph and connections and is idempotent. The authoring
script backs up the imported asset and verifies compilation and before/after
hashes. `Carnival.Rides.AnnouncementQueueSafety` exercises the actual imported
parent in a real temporary world with empty/populated/refilled/exhausted queues
and later source removal. It does not claim sound audition. Both native targets
passed and the then-current suite was **37/37 clean**, with evidence in
`Saved/RideDevelopment/AnnouncementQueue/Native_20260930`. This supersedes the
earlier announcement warning; source/content warnings unrelated to it remain.

Both imported night lighting maps had a movable skylight with `AffectsWorld`
disabled. The backed-up saved repair enables that existing skylight at intensity
1 and removes global chromatic aberration. Night-snow bloom changes from .45 to
.2; the night map already used .2. Existing exposure and directional lighting
are retained. Evidence and hashes:
`Saved/PresentationAcceptance/NightLightingRepair_20260930/index.json`.
The first attempt encountered a map file lock during a live observation run;
its failure is preserved under `InitialFileLock`, and the source hash verified
unchanged. The successful retry ran after that Unreal process closed. Fresh
rendered review is required before accepting silhouettes/glare.

Moving avoidance now retains full force at path starts/ends and around standing
guests, uses the full agent radius, and raises boundary separation stiffness to
the engine's documented maximum. The strict fresh near-view run still **FAILS
spacing**: all 240 move, 236 change lanes over 40.312 game seconds, with zero
representation errors; first/final samples contain 14/22 pairs below 80 cm and
some exact coincidences. This is preserved in
`Saved/CrowdAcceptance/RoamingFullAvoidanceNearValidated_20260930/index.json`.
An earlier Python property-binding failure is preserved separately and is not
counted as acceptance. The verifier now measures every sampled frame's spacing,
actual agent radii, avoidance-grid membership and steering falling-behind state.

The read-only actual spawn-generator survey finds four 2000 cm long, 600 cm wide
pedestrian lanes and 240 requested guests. The stock generator's 100–300 cm
longitudinal gaps provide **39 unique positions**, which its modulo distribution
reuses to produce 240 transforms: **621 coincident pairs** at spawn. Evidence:
`Saved/CrowdAcceptance/SpawnPositionSurvey_20260930.json`. No play session or
asset save is used for that survey. The new runtime generator enumerates lane
length and width, keeps each agent radius inside the lane boundary, rejects
overlapping candidates across connected/intersecting lanes, and selects distinct
positions. It rejects insufficient capacity rather than repeating positions or
silently reducing density. Its native test covers the actual loop dimensions,
corner overlap, all 240 unique positions, insufficient capacity, narrow lanes,
non-pedestrian tags and invalid spacing. The latest Editor build and full suite
are **38/38 PASS without warnings**. The Windows game build also passes. The
saved main-map generator repair is backed up and hash-verified in
`Saved/CrowdAcceptance/DistinctSpawnRepair_20260930/index.json`, with native
evidence in its `Native` subfolder. The actual preview now supplies 240 unique
positions, zero coincident pairs and 99.99996 cm minimum separation. Lane shapes,
count, spawn scale, auto-spawn and entity config references are unchanged.
The first authoring attempt encountered Unreal's bool/out-parameter Python
binding convention before saving; its evidence remains in `InitialBindingFailure`
and the original map hash was verified unchanged. The corrected authoring run
saved successfully. The fresh DX12 run confirms 240 guests from 396 distinct
spaced candidates and the enabled night-snow skylight. Full movement and visual
verification are in progress; ongoing guest spacing,
world obstruction, appearance and performance are not yet accepted.

The completed DX12 movement run in
`Saved/CrowdAcceptance/RoamingDistinctSpawnRendered_20260930` **FAILS overall
acceptance**, engine exit 0. All **240/240** stable guests move **11.81–50.75 m**
over **40.839 game seconds**, and **238** change lanes. All sampled frames have
**zero exact coincident pairs** after the generator repair. However, first/final
frames still contain 15/17 pairs below 80 cm; minimum separation across the run
is 7.42 cm, with up to 25 close pairs. Distinct spawning repairs the measured
initial duplication but does not establish acceptable ongoing separation.
Both generated 1280×800 PNGs were inspected: faces and clothing remain dark
silhouettes. Ride geometry occupies the foreground; clear-angle near/far
review is also needed. The enabled night-snow skylight and reduced fringe are
active, but lighting/readability remains unaccepted.

That run has zero Mass representation errors and zero measured empty
announcement-queue warnings, but **161 Blueprint runtime errors** reading a
missing `MetaHuman Instance` in the stock crowd actor's BeginPlay. The copied
engine log and post-run audit preserve that failure. The runner now independently
rejects Blueprint runtime, owned spawn and MetaHuman representation errors, even
when movement checks or engine exit succeed.

Inspection confirms the stock BeginPlay goes directly to `Get Assembly Output`
before Mass's actor-identity processor assigns an appearance. The existing
`SetMetaHumanInstance` event already checks validity before assembly. A
project-owned copy, `BP_CarnivalCrowdActor`, now guards the BeginPlay read and
preserves that setter event. Both actor LOD slots reference the owned class;
new config creation requires it. The stock plugin asset's SHA-256 is identical
before/after. Config/owned-actor hashes, graph preflight, idempotency and backups
are recorded in `Saved/CrowdAcceptance/ActorBeginPlayRepair_20260930/index.json`.
The first duplicate attempt failed because plugin asset data was absent from
the commandlet registry; `InitialRegistryFailure` preserves it. Duplicating the
explicitly loaded stock object then succeeded without changing plugin content.

`Carnival.Crowd.DelayedActorAppearance` passes against the actual saved owned
actor: BeginPlay before assignment, delayed assignment of the actual `MHI_Dean`
appearance, actual face-mesh assembly, repeated assignment, null reset and
reassignment. Current Editor and Windows game builds **PASS**, and the full suite
is **39/39 PASS without warnings**. Evidence:
`Saved/CrowdAcceptance/ActorBeginPlayRepair_20260930/Native`.
The fresh populated DX12 review after this guard completes with **zero Blueprint
runtime errors, zero Mass/MetaHuman representation errors and zero owned spawn
errors**, engine exit 0. Its live census includes all **240** guests: **5 high,
17 medium and 218 skinned-instance representations**, across **110** live mesh
part components. Both 1280×800 captures are valid and inspected. Evidence:
`Saved/PresentationAcceptance/PopulatedCarnivalGuardedActors_20260930`.
Capture/runtime execution passes, but **visual acceptance FAILS**: player and
guests remain silhouettes under bright foliage. The arrival view also exposes
large reversed notice-board text behind the entrance gate. No night-time
appearance, full crowd collision, child integration or 30/60 FPS acceptance is
claimed.

GPU-only skinned instances expose counts but not CPU-readable instance
transforms; this completed review has two viewpoints, not six-group appearance
coverage. The review script now records collection groups independently of CPU
transform availability and uses real Mass entity locations for four lane
viewpoints. It refreshes a selected entity's actual location before camera
setup, without moving any guest. Fresh review with these additional views remains
required. The observed editor warmup/frame intervals include asset compilation;
they are not a packaged 1080p performance benchmark.

Four actual load warnings identified legacy RailBridge material-layer instances
saved without a shader state GUID: `ML_Buoy_Paint_01a`, `ML_Buoy_Rust_01a`,
`ML_Ballast`, and `ML_RR_Grade_Unique`. They are now backed up and resaved with
their parents and all reflected parameter arrays unchanged. A new editor-only
read helper returns the protected native GUID for diagnostics. Fresh-process
readback verifies the exact saved GUIDs and parameters for all four, with **zero
invalid-StateId warnings**. Evidence:
`Saved/PresentationAcceptance/LegacyMaterialStateRepair_20260930/index.json`,
`Reload.json`, and copied save/reload logs. Earlier Python property-binding
failures occurred before saving and remain preserved in separate subfolders.
Other asset-registry/spline warnings, lighting, full cooking and performance
remain open. Latest Editor build and Python syntax/whitespace checks pass.

## Night bounce and activity presentation — September 30 continuation

The completed transient DX12 comparison renders five lighting variants at the
unchanged arrival camera and at actual moving guest viewpoints, with all 240
entities retained. All ten 1280×800 images were inspected. Moderate lower-sky
fill (linear RGB 0.12/0.16/0.22) reveals the player, motorcycle, gate masonry,
faces and clothing while retaining the night scene. The two default cubemap
levels leave the player and guests as silhouettes. The guest views change with
the live simulation and are not identical geometry/timing comparisons.
Capture/runtime execution passes with zero Blueprint, Mass/MetaHuman
representation and owned spawn errors; **complete visual acceptance still fails**
because the brighter view exposes clothing/material defects, body intersections
and compressed guests. Evidence:
`Saved/PresentationAcceptance/NightFillComparisonValidated_20260930`.
The initial colour-binding error and its interrupted run are preserved under
`NightFillComparison_20260930`; the fixed API was preflighted before the valid run.

The moderate bounce setting is now backed up and saved in `Lv_LightingNight`
and `Lv_LightingNightSnow`. Sky source, cubemap, intensity, light colour,
exposure, bloom and other lights are preserved. Fresh-process readback confirms
both saved lower-hemisphere colours. Evidence:
`Saved/PresentationAcceptance/NightBounceRepair_20260930` (save/readback logs,
hashes and backups). A fresh populated saved-content render is in progress;
these configuration checks alone do not close night presentation acceptance.

The fresh saved-content DX12 review has now completed, engine exit 0, with
**seven inspected 1280×800 captures**: arrival, guest approach, all four lane
views and a local activity approach. The saved lower-sky colour is active; all
240 guests and all six collection groups remain present. There are **zero
Blueprint runtime, Mass/MetaHuman representation and owned spawn errors**.
The player enters the nearby stunt-rally trigger through ordinary
`Character.AddMovementInput` and sees its readable title/objective in the
production HUD. This is a short local approach, not a complete activity route
or physical input pass. Evidence:
`Saved/PresentationAcceptance/PopulatedCarnivalNightBounce_20260930`.
The report distinguishes successful captures/local prompt readability from
**failed overall visual acceptance**: grey faces, blue clothing regions,
black cutouts/body intersections, bunching and detailed appearance transitions
remain unresolved. The player is still the placeholder mannequin.

The actual text-component census corrects an earlier visual inference: the
large reversed entrance text comes from activity start labels, including
`Activity_MidwayStuntRally`, rather than the missing-worker notice board.
Native activity labels now show a short human-readable title at 14 cm, face the
local camera, and appear only within 12 m. Descriptions and weapon instructions
remain in the contextual HUD; weapon hints resolve current device/remapped
action labels. Authored identifiers, targets, timing, scoring, placement and
collision remain intact. Latest Editor build **PASS** and full native suite
**39/39 PASS without warnings** after these changes. API preflight:
`Saved/PresentationAcceptance/ActivityPresentationApi_20260930.json`.
Rendered context and ordinary movement into the stunt-rally trigger are
limited to the local pass described above; no physical input acceptance is claimed.

The full rendered load also identifies a Crewneck source-mesh LOD3 section
using an out-of-range material slot; Unreal falls back to slot 0. That mapping
must be inspected against the clothing's actual section/slot design rather than
accepting the fallback. Character assembly/materials, crowd spacing, complete
world gameplay and packaged 30 FPS minimum / 60 FPS target remain unfinished.
An offline inventory expands that diagnosis: the actual comparison load logs
**4,459 automatic LOD material-index repair events across 173 package files**,
including the six owned collection packages and clothing source variants.
Multiple embedded meshes share a collection package, so this is a package/event
count, not a count of 173 visible people or proven bad garments. Evidence:
`Saved/CharacterRepairs/ObservedClothingMaterialFallbacks_20260930.json`.
No blanket resave or material reassignment is accepted as a fix.

Read-only inspection now resolves **31 exact observed material objects**,
including runtime clothing materials after assembling four temporary actual
MetaHuman instances in an unsaved Entry world. Evidence:
`Saved/CharacterRepairs/LiveCrowdMaterialBindings_20260930/index.json` and its
copied engine log. The first unresolved runtime-path lookup and subsequent
dynamic-material binding error are preserved separately; the corrected run
completes with no errors and changes no saved assets.
Dean's observed face LOD4/LOD5–7 materials inherit the owned sampler-repair
master and resolve `Basecolor Baked` to the grey placeholder texture. This is
a concrete lead for the grey faces, but active switches, actual baked texture
bindings and rendering still need inspection before a repair. The long-sleeve
shirt's blue region matches its authored `diffuse_color_2` tint
(0.038204/0.258183/1.0), so blue alone is not evidence of a missing shader or
normal texture in the colour input. Preserve intended clothing choices while
resolving material/section and body-intersection failures.

### Stock skin-bake diagnosis and isolated rendered proof

The saved collection survey inventories 149 face/body skin instances and 191
embedded textures across all six owned collections. No embedded baked texture
is present. The face instances have `Use Baked Material=false`; therefore the
grey `Basecolor Baked` default alone did not prove which shader branch caused
the visible failure. The active original-texture inputs are placeholders too.
Evidence: `Saved/CharacterRepairs/CrowdFaceBakeSurvey_20260930/index.json`.

A read-only source survey resolves four original characters from collection
one's eight head/body wardrobe references. Those wardrobe items use the
collection's fallback pipeline rather than an item-local pipeline. Generating
a temporary Dean face with the character editor yields actual `Basecolor`,
`Normal` and `Cavity` textures, which the crowd shader's different original/
baked parameter names do not receive. No source character or collection was
saved during diagnosis. Evidence: `CrowdSourceMaterialSurvey_20260930` and
`GeneratedSourceFaceSurvey_20260930` under `Saved/CharacterRepairs`.

The new editor-only `CarnivalCrowdMaterialEditorLibrary` generates a temporary
source face and runs copies of Unreal's stock `TGI_Skin_Head` and
`TGI_Skin_sRGB` bake graphs into a constrained, project-owned proof folder.
It exports unsaved textures; it never edits the stock graphs or engine content.
The four 512-pixel outputs contain detailed base colour, normal, SRMF and
scatter data, with the stock colour-space/compression settings. PNG evidence:
`Saved/CharacterRepairs/DeanSkinBakeProof_20260930`.

Six actual PIE captures compare Dean's crowd actor face before and after the
baked inputs at two fixed camera positions, plus source-reference views.
The baked candidate restores skin colour, visible facial detail, eyes and mouth
where the original is flat grey/white. This **passes the isolated skin-binding
proof**; it does not accept the full character, instanced GPU crowd, every LOD,
hair/body fit, animation, populated-world lighting or packaged performance.
The source actor was rotated 180 degrees in this completed run, so compare
each crowd baseline/candidate at the common camera, and do not claim identical
source/crowd lighting angles. The future script aligns their orientation.
Evidence: `Saved/CharacterRepairs/DeanSkinRenderedProof_20260930/index.json`
and its six PNGs. The final process exits 0, with no material, Blueprint,
Mass representation, MetaHuman representation or Python runtime errors.

Earlier preview binding/visibility failures are preserved separately in that
folder. One failed-preview shutdown returned 3221225477 without a diagnostic
stack in its log; subsequent complete rear and six-view runs exit cleanly.
Repeated editor/package stability still requires acceptance. The installed
material-library texture setter returns false unconditionally despite applying
the value, so the corrected script validates texture and static-switch readback.
Source/runtime dynamic material instances require the appropriate getters and
a constant parent when constructing a temporary constant proof instance.

The editor helper builds successfully. Fresh native regression remains
**39/39 passed, zero warnings/failures/skips**, copied alongside the proof under
`Native`. The four validated texture outputs are now saved separately, with
SHA-256 evidence proving the Dean source and collection-one package unchanged.
A fresh process reloads all four textures with the expected colour space and
compression and exports PNGs byte-identical to the pre-save source exports.
Evidence: `Saved/CharacterRepairs/DeanSkinSavedProof_20260930/index.json`,
`Reload.json`, `Save_engine.log` and `Reload_engine.log`. These saved proof
outputs were not bound at that checkpoint. Binding, all other source heads,
instanced/LOD acceptance and whole-population visuals remain required.
The full demo goal remains active, with packaged 30 FPS minimum / 60 FPS target
and the remaining scope in the attached checklist still required.
The game target is also checked successfully (up to date); its console evidence
is copied under the rendered proof's `Native` folder. No Unreal process remains
open after these authoring, rendering, reload and regression checks.

### Dean integration and live representation check

Dean's four reviewed bake textures are now bound to the eight matching face
and face-combination material instances in owned collection one. Before saving,
the original collection package was copied and SHA-256 verified under
`Saved/CharacterRepairs/DeanCrowdSkinBinding_20260930/Backups`. All 104 embedded
material instances retained their effective parents and parameters outside the
four intended textures and `Use Baked Material` switches. Fingerprints of 256
loaded skeletal meshes retained geometry, reference poses, skin weights and
material mappings before/after saving and in a fresh reload. This fingerprints
runtime-normalized loaded state; it does not establish that the original invalid
clothing slot design was correct. The raw package backup remains available.
Save and fresh-reload evidence is in that folder's `index.json` and `Reload.json`.

`DeanCrowdLiveAcceptance_20260930` tracks the same actual moving Dean identity
through high-resolution actor, skinned instance, skinned instance and actor
representations with all 240 guests retained. Runtime face bindings use the
saved textures and baked switch throughout; the process exits cleanly with no
Blueprint/Mass/MetaHuman representation errors. The near view visibly restores
Dean's skin colour. **Overall visual review fails:** foliage obstructs medium
and far views, and the return-near frame is crowded. The report distinguishes
successful capture/state checks from rejected visual acceptance. GPU appearance
at distance, other heads, full clothing/body/pose, crowd spacing and packaged
performance remain open. An elevated multi-angle follow-camera retry is prepared;
it does not change guest placement, density, simulation or LOD budgets.

The stock bake process now covers the remaining 14 unique original heads:
**56 newly saved textures**, all fresh-reloaded with matching compression/colour
space and PNG source pixels identical to their pre-save exports. All fourteen
original character package hashes remain unchanged. Separate process runs bound
character-editor memory and preserve per-head save/reload logs under
`CrowdHeadSkinBakes_20260930`; `VerifiedSummary.json` rechecks every saved hash.
All fourteen four-map panels are inspected and show detailed distinct skin data.
These texture checks still require actual actor visual review and scoped binding
before full-population acceptance. Fresh native regressions remain **39/39
passed, zero warnings/failures/skips**, copied under that folder's `Native`.

The fourteen additional heads now pass **isolated near-actor skin binding**:
baseline/candidate and opposite-side comparisons visibly restore skin colour
and detail while retaining facial shape and eyes. The first 56-frame roster run
shows twelve heads correctly but has empty frames for Skotukeda4/base female;
its overall review remains failed and is preserved. A fresh eight-frame focused
run anchored to actual head bones shows both remaining heads correctly. This
does not establish the cause of the initial empty frames or accept repeat-run
population stability. Both processes exit 0 with zero Blueprint/Mass/MetaHuman
representation errors. Individual accepted cases are aggregated under
`CrowdHeadSkinCandidatesAcceptance_20260930`; original runs are in
`CrowdHeadSkinCandidates_20260930` and
`CrowdHeadSkinCandidatesTwoHeadDiagnosis_20260930`. Body/grooms were hidden and
near LOD forced for these focused comparisons; GPU/full-body/other LOD and live
population visuals remain open.

All six owned crowd collections now bind the correct saved stock textures to
**132 head material instances** (actor and instanced/composite variants, including
Dean). Each package has a verified pre-edit raw backup, scoped effective material
comparison, save and separate fresh-process reload. Across the six collections,
**586 loaded skeletal mesh fingerprints** and **400 material instance states**
remain consistent outside the four intended head textures and baked switches.
Backups and current saved-package SHA-256 hashes are rechecked after the batch.
Evidence: `Saved/CharacterRepairs/CrowdHeadSkinBindings_20260930`, per-group
`index.json`/`Reload.json`/logs and `VerifiedSummary.json`. The prior raw invalid
clothing mappings may be normalized by post-load/save; this check preserves
loaded runtime structure and does not accept the intended original slot design.
The game target check succeeds (up to date). Full-population actor/GPU/LOD skin
rendering, complete characters and packaged performance still require acceptance.
Fresh post-binding native regressions also pass **39/39, zero warnings/failures/
skips**, with automation and game-build evidence copied under the binding
folder's `Native` directory.

`DeanCrowdLiveClearance_20260930` retains all 240 moving guests and all 32
appearances for 18 elevated near/medium/far/return captures. The tracked entity
switches actor → skinned instance → actor, with saved Dean bake bindings intact.
Medium270 and Far135 visibly show restored skin on instanced Dean guests; near
and return frames also show coloured faces throughout the visible population.
These are zoomed review cameras, which affect screen-size mesh LOD selection;
they do not verify every actual drawn LOD or every head in normal player views.
Many angles remain obstructed and clothing cutouts, body/pose failures, crowd
bunching and excessive foliage lighting still fail overall appearance.

The capture produces zero Blueprint/Mass/MetaHuman representation/owned spawn
errors, but exits **3221225477 (0xC0000005)** after normal teardown/log closure.
CrashReportClient records the abnormal death without a new project crash dump
or diagnostic stack. Overall appearance and stability acceptance remain failed.
All captures, state/binding evidence, engine and console logs are preserved in
that folder. A script cleanup now releases transient PIE actor wrappers before
end-play; its relation to the late access violation is unproven and a fresh
reproduction is required. Do not infer packaged stability or FPS from these
editor captures. The complete demo goal remains active.

The first cleanup repeat, `DeanCrowdLiveCleanupRepeat_20260930`, aborts after
13 views: a pooled actor in the camera's two-second cached trace-ignore list is
destroyed during representation changes, and its Python wrapper cannot be
converted for a native trace. The process exits 0 after the script failure;
this is not a completed teardown reproduction. The script now builds a fresh
ignore list for every trace. Original failure evidence remains preserved.

A read-only saved animation-input survey finds Manny `MM_Idle` and
`MM_Walk_InPlace` directly configured as crowd body bake inputs (7.567/2.733
seconds, looping, root motion disabled), with no face or merged sequences.
Their skeleton is `SK_Mannequin`. Installed crowd bake configuration describes
direct bone-track sampling, so source/target bone-basis and retarget compatibility
need checking as a pose-defect lead; these metadata observations do not prove
the rendered poses or their cause. The config hash remains unchanged. Evidence:
`Saved/CharacterRepairs/CrowdAnimationInputSurvey_20260930/index.json` and logs.

The corrected full `DeanCrowdLiveFreshTrace_20260930` repeat completes all 18
views and exits **0**, with all 240 moving guests/32 appearances and zero
Blueprint/Mass/MetaHuman representation/owned spawn errors. Medium270/315 show
coloured skin on instanced Dean guests, and near/return frames show coloured
faces in the population. All captures are inspected. Overall visual review
remains **failed** on clothing cutouts, body/pose defects, bunching, foliage
lighting and obstructed far views; all heads/actual drawn LODs and normal-player
views remain open. The original late access violation and partial repeat remain
preserved. This successful repeat does not establish their cause, extended or
packaged stability, or the 30 FPS minimum / 60 FPS target. Reports distinguish
capture/exit success from rejected full appearance acceptance. No Unreal editor
process remains open after the completed checks. The full demo goal stays active.

Further isolated Dean diagnostics distinguish intact shirt geometry from missing
assembled body surfaces. The original body has complete hands; exposing it
untrimmed is rejected for skin intersections. A transient copy trimmed with the
three selected garments' original coverage maps restores hands in reference and
sampled idle/walking views. It is not a saved or integrated surface fix. Native
section/slot diagnostics and exported geometry-removal proof helpers build, the
game target check succeeds, and 39 native regressions pass with zero warnings.
Six collection and recorded source hashes remain unchanged. Groups 1–5 mix full
outfits and separate pieces; cross-slot body ownership is a diagnosis lead, not
an established cause. Unlit one-/two-sided silhouettes show the dark idle sleeve
surface exists. The one-sided probe again exits 0xC0000005 after successful
capture and normal log closure; stability remains failed. Details and evidence:
[crowd body surface diagnosis](CROWD_BODY_SURFACE_DIAGNOSIS.md).

The one-sided cleanup repeat completes both views and exits 0 after releasing
all retained PIE wrappers before end play. No cause is established for the prior
native failures; extended/package stability remains open. The body diagnosis
aggregate preserves 46 reviewed images from 10 runs, including the failed exit.
All probes are transient and collection/source package hashes are unchanged.

The later isolated rebuild reproduces Dean's ownership cause: unselected
complete-outfit items receive his hand vertices when mixed with separate
garments. Parts-only construction restores hands in fixed idle/walk views.
The first saved G1 Parts candidate preserves six original appearances' selected
keys and authored parameter overrides, binds all 32 generated head materials
to the reviewed head bakes, and reloads successfully. Its inspected source
256 meshes, 104 materials and scoped package hashes remain unchanged. Twelve
baked-idle gallery images show complete hands on all six, with male head framing,
hair presentation and dark sleeves still unaccepted. The live config is unchanged.

The Parts proof idle again exits 0xC0000005 after capture and normal teardown.
A local Windows SDK observer now captures unhandled native stacks/minidumps;
an intentional crash fixture validates it. Two later candidate renderer runs
exit 0 with it attached, but no real engine crash was captured or resolved.
Editor/game checks and 39 native regressions pass with zero warnings/failures/skips.
Twenty-two new reviewed images, source roster, candidate/reload records and
limits are in [the clothing family record](CROWD_CLOTHING_FAMILIES.md).
Remaining families, all LOD/GPU/animation review, integration, cook/package,
stability, 30/60 FPS and the complete demo scope remain open.

### Animation-space diagnosis and candidate conversion

Sixty-four additional studio captures compare original/candidate clothing,
direct source animation, shadow isolation, reference-pose experiments and
sampled animation conversion. Hands remain complete in the parts candidate.
Copying translation policies does not fix the tall baked pose. A named source
reference improves stature but leaves corrective-bone differences. Sampled
conversion restores the compared idle/walk proportions. The dark idle patch
is isolated to the shirt's shadow casting; high fill lighting is rejected as
a fix. No shirt material or shadow setting is saved by these probes.

Complete-clip checks retain the failed raw-source comparisons, including
weighted corrective-bone differences. The installed engine remaps unanimated
mesh-reference bones during compatible-skeleton source playback. The explicit
neutral reference restores only bones without a compressed source track to
their mesh reference; animated source bones stay evaluated. All eight
body/shirt/jeans/shoes comparisons then pass at 65 times per clip, with maxima
0.016004 cm and 0.048716 degrees against 0.1 cm / 0.1 degree limits. This is
native pose evidence, not rendered GPU or full character acceptance.

The fresh G1 Parts retargeted candidate saves seven packages for six appearances,
preserving authored selections/overrides, 32 reviewed head material bindings,
256 source mesh states, 104 source material states and scoped source hashes.
Fresh reload passes all 96 shared/selected-head animation comparisons with the
same maxima and limits, plus the saved geometry/material/selection checks.
Both instrumented editor runs exit 0. Twenty-four new idle/walk gallery views
are manually inspected: all six appearances retain complete hands and corrected
proportions, with complete head/feet framing. Dark idle sleeves and noisy hair
remain unaccepted. Both instrumented renderers exit 0 and checked source and
candidate hashes stay unchanged. Fixed-time actor LOD 0 views do not accept
live GPU animation, all LODs, continuous fit, world lighting or performance.
Existing assets and the live crowd configuration are preserved. Details and
report paths: [clothing family record](CROWD_CLOTHING_FAMILIES.md).

Playback metadata review identifies and repairs six missing shared-walk sync
markers. The sampler now preserves them and playback rate, while explicitly
rejecting notify-bearing inputs until event copying is supported. Both the
saved input and shared walk clip receive the original marker names/times,
with a package backup and unchanged source hashes/candidate mesh fingerprints.
Fresh reload passes all 12 metadata comparisons and repeats all 96 pose checks
at the same error maxima. The instrumented repair and reload exit 0. This does
not establish runtime event delivery, audio acceptance or live integration.

The final editor build succeeds. A fresh native regression run passes all
39 tests with zero warnings, failures or skips. This goal turn reviews 88
additional studio images. The G1 conversion is a verified saved candidate;
remaining appearance issues, other families, live crowd behavior/integration,
complete gameplay, fresh cook/package, stability and 30/60 FPS remain open.


The G1 complete-outfit retargeted candidate now saves two packages for its
original selected appearance, retaining exact selections/overrides, 32 reviewed
head material bindings and scoped source mesh/material/file fingerprints.
Fresh reload passes eight complete-clip body/outfit pose comparisons and all
12 playback metadata checks. Rendered inspection catches a separate actor
defect that those per-mesh pose checks cannot establish: an empty clothing
material-override map skips the body pose link. The project-owned actor now
links clothing at map-loop completion. Its original package is backed up and
stock plugin/Mass configuration/appearance packages remain unchanged. Fresh
actor and pooled parts/complete/clear regression coverage passes; four saved
actor idle/walk front/back captures confirm a visible head and following outfit.

Hair remains unaccepted. Transient instanced-data, actor-parent, custom-highlight
and mask-sampler changes retain the white/noisy patches and are not saved.
Original groom card materials produce fallback warnings and are rejected.
Capture-time material/parameter validation and read-only graph/atlas records
preserve these findings. No packaged frame-rate acceptance or full demo
completion is claimed. Detailed evidence: [clothing family record](CROWD_CLOTHING_FAMILIES.md).

The user's campaign direction is now authored in [CAMPAIGN_AND_INVENTORY.md](CAMPAIGN_AND_INVENTORY.md).
The native sequel has 22 stable stations spanning every required location, reserved
quest-item exchanges, eight supply stacks, limits, a persistent journal and inventory,
controller-accessible pause-menu pages and save version 2 with version-1 migration.
Editor and Development game builds pass. Forty native tests pass with no failures,
warnings or skipped tests, including sequence/order guards, capacity and overflow,
quest preservation, independent slots, legacy migration and transactional load rejection.
One initial fixture assertion was corrected; its failed log remains preserved.

A transient rendered fixture dispatches the actual character's context interaction
and verifies range, wall, story and repeat guards. Five manually inspected objective,
inventory and journal captures are readable, including the 800x600 journal record.
This does not establish production station placement, continuous world travel,
full reward/consumable effects or physical controller acceptance. Evidence:
Saved/CampaignAcceptance/SignalNetwork_20260930 and
Saved/CampaignAcceptance/SignalNetworkRenderedGuardedStory_20260930.

G2 Parts candidates now include six saved appearances. Fresh reload verifies 92
complete-clip pose comparisons and ten metadata comparisons, with maximum errors
0.0155451 cm and 0.0487164 degrees. The verifier records the engine's exact imported
material-name fill/uniqueness normalization; the first rejected reload is preserved.
Twenty-four frozen idle/walk front/back captures expose an absent crew-neck shirt
and torso/arms on Kabir. Source assembly has the same missing shirt. Source clothing
compatibility is unrestricted; the build warns that requested garment LODs 1/2 are
unavailable in a one-LOD bundle. This candidate is not visually accepted or integrated.
A fresh isolated source-LOD-0 diagnostic build is in progress; it keeps the old
candidate and all licensed sources and must pass selected-garment, reload, pose,
GPU and visual checks before any integration decision.

## Hospital stations and G2 reference pose — continuation

The first hospital approach probe rejected every node because its sight line
ended on the clue board itself. With a hit on the target counted as seen, all
three approaches pass floor, capsule and sight-line checks. The three hospital
campaign stations are placed in the hospital set-dress sublevel and pass PIE
range, story-gate, native focus, ordered dispatch, item exchange and repeat
guards. The records station focuses on the desk-top centre because the desk
pivot is occluded at knee height. The sublevel is backed up and saved, the
persistent map is unchanged, and a fresh reload verifies the actors. See
[CAMPAIGN_AND_INVENTORY.md](CAMPAIGN_AND_INVENTORY.md). The other 19 stations,
walked routes, rendered prompts and controller acceptance remain open.

The G2 LOD 0 reference-pose review shows Kabir's crew-neck penetration even
without animation, so the fault is in the garment fit at rest, not retargeting.
Details: [clothing family record](CROWD_CLOTHING_FAMILIES.md). The full demo
scope remains active and incomplete.

## Scope reduction and campaign station placement — continuation

The user removed Town, Lighthouse, Castle, Arena and Mars from the demo scope. The campaign drops their five stations (17 remain), with story text bridged and saves moved to version 3. Version-2 slots migrate onto the shorter chain, and new native regressions cover each mapping plus a full slot load. Editor and Development game builds pass, and the native suite passes 40/40 with no warnings, failures or skips.

Fourteen stations are now placed and proven in one whole-campaign PIE run through native context interaction; ten region levels were saved with backups and reload-verified (23 station actors). The prison archive and both Lab B stations remain unplaced, because their interiors are not reachable from the connection anchors by collision probe. Details and limits: [CAMPAIGN_AND_INVENTORY.md](CAMPAIGN_AND_INVENTORY.md). The full demo scope remains active and incomplete.

## World-expansion access repair and full station placement — continuation

The Prison, Lab A and Lab B sublevels had been saved pitched instead of yawed, because a positional `unreal.Rotator` argument put the yaw into pitch. Their transforms are corrected, and Lab B now joins Lab A through the authored west opening instead of overlapping it. A lab capsule blocking that opening was removed, and a matching two-step group bridges its 50 cm rise.

With these repairs, the last three campaign stations are placed: the prison archive (as a desk) and the Lab B chart and remote relay. Lab A's calibration controls moved inside the lab. All 17 stations pass one native-interaction PIE proof, and the production character walked to and from each repaired site.

Remaining defects, documented in `Docs/WorldExpansion/LAYOUT_AND_CONNECTIONS.md`:

- prison tower paintings that cannot be seen
- one spruce growing through Lab A
- other scripts with the same Rotator pattern

Details: [CAMPAIGN_AND_INVENTORY.md](CAMPAIGN_AND_INVENTORY.md). The full demo scope remains active and incomplete.

## Levels playable first — 2026-10-01

User direction: get the levels fully playable before more crowd or clothing work. Every route was re-walked with the production character, and the defects found were repaired:

- the prison rock across the spine, and the prison's 5 km ground strip
- the spine junctions at the mansion and the hospital road
- the spine's Catmull hairpin
- station props standing on routes
- the North Dock boat ramp lip

Results:

- **R01-R12:** every connection passes walking in both directions.
- **Motorcycle:** passes both ways on the mansion route, the hospital road and the 3 km outer spine.
- **Water vehicles:** both North Dock lifecycles pass.
- **Return to path:** a new pause-menu escape to the nearest verified route anchor, so a pit cannot permanently trap the player.

Native tests pass 40/40, and the Editor and Development game builds pass. Details and evidence are in `Docs/WorldExpansion/LAYOUT_AND_CONNECTIONS.md`.

Still open for "playable world":

- rooms, doors, stairs and ladders inside every region
- terrain seams, invisible barriers and floating props beyond the routes
- water boundaries and journeys between docks
- signs and landmarks, including the prison gate gap and a road that leads into it
- physical controller and cooked play

## Doors, docks, hospital floors and swimming (2026-10-01)

- **Doors:** all 65 vendor `BP_Door*` doors open and close on context interact (`UCarnivalDoorSubsystem`). The music-room door stays mission-keyed.
- **Hospital:** every floor is open. The 50 cm audit finds all 17,997 reachable cells returnable, with no traps, after doorway props were moved and the floor holes that led into closed rooms were guarded.
- **Docks:** the North Dock End Platform and all three East Dock loading fingers are linked. Every deck is reachable and returnable.
- **Swimming:** works in the river (including under the North Dock) and in flooded Atlantis and the Shipwreck. It covers surface floating, diving, walking on the bottom, climbing out at low ledges, the four retargeted swim loops and an underwater camera look.

Native tests pass 42/42, and the Editor and game builds pass. Every route still walks both ways with the water in place, including the flooded R11 and R12. Details are under "Vendor doors" and "Water and swimming" in `Docs/WorldExpansion/LAYOUT_AND_CONNECTIONS.md`.

Newly found and still open:

- the Shipwreck's vendor ship sublevels are not loaded
- the hospital double door `BP_Door_02a2` still stops the character just past its frame
- no underwater-stroke, dive or climb-out animations
