# September 29 completion pass

This continuation follows the user's six-part request. It does **not** establish
that the complete demo is finished. Pre-existing asset/script changes were
preserved. Purchased source assets remain local.

## Resumed goal â€” 22:26 UTC

### 05:20 UTC Git checkpoint (September 30 UTC / September 30 local)

User requested commit and push. This checkpoints the implementation and its
current acceptance limits; the complete demo goal is not achieved or marked
complete. Newly imported licensed/source asset directories and Saved reports,
backups and captures remain local under the repository's existing policy.
Source, tools, documentation and already tracked authored assets are included.

Latest populated DX12 run completes with engine exit 0 and capture success:
240 actual crowd entities, 110 nonempty instanced skin components and two
1280x800 captures (PlayerArrival and CrowdLaneApproach). Instance counts include
body/clothing/groom parts, not unique people. All six collection asset paths
are represented in the live component census. Moving only the transient
review camera into the real crowd lane activates representations normally;
the saved scene, player, entity positions, density and LOD settings are unchanged.
The near-view census has 216 Low, 18 Medium and 6 High entities. Spawning and
actual representation now have direct evidence, superseding the earlier empty
arrival-view inference. Preserve earlier failed reports and the arrival census.

Both images have been visually inspected. Crowd characters are visible but
too dark for reliable face, clothing or material review; large HUD overlays
also obscure the views. Overall visual acceptance remains FALSE. The individual
collection-camera selector returns no transforms: these Mass components use
GPU-only instance data, for which the engine's GetInstanceId returns an invalid
ID. A future selector must use live Mass appearance/entity transforms rather
than fabricate positions or depend on unavailable CPU instance buffers. No
native appearance-sampling API has been implemented yet. Roster detail, lighting,
proper frustum collection, actual roaming, seat fit, full mission/interior/audio,
fresh cook/package/performance and physical hardware acceptance remain open.

Latest Editor build passes (8.15 seconds). The prior full native suite remains
34/34 clean; this checkpoint adds only read-only editor diagnostics afterward.
Python syntax and diff whitespace checks pass. No claim of a finished demo.

### 05:09 UTC continuation (September 30 UTC / September 30 local)

Full-scene cold-compilation retry now reaches a real census: all 240 crowd
entities exist with Transform fragments. Earlier empty/premature reports remain
preserved and are superseded for spawning. Representation is still absent from
the arrival viewpoint. PopulatedCarnival_Entities240NoRepresentations_20260930
records the first real count; this is not a crowd appearance acceptance.

Read-only graph planning PASSES for 105 reachable supplied Amanda packages,
seeded by 56 observed missing-reference edges across crewneck, shorts and shoes.
The exact-copy guard verifies 105 files, including 88 new copies, with matching
SHA hashes and untouched supplied originals. AmandaLiveDependencyClosurePlan
and Copies_20260930.json record the graph and per-file evidence. A fresh full
reload after restoration has ZERO missing package-reference errors. Material
rendering, all shader/cook diagnostics and packaged appearance remain open.

Expanded native read-only diagnostics build PASSES in 8.15 seconds. An initial
link attempt failed because FViewerInfo::IsLocal is not exported; removing that
unnecessary call fixes the build. Diagnostics now sample actual transforms,
LOD/representation values and viewer information without flushing deferred
commands or mutating entity data. Actual PIE confirms NetMode=Standalone,
effective count=240, density scale=1, one enabled player-controller LOD viewer.
All 240 entities are Off LOD with no representation. Minimum viewer-distance
squared is approximately 1.47e8 cm2 (121 metres), and sampled crowd locations
are around X=5600..7400, Y=-7500..-5000, Z=114 versus the arrival viewer near
(-6858,-7892,267). The distant arrival viewpoint explains this Off-LOD result;
no spawning failure or general visibility fix is inferred. Frustum distance is
still FLT_MAX with the saved distance-only collector; full visibility/culling
and roaming behavior require later acceptance.

Preserve PopulatedCarnival_Entities240DistantViewer_20260930. The next sequential
DX12 capture is active: capture PlayerArrival, move only a transient review
camera near an actual live entity transform, warm the ordinary simulation,
then census/capture actual representations and collection groups. No player,
entity, map, spawner count, density or LOD-setting change. Owned mesh-key saves
also have ZERO repeated unstable-key warnings in the fresh reload. Compilation
still consumes substantial host memory; lightweight read commands work while
PowerShell initialization stalls. No user apps or Windows settings changed.

Python syntax and git diff whitespace checks pass. Complete six-part scope is
still active and incomplete: rendered crowd/roaming, full child/adult/player
roster/clothing/seat fitting, interiors/missions/audio, fresh full cook/package,
packaged performance and physical controller acceptance remain required.

### 04:48 UTC continuation (September 30 UTC / September 30 local)

The asset-wait populated run exits cleanly but FAILS Timeout in warm while
compiling clothing on the game thread. No live query census was reached;
absence of that census does not prove zero entities. Preserve its full report
and logs at PopulatedCarnival_AssetWaitColdCompileTimeout_20260930.

Read-only registry closure guard PASSES for 31 supplied crewneck packages.
Seventeen additional exact files restore the material-function/texture closure;
all source and destination hashes match, and licensed originals are unchanged.
The earlier 14-file restoration report is preserved separately. Final material
compilation/appearance is not yet accepted. The completed log also has 56
missing-reference edges involving crewneck meshes, shorts and running shoes;
all 56 have exact local Amanda counterparts. A separate graph-closure planner
is prepared to trace those measured references before copying further files.

Guarded backup/save PASSES for all 60 owned SkeletalMesh packages identified
by the completed log as having unstable derived-data keys. Material slots and
skeleton references remain equal after save; backups and hashes are recorded
in ObservedCrowdMeshBuildSave_20260930.json. Fresh reload must still demonstrate
reduced rebuilds, and no geometry/cloth/cook acceptance is inferred.

A fresh sequential full populated DX12 run is active with the original 240
spawner count. It allows 1200 seconds for cold compilation, requires at least
30 wall seconds and 20 actual game seconds of warmup, and records a read-only
census even on warm timeout. It has reached PIE asset wait/warm phase, while
compiling source cloth assets under low available host memory. No density,
project RHI, user application or Windows memory settings changed. The complete
six-part goal remains active; crowd, full roster/seat/interior/audio, fresh
package and physical-input acceptance remain open.

### 04:27 UTC continuation (September 30 UTC / September 30 local)

Live engine diagnostics confirm Mass simulation present/started and four built
ZoneGraph lanes. Player location is in the Carnival at approximately
(-6671,-7596,207), ruling out a distant start. RawDebugEntityCount returns -1
with two empty archetype details; that debug value is not a trustworthy active
crowd count. A read-only query now counts actual FMassCrowdTag+Transform entities.
An initial link attempt failed missing MassCore/MassCommon; explicit editor
module dependencies fix it. Fresh Editor build PASSES in 13.42 seconds. No
runtime gameplay behavior changed.

