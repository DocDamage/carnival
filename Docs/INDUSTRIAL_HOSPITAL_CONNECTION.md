# Industrial slums and hospital branch

Updated 2026-09-27. This note covers the branch leaving the Carnival from the gate opposite the mansion-side route. See [DEVELOPMENT_HANDOFF.md](DEVELOPMENT_HANDOFF.md) for the wider project state and older ride work.

## Layout

The route starts at the opposite-side Carnival gate at `(7093.926, 6841.718, 42.781)` cm, runs through a selected and cropped industrial slum block, and reaches the front door of the fully explorable abandoned hospital. The supplied industrial factory facade forms the hospital's front gate/forecourt.

| Segment | Approximate distance from Carnival gate | Notes |
|---|---:|---|
| Carnival gate | 0 m | Opposite side from the mansion route |
| Industrial slums | 600–760 m | Cropped source district with a dedicated road connection |
| Hospital approach | 760–1,510 m | Industrial road, audio cues, and progressively denser local fog |
| Hospital entrance | 1,510 m | Road endpoint is aligned to the hospital's source entrance door |

The spline/chunk layout totals about **1,536 m**. The config estimates about **5:41 on foot** at 4.5 m/s and **4:00 on a cautious motorcycle** at 6.4 m/s. Those estimates come from authoring constants; neither speed has been measured in a gameplay traversal. The built road lane is 9 m wide. Road collision was set to complex-as-simple, but still needs a runtime collision check.

Weather keeps the Carnival's night-snow environment. Five local fog volumes increase in density and size toward the hospital. The local snow-flare particles are omitted: the effect referenced a missing Village vector field and generated excessive bloom. The branch has six looping spatial audio cues, three outdoors and three inside the hospital, sourced from the user's toy-factory audio archive.

## Connected levels

The persistent map is `/Game/Creepwood_Carnival_Meshingun/Environment/Map/LV_Carnival`. It references these nine branch levels as always-loaded sublevels:

1. `/Game/Carnival/World/Levels/L_IndustrialHospitalRoute`
2. `/Game/Carnival/World/Levels/L_IndustrialSlums_DistrictFinal`
3. `/Game/Carnival/World/Levels/L_IndustrialHospitalExterior`
4. `/Game/Carnival/World/Levels/L_IndustrialHospitalInteriorArchitecture`
5. `/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_SetDress`
6. `/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Main_Decal`
7. `/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_VFX`
8. `/Game/Hospital_Meshingun/Environment/Map/LV_Hospital_Volume`
9. `/Game/Carnival/World/Levels/L_IndustrialHospitalInteriorLights`

The branch deliberately omits the source hospital's global atmosphere and directional light so it inherits the Carnival's night environment. The original hospital interior architecture and dressing are retained. The entrance door reference is source-local `(5000, -1750, 80)` cm and is aligned to the final road point.

## Source assets and Git policy

The source archives and purchased/licensed packs are local inputs. Do not commit or redistribute them. The audio archive is `F:\Carnival\Assets\Abandoned Toy Factory.zip`; extracted/imported Unreal sounds are under `Content/Carnival/Audio/IndustrialHospital/`. The facade source is `F:\Carnival\Assets\High facade of the factory with exit gates`. The imported hospital and cropped slum content stay under their existing ignored source-pack directories. The authored connected layouts under `Content/Carnival/World/Levels/` are also ignored, consistent with the existing project policy for maps that depend on local packs. Reproducible authoring scripts are under `Scripts/`.

## Authoring scripts

The scripts operate on the supplied local assets and existing source maps. Run one Unreal command at a time through `Scripts/run_doll_tool.py`'s Unreal mode. The intended sequence is:

1. Extract/import the selected source assets: `prepare_industrial_hospital_sources.py`, `import_industrial_hospital_assets.py`.
2. Build the slum patch: `sample_industrial_slums_terrain.py`, `build_industrial_slums_terrain_mesh.py`, `prepare_industrial_slums_district.py`, `finalize_industrial_slums_district.py`.
3. Build and import the route chunks: `build_industrial_hospital_route_meshes.py`, `import_industrial_hospital_route_assets.py`.
4. Prepare the copied hospital interior: `prepare_hospital_interior_architecture.py`, `prepare_hospital_interior_lights.py`.
5. Author the branch maps and connect them: `author_industrial_hospital_route.py`, `author_industrial_hospital_facade.py`, `connect_industrial_hospital_world.py`.
6. Capture an editor preview with `capture_industrial_hospital_connected.py`.

`Scripts/industrial_hospital_route_config.py` holds the gate, road control points, crop, hospital door alignment, and transforms. The scripts are intended to be idempotent for their generated levels. The connector replaces only the nine branch level references and backs up the root `.umap` before saving it. Reports and the backup are under `Saved/IndustrialHospital/`; generated content in `Saved/` is ignored by Git.

## Current verification and next steps

`Saved/IndustrialHospital/World_Connection.json` reports a completed connection and records the root-map backup/hash. `Saved/IndustrialHospital/Industrial_Hospital_Authoring.json` reports the 1,536 m road, seven imported road meshes, six audio cues, and five fog cells. The connected capture loaded all expected branch levels and returned no errors.

Visual acceptance is pending: the latest connected previews are washed out in the slum, hospital approach, and interior shots. Resolve exposure and fog presentation in the editor while preserving the Carnival's night setting. PIE has not verified walking/motorcycle traversal, collisions, door access, or the complete hospital interior. Validate those before treating the branch as playable or the estimated route times as confirmed.

Preview files:

- [Carnival exit](../Saved/IndustrialHospital/Previews/Connected/01_Carnival_Exit.png)
- [Industrial slums](../Saved/IndustrialHospital/Previews/Connected/02_Industrial_Slums.png)
- [Hospital approach](../Saved/IndustrialHospital/Previews/Connected/03_Hospital_Approach.png)
- [Hospital entrance interior](../Saved/IndustrialHospital/Previews/Connected/04_Hospital_Entrance_Interior.png)
