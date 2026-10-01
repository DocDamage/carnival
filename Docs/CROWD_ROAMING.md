# Carnival guest roaming

The owned crowd entity config references `ST_CarnivalGuestRoaming`. Its Mass
StateTree alternates walking along the authored pedestrian lanes with a
1.5-second look-around pause. At a junction, the native task selects a valid
outgoing pedestrian lane; at a disconnected end it walks back along the lane.
Long paths continue through the engine's partial-path requests.

Unreal's Mass movement, steering, lane-boundary avoidance, guest obstacle grid,
and smooth orientation perform movement. The task requests paths; it does not
set guest transforms. Default agent radius is 40 cm, height 180 cm, desired
walking speed 140 cm/s with engine variation, maximum speed 200 cm/s. Current
appearance collections, representation distances, pedestrian routes and spawner
density are preserved. The main map's owned spawner now references the distinct
initial-position generator described below.

`Scripts/author_crowd_roaming.py` creates or updates only the owned behavior and
entity config. It backs up existing assets and records before/after SHA-256
hashes before saving. Run it through `run_editor_authoring_guarded.py` with
`CARNIVAL_EDITOR_SCRIPT=author_crowd_roaming.py` after an Editor build. Repeated
authoring finds existing trait classes rather than adding duplicates.

`Scripts/verify_crowd_roaming_pie.py` loads the complete Carnival map with the
authored spawner. It samples actual Mass entity handles, transforms, velocities,
lane positions and behavior instances once per game second over at least
40 seconds. It requires 240 distinct stable handles, valid lanes and behavior
instances, at least 200 cm of sampled movement per guest, at least one lane
transition, and no implausible movement steps. It changes no guest/player
transform, density, time dilation or map asset. Results and raw samples go to
`Saved/CrowdAcceptance/RoamingPIE_20260930`, or a separate directory selected
with `CARNIVAL_CROWD_REPORT`.

This simulation test uses NullRHI. Rendering, near/far representation transitions,
animation contacts, world collision/door/queue safety, child guests, attractions,
extended play, packaged behavior and the confirmed 30/60 FPS target require
further acceptance. The presence of avoidance traits alone does not prove those
world interactions safe.

The first arrival-viewpoint run passes roaming at far/off representation LOD:
240/240 stable guests move
16.09–56.82 metres and change lanes over 40.269 game seconds, engine exit 0.
Spacing remains open: offline first/final samples have 68/66 pairs closer than
80 cm. `CARNIVAL_CROWD_OBSERVER=near` moves only a transient observation camera
to a sampled live position before warmup and measurement; use a separate
`CARNIVAL_CROWD_REPORT` directory to preserve the arrival evidence. The script
also records first/final pair-spacing diagnostics without treating them as
world collision or avoidance acceptance.

The fresh near-view run also passes movement: all 240 stable guests move
10.69–56.87 metres over 40.251 game seconds; 238 change lanes. At the initial
measurement census there are 9 high-detail actors, 15 medium-detail actors and
216 skinned-instance representations. The stock medium-LOD actor reference was
missing; `repair_crowd_actor_template.py` backs up the config and assigns the
already configured BP_CrowdActor class to that slot. The repaired fresh run has
zero Mass representation errors. New config creation supplies both actor slots.
Near-view spacing remains open (66/67 first/final pairs closer than 80 cm).
Evidence: `Saved/CrowdAcceptance/RoamingNearPIE_20260930/index.json`.

Full-force path-start/end and standing-guest avoidance improves but does not
accept spacing: the strict near run retains 240 moving guests and zero
representation errors, with 14/22 first/final pairs below 80 cm, including exact
coincidences. The actual initial-generator survey identifies 39 unique slots
being reused for 240 guests (621 coincident pairs). Four existing lanes are each
2000 cm long and 600 cm wide. `UCarnivalCrowdSpawnGenerator` supplies unique
initial positions across this existing width with 100 cm candidate separation,
40 cm edge clearance, and overlap rejection at corners and across all registered
lane storage. It supplies the engine's ordinary spawn-location initializer;
it never updates a live guest transform. Insufficient capacity returns no crowd
and an explicit error rather than repeating positions or lowering the request.
The saved main-map repair previews 240 unique positions, zero coincident pairs
and a minimum separation of 99.99996 cm (floating-point rounding). Both native
builds pass and all 38 native tests pass cleanly. A fresh DX12 gameplay run
confirms 240 requested/spawned guests and 396 spaced candidates. Live movement
and rendered verification remain in progress.