Live asset loading exposes 14 missing hard references from Amanda's supplied
crewneck material to /Game/Fab/MetaHuman/OA_Crewneckt. Exact corresponding files
exist in the pre-existing relocated Amanda source tree. Fourteen dependency
files were copied to their expected package paths with SHA equality and source
unchanged verification; conflicting pre-existing targets are refused. This is
bounded dependency restoration, not a material/crowd appearance acceptance.
AmandaClothingDependencyCopies_20260930.json records every source/target/hash;
fresh reload and any remaining transitive dependencies remain open.

Child EV3 fixed-exposure DX11 comparison PASSES capture with engine exit 0.
All four faces are framed; BlackGirl, WhiteBoy and WhiteGirl now have readable
skin and dark/brown hair in these isolated front samples. This demonstrates
the earlier bright preview lighting contributed to pale appearance. BlackBoy
still has a grey-iris appearance, some skin shine and a dark left shoulder
patch. Overall visual report remains false; full clothes/motion/seating/world
lighting and DX12 stability are not accepted. Preserve the earlier failures.

A fresh sequential populated render is active after dependency restoration
and the query-helper build. The runner now calls the actual spawner's official
WaitForStreamingAssets before starting its warmup, avoiding a premature census
while appearance assets are loading; no forced spawning or reduced crowd.
Continue until actual entity/representation failure is diagnosed and repaired,
then the remaining complete roster/seat/interior/audio/package/hardware work.
Full six-part demo goal remains active and incomplete.

### 04:17 UTC continuation (September 30 UTC / September 30 local)

Two full-scene throttled populated retries exit cleanly, but both fail their
live-instanced-representation check. The broader report confirms actual game
simulation is unpaused, time dilation 1 and game time advances (20.14 seconds
sampled after 30 seconds wall time). Saved spawner has auto_spawn=true,
count=240, scale=1 and the intended ZoneGraph generator/entity config. There
are three MassVisualizer actors, four ZoneShapes and one ZoneGraphData, but no
nonempty InstancedSkinnedMeshComponent. The only CrowdActor is separately
placed Eli in the music room, not evidence of roaming crowd. Preserve
PopulatedCarnival_BroaderRepresentationCensus_20260930 and the earlier failure.
No crowd appearance or population performance acceptance.

A read-only DescribeLiveMassSimulation editor helper now reports engine Mass
simulation start, registered built ZoneGraph lane count and raw debug entity/
archetype counts/details. Editor build PASSES (five actions, 35.19 seconds).
No gameplay behavior changed. The next sequential live populated census using
this helper is active; distinguish spawning from representation failure before
changing crowd settings or scene density.

DX11 fixed-exposure diagnostic captures all four faces with engine exit 0 and
no physics LoadErrors, but appearance still fails pale white-child skin and
BlackBoy gloss/shoulder patch. Live MID values retain authored tints, ruling
out runtime reset. This single run does not establish DX12 stability. Report:
ChildPreview/FaceCloseupsDX11FixedExposure/index.json (capture_success true,
overall success false). EV3 exposure comparison is prepared, unexecuted.

Read-only shading/texture export guard PASSES. Three supplied head diffuse
maps are flat greys (BlackGirl 216, WhiteBoy 214, WhiteGirl 221); BlackBoy head
is 166 and both iris maps contain 1024px coloured texture detail. BlackGirl top
and top_0 diffuse are solid white, so those maps do not explain shirt holes.
ShadingDetail/index.json and PNGs preserve actual pixel evidence; no texture
replacement or clothing fix is claimed. Continue geometry/mask/material and
full motion/roaming/seat work plus all remaining full-demo acceptance.

### 04:05 UTC continuation (September 30 UTC / September 30 local)

Child face/hair repair guard PASSES with owned per-file backups. WhiteBoy and
WhiteGirl authored skin tints now stay below one; all supplied HairShader
instances use reduced scatter/specular and higher roughness. Default palette
script preserves the new skin values. Four eye-position-framed closeups capture
with engine exit 0, but visual review still fails pale white-child skin and
BlackBoy glossy skin/shoulder patch. BlackGirl hair improves. Preserved evidence:
FaceCloseups_MaterialRepair_MissingPhysics_20260929. Do not claim complete child
appearance or clothing acceptance.

Fresh preview exposed a generated but unsaved BlackBoy physics dependency.
ImportTask save=true had omitted the extra physics package. Separate recovery
import using the verified FBX and existing corrected skeleton now explicitly
saves its generated physics asset and every recovery package, then assigns that
asset to the backed-up corrected working mesh. Final guard PASSES. Original
geometry/skeletons/animations remain; ragdoll/seat fitting is not accepted.
The normal candidate importer now explicitly saves/checks that dependency.
A fresh four-face capture loads it without LoadErrors and records actual runtime
MID tints/scatter matching the saved values. Its DX12 shutdown again exits
3221225477, so overall success remains false. An overly broad physics assertion
initially rejected BlackGirl's legitimate null slot; corrected to permit null
for those source meshes, while requiring BlackBoy's generated dependency.

First populated carnival render fails before PIE with a real out-of-memory
error allocating 605656 bytes; Windows reports paging file too small, with
less than 0.5 GiB physical memory available. Engine exits 3 and frees memory.
Full failure/logs preserved in PopulatedCarnival_OutOfMemory_20260930; no maps
or spawners removed. A sequential retry uses process-local single compilation
workers and a 4 GiB asset compilation budget, retaining the full scene/crowd
and normal wait-for-complete visuals. This retry has reached PIE and is active.
No crowd appearance, full roster or packaged-performance claim yet.

Runner now retains failure reports/logs even when engine exits before reporting,
and supports an explicit process-local DX11 diagnostic override without changing
project defaults. A fixed-exposure child diagnostic camera is prepared, not run;
runtime tint overrides are ruled out, but lit appearance still needs diagnosis.
Checklist front matter now points to current 34-test/ride/water/sewer/settings
evidence while keeping historical entries and all unchecked full-demo work.
Continue this populated capture, material/cloth/roaming/seat work, all remaining
interiors/missions/audio, fresh package and physical input. Goal remains active.

### 03:47 UTC continuation (September 30 UTC / September 29 local)

Settings readability PASSES: six actual production-HUD settings/remapping
screenshots at 1280x800, 800x600 and 640x480 were reviewed, engine exit 0.
SettingsReadability/index.json records visual success and limits: first remap
page, existing preferences and API-driven display only; physical input,
remapping mutations and every scrolled row remain unverified.

Owned translucent/Nanite component repair PASSES its authoring guard: 65
components across the connected mansion and hospital architecture maps now
set disallow_nanite when their materials require translucency. Both maps were
backed up; vendor meshes, materials and collision remain unchanged. Fresh
rendered glass and cooked warning acceptance remain open.

BlackBoy complete source-versus-first-FBX inspection finds faithful bind/pose
matrices, evaluated vertices and skin weights. The supplied default pose is
nonidentity: weighted twist branches and main arm bind segments disagree.
A separate consistent-bind working FBX applies that supplied pose to the rig
and every mesh Basis/morph vertex, preserving all 12 meshes, 101 bones,
weights and material slots. Full fresh FBX round trip passes: evaluated skin
error <=0.000033 m, bone error <=0.000002 m; original sources untouched.

