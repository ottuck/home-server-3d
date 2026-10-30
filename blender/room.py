"""방 전체: 벽·창·바닥, 소품 배치, 낮/밤 조명. 바닥은 x[-1.7,1.7], y[-1.4,1.4]이고 벽은 뒤(+Y)와 왼쪽(-X)."""
import math

import bpy
import numpy as np
from mathutils import Euler

import props
import textures as tx
from lib import box, cable, image, mat, screen_mat, screen_plane, tex_mat

R = math.radians
X0, X1, Y0, Y1 = -1.7, 1.7, -1.4, 1.4
WALL_H, WALL_T = 2.3, 0.12
WIN = (-1.35, -0.35, 0.80, 2.00)  # 뒤 벽 창: x0, x1, z0, z1

THEMES = {
    "day": dict(bg=(0.93, 0.91, 0.87), world=(0.82, 0.80, 0.76), world_strength=0.65, sun=2.6, fill=170.0, window=140.0,
                window_color=(1.0, 0.93, 0.80), floor_lamp=0.0, desk_lamp=0.0, sconce=0.0, table_lamp=0.0),
    "night": dict(bg=(0.025, 0.032, 0.065), world=(0.010, 0.016, 0.040), world_strength=0.30, sun=0.0, fill=0.0, window=18.0,
                  window_color=(0.50, 0.62, 1.0), floor_lamp=55.0, desk_lamp=14.0, sconce=22.0, table_lamp=20.0),
}


def shell(m, night, col):
    wall = mat("wall_cream", (0.86, 0.81, 0.72), rough=0.85)
    slab = mat("slab", (0.24, 0.22, 0.21), rough=0.8)
    # 미니어처 받침과 나무 바닥
    box("slab", (X1 - X0 + 0.17, Y1 - Y0 + 0.17, 0.16), ((X0 + X1) / 2 - 0.06, (Y0 + Y1) / 2 + 0.06, -0.10), slab, bevel=0.015, col=col)
    # 나무 바닥: 웹에서도 같은 그림이 나오도록 절차 텍스처 대신 이미지 + UV 평면을 쓴다
    fw_, fd_ = X1 - X0 + 0.05, Y1 - Y0 + 0.05
    fc = ((X0 + X1) / 2 + 0.025, (Y0 + Y1) / 2 - 0.025)
    box("floor", (fw_, fd_, 0.02), (*fc, -0.011), mat("floor_edge", (0.45, 0.29, 0.16), rough=0.6), bevel=0.004, col=col)
    px = tx.wood_planks(fw_, fd_)
    planks = image("tex_floor", px.shape[1], px.shape[0], px)
    screen_plane("floor_top", fw_, fd_, (*fc, 0.0), tex_mat("floor_wood", planks, rough=0.55, coat=0.1), rot=(R(-90), 0, 0), col=col)
    # 뒤 벽(창 구멍을 남기고 네 조각)
    wy = Y1 + WALL_T / 2
    wx0, wx1, wz0, wz1 = WIN
    left_end = X0 - WALL_T
    box("wall_back_l", (wx0 - left_end, WALL_T, WALL_H), ((left_end + wx0) / 2, wy, WALL_H / 2), wall, bevel=0.006, col=col)
    box("wall_back_r", (X1 - wx1, WALL_T, WALL_H), ((wx1 + X1) / 2, wy, WALL_H / 2), wall, bevel=0.006, col=col)
    box("wall_back_b", (wx1 - wx0, WALL_T, wz0), ((wx0 + wx1) / 2, wy, wz0 / 2), wall, col=col)
    box("wall_back_t", (wx1 - wx0, WALL_T, WALL_H - wz1), ((wx0 + wx1) / 2, wy, (wz1 + WALL_H) / 2), wall, col=col)
    box("wall_left", (WALL_T, Y1 - Y0, WALL_H), (X0 - WALL_T / 2, (Y0 + Y1) / 2, WALL_H / 2), wall, bevel=0.006, col=col)
    box("skirting_back", (X1 - X0, 0.02, 0.08), ((X0 + X1) / 2, Y1 - 0.01, 0.04), m.wood, bevel=0.004, col=col)
    box("skirting_left", (0.02, Y1 - Y0, 0.08), (X0 + 0.01, (Y0 + Y1) / 2, 0.04), m.wood, bevel=0.004, col=col)
    # 창틀·창살·창턱
    fw = 0.045
    cx, cz = (wx0 + wx1) / 2, (wz0 + wz1) / 2
    for nm, size, loc in [
        ("win_frame_l", (fw, WALL_T + 0.02, wz1 - wz0), (wx0 + fw / 2, wy, cz)),
        ("win_frame_r", (fw, WALL_T + 0.02, wz1 - wz0), (wx1 - fw / 2, wy, cz)),
        ("win_frame_t", (wx1 - wx0, WALL_T + 0.02, fw), (cx, wy, wz1 - fw / 2)),
        ("win_frame_b", (wx1 - wx0, WALL_T + 0.02, fw), (cx, wy, wz0 + fw / 2)),
        ("win_mullion_v", (0.025, 0.03, wz1 - wz0), (cx, wy, cz)),
        ("win_mullion_h", (wx1 - wx0, 0.03, 0.025), (cx, wy, wz0 + (wz1 - wz0) * 0.62)),
    ]:
        box(nm, size, loc, m.black_metal, bevel=0.004, col=col)
    box("win_sill", (wx1 - wx0 + 0.10, 0.20, 0.035), (cx, Y1 - 0.03, wz0 - 0.0175), m.wood, bevel=0.008, col=col)
    # 창밖 풍경
    sky = image("skyline_night" if night else "skyline_day", 1200, 1280, tx.skyline(night=night))
    smat = screen_mat("skyline", sky, strength=1.0)
    # 정사영 카메라라 창을 지나는 시선이 모두 평행하다. 창 바로 뒤에 두어 창으로만 보이게 한다.
    screen_plane("skyline", 1.5, 1.6, (cx - 0.37, Y1 + 0.55, 1.0), smat, col=col)