`survey_crowd_spawn_positions.py` previews the reviewed synchronous generators
without spawning or saving. `repair_crowd_spawn_positions.py` backs up the main
map, replaces only the owned spawner's generator, verifies all 240 unique
positions, and checks that routes, count, scale and entity config references are
unchanged before saving. The movement verifier's optional strict spacing gate
uses `CARNIVAL_CROWD_REQUIRE_SPACING=1`; every sampled frame is recorded.
This 2D root-distance proxy is not continuous body collision or door/queue safety.

The completed `RoamingDistinctSpawnRendered_20260930` DX12 run retains all 240
stable moving guests; 238 change lane over 40.839 game seconds. Every sampled
frame has zero exact coincident roots. It nevertheless fails spacing (15/17
close pairs initially/finally, 7.42 cm minimum across the run). Both captures
still show dark silhouettes. These failures remain open.

The same run exposes stock `BP_CrowdActor` reading a missing appearance at
BeginPlay (161 Blueprint runtime errors). The saved project-owned
`BP_CarnivalCrowdActor` guards that read; the existing delayed appearance setter
still assembles geometry. Both config actor slots now use the guarded class,
with all 32 appearances and existing representation parameters retained. The
native delayed-appearance regression passes actual guest-face assembly,
repeated assignment and null/reassignment without warnings. Current builds pass;
the full suite is 39/39 clean. A fresh full-world rendered review remains
required. Plugin content is unchanged and hash-verified by the authoring script.

Fresh DX12 `PopulatedCarnivalGuardedActors_20260930` verifies zero Blueprint,
Mass/MetaHuman representation and owned spawn errors, with 5 high, 17 medium and
218 skinned-instance representations for all 240 guests. Both images still fail
appearance review (player/guest silhouettes and bright foliage). No spacing,
clothing/animation contact or FPS acceptance follows from the clean runtime log.
The capture script now uses actual Mass entity positions for lane views when
GPU-only instancing supplies no CPU-readable per-instance transforms. Its
additional lane views still need a fresh run.

Fresh `PopulatedCarnivalNightBounce_20260930` now includes all four lane views,
arrival, guest approach and a locally walked activity approach. All seven
images are inspected. All 240 guests and six collection groups remain present,
with zero Blueprint/Mass/MetaHuman representation/owned spawn errors. Saved
moderate lower-sky bounce improves night visibility, but grey faces, clothing
colour/cutout/body defects and crowd bunching still fail overall appearance.
This review does not accept crowd spacing, full locomotion/LOD transitions,
physical controller input or packaged performance. Native suite remains 39/39
clean after compact world labels and contextual HUD improvements.

An isolated stock skin-bake proof now restores colour and face detail on Dean's
actual crowd actor face in PIE. Six front/rear/source captures and four saved,
fresh-reloaded bake textures are documented in
`Saved/CharacterRepairs/DeanSkinRenderedProof_20260930` and
`DeanSkinSavedProof_20260930`. The saved source/collection package hashes remain
unchanged at that proof checkpoint. Dean's eight matching face materials have
since received those four baked textures, with a verified original-package
backup and fresh reload preserving all 256 loaded mesh fingerprints and the
104 material states outside the intended changes. Evidence is in
`Saved/CharacterRepairs/DeanCrowdSkinBinding_20260930`.
An actual moving Dean identity switches actor → skinned instance → skinned
instance → actor with baked bindings intact, all 240 guests retained and clean
runtime errors. The near image restores skin colour, but medium/far images are
obstructed; overall visual acceptance remains failed in
`DeanCrowdLiveAcceptance_20260930`. State checks do not prove visible GPU skin.
Do not mark the grey-face, whole-character or crowd presentation gates complete
until actor and GPU instanced variants, every affected head/LOD, grooms, body
fit and populated-world rendering pass. Native regressions remain 39/39 clean.