Candidate import, six retarget clips and guest Blueprint guards pass cleanly.
All 277 UE morph target names are retained. Four candidate pose images capture
with engine exit 0; reviewed reference/idle/walk frontal samples resolve the
former shoulder collapse, but the seated-source shirt still clips/deforms.
ChildPreview/BlackBoyConsistentBind/index.json records capture_success=true
and overall success=false. This is not full-cycle gait or fitted-seat proof.

The original main BlackBoy guest Blueprint now uses that corrected body and
idle clip, with original Blueprint/manifest backed up and CDO readback passing.
Child_Rig_Overrides.json prevents default authoring/retarget scripts reverting
to the old bind. Original meshes/skeletons/clips and licensed sources remain.
Candidate assets stay in their distinct namespace. Full clothing, seating,
roaming and populated-world child acceptance remain open.

Four face closeups captured but DX12 shutdown exits 3221225477, so that run
fails. Irises/pupils are visible; WhiteBoy/WhiteGirl skin is washed out and
hair highlights remain overly bright. Their face framing also needs to use
actual posed eye position. BlackBoy retains a shoulder dark patch and skin
material review. Read-only corner-normal comparison now PASSES all 12 meshes:
maximum angular difference <=0.214 degrees, zero corners over 5 degrees.
This rules out normal bake corruption as the cause; no guessed normal repair.

LevelAudioCensus.json completes with engine exit 0: 96 components and
reachable cue-node attenuation/class wiring inspected, no census errors or
findings. Vendor manager percentages are recorded as exact raw values. No
sound was auditioned and no mix or spatial audio acceptance is claimed.
Empty ride-announcement array runtime warnings still require diagnosis.

Only the read-only child material parameter census is active at this checkpoint.
Continue actual skin/hair material diagnosis and posed face framing, then
populated crowd and moving child roster, full ride fit/casting/interiors,
audio, fresh package and physical hardware. Keep all six requested parts;
the goal remains active and the full demo is not yet complete.

### 03:05 UTC continuation (September 30 UTC / September 29 local)

Full sewer handoff now PASSES with engine exit 0. Fresh combined survey finds
59 capsule-clear candidate points with current map hashes. Production
BP_CarnivalPlayerCharacter walks from the actual lower R10 stair landing into
R11 in 17.54 seconds and continuously returns in 17.22 seconds. All 12 actual
PlayerCameraManager checks pass; no walk/return teleport or time dilation.
Saved/WorldExpansion/InteriorCameraAcceptance/SewerFullHandoff_20260929.json
and adjacent engine/console logs preserve the clean result. Earlier failed
partial traversals and self-overlap candidates remain preserved. This accepts
this normal-pawn geometry/camera round trip, not rendered sewer appearance,
complete prison mission return, populated navigation or physical input.

BlackBoy actual IKRig mesh-bind survey passes read-only with exit 0. His primary
upper-arm->forearm bind segment is nearly horizontal, while upper-arm twist
branch positions angle down; the reference skin is coherent but transferring
motion on the primary chain yields visibly different deformation. This suggests
a bind/weighted-bone alignment issue; verify source skin weights and complete
bind matrices before any production re-rig or animation replacement. Resetting
all alignment offsets reduced collapse but left incorrect spread arms; the
comparison remains diagnostic and its abnormal DX12 shutdown remains failed.
No child visual, clothing, roaming or fitted ride-seat acceptance is claimed.

No Unreal process is active at this checkpoint. Immediate next work: inspect
actual source weighting/bind transforms and repair child deformation/materials,
then settings readability, owned translucent/Nanite repair, audio, populated
crowd/roster/ride fit, remaining complete interiors/missions, fresh package and
hardware. Preserve the complete six-part scope and all original licensed assets.
The goal remains active and the demo is not yet complete.

### 02:58 UTC continuation (September 30 UTC / September 29 local)

Fresh geometry initially reports ramp self-contact. Grounding now accounts for
capsule support on slopes using R*(sec(slope)-1), and the sweep retries after
only exact tagged low ramp/floor risers, retaining separate overhead/other-actor
checks. Floor edges still require <=45 cm height change and all candidates
require actual pawn proof. With these checks, the new north doorway is reachable
and the remaining gap reduces to 425 cm. No whole-wall collision is disabled.

The measured sewer floor ends near y=-10075. R11 starts at (-27100,-9654), with
its tunnel facing west along -9.43 degrees; approaching from the south crosses
its preserved side wall. Two short owned floor pieces now bridge from
(-27300,-10100,-1850), through (-27300,-9621,-1782.5), to the R11 mouth. Width is
200 cm and slope 8.02 degrees, source tunnel walls unchanged. Backup and guard
pass. Fresh combined candidate is active; run full sewer_stair_handoff only if
route_found is true and map hashes match, otherwise diagnose remaining failures.
Do not substitute partial traversal for complete R11 acceptance.

### 02:50 UTC continuation (September 30 UTC / September 29 local)

The vent repair guard passes with collision retained. The lower-corridor actual
pawn reaches the outbound end, with six camera checks, but continuous return
fails at crossing beam StaticMeshActor_584 (SM_Sewer_Wall_Beam_01d42) near
(-26950,-12310,-1784). Preserve SewerLowerCorridor_VentRaised_20260929.json as
failed; no round-trip claim. A backed-up two-segment ramp now stays at least 5 cm
above the measured beam at its crossing, replacing the owned earlier floor and
adding its lower segment. Guard passes; actual return is still unverified.

The north survey identifies cross-wall StaticMeshActor_369 (copied Cube5) as
blocking R11. A bounded 220x320 cm doorway is saved with four retained wall
pieces, preserving material, thickness, 90-degree source axis, wall outside the
opening, and lower sill. The first axis assertion rejected before modifications;
its failed guard and backup remain. Corrected guard passes. Fresh combined
geometry survey is active; full passage, cameras and rendered review remain open.

BlackBoy comparison now saves its diagnostic clip durably. Reference-alignment
idle reduces shoulder collapse but leaves arms spread approximately 45 degrees,
so it is not accepted or applied to production. Both requested poses captured;
DX12 shutdown again exits 3221225477 and runner correctly fails the report.
An actual IKRig mesh-bind/source-idle/target-idle survey is prepared, unexecuted.
The earlier diagnostics used skeleton reference transforms, which must not be
confused with a differently proportioned skeletal mesh's bind transforms.

Continue the fresh sewer candidate and production-pawn round trip, then actual
mesh-bind diagnosis and child material/clothing fixes. Settings, audio, populated
crowd, complete interiors/roster/ride fitting, package and hardware remain open.

### 02:39 UTC continuation (September 30 UTC / September 29 local)

The corrected child preview completes 16 images with engine exit 0. Actual
pelvis/head/hands/feet positions match evaluated requested clips (maximum
allowed error 5 cm); reference poses are separately captured. CurrentAsset is
not reflected in this installed Python binary, so the earlier proposed property
check was replaced with actual pose comparison. Capture succeeds, visual review
fails: BlackBoy reference is coherent but animated shoulders/sleeves deform;
BlackGirl reference top has holes and a distorted hem; WhiteBoy/WhiteGirl skin
is too pale; eyes and full clothing fit require close review. Evidence and all
images are preserved in ChildPreview/PaletteVerifiedPoses_20260929. The current
index records capture_success=true but overall success=false. These are not
accepted seated or roaming guests. The eye-occlusion repair guard passed.

