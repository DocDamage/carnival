# Third-party assets: buy before rebuilding

This repository contains only the project's own code, scripts, configuration and a small set of authored assets under `Content/Carnival/`. **Every environment, character, clothing, hair, animation and audio pack the game uses is a paid or licensed third-party asset.** They are not in this repository, and they must not be redistributed.

To rebuild the project, buy (or claim, for listings the seller offers at no charge) your own copy of every pack below from its store, under your own account. Then install each one at the `Content/` path shown. Unreal references assets by path, so a pack in the wrong folder shows up as missing references.

Listing links were taken from the original owner's Fab library on 2026-10-01. Prices and availability may have changed since. Where the exact listing could not be confirmed, the row says so and links a store search.

## How to rebuild

1. Install Unreal Engine 5.8 and clone this repository.
2. Buy every pack in the tables below.
3. For Fab packs sold in Unreal format, use **Add to Project** in the Epic Games Launcher or Fab plugin, targeting this project. Confirm each pack lands at its `Content/` path.
4. Some packs are delivered as a separate Unreal project, an FBX set or a Unity package. Place the download in `Assets/` (ignored by Git), then run the matching `Scripts/import_*.py` script with `py -3 Scripts/run_doll_tool.py unreal Scripts/<script>.py`. The relevant script is named in the table.
5. Open the project. The authored levels under `Content/Carnival/World/Levels/` and `Content/__ExternalActors__/` are also ignored by Git. They are rebuilt by the `author_*` and `connect_*` scripts in `Scripts/`, in the order given in `Docs/DEVELOPMENT_HANDOFF.md`.

## Environments and levels

