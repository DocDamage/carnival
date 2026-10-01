# Crowd body surface diagnosis — September 30, 2026

The actual Dean crowd actor loses most of its hand surfaces when assembled with
the long-sleeve shirt, slim jeans and casual sneakers. The shirt itself is intact
in isolated reference-pose front/back views. Making the original full body
visible restores the hands but introduces skin intersections through clothing;
that candidate is rejected.

The original actor body contains complete hands. A **transient** copy, trimmed
with the three selected source garments' original hidden-face maps and settings,
restores the hands and ankle surfaces without observed skin intersections in the
reference pose and sampled Manny walking/idle poses. No persistent body surface
repair or runtime integration had been made at this stage. A later rebuild now
reproduces the ownership cause and saves an isolated G1 candidate; see the
[clothing family record](CROWD_CLOTHING_FAMILIES.md). Full character, animation,
other appearance, GPU instance, LOD and performance acceptance remain open.

The loaded body has 15,196 triangles. The shirt/jeans/sneaker meshes contain only
208/480/54 appended skin triangles, whereas combining the original garment masks
on the same body preserves 5,433 triangles. The actor's original Body component
is hidden: installed crowd assembly expects the body surface to be carried by
the clothing. These observations support an assembly/distribution loss; they do
did not yet identify its exact algorithmic cause.

Loaded clothing sections have valid effective material remaps, weight sums of
65,535, and no zero weights or out-of-range weighted bones. Original polygon
group IDs differ from material slot indices; the valid remap matters. This is
loaded metadata, including runtime normalization, and does not independently
accept original authored mappings. Source shirt LOD assets are static meshes;
its CombinedSkelMesh is a source character/body reference, not the shirt alone.

Groups 1–5 contain complete outfits alongside separate clothing slots:

| Group | Complete outfits | Tops | Bottoms | Shoes |
| --- | ---: | ---: | ---: | ---: |
| G1 | 2 | 10 | 6 | 6 |
| G2 | 1 | 6 | 3 | 3 |
| G3 | 1 | 5 | 3 | 3 |
| G4 | 1 | 5 | 2 | 2 |
| G5 | 2 | 2 | 2 | 2 |
| G6 | 1 | 0 | 0 | 0 |

`Bottom Garment`, `Top Garment` and `Shoes` resolve to the real `Outfits` slot.
Installed `MetaHumanCrowdBodyMerge.cpp` builds ownership using every slot's items,
then assigns visible geometry to a slot using UV ownership and bone hierarchy.
Competition between complete-outfit and separate-piece compositions is a
**hypothesis** at this stage for unselected items receiving visible body surfaces.
The later isolated rebuild and ownership images reproduce this cause for Dean.
The earlier idea
of an empty first clothing slot is not supported by these collection counts.

In the idle pose, the dark sleeve patch disappears with opaque unlit materials
in both one-sided and two-sided views. Its surface exists; investigate its
shading/material response separately from the missing hands. These studio
renders do not accept the full world's lighting.

Owned editor helpers now describe loaded sections and collection slots, and
build a transient masked body with the exported MetaHuman geometry-removal API.
They do not save assets. Editor build, game target check and **39/39 native tests
with zero warnings/failures/skips** pass. All six collection package hashes and
recorded garment/coverage-map hashes are unchanged. The direct animation probes
show that the current Manny sequences can pose this actor when played directly;
they do not establish Mass animation handover, continuous locomotion or GPU
animation correctness.

Evidence is under `Saved/CharacterRepairs`:

- `DeanOutfitSectionSurvey_20260930`: loaded sections, remaps, weights and source metadata.
- `DeanOutfitIsolation_20260930`: 10 source/shirt/opaque/full-character views.
- `DeanBodyIsolation_20260930`: 6 original body/opaque/full-character views.
- `DeanBodyVisibilityCandidate_20260930`: 4 rejected untrimmed-body views.
- `DeanTrimmedBodyCandidate_20260930`: 6 reference-pose baseline/candidate/body-only views.
- `DeanTrimmedBodyWalkCandidate_20260930`: 4 looping-walk views at differing times.
- `DeanTrimmedBodyWalkPhase1_20260930` and `DeanTrimmedBodyIdlePhase1_20260930`: 4 matched views each at source time 1.0.
- `DeanIdleSleeveSilhouette_20260930`: 4 shaded/two-sided-unlit views.
- `DeanIdleSleeveOneSidedSilhouette_20260930`: 2 one-sided-unlit views; late native exit 3221225477.
- `DeanIdleSleeveOneSidedCleanupRepeat_20260930`: 2 matching views, exit 0 after releasing retained PIE wrappers.
- `CrowdClothingSlotSurvey_20260930`: six saved slot/item/hash audits.
- `CrowdBodySurfaceDiagnosis_20260930`: comparison sheets, aggregate status and native evidence.

Early opaque probes applied BasicShapeMaterial, which lacks skeletal usage and
fell back to Engine DefaultMaterial for skeletal meshes. Those images establish
opaque geometry, not matching photometry. Later probes explicitly use the engine
default or a transient unlit material with skeletal usage.

The one-sided probe captured both images, then exited **0xC0000005** after normal
teardown/log closure. This repeats the earlier late native failure. No new project
crash dump or stack is available; appearance evidence and failed exit are recorded
separately. The cleanup repeat completes both views and exits 0 after releasing
all retained PIE wrappers before end play. Both one-sided views again show a
complete sleeve; this eliminates one-sided backface removal as the explanation
in this sampled pose. The cleanup's relationship to the native failure remains
unproven. The aggregate retains all 46 reviewed views from 10 runs, including
the failed exit. Extended and packaged
stability and the **30 FPS minimum / 60 FPS target** remain unaccepted. The full
demo goal remains active.