The retrying sewer sweep now exposes the real overhead vent and reduces the
reachable candidate to the lower stair before it, rather than falsely accepting
through it. One owned-copy vent is being raised 100 cm with collision preserved
and a map backup. A wrong wrapper filename was rejected before authoring; its
editor was stopped and the corrected filename-only launch is active. Wrapper
validation now occurs inside its guaranteed report/exit block. No additional
Unreal processes run concurrently. Fresh survey and actual pawn traversal must
follow the saved repair; full R11 handoff is still open.

Immediate order: finish the vent guard, inspect bind/animated child rotations
and eye/top material wiring, refresh sewer collision candidate and actual pawn
round trip. Continue settings, Nanite, audio, populated crowd, full interiors,
roster/seat fitting and a fresh package. The six-part demo remains incomplete.

### 02:18 UTC continuation (September 30 UTC / September 29 local)

The padded/analogue sewer partial retest still fails, now identifying the actual
low vent `StaticMeshActor_114` (SM_Ventilation_Set_07a), with head contact near
(-26937,-12503,-1583). The guard/survey could mask a second overhead obstacle
behind its first low stair hit. The prepared survey now retries after ignoring
only each individually validated low stair tread, retaining header/vent checks.
Do not infer passage from the earlier candidate. The source inventory records
the exact vent bounds/transform for a bounded ceiling-clearance repair if needed.
Full R11 handoff remains open with a nominal 950 cm candidate gap.

The palette succeeds across all four children. Their corrected preview remains
unexecuted after palette: it now verifies the actual active clip and includes
reference poses. A targeted BlackBoy eye-occlusion authoring guard is active:
its supplied right opacity texture is uniformly zero, but the first simple
material importer made both eye-occlusion surfaces opaque white. The repair
preserves both meshes and applies transparent zero-opacity source intent; the
paired left mapping is explicit. Eye/face visual acceptance remains required.

Immediate order: finish this guard, execute corrected coloured 16-view child
preview and inspect reference-versus-animation deformation. Refine the sewer
survey/vent clearance and real pawn round trip, then continue unexecuted settings,
Nanite, audio, populated-crowd, full interiors/roster/seating and fresh package
work. No complete demo, physical controller, or visual child acceptance claim.

### 02:12 UTC continuation (September 30 UTC / September 29 local)

The child palette now saves **64** owned material changes across all four
children, with per-file backups and before/after hashes. Guard and engine exit
are clean. The initial attempt rejected UE5.8's vector setter return value;
installed MaterialEditingLibrary.cpp confirms it always returns false even after
performing the update. The successful guard verifies stored RGBA values instead.
BlackBoy's first 16 saved changes and the original failed report are preserved.
This intentionally changes owned source material-instance files; the earlier
753-file immutable-transfer hash census is historical pre-palette acceptance,
not a current unchanged-file claim. All original archives/staged sources and
pre-palette files remain preserved. Coloured views still require acceptance.

The fresh padded sewer candidate still correctly reports no complete R11
handoff, with a 950 cm remaining gap. The lower-corridor real-pawn retest is now
active. It uses the production capsule/movement, normal time, strict markers,
and analogue slowing around corners. No mid-run actor repositioning occurs.
After its terminal result, run the corrected child reference/idle/walk/seated
preview, verify CurrentAsset and inspect images before any pose/clothing claims.
All Unreal editor/build/render processes remain sequential.

### 02:03 UTC continuation (September 30 UTC / September 29 local)

Child Blueprint authoring passes all four bodies with individual capsule/foot
fitting. The first successful isolated renderer produced 12 captures and exited
0, but appearance review fails: grey source presentation and BlackBoy arm
skin deformation. The explicit-lit rerun captured 12 images then exited
3221225477 during shutdown. Its current `ChildPreview/index.json` is explicitly
failed with the exit code and visual findings; earlier clean capture-only evidence
is preserved under `BeforeExplicitLitMode_20260929`. It is not visual acceptance.
The runner now records engine exit codes and forces fresh acceptance reports
false after a process failure, even when callbacks completed their captures.

`Child_Material_Roots.json` is a clean read-only reload: output wiring and texture
references are present. Direct source inspection finds BlackBoy's skin/hair
Diffuses are flat 64x64 RGB166 maps; shirt/shorts are flat RGB247. The detailed
BCB head texture also uses a grey base. Source child instances use white Base
Color Tint values. Thus supplied grey colour is real source data, not established
missing shader bindings. `author_child_material_palette.py` is active (runner
`89055`): it authors natural skin/hair and casual clothing tints on owned copies,
with per-asset backups/hashes. This is an authored palette, not recovery of
unavailable original colour. Fresh coloured views remain required.

The pose preview also exposed a harness-only issue: OverrideAnimationData updates
construction defaults but leaves an already active single-node instance playing
its old clip. The prepared correction uses PlayAnimation/SetPosition/zero play
rate, checks the actual CurrentAsset, and adds reference-pose captures. The prior
Idle/Walk/SeatedSource images therefore do not accept those different poses.
BlackBoy deformation still requires reference-versus-animation investigation.

The bounded sewer repair is saved with backups: copied gate, one beam and both
stacked brick wall sections are moved, plus a 10.74-degree floor transition.
The latest finer collision survey reaches the lower corridor but still leaves a
**950 cm** gap to R11; its full route_found remains false. The first real-pawn
partial walk fails at header StaticMeshActor_378 near a tight corner; preserved
as `SewerLowerCorridor_HeaderCorner_20260929.json`. The new candidate uses a
12 cm capsule-route clearance margin, and the prepared harness slows analogue
input near tight markers instead of cutting corners at full speed. No geometry
or full sewer handoff acceptance is claimed. Actual retest remains required.

### 01:38 UTC continuation (September 30 UTC / September 29 local)

All four supplied children now have separate saved guest Blueprints and measured
mesh proportions: BlackGirl 110.26 cm, WhiteBoy 157.33 cm, WhiteGirl 155.69 cm,
BlackBoy 155.47 cm. The guarded Blueprint pass saves distinct capsules and foot
origins and independently reads back the bodies and capsule sizes. No world
placement or roaming/seat behavior is accepted by that authoring report.

`Child_Roster_Retarget.json` now passes all **24 clips** (six per child): idle,
walk, run, two gestures and a seated fitting source. Each rig has its own IK
chains/retarget assets, including explicit CC bone mapping on BlackBoy. Samples
at five times contain finite positions/scales and a stationary root. The first
run correctly rejected MM_Run_Fwd's translated root. The owned copies now bake
that root position in place while preserving rotations/scales and limb motion;
source animation assets are untouched. This accepts saved numerical poses only.
The bike seated source is explicitly not a fitted chair/ride pose. All-child
clothing/gait/roaming/ride-seat visual and runtime integration remain open.

