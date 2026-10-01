# Crowd clothing composition repair — September 30, 2026

The SDK ownership competition is reproduced for Dean. Two fresh owned
collections keep his exact selected shirt, jeans and sneakers. `Mixed` also keeps
G1's two complete outfits; `Parts` excludes them. Both hide the original body,
use the same source quality and separate duplicated target skeletons, and bind
the already reviewed Dean head textures. Neither changes the live config.

Native ownership logs assign `hand_l`/`hand_r` to `Outfits` in Mixed and to
`Top Garment` in Parts. The final ownership bitmaps visibly change the hand
regions. The selected shirt's appended skin increases from 206 to 5,041
triangles; the jeans/sneakers contain 299/91 in Parts. Both collections reload
and assemble in a fresh process with their reviewed skin bindings intact.
Source collection/character/garment/skeleton hashes and the 256 inspected source
mesh fingerprints remain unchanged in the Dean proof.

All eight front/back captures at fixed source idle/walk time 1.0 were inspected.
Mixed reproduces empty cuffs; Parts restores both hands without obvious skin
clipping in these views. The dark idle sleeve patch remains. The Parts idle run
captures both images then exits **0xC0000005** after normal log closure. Three
other proof render runs exit 0. This establishes the isolated ownership cause,
not full character or stability acceptance.

The 32-appearance live roster was read and hashed. It contains 24 explicit
separate-garment selections, seven explicit complete-outfit selections and one
G6 appearance using defaults. G1–G5 mix clothing compositions; G6 already
contains only complete outfits. All existing appearance selections must be
retained when replacing the mixed collections.

The first broader candidate is saved at
`/Game/Carnival/Crowd/ClothingFamilies/G1Parts/DA_CarnivalCrowd_G1_Parts`, with
copies of Dean, Advika, Kate, Alt01 Dean, Alt02 Advika and Petra under its
`Instances` directory. It retains all G1 part, head, body and hair items and
excludes only the complete-outfit items. The SDK generated a new collection;
32 generated head materials were rebound to the four reviewed head bakes.
Every copied instance preserves the source selected keys and authored parameter
override fingerprint. Its seven new packages total about 1.61 GB. The live
config and original appearance packages are unchanged.

The build preserves the inspected source's **256 meshes and 104 materials**
and scoped source package hashes. Fresh reload verifies all six selections,
override fingerprints, head bindings, geometry, visibility and material paths.
The initial strict comparison found 18 empty imported material-slot names filled
with their existing slot names. The final check permits precisely those fills,
records them, and requires every other field to match. Both initial failed
comparisons and their logs are preserved; no geometry or effective material
remap difference was accepted.

Dean's copied candidate was rendered front/back at direct Manny idle time 1.0.
Both hands are present and the authored clothes remain; no obvious skin clips
appear. Its dark sleeve patch persists. The render exits 0 with the new crash
observer attached. This single instrumented exit does not resolve the prior
intermittent failure. The gallery of all six uses the saved collection's baked
`AS_Idle`; its first attempt stopped before capture because Python cannot read
the protected `CurrentAsset` property. That failure is preserved. The corrected
gallery explicitly plays the collection-owned baked clip. All 12 images were
reviewed: hands are complete on all six appearances, but the two Dean heads are
clipped by the fixed framing, hair presentation has artifacts, and dark sleeve
shading persists. Baked idle height/proportions need comparison with the original
source collection before attributing the framing difference to camera or pose.
The corrected gallery exits 0 under the observer; full appearance remains failed.
There are **22 new reviewed images** across the ownership proof, copied Dean and
six-appearance gallery, in addition to the earlier 46-image diagnosis.

