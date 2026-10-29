"""미리보기용 무대: 바닥·벽 모서리, 낮/밤 조명, 아이소메트릭 카메라, 렌더 설정."""
import math

import bpy
from mathutils import Euler, Vector

from lib import box, collection, mat, node_mat

THEMES = {
    "day": {
        "world": (0.80, 0.78, 0.74), "world_strength": 0.55,
        "sun": 3.2, "sun_color": (1.0, 0.90, 0.76),
        "fill": 450.0, "fill_color": (1.0, 0.95, 0.88),
        "lamp": 0.0, "window": 0.0, "led_boost": 1.0, "interior": 0.0, "bloom": False,
    },
    "night": {
        "world": (0.012, 0.018, 0.040), "world_strength": 0.35,
        "sun": 0.0, "sun_color": (1.0, 1.0, 1.0),
        "fill": 0.0, "fill_color": (1.0, 1.0, 1.0),
        "lamp": 14.0, "window": 22.0, "led_boost": 3.0, "interior": 12.0, "bloom": True,
    },
}


def wood_floor():
    m = node_mat("floor_wood")
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.55
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.squash_frequency = 1
    brick.inputs["Color1"].default_value = (0.42, 0.25, 0.13, 1)
    brick.inputs["Color2"].default_value = (0.55, 0.34, 0.18, 1)
    brick.inputs["Mortar"].default_value = (0.20, 0.11, 0.06, 1)
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.004
    brick.inputs["Brick Width"].default_value = 0.9
    brick.inputs["Row Height"].default_value = 0.15
    noise = nt.nodes.new("ShaderNodeTexWave")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Distortion"].default_value = 6.0
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.18
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return m


def room():
    col = collection("stage")
    wall = mat("wall_cream", (0.86, 0.81, 0.72), rough=0.85)
    trim = mat("trim_wood", (0.50, 0.32, 0.17), rough=0.5)
    box("floor", (3.0, 3.0, 0.06), (0, 0, -0.03), wood_floor(), bevel=0.01, col=col)
    box("wall_back", (3.0, 0.08, 2.0), (0, 0.85, 1.0), wall, bevel=0.01, col=col)
    box("wall_left", (0.08, 3.0, 2.0), (-1.1, 0, 1.0), wall, bevel=0.01, col=col)
    box("skirting_back", (3.0, 0.02, 0.08), (0, 0.80, 0.04), trim, bevel=0.004, col=col)
    box("skirting_left", (0.02, 3.0, 0.08), (-1.05, 0, 0.04), trim, bevel=0.004, col=col)


def lights(theme):
    t = THEMES[theme]
    world = bpy.data.worlds.new("world")
    bpy.context.scene.world = world
    try:
        world.use_nodes = True
    except AttributeError:
        pass
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*t["world"], 1)
    bg.inputs["Strength"].default_value = t["world_strength"]

    def add(name, kind, loc, rot, energy, color, **kw):
        if energy <= 0:
            return None
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        for k, v in kw.items():
            setattr(ld, k, v)
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        ob.rotation_euler = Euler([math.radians(a) for a in rot])
        bpy.context.scene.collection.objects.link(ob)
        return ob

    add("sun", "SUN", (0, 0, 5), (48, 0, 32), t["sun"], t["sun_color"], angle=math.radians(6))
    add("fill", "AREA", (2.2, -2.4, 2.6), (55, 0, 42), t["fill"], t["fill_color"], size=2.5)
    # 밤: 따뜻한 벽등과 창가의 차가운 달빛
    add("lamp", "POINT", (-0.7, 0.55, 1.65), (0, 0, 0), t["lamp"], (1.0, 0.70, 0.42), shadow_soft_size=0.15)
    add("window", "AREA", (-0.2, -2.0, 2.2), (60, 0, -10), t["window"], (0.55, 0.65, 1.0), size=2.0)


def camera(target=(0.0, 0.0, 0.72), ortho_scale=2.1, tilt=58, yaw=34):
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = ortho_scale
    ob = bpy.data.objects.new("cam", cd)
    rot = Euler((math.radians(tilt), 0, math.radians(yaw)))
    ob.rotation_euler = rot
    ob.location = Vector(target) + rot.to_matrix() @ Vector((0, 0, 8))
    cd.clip_end = 30
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob


def render_settings(res, samples, res_y=None):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.render.resolution_x = res
    sc.render.resolution_y = res_y or res
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "ONEAPI"
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == "ONEAPI"]
        for d in prefs.devices:
            d.use = d.type == "ONEAPI"
        sc.cycles.device = "GPU" if gpus else "CPU"
        print("cycles device:", sc.cycles.device, [d.name for d in gpus])
    except Exception as e:  # GPU가 없으면 CPU로 그린다
        print("gpu setup failed:", e)
        sc.cycles.device = "CPU"
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue


def _set(node, key, value):
    """5.x는 노드 옵션이 입력 소켓으로 바뀐 경우가 있어 둘 다 시도한다."""
    if hasattr(node, key.lower().replace(" ", "_")):
        try:
            setattr(node, key.lower().replace(" ", "_"), value)
            return
        except (TypeError, AttributeError):
            pass
    if key in node.inputs:
        node.inputs[key].default_value = value


def bloom(enabled):
    if not enabled:
        return
    sc = bpy.context.scene
    try:
        if hasattr(sc, "compositing_node_group"):
            tree = bpy.data.node_groups.new("comp", "CompositorNodeTree")
            tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            sc.compositing_node_group = tree
            out = tree.nodes.new("NodeGroupOutput")
        else:
            sc.use_nodes = True
            tree = sc.node_tree
            tree.nodes.clear()
            out = tree.nodes.new("CompositorNodeComposite")
        rl = tree.nodes.new("CompositorNodeRLayers")
        glare = tree.nodes.new("CompositorNodeGlare")
        try:
            glare.glare_type = "BLOOM"
        except (TypeError, AttributeError):
            glare.inputs["Type"].default_value = "Bloom"
        _set(glare, "Threshold", 1.0)
        _set(glare, "Strength", 0.6)
        _set(glare, "Size", 0.5)
        tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
        tree.links.new(glare.outputs["Image"], out.inputs[0])
        print("bloom on")
    except Exception as e:  # 블룸이 없어도 렌더는 계속한다
        print("bloom failed:", repr(e))