def layout(m, night, col, rack_root, cable_mats):
    rack_root.location = (0.35, 1.0, 0)
    # 뒤 벽: 서버 밖 서비스 화면, 수납장, 벽등, 케이블 트레이
    props.wall_screen(m, "screen_grafana", (1.17, Y1 - 0.035, 1.47), 0, col,
                      image("tex_dashboard", 640, 360, tx.dashboard()), "GRAFANA CLOUD")
    props.cabinet(m, "cabinet", (1.18, Y1 - 0.22, 0), 0, col)
    props.speaker(m, (1.18, Y1 - 0.22, 0.52), -8, col)
    props.plant(m, "plant_cabinet", (1.46, Y1 - 0.22, 0.52), col, height=0.2, pot=3, seed=8)
    props.table_lamp(m, "table_lamp", (0.80, Y1 - 0.20, 0.52), col)
    props.sconce(m, "sconce", (-0.13, Y1 - 0.021, 1.72), 0, col)
    props.cable_tray(m, "tray", X0 + 0.05, 0.42, Y1 - 0.12, 2.06, col, cable_mats)
    for k in range(4):
        dx = -0.04 + k * 0.025
        cable(f"tray_drop_{k}", [(0.30 + dx, Y1 - 0.12, 2.04), (0.30 + dx, Y1 - 0.16, 1.70), (0.30 + dx, 1.12, 1.36)],
              0.0055, cable_mats[k % len(cable_mats)], col=col)
    # 구석에는 사무실에 흔한 벤자민 고무나무: 책상 너머로 둥근 수관이 보인다
    props.ficus(m, "plant_corner", (-1.36, 1.06, 0), col, seed=3)
    # 왼쪽 벽: 작업 책상, 의자, 선반, 간판
    # 와이드 모니터: 좌우로 나눈 에디터 두 칸
    code = np.concatenate([tx.code(w=420, h=340, seed=3), tx.code(w=420, h=340, seed=9)], axis=1)
    props.desk(m, "desk", (X0 + 0.35, 0.05, 0), 90, col, image("tex_code", 840, 340, code))
    props.chair(m, "chair", (-0.80, 0.02, 0), -78, col)
    props.wall_shelf(m, "shelf_low", (X0 + 0.12, 0.10, 1.38), 90, col, length=1.15, seed=2)
    props.wall_shelf(m, "shelf_high", (X0 + 0.12, 0.30, 1.76), 90, col, length=0.80, seed=6, decor=False)
    props.wall_sign(m, "sign", (X0 + 0.031, -0.92, 1.80), 90, col, "HOME LAB", "build · monitor · enjoy")
    props.floor_lamp(m, "floor_lamp", (-1.36, -1.08, 0), col)
    # 가운데·앞: 러그, 안락의자, 협탁, 고양이, 화분
    props.rug(m, "rug", (0.15, -0.42, 0), col)
    props.armchair(m, "armchair", (1.25, -0.70, 0), -58, col)
    props.side_table(m, "side_table", (0.62, -1.12, 0), col)
    # 로봇 청소기는 창 아래 충전대에 붙어 있다가 웹에서 방을 돈다
    props.dock(m, "dock", (-0.62, Y1 - 0.07, 0), 0, col)
    props.vacuum(m, (-0.62, Y1 - 0.25, 0), col)
    props.blinds(m, "blinds", WIN[0] - 0.03, WIN[1] + 0.03, WIN[3] + 0.035, Y1 - 0.035, col)