The stock head bake now covers all fifteen unique source heads. Fourteen new
heads add 56 textures with source hashes unchanged and lossless fresh reloads;
their near-actor skin bindings pass manually reviewed baseline/candidate views.
Two heads were empty in the first roster capture, then visible in a fresh focused
head-bone-camera run; preserve that earlier failure and do not infer population
stability from the repeat. Per-head acceptance is aggregated under
`CrowdHeadSkinCandidatesAcceptance_20260930`.
All six owned collections now bind 132 actor/instanced/composite head materials,
with verified raw backups and fresh reload preserving 586 loaded mesh structures
and 400 material states outside the intended textures/switches. Reports are in
`Saved/CharacterRepairs/CrowdHeadSkinBindings_20260930`. This does not accept
original clothing-slot intent, full grooms/body/poses, live GPU rendering/LODs,
crowd spacing, physical controller input or packaged FPS. Full-population review
remains required.

A read-only path-code review finds a spacing lead: `FCarnivalCrowdRoamTask`
requests the same per-entity signed `EndOfPathOffset` of up to one radius on
each path request. Installed `FMassZoneGraphShortPathFragment::RequestPath`
adds that value to the starting lateral offset, then clamps it to lane edges;
it is an incremental shift, not an absolute preferred position. Repeated
requests can therefore push guests toward the edges. This is a code-supported
hypothesis for bunching, not an accepted runtime cause. Measure per-entity
lateral offsets over repeated lane transitions before changing route behavior.

Live `DeanCrowdLiveFreshTrace_20260930` completes 18 elevated zoomed near/
instanced/far/return views, all 240 guests and 32 appearances, runtime baked
bindings and exit 0 with zero crowd/Blueprint representation errors. Clear
medium views show restored instanced skin. Overall appearance remains failed:
clothing/body/pose, bunching, foliage lighting and far obstruction are unresolved.
Earlier late exit 0xC0000005 and a partial stale-camera-ignore-wrapper failure are
preserved in `DeanCrowdLiveClearance_20260930` and
`DeanCrowdLiveCleanupRepeat_20260930`. Fresh trace actor lists fix the definite
wrapper conversion error; no cause is established for the earlier late native
exit. This single clean repeat does not accept extended/package stability or
every head and actual drawn LOD. Saved animation-input inspection also identifies
Manny idle/walk sources on SK_Mannequin; bone-basis/retarget compatibility remains
a pose-diagnosis lead, not an accepted cause.

Isolated body/clothing diagnosis now shows Dean's shirt is intact while the
assembled character loses hand surfaces. A transient body trimmed with original
garment coverage maps restores them in reference and sampled idle/walk poses;
there is no saved/runtime body repair. Direct Manny playback can pose this actor,
which does not accept Mass/GPU animation. Mixing full outfits and separate pieces
in G1–G5 is a body ownership lead. A one-sided silhouette probe repeats the late
0xC0000005 exit; clean prior runs do not accept stability. See
[body surface diagnosis](CROWD_BODY_SURFACE_DIAGNOSIS.md) for limits and evidence.

The isolated one-sided cleanup repeat captures both views and exits 0 after
releasing all PIE wrappers; the earlier native failure remains unexplained and
preserved. The complete sleeve is visible with one-sided unlit shading, so its
dark shaded patch is a separate material/shading issue in that sampled pose.

The later rebuilt Dean proof confirms complete-outfit/separate-garment ownership
competition. The first saved G1 Parts candidate keeps six appearance selections
and parameter overrides and reloads correctly; its 12 baked-idle gallery images
show complete hands on all six. Framing/pose comparison, hair presentation and
sleeve shading remain open. No live Mass config or density has changed. A Parts
idle proof repeats the late native access violation; a validated local crash
observer has not yet captured a real engine exception. The two later candidate
renders exit cleanly while instrumented, without accepting stability or FPS.
See [clothing families](CROWD_CLOTHING_FAMILIES.md) for the 22 new reviewed images,
six cloned candidates, source snapshots and remaining full-population work.
