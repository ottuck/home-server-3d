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
