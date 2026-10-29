"""Blender 씬 생성 공통 도구: 재질, 기본 도형, 케이블, 글자."""
import math

import bmesh
import bpy
from mathutils import Vector

_MATS = {}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()


def collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _link(ob, col):
    (col or bpy.context.scene.collection).objects.link(ob)


def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, coat=0.0):
    """Principled BSDF 재질. 같은 이름은 재사용한다."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except AttributeError:
        pass
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1.0)
        b.inputs["Emission Strength"].default_value = strength
    _MATS[name] = m
    return m


def node_mat(name):
    """노드를 직접 짜는 재질용 빈 Principled 재질."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except AttributeError:
        pass
    _MATS[name] = m
    return m


def _finish(ob, material, bevel, segments, parent, col):
    _link(ob, col)
    if material is not None:
        ob.data.materials.append(material)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = segments
        md.limit_method = "ANGLE"
        md.harden_normals = True
        for p in ob.data.polygons:
            p.use_smooth = True
    if parent is not None:
        ob.parent = parent
    return ob


def box(name, size, loc, material, bevel=0.0, segments=3, parent=None, col=None, rot=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    return _finish(ob, material, bevel, segments, parent, col)


def cyl(name, radius, depth, loc, material, axis="Z", segments=20, bevel=0.0, parent=None, col=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if axis == "Y":
        ob.rotation_euler = (math.radians(90), 0, 0)
    elif axis == "X":
        ob.rotation_euler = (0, math.radians(90), 0)
    ob = _finish(ob, material, bevel, 2, parent, col)
    if bevel <= 0:
        for p in ob.data.polygons:
            p.use_smooth = len(p.vertices) == 4
    return ob


def cone(name, r_bottom, r_top, depth, loc, material, segments=24, bevel=0.0, parent=None, col=None):
    """밑면이 z=0인 원뿔대(화분·전등갓·다리)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r_bottom, radius2=r_top, depth=depth)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, depth / 2))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob = _finish(ob, material, bevel, 2, parent, col)
    if bevel <= 0:
        for p in ob.data.polygons:
            p.use_smooth = len(p.vertices) == 4
    return ob


def sphere(name, radius, loc, material, scale=(1, 1, 1), segments=24, parent=None, col=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=radius)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.scale = scale
    return _finish(ob, material, 0.0, 0, parent, col)


def mesh(name, verts, faces, loc, material, smooth=True, parent=None, col=None, rot=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    return _finish(ob, material, 0.0, 0, parent, col)


def screen_plane(name, w, h, loc, material, rot=None, parent=None, col=None):
    """-Y를 보는 UV 있는 사각형(화면·창밖 풍경)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for li, co in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = co
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    return _finish(ob, material, 0.0, 0, parent, col)


def image(name, w, h, pixels):
    """numpy RGBA(0..1, 아래쪽 행부터) 배열로 이미지를 만들어 .blend에 넣는다."""
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.pixels.foreach_set(pixels.astype("float32").ravel())
    img.pack()
    return img


def tex_mat(name, img, rough=0.5, coat=0.0):
    """이미지를 바탕색으로 쓰는 일반 재질(GLB로 그대로 나간다)."""
    m = node_mat(name)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
    return m


def screen_mat(name, img, strength=1.0):
    """빛을 내는 화면 재질(조명 영향 없이 그림이 그대로 보인다)."""
    m = node_mat(name)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = strength
    bsdf.inputs["Roughness"].default_value = 0.25
    return m


def cable(name, points, radius, material, parent=None, col=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.resolution_u = 14
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    return _finish(ob, material, 0.0, 0, parent, col)


def text(name, body, size, loc, material, align="CENTER", extrude=0.0004, parent=None, col=None, rot=None):
    """정면(-Y)을 보는 글자."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = rot or (math.radians(90), 0, 0)
    return _finish(ob, material, 0.0, 0, parent, col)


def empty(name, loc, parent=None, col=None):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    ob.empty_display_size = 0.05
    return _finish(ob, None, 0.0, 0, parent, col)