A local Windows SDK observer can now launch only the diagnostic engine child
and capture an unhandled exception's minidump, thread context, module offsets
and available native stack. It does not change global crash settings. An
intentional null-write fixture produced a valid dump and a symbolized `wmain`
stack; no real engine crash has been captured yet. Its implementation follows
Microsoft's [debug loop](https://learn.microsoft.com/en-us/windows/win32/debug/writing-the-debugger-s-main-loop)
and [minidump API](https://learn.microsoft.com/en-us/windows/win32/api/minidumpapiset/nf-minidumpapiset-minidumpwritedump).
Debugger-attached runs can change timing and are not performance evidence.

Evidence:

- `Saved/CharacterRepairs/DeanBodyOwnershipBuild_20260930`: both builds, source/geometry checks, six ownership images, reload, eight-image visual review and failed-exit logs.
- `Saved/CharacterRepairs/CrowdClothingFamilies_20260930/SourceRoster.json`: all 32 source selections and scoped hashes.
- `Saved/CharacterRepairs/CrowdClothingFamilies_20260930/G1Parts`: candidate build, six copied instances, 32 skin bindings, source snapshots, reload and preserved comparison failures.
- `Saved/CharacterRepairs/G1DeanClothingFamilyIdle_20260930`: the copied Dean's two inspected views and instrumented clean exit.
- `Saved/CharacterRepairs/G1ClothingFamilyGallery_20260930`: protected-property failure before capture.
- `Saved/CharacterRepairs/G1ClothingFamilyBakedIdleGallery_20260930`: corrected six-appearance gallery.
- `Saved/CharacterRepairs/NativeObserverFixture_20260930`: intentional crash fixture, minidump and native stack.

Editor helpers build, the game target is up to date, and **39/39 native tests
pass with zero warnings, failures or skips**. Candidate rendering still reports
generated section-index fallback messages even though its effective remaps
match. Those diagnostics need assessment before final cook acceptance.

### Original/candidate pose and shadow comparison

`Saved/CharacterRepairs/DeanFamilyPoseAndShadow_20260930` contains 22 reviewed
front/back images of the actual original and copied Dean actors. The camera is
wider and includes the complete head and feet. Reference pose, direct Manny
idle, each collection's `AS_Idle`, crossed collection clips, and default versus
always-refresh animation ticking were compared at fixed time 1.0. Source and
candidate package hashes remain unchanged; the instrumented engine exits 0.

Both original and candidate have reference head height 174.734 cm and direct
Manny idle head height 172.078 cm. Their own and crossed baked idle clips put
the head at 191.146 cm: **19.068 cm above direct source playback**. All baked
head measurements agree within 0.001 cm. Both default tick policies already
refresh hidden-body bones; forcing that policy does not change the result.
The candidate retains both hands in all sampled poses; the original does not.
This establishes a pre-existing shared animation defect rather than a family
rebuild regression. The source animation skeleton's translation-retargeting
policy was investigated using an unsaved transient clip and skeleton.

The candidate's black upper-arm patch disappears when light and mesh shadows
are disabled. This isolates a shadow contribution; it does not justify
disabling gameplay shadows. The body-only shadow experiment leaves it unchanged.
The initial PIE body single-node animation is empty before the script explicitly
starts the clip; this also needs checking in actual runtime representation
initialization. These studio comparisons do not accept GPU crowd, transitions,
all LODs, or final character appearance. The report remains `success: false`
with `capture_success: true`.

`DeanRetargetPolicyAndBodyShadow_20260930` adds 14 reviewed images. Copying
source translation modes alone leaves the stretched pose unchanged. All original
and candidate mesh components have hidden-shadow casting disabled; disabling
only the invisible Body shadow also leaves the sleeve patch unchanged.

`DeanAuthoredReferenceAndGarmentShadow_20260930` adds 16 reviewed images.
A transient named retarget pose maps the original source clip's reference
transforms by bone name onto a copied candidate skeleton. This restores sampled
head height to 172.078 cm and pelvis height to 98.084 cm, close to direct source
playback. Copying the source translation modes adds no improvement here.
The complete left-foot position still differs by **2.23 cm**, hands by about
1 cm, and head position by 0.057 cm. This is evidence of the missing authored
reference relationship, not full animation acceptance.

Only disabling the shirt's shadow removes the black sleeve patch. Disabling
face or other outfit shadows does not. This identifies shirt self-shadowing;
disabling those shadows is a diagnostic control, not an accepted fix. Raising
fill-light intensity from 20 to 100 leaves the front patch and washes out the
back, so that change was rejected. Both new engine runs exit 0 under the observer
and preserve original/candidate hashes. All experimental clips/skeletons are
transient; the saved candidate and live config are unchanged.

`DeanAnimationSpaceConversion_20260930` preserves the initial conversion API
failure: `ReplaceSkeleton(..., true)` cannot update the copied animation data
model because its control rig remains bound to `SK_Mannequin`. No images were
captured. The editor exits 0, but the guarded script correctly reports failure.

`DeanAnimationSpaceConversionSampled_20260930` contains 12 reviewed images of
fresh sequences produced by sampling the source clip through the canonical
target skeleton, then writing matching animated bone tracks and float curves
through a newly initialized animation data controller. Both idle and the actual
configured `MM_Walk_InPlace` correct the stretched pose. Seven landmarks agree
with direct playback within **0.0081 cm in idle** and **0.00021 cm in walk** at
the sampled time. Clothing and hands remain intact in the compared views; the
idle shirt self-shadow persists. Source/candidate hashes stay unchanged and the
instrumented engine exits 0.

The stronger 65-sample, every-bone check in
`DeanConvertedAnimationTrackAgreement_20260930` finds a **1.055 cm wrist-inner
corrective bone difference** over the complete idle clip. Main landmark maxima
are below 0.015 cm. This failure is preserved and blocks a saved rebuild.
`DeanConvertedAnimationAllBodyBones_20260930` preserves the subsequent rejected
constant-bone variant, whose maximum difference increases to 2.019 cm at
`clavicle_pec_l`. The sampler's default again converts animated tracks only.

`DeanConvertedAnimationFullMeshAgreement_20260930` completes all eight
comparisons: 65 samples for idle and walk on the actual body, shirt, jeans and
shoes. All four walk checks pass, with maximum bone-position differences below
0.0048 cm. All four idle checks fail the unchanged 0.1 cm tolerance. Their
worst wrist bones have no animated source or candidate track; they do influence
geometry (up to 862 shirt/skin vertices and maximum weight 0.299). The report
records bone modes, track presence and LOD 0 weighting. Original/candidate/source
clip hashes remain unchanged. These differences cannot be dismissed as unused
control bones. The hybrid named-reference experiment and the experiment that
retained extra moving source bones both preserve the same idle differences.
The latter finds no extra moving tracks. These rejected reports remain saved.

`DeanConvertedAnimationRotationAgreement_20260930` adds rotation checks: raw
source playback differs by up to 18.75 degrees on an unanimated corrective
bone. Inspection of the installed engine's `AnimationDecompression.cpp`
shows compatible-skeleton reference remapping applied to every compact bone,
including unanimated bones already initialized from the target mesh reference.
The target meshes do not use compatible-source translation modes.

`DeanConvertedAnimationNeutralReference_20260930` therefore records two
explicit comparisons. The raw source comparison is preserved; the additional
reference restores only bones absent from the source compressed-track table
to the target mesh's local reference transforms. Animated source bones retain
their evaluated pose. All eight complete-clip comparisons pass unchanged
0.1 cm position and 0.1 degree rotation limits. Maxima are 0.016004 cm and
0.048716 degrees. This defines the expected neutral corrective-bone behavior;
it does not establish equality with raw compatible-skeleton playback.
Source and candidate package hashes remain unchanged and the instrumented
editor exits 0. No assets are saved by this comparison.

A fresh family build can opt into conversion only after the complete-clip
check in `DeanConvertedAnimationNeutralReference_20260930` passes. The builder
enforces this gate before creating or saving candidate packages. Existing
candidates and the live config remain unchanged. The fresh `G1PartsRetargeted`
build saves one collection and six instances (seven packages, 1.501 GiB).
All selected keys and authored parameter overrides are preserved. Thirty-two
head materials use the reviewed skin textures. The scoped source package
hashes, 256 source mesh states and 104 source material states are unchanged.
The instrumented build exits 0.

Its fresh-process reload passes all geometry/material/selection checks, allowing
only the existing imported-slot-name fill normalization. All **96 animation
comparisons** pass: six appearances, two clips, shared and selected-head baked
animations, four actual body/outfit meshes, 65 times per clip. Maximum errors
are again 0.016004 cm and 0.048716 degrees against the explicit neutral
reference. Candidate and scoped source package hashes are unchanged; the
instrumented reload exits 0. Build and reload evidence is under
`Saved/CharacterRepairs/CrowdClothingFamilies_20260930/G1PartsRetargeted`.

`G1RetargetedIdleGallery_20260930` and `G1RetargetedWalkGallery_20260930`
capture 24 actual PIE views (six appearances, front/back, two clips), all
manually inspected. Hands remain complete on all six; corrected body
proportions survive rebuilding and reload. The wider camera includes heads
and feet. Dean's idle head height is 172.0773 cm, compared with the earlier
stretched baked pose at 191.1462 cm. No obvious hand/clothing intersection
appears in these fixed-time views. Dark idle sleeve self-shadow and noisy white
hair on Kate/Alt01 Dean remain unaccepted. These are actor LOD 0 studio views
at clip time 1.0, not continuous/GPU/all-LOD/world-lighting acceptance.
Both instrumented renderers exit 0, with all checked package hashes unchanged.
The diagnostic wrapper returns 1 because visual acceptance is deliberately
false; each report separately records successful capture and the open issues.

The playback metadata probe preserves an initial protected-property API failure
and a subsequent public-API comparison. The latter finds a real omission:
the converted shared `AS_Walk` loses six sync markers. Clip duration, playback
rate and zero notify counts are unchanged; head-specific clips match their
prior metadata. This blocks candidate integration despite passing pose checks.
The sampler now retains source markers/notify tracks and playback rate, and
rejects notify-bearing inputs until copying those events is supported. A bounded
candidate-only repair restores the six original L/R marker names/times on
`AS_Input_Walk` and `AS_Walk`, with a full before-package backup. All candidate
mesh fingerprints and scoped source/other-candidate package hashes are unchanged.
The collection's revised hash and backup are recorded as a build amendment,
preserving the before-build record and package. The instrumented repair exits 0.
Fresh reload passes all **12 playback metadata comparisons**, including exact
marker names/times, and all **96 pose comparisons** with unchanged error maxima.
Saved source/candidate hashes, head bindings, authored selections/overrides and
assembled geometry checks also pass. The instrumented editor exits 0. The
before-marker reload report remains as `ReloadBeforeMarkers.json`; the fresh
result is `Reload.json`, with separate after-marker engine/guard records.
The 24 gallery views describe the preceding marker-only revision; marker repair
does not change their mesh fingerprints or bone-pose results. Visual acceptance
remains false for the documented hair/sleeve and coverage limits.

The final editor build succeeds and the fresh native regression run passes
**39/39**, with zero warnings, failures or skips. Its report/log and final
editor build log are copied into the G1 retargeted evidence folder. This goal
turn inspects 88 additional studio images, including the 24 saved-candidate
idle/walk views. The aggregate progress record preserves its preceding version
and retains full/visual acceptance as false. No live config or engine/vendor
file is changed by this work.

### Complete-outfit G1 candidate

`G1CompleteRetargeted` saves the original `MHI_Full_CasualFemale` appearance
with its exact selected keys and parameter-override fingerprint. Separate
garment slots are excluded; both original complete-outfit items remain.
Thirty-two head materials bind the reviewed textures. Scoped source hashes,
256 source mesh states and 104 source material states remain unchanged, and
the instrumented build exits 0.

The first reload passes all 12 metadata comparisons but its verifier rejects
the two unused, empty outfit components in the actor blueprint. Its failed
report/guard/log remain preserved. The body driver is present and hidden;
the failure is not a missing driver. The corrected check explicitly requires
that driver and assembled clothing, records unused outfit slots, and checks
only meshes actually assembled. Fresh reload then passes eight full-duration
body/outfit pose comparisons and all 12 metadata comparisons, with maximum
errors 0.016004 cm and 0.048716 degrees. Geometry/material/selection and scoped
file-hash checks also pass; the instrumented editor exits 0. The live appearance
configuration is unchanged.

Actual rendered complete-outfit views fail despite those per-mesh numerical
checks: the face follows the selected Kate body (head around 147 cm during
idle), while the unlinked outfit stays in its taller reference pose. Driving
the outfit directly animates it but leaves the face around 149 cm, below the
collar. The two driver trials each preserve two front/back images and leave
all candidate/source packages unchanged.

A transient body-leader trial restores the visible head and clothing alignment.
The inspected stock actor execution graph explains the missing link: it calls
SetLeaderPoseComponent after each material-map element, so an empty override
map never establishes the link. The owned actor repair moves that execution
link to the map loop completion, retaining the unused-outfit branch. It is
idempotent, saved with a verified backup, and leaves the stock plugin actor,
Mass configuration and appearance packages unchanged. The final native run
passes 39/39, including fresh complete-outfit assignment and parts/complete/clear
pooling transitions. Four inspected saved-actor idle/walk front/back views
confirm a visible head and body-following outfit without the transient link.
See Saved/CrowdAcceptance/ClothingPoseLinkRepair_20260930.

Hair diagnostics rule out a compact-card texture-layout mismatch: both source
grooms use Layout2, with the expected tangent/coordinate and attribute atlases.
The actor materials inherit Use PerInstanceCustomData=1. Setting it to zero
transiently is verified on every affected MID but does not remove the white,
noisy hair in inspected Kate and Alt01 Dean views. That proposed material
change is rejected and unsaved. Twelve captures and complete parameter/hash
records remain in G1PartsActorHairParameterProof_20260930. Hair acceptance
remains false. Four original-source-material captures are rejected because
Unreal reports missing SkeletalMesh usage for both source card materials;
the gray result is a fallback material. Four more transient SDK actor-parent
captures preserve effective texture/scalar/vector/static-switch values but
retain the white patches, without fallback warnings. Both trials leave source
and candidate package hashes unchanged; neither is saved.

Zeroing the custom highlight parameters also retains white patches. A fresh
four-view repeat verifies material identity and parameter values at the instant
of capture, ruling out an overwritten proof before rendering. Those parameters
do not establish removal of physical hair specular shading. A read-only graph
inspection records 25 material/function graphs and unchanged hashes for four
compact atlases: sRGB is false, compression is Masks. Both SDK master atlas
samples use Color. Four transient-master sampler trials replace just those two
samplers with Masks and exact current atlases, preserve effective appearance
parameters, and verify assigned materials at capture. White patches remain;
that change is rejected and unsaved too. SDK master/source/candidate hashes
stay unchanged. Evidence is in CrowdHairGraph_20260930 and the G1PartsHair*
diagnostic folders. Full hair shading/coverage and live GPU review remain open.

The remaining work includes resolving the gallery presentation/pose findings, complete-outfit
candidates, G2–G5 candidates, all 32 appearances and animation transitions,
live actor/instanced/all-LOD review, source-preserving integration, sleeve
shading, crowd spacing, actual native exit diagnosis, fresh package/cook and
**30 FPS minimum / 60 FPS target** measurement. The full demo goal remains active.

## G2 saved family and missing garment

G2PartsRetargeted saves six appearance clones and its collection. A fresh reload
matches their selections, parameter fingerprints, head bindings and assembled
geometry/materials. It passes 92 pose comparisons and ten metadata comparisons;
maximum position/rotation errors are 0.0155451 cm / 0.0487164 degrees. Four expected
comparisons are absent because Kabir's selected shirt has no assembled mesh. This
is a fidelity failure despite the saved-geometry agreement, and the family remains
outside the live crowd configuration.

The first reload rejects a duplicated nonempty imported moustache material-slot
name. Engine SkeletalMesh PostLoad calls MeshUtilities FixupMaterialSlotNames:
missing imported names are filled and duplicates receive a numeric suffix. The
verifier now reproduces only that exact name rule and records the normalization;
all material paths, section bindings and geometry remain strictly compared. The
failed original report is preserved as ReloadBeforeImportedSlotNormalization.json.

Twenty-four idle/walk front/back images from the saved project actor were captured.
All six front idle views and all twelve walk views were inspected as contact sheets;
Kabir's front idle view was also inspected at full size. His crew-neck shirt and
torso/arms are absent, while his alternate top renders. Read-only source assembly
already omits the same selected shirt. Its clothing pipeline CompatibleBodies is
empty, ruling out a restricted body list as the explanation. The build reports
requested LODs 1/2 unavailable in a one-LOD garment bundle. Evidence:
G2SelectedClothingSource_20260930, G2PartsSavedActorIdle_20260930 and
G2PartsSavedActorWalk_20260930.

A fresh G2PartsRetargetedLOD0 candidate now diagnoses that source-LOD mismatch.
Only the candidate actor/instanced body settings select source LOD 0; the original
collection and wardrobe assets remain unchanged. Its builder requires every
selected garment to produce a component and compares original loaded LOD settings
before/after. It is a diagnostic, with higher geometry cost and no performance or
visual acceptance yet. The original G2 candidate is preserved.

Exact per-input hair graph inspection also resolves a misleading SDK helper result:
the salt-and-pepper function feeds WhiteColorValue into the melanin lerp's B input
and WhiteColorCoverage into Alpha. They are different output indices. No wiring
patch is justified. Recorded reversed smoothstep bounds use max=min-0.05; this
also prevents inferring a white-coverage fault from WhiteAmount=0 alone. Four
physical-specular-show-flag captures retain the white patches. Hair remains open.

The pending reference-pose review is complete. Kabir's front/back captures in
the unanimated reference pose (G2PartsLOD0ReferenceFit_20260930) show the same
skin breaking through the crew-neck shirt across the chest, abdomen, shoulders
and upper back. The fault therefore exists at rest and is not caused by
retargeting or sampled conversion. The next suspects are garment fit to this
body at source LOD 0 and absent hidden-surface removal under the shirt. The
record is G2PartsRetargetedLOD0/ReferencePoseReview.json; no assets were saved
and the live configuration is unchanged.