An unsaved lit PIE preview of these actual saved Blueprints is active (runner
`68520`; inspect live process/session before next engine launch).
`review_child_roster_pie.py` captures idle/walk/seated-source poses and records
actual runtime meshes/materials, capsule sizes and bone locations. Image review,
clean exit and fresh report are required; no preview acceptance yet.

The sewer fine survey retains the genuine gate/beam/wall obstructions while
handling previously traversed low authored stair risers separately. Its candidate
is still false. A bounded backed-up repair moves exact copied gate/beam and both
stacked brick wall sections beside the lower approach, and adds a 10.74-degree
floor handoff in the owned connector map. Authoring passes, but a fresh survey
and real-pawn normal-speed continuous return/camera checks remain required.
The new `sewer_stair_handoff` harness case requires matching level hashes and
uses tight 8-25 cm waypoint tolerance. No interactive-door claim is made.

### 01:17 UTC continuation (September 30 UTC / September 29 local)

Both saved water vehicles now pass full sampled lifecycle reports with clean
engine exits: boat powered outbound about **12 m**, hovercraft about **20 m**,
continuous reverse returns, ordinary safe unloads and normal-speed walking returns.
Reports: `WaterVehicleAcceptance/Boat_NorthDock_Inflatable_Lifecycle.json` and
`Hovercraft_NorthDock_Handling_Lifecycle.json`, each with all seven events and no
errors. The boat's first return harness incorrectly compared pawn height to the
next uphill marker; it now compares the measured floor along the current ramp
segment and records floor/movement samples. The hovercraft's first return tried
to cross its own parked hull after the native left-side unload. The passing run
uses the real hull's rear perimeter, with three clear Pawn-profile capsule sweeps
and measured existing-pier floors, then walks continuously to the original start.
The failed hovercraft report and logs are preserved as `CrossHullReturn_20260929`.
These remain short handling-lane/API tests with Mass excluded; full activity
courses, rendered hull/seat/camera fitting, water boundaries, physical controls
and populated/package performance remain open.

BlackBoy now imports successfully into its separate owned namespace: **101 bones,
24 material slots and 79 supplied texture maps**, guarded authoring success and
clean engine exit. The prepared FBX retains all 12 rigged meshes, excludes only
the unskinned helper Cube and round-trips within 0.0000011 m in Blender. Source
archives/FBX/textures are untouched. `BlackBoy_Prepared_FBX.json` and
`BlackBoy_Unreal_Import.json` record source hashes and bindings. This is import
and material-reference acceptance only. All four children still require actual
mesh/capsule proportions, animation/actor integration, clothing and seating
views. A read-only source animation and mesh-bounds census is prepared next.

### 00:53 UTC continuation (September 30 UTC / September 29 local)

Atlantis's floor handoff passes its fresh actual-pawn normal-speed round trip:
**28.96 / 28.47 seconds and 12 camera checks**, no errors, clean engine exit.
See `AtlantisFloorHandoff_20260929.json`. Full rendered/room/mission acceptance
remains separate. The sewer handoff is still open; a read-only capsule graph
survey (`survey_sewer_handoff_route.py`) is prepared but **unexecuted**.

Three supplied child bodies are now transferred into separate namespaces under
`/Game/Carnival/Characters/Children`: BlackGirl **280**, WhiteBoy **233**,
WhiteGirl **240** assets. All three final transfer processes exit 0. A separate
fresh main-project reload passes all 753 file hashes and hard dependencies,
three distinct skeletons (108 bones each), required body bones and all 74
material slot references (`MainProjectAssetReload.json`). This is asset/rig
reference acceptance only: actors, animation, actual mesh proportions/capsules,
clothing appearance, seating and rendered acceptance remain open. The recorded
pose is the skeleton's reference pose, not a measurement of model height.

Migration moves only each body's hard dependency closure through UE asset
rename/save APIs. Irrelevant source mannequin ControlRig pose animations were
excluded after the initial directory rename failed. Subsurface profiles require
AssetRegistry asset names rather than assuming the package filename equals the
object name. UE5.8's new migrator unconditionally cancels with conflict=CANCEL,
and its instanced Blueprint migration then hits a FindInBlueprintManager ensure.
Final successful transfers use explicit destination-conflict preflight plus
SKIP and the supported legacy package-copy backend through a **process-local**
`AssetTools.UseNewPackageMigration 0` override. No existing destination or vendor
asset was overwritten; failed workspaces/reports and the ensure-bearing transfer
were preserved separately before clean recopy. Original archives/staged sources
remain immutable. Do not reuse the failed ensure report as clean acceptance.

The fourth source (BlackBoy) was inspected read-only with Blender: 12 rigged body/
clothing/hair/accessory meshes, a separate unskinned 2 m helper Cube, one 101-bone
rig and 166 textures. Body bounds are about 1.53 m tall. It uses CC bone names
(e.g. BoneRoot/Pelvis/L_Thigh), requiring explicit retarget-chain mapping. FBX
Unreal import and material binding are still open. Preserve/exclude the unskinned
helper Cube during import, rather than including it in the character.

Dense berth survey passes **1,066** water/overlap/terrain samples. All **207**
handling-lane samples pass actual membership and >=200 cm terrain depth, with a
minimum of **218 cm**. The boat/deck/activity plan was prepared and guarded
authoring now saves both `Boat_NorthDock_Inflatable` and
`Hovercraft_NorthDock_Handling` in the project-owned north docks map, with backups.
The boat seat offset was EditDefaultsOnly and rejected instance fitting. It is
now EditAnywhere (default/handling behavior unchanged); editor rebuild succeeds.
The first boat walk remained grounded but stopped short of the mount trigger.
The harness now reaches the final marker within 15 cm (previously 55 cm), then
records exact trigger and Pawn-profile capsule-to-seat clearance. The second
run proves overlap and a clear seat path, but fails a harness-only unsupported
controller `get_pawn` call. It now uses GameplayStatics.get_player_pawn, as the
passing bumper harness does. Both failed reports/logs are preserved. The fresh
corrected full boat lifecycle is active (runner `46392`), followed by hovercraft. Source: `Authoring.json`,
`DockWaterBerth.json`, `PlacementPlan.json`. Saved placement/depth evidence does
not accept these lifecycle, activity-course, rendered hull/rider/camera or
physical-input requirements.

### 00:24 UTC continuation (September 30 UTC / September 29 local)

All three hospital corridor candidates now pass real-pawn outbound/continuous
return at normal time, with **36 camera checks** in total. West takes 9.78/9.62
seconds, east 14.30/14.22, south 20.49/20.34. The combined five-case report
`ExpandedCorridors_20260929.json` correctly remains failed for Sewer and Atlantis.
Sewer's endpoint probe intersects a beam. Atlantis walked through its hall but
fell into the gap before R12's floor. A backed-up project-owned 4.2 m-wide,
2.37-degree floor handoff is saved in the connector map; its actual-pawn retest
is active (`AtlantisFloorHandoff_20260929.json`, runner `9566`).

