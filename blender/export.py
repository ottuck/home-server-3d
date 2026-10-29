"""웹용 GLB 내보내기: 수정자·글자를 메시로 굳히고 소품·장비 단위로 합친 뒤 Draco로 압축한다.

남기는 것(웹에서 따로 다룬다): unit__* 빈 객체(extras 포함), led__* LED, *_screen 화면, skyline 창밖 그림.
"""
import os

import bpy

KEEP_SUFFIX = ("_screen",)


def _keep(ob):
    return ob.name.startswith("led__") or ob.name.endswith(KEEP_SUFFIX) or ob.name == "skyline"


def _descendants(ob):
    out = []
    for c in ob.children:
        out.append(c)
        out += _descendants(c)
    return out


def _bake_geometry(objs):
    """글자·커브·수정자를 실제 메시로 바꾼다."""
    bpy.ops.object.select_all(action="DESELECT")
    targets = [o for o in objs if o.type in ("FONT", "CURVE") or (o.type == "MESH" and o.modifiers)]
    for o in targets:
        o.select_set(True)
    if targets:
        bpy.context.view_layer.objects.active = targets[0]
        bpy.ops.object.convert(target="MESH")


def _unparent(ob):
    mw = ob.matrix_world.copy()
    ob.parent = None
    ob.matrix_world = mw


def _parent(ob, parent):
    mw = ob.matrix_world.copy()
    ob.parent = parent
    ob.matrix_world = mw


def _join(meshes, name, parent):
    meshes = [m for m in meshes if m.type == "MESH"]
    if not meshes:
        return None
    for m in meshes:
        _unparent(m)
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    if parent is not None:
        _parent(ob, parent)
    return ob


def optimize():
    """씬의 메시를 묶음별로 합친다. 반환: 합친 뒤 메시 수."""
    _bake_geometry(list(bpy.context.scene.objects))
    rack = bpy.data.objects.get("rack")
    if rack is not None:
        units = [c for c in rack.children if c.name.startswith("unit__")]
        for u in units:
            parts = _descendants(u)
            for led in [p for p in parts if _keep(p)]:
                _parent(led, u)
            _join([p for p in parts if not _keep(p)], f"{u.name}_body", u)
        in_units = set(units)
        for u in units:
            in_units.update(_descendants(u))
        frame = [d for d in _descendants(rack) if d not in in_units]
        _join([d for d in frame if d.type == "MESH" and not _keep(d)], "rack_frame", rack)
    room_col = bpy.data.collections.get("room")
    if room_col is not None:
        roots = [o for o in room_col.objects if o.parent is None and o.type == "EMPTY"]
        for r in roots:
            parts = _descendants(r)
            for s in [p for p in parts if _keep(p)]:
                _unparent(s)
            _join([p for p in parts if not _keep(p)], f"prop__{r.name}", None)
        loose = [o for o in room_col.objects if o.parent is None and o.type == "MESH" and not _keep(o) and not o.name.startswith("prop__")]
        _join(loose, "room_shell", None)
    # 자식이 없어진 빈 객체 정리(unit__·rack은 남긴다)
    for o in list(bpy.context.scene.objects):
        if o.type == "EMPTY" and not o.children and not o.name.startswith("unit__") and o.name != "rack":
            bpy.data.objects.remove(o)
    return sum(1 for o in bpy.context.scene.objects if o.type == "MESH")


def export(path, collections):
    bpy.ops.object.select_all(action="DESELECT")
    for name in collections:
        col = bpy.data.collections.get(name)
        if col is None:
            continue
        for o in col.all_objects:
            o.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_extras=True,
        export_lights=False,
        export_cameras=False,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
    )
    return os.path.getsize(path)