def lights(theme):
    t = THEMES[theme]
    world = bpy.data.worlds.new("world")
    bpy.context.scene.world = world
    try:
        world.use_nodes = True
    except AttributeError:
        pass
    # 조명용 하늘색과 카메라에 보이는 배경색을 따로 둔다
    nt = world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (*t["world"], 1)
    bg.inputs["Strength"].default_value = t["world_strength"]
    seen = nt.nodes.new("ShaderNodeBackground")
    seen.inputs["Color"].default_value = (*t["bg"], 1)
    path = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes["World Output"]
    nt.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg.outputs[0], mix.inputs[1])
    nt.links.new(seen.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

    def add(name, kind, loc, rot, energy, color, **kw):
        if energy <= 0:
            return
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        for k, v in kw.items():
            setattr(ld, k, v)
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        ob.rotation_euler = Euler([R(a) for a in rot])
        bpy.context.scene.collection.objects.link(ob)

    warm = (1.0, 0.72, 0.45)
    add("sun", "SUN", (0, 0, 6), (50, 0, -40), t["sun"], (1.0, 0.91, 0.78), angle=R(5))
    add("fill", "AREA", (3.2, -3.4, 3.6), (55, 0, 42), t["fill"], (1.0, 0.96, 0.90), size=4.0)
    wx0, wx1, wz0, wz1 = WIN
    add("window_light", "AREA", ((wx0 + wx1) / 2, Y1 + 0.05, (wz0 + wz1) / 2), (-90, 0, 0), t["window"], t["window_color"],
        shape="RECTANGLE", size=wx1 - wx0, size_y=wz1 - wz0)
    add("floor_lamp_light", "POINT", (-1.36, -1.08, 1.40), (0, 0, 0), t["floor_lamp"], warm, shadow_soft_size=0.12)
    add("desk_lamp_light", "POINT", (-1.25, 0.66, 1.08), (0, 0, 0), t["desk_lamp"], warm, shadow_soft_size=0.05)
    add("table_lamp_light", "POINT", (0.80, Y1 - 0.20, 0.76), (0, 0, 0), t["table_lamp"], warm, shadow_soft_size=0.06)
    add("sconce_light", "POINT", (-0.13, Y1 - 0.09, 1.74), (0, 0, 0), t["sconce"], warm, shadow_soft_size=0.06)