Balloon index 0 is resolved. Native diagnostics identified Snow scenery
`StaticMeshActor_73` overlapping the canopy. The old authoring survey used
Visibility while production uses WorldStatic/WorldDynamic/PhysicsBody objects.
Authoring now matches production object sweeps and can repair one station while
preserving all other positions/routes. Index 0 moved from (-7250,-8000) to
(-6500,-8750); guarded authoring passes, and all other nine stations are unchanged.
The fresh focused lifecycle passes **15/15**, with no flight obstruction and
clean exit (`BalloonZeroFinalStation/index.json`). Its fresh walking run passes
both legs (`BalloonZeroFinalStation_Walks.json`). Combined with unchanged earlier
stations, current station walking coverage is 20/20 legs and sampled flight/
handover coverage is complete. This does not accept all seats, rendered fitting,
full crowd or physical input. Preserve the earlier failed combined reports.
`Balloon_Stations_BeforeObjectSweep_20260929.json` retains the old report with SHA
`ec17b219c525fe1f36ad65ecc182606474c78b244c65ef00457626c7348cdfc0`.

Editor rebuild succeeded. The fresh audio-enabled native suite passes **34/34**
cleanly (00:10 UTC), including the new exact obstruction-actor diagnostic,
reset after removing the blocker and successful operator restart/stop/handover.
The all-ride harness now uses each balloon's saved grounded public approach
and records position/ownership/flight-clearance diagnostics. Original sources,
vendor assets and old failed evidence remain preserved.

### 00:07 UTC continuation (September 30 UTC / September 29 local)

The nine relocated balloon retest finished with clean engine exit but failed
combined acceptance: **eight instances pass 15/15**, and index 0 passes passenger
flight/return/unload but rejects operator stop. A separate focused diagnostic
reproduces it: player remains stationary, grounded, in interaction range and
retains operator ownership; the flight clearance handler starts an automatic
return immediately after securing. Do not label this a distance/ownership failure
or accept the combined report. Collision actor/component diagnostics and a native
obstruction-reset/operator regression are being added; rebuild and retest remain
required. Failed reports and per-case logs are preserved in
`AllRidePIE_FinalBalloonStations` and `BalloonZeroOperatorDiagnostic`.

Five expanded interior corridor cases are now executing in
`ExpandedCorridors_20260929.json`. Child projects were cloned into independent
`MigrationWorkspace` folders, preserving immutable staged sources. Namespace
rename/dependency migration scripts are prepared but **not executed** yet; no
child asset integration claim is warranted.

### Previous continuation — 23:41 UTC

The durable Ferris repair and all three lighting runs are complete. Day, Night
and Snow each pass **30/30 checks** (Ferris and Carousel, 15 each), with clean
engine exits and per-case logs in `AllRidePIE_day`, `AllRidePIE_night` and
`AllRidePIE_snow`. The separate fresh seat census confirms 160 unique Snow
Ferris seats and no unready active rides. These reports plus the preserved
default 19-attraction passes and dedicated bumper 15/15 report establish sampled
lifecycle/handover evidence for **all 25 authored attraction instances**. They
do not establish every seat/car, walking approach, rendered fitting, NPC crowd,
mission-return coverage, or physical controller input. Vendor empty announcement
array warnings remain an audio/runtime cleanup item.

The user could not identify the child roster sources. Local asset inspection
found four supplied rigged game-ready child characters under
`F:\3D Characters\Metahuman Downloads\Children`. Three have clean UE5.3 projects;
the fourth has FBX and textures. **1,508 source files** were staged separately
under `Saved/CharacterAcceptance/ChildSources`, with source/member SHA256 hashes
in `SourceManifest.json`. The three same-named UE4 skeleton assets have different
hashes, so do not merge/overwrite them blindly. Project Content is unchanged by
staging; namespace-safe migration, animation/rig/clothing/capsule/seating and
rendered acceptance remain open. This closes the source-location uncertainty.

Balloon station authoring and walking are complete. The first walk correctly
failed at stations 1/2 because their planned route crossed the destination
basket. The survey now excludes that future footprint as well as other stations
and reserved routes. Guarded authoring saved ten stations; the fresh real-pawn
run passes **20/20 outbound/continuous-return legs**, with no intermediate
teleports, no failures, and clean exit. See `Balloon_Station_Walks.json` and its
preserved logs; the failed report is `Balloon_Station_Walks_BasketObstruction_20260929.json`.
Nine stations moved relative to the original lifecycle run (all except index 5).
Their current-position lifecycle retest was started in
`AllRidePIE_FinalBalloonStations/index.json`. Its report records the station
authoring SHA256 and actual ride positions. Walking/rendered/physical-input
limits are retained; the changed flight positions remain unaccepted until this
fresh cycle report passes. The 00:07 continuation records its later failure.

### Historical checkpoints — superseded by the continuations above

The default placed-ride lifecycle run has now finished with a clean engine exit.
**19/20 attractions and 273/274 checks passed**, including all ten balloons,
Swing, Pirate Ship, Balloon Tower, Flying Bobs, Haunted House and Teapot. The
sole failure is Ferris readiness from the persistent duplicate seat; the combined
acceptance is correctly failed. The report is preserved as
`AllRidePIE/Default_BeforeDurableFerrisRepair_20260929.json`. Bumper Cars has its
separate passing lifecycle report. Hidden Day/Night variants, walking approaches,
rendered seating, crowd and physical input still require separate acceptance.

The editor-instance deletion attempt was rejected. A native read-only construction
census then found the actual source: each project attended Ferris Blueprint had
161 SCS nodes, including a `CarnivalRideSeat` node omitted by the normal subobject
census. The bounded native authoring helper now validates the exact duplicate's
ID, transforms, passenger offset and attachment, and removes only that node.
The guarded repair saved all three Blueprints and their backed-up lighting maps;
all **480 calibrated seat transforms are unchanged**. A separate fresh PIE
process passes the seat census: Snow Ferris has 160 unique seats, is ready, and
there are no unready active rides. The three lighting-variant lifecycles remain
pending. Editor rebuild succeeded. Day streaming now uses exposed properties;
the harness waits for streamed actors' natural first initialization ticks.

The completion goal is active; the full demo remains unaccepted. The Development
Editor rebuild succeeded after the bumper display-car collision fix. Authoring
saved the eleven explicit replaced-component names on the project arena.
Initialization now removes their collision after vendor Blueprint BeginPlay,
while retaining platform/scenery collision. The native regression is compiled;
the fresh audio-enabled suite passes **34/34**, with zero warnings, failures or
not-run tests (`Saved/HauntedDollIntegration/FullAutomationAudio/index.json`,
22:36 UTC). This includes the bumper replacement regression and actual audio
device gain/mute readback.

The real placed bumper arena now passes **15/15** lifecycle checks, including
boarding, possession, driving (149.83 cm measured displacement), arena containment,
safe unloading, walking return, operator start/stop and attendant resumption.
Evidence: `Saved/RideDevelopment/BumperArenaPIE/index.json`, clean process exit 0.
This uses direct production APIs, excludes the Mass crowd, and does not establish
physical input, rendered seat fit, or full arena driving coverage.

