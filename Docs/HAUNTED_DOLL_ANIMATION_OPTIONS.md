# Haunted doll animation options

**Current integration:** The mobile rig and Unreal character now have their own [setup guide](HAUNTED_DOLL_IN_UNREAL.md). The research and seated-rig notes below describe the earlier asset audit.

**Rigging update (2026-09-26):** A separate seated rig is now available at `F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Seated\Possessed_Doll_Seated_Rig.blend`, with FBX/GLB exports, optional hand IK, packed textures, and a short original demonstration action. See the [rig's README](<F:/3D Characters/Metahuman Downloads/Possessed Doll/Rigged_Seated/README.md>). The original GLB described below is still unchanged and unrigged. The user confirmed that the doll can stay seated; locomotion preparation is not part of the delivered rig.

Inspected 2026-09-26. Recommendation: **RamsterZ Creepy Doll** for the seated possessed doll. Suitable commercial animation packs exist, so a complete custom animation library is unnecessary. The supplied model needs a rig before any of these animations can drive it.

## What is in the doll file

Source: `F:\3D Characters\Metahuman Downloads\Possessed Doll\possessed_doll.glb`

- One static mesh; no skeleton, skin weights, morph targets, or animation clips.
- Blender 4.5.5 imported it successfully: 44,250 vertices and 48,687 triangles.
- The model is already seated, with its dress shaped around that pose. It is not an upright humanoid reference pose.
- The apparent eye and mouth details are part of the same mesh, not separate animation controls.
- Being in the MetaHuman Downloads folder does not make this file a MetaHuman character.

![Imported doll, front](F:/Carnival/Saved/HauntedDollAudit/doll_front.png)

The seated shape makes a small custom head/neck/torso/arm rig a sensible starting point. Full walking, running, or crawling needs additional mesh preparation and deformation checks around the legs, hips, dress, shoulders, and hair. Automatic weights alone should not be assumed to produce a finished character.

## Recommended packs

Prices below are the public listings checked on 2026-09-26, before any checkout taxes or license-tier differences. Motion coverage is from the creators' descriptions; these paid packs have not been purchased or tested on this doll.

| Pack | Best use | Source and price |
|---|---|---|
| **Creepy Doll — first choice** | 97 animations, including chair and floor sitting, hunched poses, unsettling idles, hanging, movement, and aggressive reactions. Its seated coverage is especially relevant to this model. | [Creator's raw FBX pack — US$16.99](https://www.ramsterzanimations.com/store-buy/p/creepy-doll-fbx-only); [Unreal package on Fab](https://www.fab.com/listings/252abd9c-ab59-4d66-9b1d-34b7360d68b4); [preview video](https://www.youtube.com/watch?v=LNSNcbNTRt4). |
| **Killer Doll Anims** | Alternative if the character should chase and attack. The listing advertises 75 animations plus six in-place attack updates, along with 30 poses and a character mesh. | [Fab product](https://www.fab.com/listings/7ec6aa5b-6e6b-46f2-82c4-e2abb3fbe372); [preview video](https://www.youtube.com/watch?v=P4EDSajYYug). |
| **Crawling Ghoul Anims — optional** | Add only if floor crawling is part of the design. Includes directional crawling and leaping creature movement; this doll's seated mesh would need more preparation. | [Creator's raw FBX pack — US$17.99](https://www.ramsterzanimations.com/store-buy/p/crawling-ghoul-fbx-only). |

The creator's Creepy Doll FBXs use the UE4 Mannequin skeleton and support root motion. They still need retargeting onto a newly rigged doll. The raw FBX purchase and the Fab Unreal package are different delivery options; purchase one appropriate version, not both by default. Neither supplies the gameplay behavior for this character.

## Free pack downloaded

Downloaded from [RamsterZ's official free downloads page](https://www.ramsterzanimations.com/free-stuff): **Free Grim Anims**.

Local folder: `F:\3D Characters\Metahuman Downloads\Animations\RamsterZ_FreeGrimAnims`

- Archive: `RamsterZ_FreeGrimAnims.zip`; extracted files: `Extracted\`.
- Archive integrity checked successfully: 18 motion FBXs, two prop FBXs, and a T-pose FBX.
- Mostly hanging/death poses, with two jump-scare fall variants. This is useful supplementary material, not a complete idle/walk/run doll set.
- Relevant candidates include `Death_HangingByHip01_JumpScareFall.fbx`, `Death_HangingByHip02_JumpScareFall.fbx`, and the hanging-by-feet variations.
- Source and license links are recorded in `SOURCE.txt`; the creator's [license](https://www.ramsterzanimations.com/end-user-license-agreement) applies.
- Downloaded and extracted only; not retargeted, visually validated in motion, or imported into Carnival.

Archive SHA-256: `60b3fb07caf4d4f14b3b3d4d15d758ddbe6b4609812a5f4f9766e41697c7ddd5`.

## Existing downloads worth reusing

The three Motifect packs contain **115 FBXs**: 40 Daily Life, 30 Emotes & Social, and 45 Locomotion. Their documentation says the included meshes are stickman previews and retargeting is required for a different character rig. These are filename-based candidates, not a claim that their performances have been reviewed:

| Motion need | Existing clip candidates |
|---|---|
| Sitting and waking up | `sit_idle_slouched`, `sit_idle_upright`, `sit_down_chair`, `stand_up_from_chair` |
| Slow approach | `walk_cautious`, `walk_tired`, `tiptoe_walk` |
| Floor movement | `crawl_forward`, `army_crawl` |
| Unsettling gestures | `taunt_come_here`, `point_at_opponent`, `laugh_body`, `slump_defeated` |
| Basic locomotion | `walk_forward`, `run_jog`, `turn_left_90`, `turn_right_90` |

Other new folders contain native Unreal content: `FreeAnimationSet`, `FreeLadderAnimationSet`, and `ParkLifeAnims`. ParkLife has bench, food, walking, and social activities relevant to carnival guests. These files have not been newly imported by this task.

All four child-character folders contain Blender, FBX, and texture ZIPs. Three also contain an Unreal project ZIP; the Black Boy folder does not currently contain one. Archive filenames were inspected, but their skeletons and MetaHuman compatibility have not been verified. They should not be treated as sharing a skeleton merely because the folders describe them as rigged.

## Practical integration sequence

1. Preserve the supplied GLB and create a separate rigged Blender version. Start with seated movement; inspect the underlying leg/dress geometry before committing to locomotion.
2. Add and weight the doll's skeleton. Include controllable head, neck, spine, shoulders, arms, and hands; add the full pelvis/leg/foot chains if locomotion is needed. Keep the porcelain head appropriately rigid and check hair/neck deformation.
3. Import the doll as its own skeletal mesh and skeleton. Import purchased or existing animations on their actual source skeletons.
4. Create source and doll IK rigs, map limb chains, and match reference poses. A purchased animation cannot be assigned directly to the current static GLB. Epic documents the workflow in [IK Rig Retargeting](https://dev.epicgames.com/documentation/en-us/unreal-engine/ik-rig-animation-retargeting-in-unreal-engine).
5. First validate a seated idle and a head/arm motion on the doll. Then test standing and a short walk, checking feet, knees, dress intersections, root motion, and scale before batch retargeting.
6. Add custom animation only for missing signature scares: prolonged stillness followed by a head snap, asymmetric hand twitch, slow head tracking, rocking, and a sudden seated reach. This is a proposed animation brief, not completed clips.

## Files produced by this inspection

- This report.
- `Saved/HauntedDollAudit/doll_audit.json`: measured Blender mesh and rig inventory.
- `Saved/HauntedDollAudit/doll_front.png`, `doll_back.png`, `doll_side.png`: renders of the actual supplied GLB.
- `Saved/HauntedDollAudit/inspect_doll.py` and `blender_audit.log`: reproducible inspection and render log.
- The free source archive and extracted FBXs in the external Animations folder above.

No rig, custom motion clips, paid assets, or Unreal gameplay changes were created during this sourcing pass.

## Subsequent mobile-rig delivery — 2026-09-26

After the sourcing pass and seated-rig delivery, a separate mobile version was created at `F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile` in the user's selected stiff, twitchy style. The original upper body and shoes are retained, the skirt is reshaped, and new porcelain legs are rigged under it.

The folder contains the editable Blender rig, a skeletal FBX and GLB, nine baked FBX clips (idle, in-place/root-motion walk and run, jump, lunging jump scare, head snap and reach), textures, a video preview, usage notes, validation reports and a portable ZIP. The animation exports pass re-import/deformation checks in Blender. The source model and seated deliverables are preserved. Unreal import and gameplay integration remain untested.

See `Rigged_Mobile/README.md` for clip lengths, movement speeds, rig controls and material setup. The paid/free source recommendations above describe the earlier research; these new clips were custom authored on the doll's skeleton.