| Content path | Pack | Seller | Store |
|---|---|---|---|
| `Content/Creepwood_Carnival_Meshingun/` | THE CARNIVAL – Theme Park / Amusement Park | Meshingun Studio | [Fab](https://www.fab.com/listings/bea613ad-f75f-4efb-a68a-6655a82e845e) |
| `Content/Hospital_Meshingun/` | Apocalyptic Hospital | Meshingun Studio | [Fab](https://www.fab.com/listings/84e5ee9c-1b14-4cd3-b4c3-731117221e1c) |
| `Content/LightHouse_Meshingun/` | THE LIGHTHOUSE | Meshingun Studio | [Fab](https://www.fab.com/listings/c2c1fb86-ca62-414a-99e5-6d057f4eba83) |
| `Content/Mansion/` | Modular Haunted Mansion | Hivemind | [Fab](https://www.fab.com/listings/434c503b-cd0e-4efb-abc9-347b5ae41b3d) |
| `Content/IndustrialSlums/` | Modular Street (Industrial Slums) | Hivemind | [Fab](https://www.fab.com/listings/4caf4582-f2f2-4fdc-914d-da26b6e66d9b) |
| `Content/Sewer/` | Modular Sewers & Tunnels | Hivemind | [Fab](https://www.fab.com/listings/df316c19-ce3b-443e-8172-f32662f1b34d) |
| `Content/Town/` | Modular Town | Hivemind | [Fab](https://www.fab.com/listings/27739a61-d46d-4bd9-826a-1005c8dbd30b) |
| `Content/Medieval_Castle/` | Castle Forge: Modular Medieval Castle | Hivemind | [Fab](https://www.fab.com/listings/8b55ff8e-9d1c-43d8-9078-6aa03a4ffcd7) |
| `Content/Gladiator_Arena/` | Modular Gladiator Arena (also the source of the seated ride-rider animations) | Hivemind | [Fab](https://www.fab.com/listings/13f7220f-0865-4cac-b80e-d1259c8a8683) |
| `Content/SmokePack/` | Smoke & Fog VFX | Hivemind | [Fab](https://www.fab.com/listings/bc9691f9-1ed3-49ff-babe-f241262d9072) |
| `Content/Docks/` | DOCKS VOL.2 – Powell Dock | Dekogon Studios | [Fab](https://www.fab.com/listings/c1d714a2-288f-4bfa-a820-ec0406d51c8a) |
| `Content/SciFiWorld/` | Sci-Fi Creatures Research Lab | Tirgames Assets | [Fab](https://www.fab.com/listings/c2494db5-55d2-4e35-9c57-540d0f2cf455) |
| `Content/HAUNTED_PRISON/` | Haunted Prison Environment (Exterior + Interior, Modular) | Leartes Studios | [Fab](https://www.fab.com/listings/a1b5f498-83dc-4bec-a0d8-e5f01fafc9cb) |
| `Content/UnderwaterShip/` | Underwater Sunken Ship Environment | Leartes Studios | [Fab](https://www.fab.com/listings/a8085275-4f89-43d5-a188-bf3b9366d488) |
| `Content/RailBridge/`, `Content/StarterContent/` | Coastal Wetland & Railroad Bridge. Import with `import_coastal_bridge.py`, which expects `Assets/CoastalBridge.zip`. | Switchboard Studios | [Fab](https://www.fab.com/listings/69fc3ec8-aefd-4313-9e54-f7f1a21b2d72) |
| `Content/Atlantis_Ruins/` | Atlantis Ruins / 37 Assets (Unity package). Import with `import_atlantis_ruins_fbx.py`. | PackDev | [Fab](https://www.fab.com/listings/7daaf336-d19a-4510-8151-92818bb48cf6) |
| `Content/Mars_Futuristic_Cars/` | Drivable Mars Rover Cars | Galactica Studio | [Fab](https://www.fab.com/listings/8654959d-2505-4a6b-a3f2-8564fc10852e) |

## Props, wall art and audio

| Content path | Pack | Seller | Store |
|---|---|---|---|
| `Content/HorrorPaintVol48/` | Horror Faces Paintings Pack Vol.48 | Ghostbe Studio | [Fab](https://www.fab.com/listings/74a50a19-7e53-4320-a981-fa1c6a8c66ec) |
| `Content/Carnival/WorldExpansion/WallArt/GothicPaintings/` | Medieval Furniture Props (Gothic Props). Import with `import_gothic_wall_art.py`. | Hivemind | [Fab](https://www.fab.com/listings/aa584fda-82a3-4f6f-8675-e2f8fab14daf) |
| `Content/Carnival/WorldExpansion/IndustrialSwitchboard/` | Modular Industrial Electrical Switchboard. Import with `import_world_expansion_switchboard.py`. | readmftah517 | [Sketchfab](https://sketchfab.com/3d-models/modular-industrial-electrical-switchboard-31b3fa1beafd42a6ba73a83631bc38de) |
| Zoltar fortune machine (`import_carnival_zoltar_and_inspect_world.py`) | Zoltar Machine | Ironplot | [Fab](https://www.fab.com/listings/331b8a9b-a95a-49e1-8296-ce2418146241) |
| `Content/Carnival/Audio/IndustrialHospital/` | Abandoned Toy Factory – creepy horror BGM pack (`Assets/Abandoned Toy Factory.zip`) | zonezonezonebgm | [itch.io](https://zonezonezonebgm.itch.io/abandoned-toy-factory-creepy-horror-bgm-pack-loopable-game-music) |
| Hospital exterior facade (`author_industrial_hospital_facade.py`) | High facade of the factory with exit gates. The exact store page was not confirmed; the model appears in archiwum_xyz's collection. | archiwum_xyz | [Sketchfab collection](https://sketchfab.com/archiwum_xyz/collections/fasades-4ad09790b9fd43cd89b55f66fc4bcc9f) |

## Animation

| Content path | Pack | Seller | Store |
|---|---|---|---|
| `Content/FreeAnimationLibrary/` | Free Animation Library | voxel vision | [Fab](https://www.fab.com/listings/481ef75b-892b-424f-a213-f1cc058c9c19) |
| `Content/RamsterZ_FreeAnims_Volume1/` | RamsterZ Free Anims Volume 1 (also used by the doll) | RamsterZ | [Fab](https://www.fab.com/listings/9319491d-0e91-422c-9b67-ad4bf6c01a02) |
| `Content/PlayMusicAnim/` | Play Music Anim | Jane Gintsar | [Fab](https://www.fab.com/listings/882e0631-74f5-4bb6-b44f-e40a202454fc) |
| `Content/Carnival/Character/Animations/Swim/` | Swimming Animation Pack (retargeted). The listing match is by pack name and content; confirm before buying. | — | [Fab](https://www.fab.com/listings/e57a16c3-26ff-48e3-afd9-12c53d8ba1f3) |
| Motorcycle mount animations | Motorcycle Interaction Animset | SpectraMotions | [Fab](https://www.fab.com/listings/995ce0ad-f8bc-4878-928b-a4a53d5c914c) |
| `Content/Carnival/Vehicles/Motorcycle/` (`import_motorcycle_mesh.py`, `import_motorcycle_assembly.py`) | Post Apocalyptic Motorcycle – Rigged Off Road Enduro Bike | RetroStyle Games | [Fab](https://www.fab.com/listings/2ba45f8e-de1d-40c0-b306-3d68839f3d32) |

## Characters, crowd, clothing and hair

| Content path | Pack | Seller | Store |
|---|---|---|---|
| `Content/Carnival/Crowd/` | Built from Epic's MetaHuman Crowd Sample plus the outfits and grooms below | Epic Games | [Fab](https://www.fab.com/listings/5f481d73-afb1-4d94-ba6e-7cabf5d296fa) |
| `Content/Carnival/MetaHumans/` | MetaHuman presets Hannah, Kabir and Mason. Seo, Advika, Dean and Skye were also used; their exact listings weren't recorded, so search Fab's MetaHuman channel by name. | various | [Fab MetaHuman search](https://www.fab.com/search?q=editable%20metahuman) |
| `Content/Outfits/` (most folders), `Content/Fab/MetaHuman/` | MetaHuman clothing: jeans, slim jeans, cargo pants, shorts, sweatpants, yoga pants, T-shirt variants, crop tops, hoodie, sweater, boots, sneakers, running shoes, Chelsea boots, loafers, Oxfords, flats and flip-flops | Epic Games | [Fab MetaHuman clothing](https://www.fab.com/search?q=metahuman%20outfit) |
| `Content/Outfits/Street_Wear_01` and others | Streetwear Parametric Outfit 01 and 12 | Paradoox-Fashion | [Fab 01](https://www.fab.com/listings/5691adb6-a02c-4fe9-b67b-b4b468baf36b), [Fab 12](https://www.fab.com/listings/cb85da0d-4b8e-4ef1-8844-d04a7e02ddad) |
| `Content/Outfits/KhaosMDF503`, `Shirt_01`, `Shirt_04`, `techwearOutfit`, `SleevelessShirt`, `Crew_Neck_T-Shirt`, `ARCJ_SHORTS`, `Casual_F_Outfit`, `Casual_M_Outfit`, `vivi_*` | Individual MetaHuman clothing listings. The exact listings were not recorded; search by folder name. | various | [Fab search](https://www.fab.com/search?q=metahuman%20clothing) |
| `Content/Grooms/Hair_M_UpdoDutchBraid` | MetaHuman Updo Dutch Braid Groom | Epic Games | [Fab](https://www.fab.com/listings/7fabdfc3-a431-4051-b817-72c84da00251) |
| `Content/Grooms/Hair_M_SlickPonytail`, `Hair_M_BantuKnots`, `Hair_M_UpdoCornrows`, `Hair_M_UpdoMessyBun`, `Hair_L_HighPonytail` | MetaHuman Slick Ponytail / Bantu Knots / Updo Cornrows / Updo Messy Bun / Long High Ponytail Grooms | Epic Games | [Fab search](https://www.fab.com/search?q=metahuman%20groom%20epic%20games) |
| `Content/Grooms/Hair_TEKATI_Broccoli_Fade_no2` | MetaHuman Broccoli Fade 2 | studio TEKATI | [Fab search](https://www.fab.com/search?q=broccoli%20fade) |
| `Content/Grooms/Male_ClassicCrewCut`, `NomadWaveUndercut`, `Hair_F_Ponytail_MessyWavy_01`, `Mustache_M_Parted`, `Mustache_S_PencilVeryThin`, `SimpleShair`, `Hair_MyAdvancedGroom` | Classic Crewcut; MHC Nomad Wave Undercut; Ponytail MessyWavy; Parted and Pencil Mustache (BigHair); Simple Hair; MetaHuman Groom Advanced Kit | various | [Fab search](https://www.fab.com/search?q=metahuman%20groom) |
| `Content/Carnival/Characters/Children/` | Rigged 3D Black Boy / Black Girl / White Boy / White Girl Character – Game Animation Ready. The store was not recorded. | unknown | Search the titles on [CGTrader](https://www.cgtrader.com/) or [Fab](https://www.fab.com/) |
| `Content/Carnival/Characters/PossessedDoll/` (`import_haunted_doll.py`) | Possessed doll model (`possessed_doll.glb`). The store was not recorded. Its rig and animation work is reproduced by the scripts in `Scripts/`. | unknown | — |

## Engine-provided content

`Content/StarterContent/` ships with Unreal Engine. The MetaHuman Creator plugin and its base bodies come with Unreal Engine 5.8 through the Epic Games Launcher.

## What is in Git

Only `Content/Carnival/` (minus the ignored subfolders listed in `.gitignore`), `Source/`, `Scripts/`, `Config/`, `Plugins/` and `Docs/` are committed. Everything listed above stays out of the repository.