The balloon fire-repair rerun passed, removed one redundant activation node from
the project-local base, preserved all ten actor/basket/seat numeric transforms,
and saved the adapted base and child Blueprint. Vendor Blueprint preserved.
Evidence: `Saved/RideDevelopment/Balloon_Fire_Repair.json`, guard success and exit 0.
The fresh native suite exposed stale inherited seat-parent links after reparenting.
The repair now rebinds all four seat templates to the exact inherited basket and
verifies all 40 placed links. The next full native run passes balloon ascent,
attachment, obstruction, return and scaled unload with no particle warnings.

The four hidden Day/Night Ferris Wheel/Carousel conversions and both Snow variants
now pass the focused authoring run (six instances, zero errors). Hidden components
have identity cached world transforms; conversion lookup now measures serialized
root-relative placement for unattached roots and verifies new class/level/label
and position. This is saved authoring evidence, not lifecycle/render acceptance.
The subsequent full authoring pass processed **25 instances across all 12
families with zero errors**, including eleven existing bumper cars in the
dedicated arena. `All_Attended_Authoring.json` records the current full pass.

The first placed lifecycle run passed Clown Ride, then correctly rejected the
Snow Ferris Wheel for a duplicate seat ID. The run was stopped and explicitly
marked aborted; it is not all-ride acceptance. Template IDs were unique. A live
census found a legacy `CarnivalRideSeat` exactly overlapping its calibrated SCS
seat. A backed-up, geometry-checked repair removed that duplicate from all three
Ferris variants, retaining all calibrated seats. See `ConstructedSeatIds.json`
and `DuplicateFerrisSeatRepair.json`. A fresh reload still reconstructs that
legacy component, so the initial deletion is **not a durable repair**. The helper
now uses the editor subobject deletion path; its rerun is pending while the
remaining full lifecycles continue. Clown Ride, Circus, Carousel and seven balloon
stations have passing lifecycle/handover checks so far; the combined report remains
incomplete and retains the Ferris failure.

### Immediate continuation order

1. Finish the active boat lifecycle (`46392`), repair any measured failure,
   then run hovercraft. Every engine/build process must stay sequential. Balloon
   index 0 lifecycle/walking, Atlantis handoff and all three hospital corridors
   pass; do not rerun superseded failures. Ferris Day/Night/Snow, durable SCS
   repair and seat census are also complete.
2. Execute interior/hospital corridor,
   dense water-berth survey/vehicle authoring/lifecycle, translucent Nanite,
   settings readability, audio census and GameInput passes described below.
3. The three source-project child bodies are migrated and independently reloaded.
   Import/material-bind BlackBoy's FBX (exclude the unskinned helper Cube), retarget
   animation on each distinct rig, author actors and validate clothing/capsules/
   seating and views. Existing doll retarget scripts demonstrate the installed UE
   IK API. Source archives and immutable staged projects stay preserved.
4. `review_populated_carnival_pie.py` is a new unexecuted render/PIE diagnostic:
   it retains all spawners, counts live instanced skin components, captures real
   collection-group views and reports editor frame intervals with explicit limits.
   Inspect its images, repair visual failures and freshly cook/package before
   making runtime material, full roster or packaged-performance claims.

## Stopped checkpoint â€” 22:09 UTC

Implementation and all three subagents stopped at the user's request to commit
and push. The final Development Editor build succeeded. The final focused ride
suite passed **8/8** (six clean, two with warnings, zero failures) at 22:09 UTC;
the scaled balloon fixture correction is now compiled and passing. The previous
full audio suite remains historical **33/34** evidence; it was not rerun after
this correction. No fresh package or physical DualSense acceptance was completed.

Code, authoring/acceptance scripts, documentation, calibration and project-owned
Blueprint/input/physics assets are included in the checkpoint. Licensed imports,
copied material graphs, generated builds/reports, ignored level layouts and
modified vendor-derived motorcycle/hospital geometry remain on this machine.
The authoring scripts and local reports describe those saved world changes.

The latest placed bumper test still fails boarding. Its diagnostics show hidden
original vendor-car components retaining QueryAndPhysics collision; construction
restoring that collision is a suspected cause, not an implemented repair.
The balloon FireSetup repair helper compiles, but its authoring script has not
been run. Latest hidden-ride conversion fallback, balloon station route-clearance
changes, interior reruns, water-vehicle placement, translucent Nanite repair,
settings screenshots, audio census and GameInput diagnostics remain unexecuted.
Fresh crowd render/SM5 cook, roster/clothing/animation acceptance, full ride
lifecycles, populated-world performance and physical controller checks remain open.

## Verified native changes

The UE 5.8.3 Development Editor build succeeded. The latest integrated audio run
at `Saved/HauntedDollIntegration/FullAutomationAudio/index.json` passed **33/34**
at 21:58 UTC: the new safe unload and boat boundary tests pass, while the balloon
test remains failed. Its diagnostics show the scaled fixture pawn entered the
ride penetrating its floor (entry Z98.15, capsule halfheight110.4); the safe unload
check correctly retained it. The fixture correction subsequently passed the
focused ride suite at the stopped checkpoint above.
The preceding 21:46 run passed all 32 then-existing tests, including actual audio
gain/mute readback, with vendor balloon particle warnings in one test.

This includes authored-body Chaos braking/handbrake/reverse/airborne control and
velocity-preserving mode transitions, mounted target scoring through the actual
rider, and boat/hovercraft camera rotation. The Chaos fixture explicitly advances
the engine frame counter so every simulated step runs its physics ticks.

- Saved keyboard/mouse/controller remapping uses per-player runtime copies of
  both Enhanced Input mapping contexts. Authored modifiers and triggers survive.
  Settings offers a controller-navigable remapping page, conflict detection,
  reserved Escape/Options access, capture cancellation and saved restore defaults.
  Recovery, interaction, ride and activity prompts read current bindings.
  `Carnival.Input.SavedRemapping` verifies disk reload, original asset preservation,
  conflict rejection, controller labels and real Enhanced Input key dispatch.
- Ride readiness rejects missing/duplicate seats. Queue references recover from
  removed actors, and attendant reassignment/destruction releases operator control.
  Walkthrough/show experiences retain player movement. Standing basket passenger
  support preserves the original animation state. Native ride tests pass; that
  does not accept unconfigured placed rides.
- Activity ownership, scoring, checkpoint ordering, cancellation and result
  preservation are implemented and tested. Weapons and unarmed attacks apply
  actual collision-tested damage with cooldowns. Building requires a supported,
  clear placement and handles empty categories safely.
- Boats/hovercraft receive Enhanced Input vehicle controls, clear held controls,
  reject obstructed boarding, and restore riders on dismount/destruction/lost
  possession. Ground exits are checked. The real water/shore placements are not
  accepted by these fixtures.
- Vault/mantle movement now follows checked capsule paths and restores movement
  on completion or interruption. Native ladders support explicit bottom/top exit
  markers and both directions. Prone standing checks ceiling clearance. Authored
  parkour/ladder locations and animated contact still need acceptance.
