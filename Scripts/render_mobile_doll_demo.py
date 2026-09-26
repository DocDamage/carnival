"""Render a labeled review sequence with a floor to reveal real foot contact."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(r"F:\3D Characters\Metahuman Downloads\Possessed Doll\Rigged_Mobile")
QA = Path(r"F:\Carnival\Saved\HauntedDollMobile")
FRAMES = QA / "DemoFrames"
FRAMES.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT / "Possessed_Doll_Mobile_Rig.blend"))
bpy.ops.object.mode_set(mode="OBJECT")
scene = bpy.context.scene
rig = bpy.data.objects["Doll_Mobile_Rig"]
scene.render.resolution_x = 720
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
stage = bpy.data.collections["PREVIEW | Cameras and lighting"]
stage.hide_viewport = False
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, -.001))
floor = bpy.context.object
floor.name = "Preview floor - excluded from exports"
mat = bpy.data.materials.new("Preview floor")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Roughness"].default_value = .85
checker = mat.node_tree.nodes.new("ShaderNodeTexChecker")
checker.inputs["Color1"].default_value = (.063, .073, .08, 1)
checker.inputs["Color2"].default_value = (.085, .097, .105, 1)
checker.inputs["Scale"].default_value = 2
tex = mat.node_tree.nodes.new("ShaderNodeTexCoord")
mat.node_tree.links.new(tex.outputs["Object"], checker.inputs["Vector"])
mat.node_tree.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
floor.data.materials.append(mat)
camera = scene.camera
target = Vector((0, .16, .82))
base_camera = Vector((1.75, -4.5, 1.4))
camera.location = base_camera
camera.rotation_euler = (target - base_camera).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = 1.94
lights = {o: o.location.copy() for o in scene.objects if o.type == "LIGHT"}
manifest = {a["name"]: a for a in json.loads((OUT / "Animation_Manifest.json").read_text())}

# More extreme side/back poses make the body, neck and dress easier to inspect.
for name, frame in [("Doll_Run_Twitchy_InPlace", 7), ("Doll_Run_Twitchy_InPlace", 19),
                    ("Doll_Jumpscare_Lunge", 23), ("Doll_Jumpscare_Lunge", 37)]:
    rig.animation_data.action = bpy.data.actions[name]
    scene.frame_set(frame)
    move = rig.pose.bones["root"].matrix.translation - rig.data.bones["root"].head_local
    for view, location in [("side", (4.5, -.2, 1.3)), ("back", (1.5, 4.5, 1.4))]:
        camera.location = Vector(location) + move
        camera.rotation_euler = (target + move - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(OUT / "Previews" / f"QA_{name}_{frame}_{view}.png")
        bpy.ops.render.render(write_still=True)

shots = [("Doll_Idle_Possessed_Loop", 1, "POSSESSED IDLE"),
         ("Doll_Walk_Twitchy_RootMotion", 2, "STIFF WALK"),
         ("Doll_Run_Twitchy_RootMotion", 4, "TWITCHY RUN"),
         ("Doll_Head_Snap", 1, "HEAD SNAP"),
         ("Doll_Reach_Grab", 1, "REACH / GRAB"),
         ("Doll_Jump_InPlace", 1, "JUMP"),
         ("Doll_Jumpscare_Lunge", 1, "LUNGING JUMP SCARE")]
index = 0
timing = []
for name, repeats, title in shots:
    item = manifest[name]
    rig.animation_data.action = bpy.data.actions[name]
    intervals = item["frames"][1] - 1
    start = index
    for repeat in range(repeats):
        rig.location = Vector(item["root_displacement_m"]) * repeat
        for frame in range(1, intervals + 1):
            scene.frame_set(frame)
            move = rig.location + rig.pose.bones["root"].matrix.translation - rig.data.bones["root"].head_local
            # Follow horizontal travel; retain vertical motion in the picture.
            follow = Vector((move.x, move.y, 0))
            camera.location = base_camera + follow
            camera.rotation_euler = (target - base_camera).to_track_quat("-Z", "Y").to_euler()
            for light, location in lights.items():
                light.location = location + follow
            scene.render.filepath = str(FRAMES / f"frame_{index:04d}.png")
            bpy.ops.render.render(write_still=True)
            index += 1
    timing.append({"animation": name, "title": title, "first_frame": start, "last_frame": index - 1})
    print("SHOT_COMPLETE", name, index, flush=True)
(QA / "Demo_Timing.json").write_text(json.dumps({"fps": 30, "frames": index, "shots": timing}, indent=2))
print("MOBILE_DEMO_RENDER_COMPLETE", index, flush=True)
