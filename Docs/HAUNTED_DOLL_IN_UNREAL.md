# Possessed doll in Carnival

The mobile doll is a separate, reusable Unreal character. Her original static GLB, seated rig, mobile authoring rig, and source animation packs remain available in the downloads folder.

## Open and play

In the Content Browser, open `/Game/Carnival/Characters/PossessedDoll/Maps/L_DollTest` and press **Play**. The player starts facing the doll. Stay in front of her to see the head snap, stiff walk, run, and proximity scare. Move away to escape; she loses interest when sight is blocked, stops at her chase boundary, and returns after the encounter.

The reusable actor is `BP_PossessedDoll` in `/Game/Carnival/Characters/PossessedDoll`. Drag it into a level and keep the capsule above a solid floor. It uses the game's existing player and does not deal damage. The **On Scare** event is available for camera effects, damage, or other game-specific responses.

One instance, **PossessedDoll_HauntedHouse**, is already placed beside the haunted-house queue in `LV_Carnival`, at approximately **X 8000, Y 4950, Z 178**. It is in the World Outliner folder **Carnival / Haunted Doll**. A copy of the map from before this placement is saved at `Saved/HauntedDollIntegration/Backups/LV_Carnival.before_doll.umap`.

## Assets

| Asset/folder | Contents |
|---|---|
| `SK_Doll` and `SK_Doll_Skeleton` | 26 deform bones, centimeter scale, +X forward, floor-level animated root |
| `Materials` | Original doll textures and porcelain leg material |
| `Animations/Original` | Nine original clips: possessed idle; walk and run in place and with root motion; head snap; reach/grab; jump; scare lunge |
| `Animations/FreeGrim` | 18 existing RamsterZ retargets imported onto the same skeleton |
| `Animations/RamsterZ_Volume1` | Standing idle, stealth idle, and two dramatic gestures from the newly added native Unreal pack |
| `Retarget/IK_PossessedDoll` | Doll body chain definitions |
| `Retarget/IK_RamsterZ_UE4` | RamsterZ UE4 mannequin chain definitions |
| `Retarget/RTG_RamsterZ_To_Doll` | Saved pose alignment and proportional body retargeting |

The Free Grim hanging/fall clips are supplementary scene actions. Their hanging anchors and any required props must be placed for the shot. They are not part of the walking encounter. Paired and weapon motions in the original Volume 1 pack remain on their source skeleton until explicitly retargeted and staged.

## Tuning and extra actions

Select a placed doll and use the **Doll** sections of the Details panel:

- **Detection:** 850 cm range, 70-degree half-angle, visibility trace; 2.5 seconds to lose sight.
- **Movement:** 27.22 cm/s walk, 101.19 cm/s run, a 2-second approach before chasing, 1500 cm chase boundary.
- **Scare:** 130 cm trigger distance, 8-second cooldown, existing haunted-house laugh at 65% volume with distance attenuation.
- **Animations:** replace the assigned clips with animations retargeted to `SK_Doll_Skeleton`.

`Play Doll Action(Animation)` plays an extra same-skeleton sequence. The assigned **Jump Animation** uses its vertical root motion to move the capsule, then resumes falling/ground movement. `Reset Encounter` ends an action and sends her home. `Encounter Enabled` controls automatic player detection. Animation blending is handled by the native `CarnivalDollAnimInstance` controller.

Walking uses in-place clips with Character Movement. The lunge and jump use extracted root motion so their collision capsule follows the animation. Navigation is used when available; maps without navigation use collision-swept direct movement, with a stuck timeout and safe reset.

## Adding another pack

1. Import it on its own source skeleton first.
2. For a matching UE4 mannequin source, open `RTG_RamsterZ_To_Doll`, select the source animation, and preview it on `SK_Doll`.
3. Export the retargeted copy into a new doll animation folder. Assign that copy to the doll or pass it to `Play Doll Action`.
4. For another skeleton, create an appropriate source IK Rig and duplicate the retargeter before changing its source rig.

This is a custom doll skeleton, not the MetaHuman skeleton. Body motion can be retargeted; the mesh has no individual finger or facial bones. The saved retargeter transfers body chains with FK. Contact-heavy actions can require foot/hand IK and pose cleanup. The six dress bones are animated in the original clips; new packs may need dress cleanup for large kicks, crouches, or floor poses.

## Rebuilding

The scripts in `F:\Carnival\Scripts` preserve the source files and write doll assets under the dedicated Content folder:

1. `prepare_doll_unreal_fbx.py` prepares exports from the existing retargeted Blender file and performs mesh roundtrip comparisons.
2. `import_haunted_doll.py` imports the mesh, dependencies, textures, and 27 FBX clips.
3. `retarget_doll_ramsterz_unreal.py` builds the reusable retarget assets and four Volume 1 examples.
4. `setup_haunted_doll_encounter.py` creates the Blueprint and test map.
5. `place_haunted_doll_carnival.py` checks floor/capsule clearance and places the Carnival encounter, retaining a map backup.

Run Unreal scripts with `python Scripts/run_doll_tool.py unreal Scripts/<script>.py`. Run the build with `python Scripts/run_doll_tool.py build`. Run the automated encounter check with `python Scripts/run_doll_tool.py test`.

`python Scripts/run_doll_tool.py playtest Scripts/test_haunted_doll_in_carnival.py` runs the separate Carnival Play in Editor check. `python Scripts/run_doll_tool.py editor Scripts/capture_doll_viewport.py` renders the preview poses without saving changes to the test map.

The centimeter authoring copy and prepared FBXs are in `F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile\Unreal_Integration`. Logs and validation reports are in `F:\Carnival\Saved\HauntedDollIntegration`.

## Verification — September 26, 2026

- Unreal 5.8.2 editor build passed. A few existing duplicate lines in the HUD, motorcycle, and mounted-attack code were removed to unblock compilation.
- All 27 FBX clips passed Blender mesh roundtrip checks; maximum sampled difference was 1.01 mm.
- All 31 Unreal clips loaded with the doll skeleton. Five poses per clip were checked for finite transforms and correct scale: 155 sampled poses.
- `Carnival.HauntedDoll.Encounter` passed without warnings. It checks real capsule movement, detection range/cone, a visibility wall, animation changes, walk/run/scare/cooldown/return, repeat activation, jumping, and playing a RamsterZ clip. Measured run speed: 101.19 cm/s; lunge: 52.00 cm; scare hop: 21.86 cm; jump: 27.93 cm.
- A separate Play in Editor run in **LV_Carnival**, using **BP_CarnivalPlayerCharacter_C**, completed the full encounter and returned to idle after one scare. The floor, capsule, and initial approach path also passed clearance traces. Audio was disabled in the automated runs; sound and attenuation are configured for normal play.

Evidence: `Saved/HauntedDollIntegration/Automation/index.json`, `Final_Asset_Validation.json`, `Carnival_Placement.json`, and `Carnival_Playtest.json`. The preview images are rendered in Unreal and saved in the adjacent `Previews` folder.