- Kit guest capsules overlap players and do not affect navigation, preserving
  world collision while preventing those actors sealing player paths. The separate
  MetaHuman Mass representation still needs an active-world test.

## Latest continuation (21:33 UTC)

At 21:59 UTC, the copied crowd material graphs were repaired again after a fresh
editor load exposed lost function-input connections. Six local graphs/921
expressions were restored from original graph wiring, compiled with zero reported
errors and saved. See `CrowdSamplerGraphRecovery.json`; fresh SM5 cook and visual
acceptance remain required. Ten grounded balloon stations are saved, with real
walking/flight acceptance pending. Water surveys confirmed no placed boats or
hovercraft; a measured hover placement plan and deeper boat-berth survey are ready.

At 21:46 UTC, the audio-enabled suite passed **32 tests** (31 clean and one
with 20 vendor balloon particle warnings; no failures or skipped tests).
`FullAutomationAudio/index.json` and `Full_Test_Audio.log` record actual device
gain/mute verification, saved-volume reload, and the balloon ascent, blocked
flight, return and ownership regression. HUD wrapping compiles; rendered menu
acceptance remains open. Bumper authoring then saved eleven cars, an attendant
and a grounded boarding bay; placed runtime acceptance is in progress.

At 21:43 UTC, the isolated Lab B gallery passed its clean rendered rerun: all
three real-pawn walk legs and four player-camera captures succeeded, exit 0.
The north/south offset views show the eleven artworks in the entrance corridor.
Connected arrival and whole-game lighting acceptance remain separate.
The integrated mansion mission-room route and hospital entrance also passed
continuous out/return and twelve camera-clearance views each. The combined
interior report remains failed for separate Sewer/Atlantis elevation probes.

- Editor build passed; **30/30** Carnival automated tests passed with no warnings,
  failures or skipped tests (`Saved/HauntedDollIntegration/FullAutomation/index.json`).
  This includes new Bumper Cars driving/ownership/unload and passenger-scale tests.
  Placed arena and rendered seat acceptance still need separate runs.
- All supported ride authoring processed 25 instances. Ten airborne Hot Air
  Balloons have no grounded staff approach. Four hidden lighting variants were
  converted but Unreal returned an empty selection; exact actor resolution is
  now implemented for the next authoring run. Full-cycle acceptance remains open.
- R10 descent passes; a second obstructing return arch (`StaticMeshActor_245`)
  was moved in the copied sewer level with a backup. The subsequent real-pawn
  normal-speed round trip passed (`Stairs_Arch_Final_PIE.json`, return 13.84 s).
  R10, R11 and R12 now each have both-direction traversal evidence.
- All six MetaHuman collections now have saved pipeline material-parent overrides
  (`CrowdPipelineRepair.json`). Shared-sampler SM5 cook/render proof remains open.
- Development game build passed before the newest Bumper changes. A diagnostic
  new-executable/old-cook probe restored the missing MetaHuman archetype but failed
  unversioned property serialization before map load. It is not runtime acceptance;
  a fresh game build and content cook are required. Original archive preserved.

## World work and remaining verification

Latest continuation evidence (20:53 UTC): both underground tunnels passed with
the real gameplay pawn at normal time and continuous returns. R11 took
18.01 / 17.65 seconds; R12 took 2.89 / 2.55 seconds. See
`Saved/WorldExpansion/Connections_Final_Repair_PIE.json`. This combined report
correctly remains failed because R10 stairs stopped at the lower sewer wall.
The terrain hole is saved and the pawn passed the former terrain obstruction.
A measured lower-landing wall placement correction is staged for retest.

The Shipwreck project-local 10 cm kinematic sail-root asset was applied and
saved. That same integrated PIE run contains no missing-root-physics warning.
Visual sail/cloth acceptance and the final cooked package remain separate.
USB enumeration detects the Sony DualSense (VID_054C/PID_0CE6); this is hardware
detection only, not proof of physical input or a completed controller pass.

- R11 Sewerâ€“Atlantis passed a real gameplay-pawn outbound/continuous-return walk
  at normal time: **18.38 / 17.65 seconds**, after bounded copied-wall portal repair.
  Evidence: `Saved/WorldExpansion/Underground_Tunnels_Repair_PIE.json`.
- R10 stairs remain open until a new passing report exists; R12 now passes.
  Copied enclosure/roof/floor repairs and additional bounded opening scripts are
  saved with backups. A successful authoring report is not a traversal pass.
- All-ride authoring, measured seat calibration, per-instance queue ownership and
  a full cycle/handover PIE harness are staged. No all-ride completion claim is
  warranted until the authoring and runtime reports pass. Bumper Cars remains a
  dedicated gameplay gap; Carousel horse straddle poses are not calibrated.
- Lab B entrance gallery survey, relocation/lighting and real-camera PIE scripts
  are staged. Earlier north-wall placements are obstructed by display machinery.
  Bounds-only survey and unlit closeups do not establish readable player views.
- Shipwreck has a project-local kinematic sail-root repair helper. Its application
  and fresh runtime warning check must pass before calling the issue repaired.
- A UE 5.8-only runtime MetaHuman collection-archetype compatibility change is
  staged in `CarnivalGame.cpp`. It recreates the named template omitted by the
  engine's editor-only constructor, preserving engine files and collection data.
  This code is excluded from editor builds: a Development game build and cooked
  runtime test are required. The SM5 material sampler failures are separate.

## Still open

Full mansion/hospital/expansion interior and camera exploration, water boundaries,
all placed rides and seating/animation fit, Bumper Cars, complete character roster
and clothing, MetaHuman materials, populated-world performance, lighting/audio
mixing, rendered Lab B review, and the complete packaged physical DualSense pass.
The already finished settings navigation/saving and motorcycle retry reset were
preserved. No physical controller events were generated by this pass.

### Additional saved work (21:12 UTC)

- R10 descent passed in 14.56 seconds; return identified copied sewer arch
  `StaticMeshActor_66`. Its placement is now corrected with a backup, awaiting
  another both-direction run. `Stairs_Beams_Repair_PIE.json` remains a failed
  combined report and must not be presented as a staircase round-trip pass.
- Clown Ride (18 seats) and Circus now have saved attendants and distinct queues.
  Authoring passed; the first PIE rejected visitor interactions. The harness now
  uses the actual clearance-tested approaches and reports rejection predicates.
  All remaining rides and rendered seating acceptance remain open.
- Lab B art was moved into its entrance corridor and lights reduced to 60 lumens
  after the initial 900-lumen captures washed out the images. Real-pawn corridor
  travel passed. Revised captures show recognizable unobstructed art; that run
  completed its captures but returned an access-violation exit code after normal
  shutdown logging. A clean rerun with offset camera views is queued.
- `CrowdSamplerRepair.json` records 12 shared wrap samples in local function
  copies, 68 reparented material instances and 64 preserved embedded parent links;
  14 packages were saved with collection backups. Engine/vendor assets are intact.
  SM5 cook/render proof and pipeline-parent persistence verification remain open.

Unreal/editor processes must stay sequential on this workstation. Two delegated
agents hit the account usage limit after saving staged work; the root agent
continued the work directly.
