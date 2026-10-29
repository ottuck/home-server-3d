"""방 소품. 모든 소품은 로컬 좌표에서 정면이 -Y이고, 바닥 중앙이 원점이다.
root 빈 객체를 돌려 배치하므로 rotz=90이면 정면이 +X를 본다.
"""
import math

import numpy as np

from lib import box, cable, cone, cyl, empty, mat, mesh, screen_mat, screen_plane, sphere, text

R = math.radians


class Mats:
    def __init__(self, night=False):
        glow = 1.0 if night else 0.0
        self.wood = mat("wood_oak", (0.62, 0.43, 0.26), rough=0.45, coat=0.15)
        self.wood_dark = mat("wood_walnut", (0.30, 0.18, 0.10), rough=0.45, coat=0.15)
        self.cream = mat("cream", (0.84, 0.80, 0.71), rough=0.55)
        self.ivory = mat("ivory", (0.92, 0.89, 0.82), rough=0.5)
        self.charcoal = mat("charcoal", (0.045, 0.047, 0.052), rough=0.45, metal=0.3)
        self.black_metal = mat("black_metal", (0.025, 0.026, 0.03), rough=0.35, metal=0.8)
        self.brass = mat("brass", (0.78, 0.58, 0.30), rough=0.3, metal=1.0)
        self.fabric = mat("fabric_cream", (0.66, 0.60, 0.50), rough=0.95)
        self.fabric_dark = mat("fabric_charcoal", (0.10, 0.10, 0.11), rough=0.9)
        self.fabric_sage = mat("fabric_sage", (0.40, 0.50, 0.38), rough=0.95)
        self.rug = mat("rug", (0.66, 0.58, 0.46), rough=1.0)
        self.rug_border = mat("rug_border", (0.40, 0.30, 0.21), rough=1.0)
        self.leaf = [mat("leaf_a", (0.10, 0.28, 0.09), rough=0.55), mat("leaf_b", (0.20, 0.42, 0.14), rough=0.55),
                     mat("leaf_c", (0.30, 0.50, 0.20), rough=0.6)]
        self.stem = mat("stem", (0.18, 0.30, 0.10), rough=0.7)
        self.soil = mat("soil", (0.07, 0.045, 0.03), rough=1.0)
        self.pots = [mat("pot_terracotta", (0.62, 0.32, 0.19), rough=0.8), mat("pot_cream", (0.86, 0.83, 0.76), rough=0.6),
                     mat("pot_sage", (0.45, 0.55, 0.43), rough=0.6), mat("pot_charcoal", (0.10, 0.10, 0.11), rough=0.6)]
        self.books = [mat(f"book_{i}", c, rough=0.7) for i, c in enumerate([
            (0.42, 0.52, 0.40), (0.82, 0.76, 0.62), (0.62, 0.30, 0.18), (0.12, 0.20, 0.35),
            (0.78, 0.58, 0.22), (0.25, 0.25, 0.27), (0.70, 0.66, 0.58), (0.35, 0.22, 0.15)])]
        self.cat = mat("cat_orange", (0.80, 0.42, 0.16), rough=0.9)
        self.cat_white = mat("cat_white", (0.92, 0.89, 0.83), rough=0.9)
        self.shade = mat("lamp_shade", (0.92, 0.86, 0.74), rough=0.9, emit=(1.0, 0.78, 0.50), strength=1.6 * glow)
        self.bulb = mat("bulb", (1.0, 0.95, 0.85), rough=0.3, emit=(1.0, 0.80, 0.55), strength=0.5 + 25.0 * glow)
        self.sign_glow = mat("sign_glow", (0.95, 0.88, 0.72), rough=0.5, emit=(1.0, 0.72, 0.40), strength=6.0 * glow)
        self.label = mat("label_ink", (0.90, 0.87, 0.80), rough=0.6)
        self.screen_boost = 1.0 if night else 0.6


def _root(name, loc, rotz, col):
    r = empty(name, loc, col=col)
    r.rotation_euler = (0, 0, R(rotz))
    return r


# ---------------------------------------------------------------- 식물

def _leaf(name, length, width, elev, droop, yaw, base, material, root, col):
    n = 7
    verts, faces = [], []
    for i in range(n + 1):
        t = i / n
        s = t * length
        y = s * math.cos(elev)
        z = s * math.sin(elev) - droop * s * s
        hw = width / 2 * (math.sin(math.pi * min(t * 1.05, 1.0)) ** 0.8) + 0.002
        verts += [(-hw, y, z - hw * 0.12), (0, y, z), (hw, y, z - hw * 0.12)]
    for i in range(n):
        a = i * 3
        faces += [(a, a + 1, a + 4, a + 3), (a + 1, a + 2, a + 5, a + 4)]
    return mesh(name, verts, faces, base, material, rot=(0, 0, yaw), parent=root, col=col)


def plant(m, name, loc, col, height=1.0, pot=0, seed=1, rotz=0):
    rng = np.random.default_rng(seed)
    root = _root(name, loc, rotz, col)
    pr = 0.09 + 0.08 * height
    ph = 0.12 + 0.18 * height
    cone(f"{name}_pot", pr * 0.78, pr, ph, (0, 0, 0), m.pots[pot % len(m.pots)], segments=32, bevel=0.006, parent=root, col=col)
    cyl(f"{name}_soil", pr * 0.92, 0.01, (0, 0, ph - 0.012), m.soil, segments=32, parent=root, col=col)
    count = int(8 + 10 * height)
    for i in range(count):
        yaw = rng.uniform(0, 2 * math.pi)
        stem_h = ph + rng.uniform(0.05, 0.55) * height
        lean = rng.uniform(0.01, 0.06) * (1 + height)
        bx, by = -math.sin(yaw) * lean, math.cos(yaw) * lean
        cable(f"{name}_stem_{i}", [(0, 0, ph - 0.01), (bx * 0.5, by * 0.5, (ph + stem_h) / 2), (bx, by, stem_h)],
              0.0025 + 0.002 * height, m.stem, parent=root, col=col)
        _leaf(f"{name}_leaf_{i}", rng.uniform(0.10, 0.17) * (0.6 + 0.6 * height), rng.uniform(0.045, 0.07) * (0.7 + 0.5 * height),
              R(rng.uniform(15, 55)), rng.uniform(1.0, 3.5) / (0.6 + height), yaw, (bx, by, stem_h),
              m.leaf[int(rng.integers(0, 3))], root, col)
    return root


# ---------------------------------------------------------------- 작업 공간

def monitor(m, name, loc, rotz, img, root, col, w=0.56, h=0.33):
    r = empty(name, loc, parent=root, col=col)
    r.rotation_euler = (0, 0, R(rotz))
    box(f"{name}_base", (0.22, 0.16, 0.012), (0, 0.04, 0.006), m.black_metal, bevel=0.005, parent=r, col=col)
    box(f"{name}_neck", (0.045, 0.025, 0.26), (0, 0.075, 0.13), m.black_metal, bevel=0.006, parent=r, col=col)
    zc = 0.12 + h / 2 + 0.03
    box(f"{name}_body", (w, 0.03, h), (0, 0.04, zc), m.charcoal, bevel=0.008, parent=r, col=col)
    smat = screen_mat(f"{name}_screen_mat", img, strength=m.screen_boost)
    screen_plane(f"{name}_screen", w - 0.025, h - 0.035, (0, 0.0245, zc + 0.004), smat, parent=r, col=col)
    return r


def keyboard(m, name, loc, root, col):
    r = empty(name, loc, parent=root, col=col)
    box(f"{name}_case", (0.36, 0.12, 0.016), (0, 0, 0.008), m.charcoal, bevel=0.005, parent=r, col=col)
    for row in range(4):
        for k in range(14):
            kw = 0.020 if not (row == 0 and 4 <= k <= 9) else 0.020
            box(f"{name}_key_{row}_{k}", (kw, 0.019, 0.008), (-0.153 + k * 0.0236, -0.04 + row * 0.026, 0.019),
                m.ivory if (row + k) % 9 else m.fabric_sage, bevel=0.003, segments=2, parent=r, col=col)
    return r


def mug(m, name, loc, root, col, material=None):
    r = empty(name, loc, parent=root, col=col)
    cyl(f"{name}_cup", 0.035, 0.085, (0, 0, 0.0425), material or m.ivory, segments=24, bevel=0.006, parent=r, col=col)
    cyl(f"{name}_coffee", 0.031, 0.002, (0, 0, 0.078), m.wood_dark, segments=24, parent=r, col=col)
    cable(f"{name}_handle", [(0.033, 0, 0.065), (0.058, 0, 0.055), (0.058, 0, 0.03), (0.033, 0, 0.022)], 0.006, material or m.ivory, parent=r, col=col)


def desk_lamp(m, name, loc, rotz, root, col):
    r = empty(name, loc, parent=root, col=col)
    r.rotation_euler = (0, 0, R(rotz))
    cyl(f"{name}_base", 0.075, 0.018, (0, 0, 0.009), m.black_metal, segments=32, bevel=0.005, parent=r, col=col)
    cable(f"{name}_arm", [(0, 0, 0.015), (0.0, 0.03, 0.28), (0.0, -0.10, 0.42)], 0.007, m.black_metal, parent=r, col=col)
    shade = cone(f"{name}_shade", 0.085, 0.03, 0.11, (0, -0.15, 0.36), m.black_metal, segments=32, bevel=0.003, parent=r, col=col)
    shade.rotation_euler = (R(160), 0, 0)
    sphere(f"{name}_bulb", 0.025, (0, -0.155, 0.355), m.bulb, parent=r, col=col)


def desk(m, name, loc, rotz, col, screens):
    root = _root(name, loc, rotz, col)
    top_z = 0.72
    box(f"{name}_top", (1.36, 0.66, 0.035), (0, 0, top_z + 0.0175), m.wood, bevel=0.010, parent=root, col=col)
    # 왼쪽 서랍장, 오른쪽 철제 다리
    box(f"{name}_cabinet", (0.42, 0.58, top_z - 0.02), (-0.43, 0.01, (top_z - 0.02) / 2 + 0.01), m.cream, bevel=0.012, parent=root, col=col)
    for i in range(3):
        z = 0.12 + i * 0.22
        box(f"{name}_drawer_{i}", (0.38, 0.012, 0.19), (-0.43, -0.28, z + 0.06), m.ivory, bevel=0.006, parent=root, col=col)
        box(f"{name}_handle_{i}", (0.10, 0.012, 0.012), (-0.43, -0.292, z + 0.12), m.brass, bevel=0.004, parent=root, col=col)
    for sy in (-1, 1):
        box(f"{name}_leg_{sy}", (0.035, 0.035, top_z), (0.62, sy * 0.27, top_z / 2), m.black_metal, bevel=0.006, parent=root, col=col)
    box(f"{name}_leg_bar", (0.03, 0.54, 0.03), (0.62, 0, 0.08), m.black_metal, bevel=0.006, parent=root, col=col)
    z = top_z + 0.035
    monitor(m, f"{name}_mon_l", (-0.29, 0.10, z), -10, screens[0], root, col)
    monitor(m, f"{name}_mon_r", (0.30, 0.10, z), 10, screens[1], root, col)
    keyboard(m, f"{name}_kbd", (0.0, -0.16, z), root, col)
    sphere(f"{name}_mouse", 0.03, (0.30, -0.17, z + 0.012), m.charcoal, scale=(0.75, 1.0, 0.45), parent=root, col=col)
    mug(m, f"{name}_mug", (-0.42, -0.16, z), root, col)
    desk_lamp(m, f"{name}_lamp", (0.58, 0.16, z), 20, root, col)
    plant(m, f"{name}_plant", (-0.58, 0.18, z), col, height=0.15, pot=1, seed=5).parent = root
    return root


def chair(m, name, loc, rotz, col):
    root = _root(name, loc, rotz, col)
    for i in range(5):
        a = R(90 + i * 72)
        x, y = math.cos(a) * 0.24, math.sin(a) * 0.24
        b = box(f"{name}_leg_{i}", (0.26, 0.04, 0.03), (x / 2, y / 2, 0.065), m.black_metal, bevel=0.01, parent=root, col=col)
        b.rotation_euler = (0, 0, a)
        sphere(f"{name}_caster_{i}", 0.028, (x, y, 0.03), m.charcoal, parent=root, col=col)
    cyl(f"{name}_gas", 0.025, 0.30, (0, 0, 0.22), m.black_metal, segments=20, parent=root, col=col)
    box(f"{name}_seat", (0.50, 0.48, 0.09), (0, 0, 0.44), m.fabric_dark, bevel=0.035, parent=root, col=col)
    back = box(f"{name}_back", (0.47, 0.07, 0.56), (0, 0.24, 0.80), m.fabric_dark, bevel=0.035, parent=root, col=col)
    back.rotation_euler = (R(-8), 0, 0)
    for sx in (-1, 1):
        box(f"{name}_arm_post_{sx}", (0.03, 0.04, 0.18), (sx * 0.26, 0.04, 0.55), m.black_metal, bevel=0.008, parent=root, col=col)
        box(f"{name}_arm_pad_{sx}", (0.06, 0.26, 0.03), (sx * 0.26, 0.02, 0.65), m.charcoal, bevel=0.012, parent=root, col=col)
    return root


# ---------------------------------------------------------------- 수납·가구

def books(m, name, x0, x1, z, depth, col, root, seed):
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1 - 0.03:
        if rng.random() < 0.12 and x < x1 - 0.18:
            x += rng.uniform(0.06, 0.14)  # 빈 틈
            continue
        bw = rng.uniform(0.022, 0.045)
        bh = rng.uniform(0.15, 0.25)
        bd = depth * rng.uniform(0.75, 0.95)
        mt = m.books[int(rng.integers(0, len(m.books)))]
        b = box(f"{name}_{x:.3f}", (bw, bd, bh), (x + bw / 2, 0, z + bh / 2), mt, bevel=0.003, segments=2, parent=root, col=col)
        if rng.random() < 0.08:
            b.rotation_euler = (0, R(-12), 0)
            b.location.z += 0.01
        x += bw + 0.002


def wall_shelf(m, name, loc, rotz, col, length=1.1, seed=1, decor=True):
    root = _root(name, loc, rotz, col)
    box(f"{name}_board", (length, 0.24, 0.03), (0, 0, 0.015), m.wood, bevel=0.006, parent=root, col=col)
    for sx in (-1, 1):
        box(f"{name}_bracket_{sx}", (0.02, 0.18, 0.08), (sx * (length / 2 - 0.12), 0.02, -0.04), m.black_metal, bevel=0.004, parent=root, col=col)
    books(m, f"{name}_book", -length / 2 + 0.03, length / 2 - (0.30 if decor else 0.03), 0.03, 0.22, col, root, seed)
    if decor:
        plant(m, f"{name}_plant", (length / 2 - 0.14, 0, 0.03), col, height=0.1, pot=2 + seed % 2, seed=seed + 20).parent = root
    return root


def cabinet(m, name, loc, rotz, col, w=0.9, d=0.40, h=0.52):
    root = _root(name, loc, rotz, col)
    box(f"{name}_body", (w, d, h - 0.08), (0, 0, 0.08 + (h - 0.08) / 2 - 0.015), m.cream, bevel=0.012, parent=root, col=col)
    box(f"{name}_top", (w + 0.02, d + 0.02, 0.03), (0, 0, h - 0.015), m.wood, bevel=0.008, parent=root, col=col)
    for i, x in enumerate((-w / 4, w / 4)):
        box(f"{name}_door_{i}", (w / 2 - 0.02, 0.01, h - 0.15), (x, -d / 2 - 0.004, 0.08 + (h - 0.12) / 2), m.ivory, bevel=0.005, parent=root, col=col)
        cyl(f"{name}_knob_{i}", 0.012, 0.02, (x + (0.12 if i == 0 else -0.12), -d / 2 - 0.016, h * 0.55), m.brass, axis="Y", segments=16, parent=root, col=col)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cone(f"{name}_leg_{sx}_{sy}", 0.012, 0.018, 0.08, (sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), 0), m.wood_dark, segments=12, parent=root, col=col)
    return root


def armchair(m, name, loc, rotz, col):
    root = _root(name, loc, rotz, col)
    box(f"{name}_base", (0.86, 0.80, 0.22), (0, 0, 0.21), m.fabric_sage, bevel=0.05, parent=root, col=col)
    box(f"{name}_cushion", (0.62, 0.66, 0.13), (0, -0.04, 0.38), m.fabric_sage, bevel=0.055, parent=root, col=col)
    back = box(f"{name}_back", (0.86, 0.20, 0.50), (0, 0.31, 0.50), m.fabric_sage, bevel=0.07, parent=root, col=col)
    back.rotation_euler = (R(-6), 0, 0)
    for sx in (-1, 1):
        box(f"{name}_arm_{sx}", (0.14, 0.78, 0.36), (sx * 0.37, 0.0, 0.40), m.fabric_sage, bevel=0.06, parent=root, col=col)
        for sy in (-1, 1):
            cone(f"{name}_leg_{sx}_{sy}", 0.016, 0.022, 0.10, (sx * 0.34, sy * 0.30, 0), m.wood_dark, segments=12, parent=root, col=col)
    pillow = box(f"{name}_pillow", (0.36, 0.12, 0.30), (0.08, 0.17, 0.58), m.fabric, bevel=0.06, parent=root, col=col)
    pillow.rotation_euler = (R(-15), 0, R(8))
    return root


def side_table(m, name, loc, col):
    root = _root(name, loc, 0, col)
    cyl(f"{name}_top", 0.24, 0.035, (0, 0, 0.50), m.wood, segments=40, bevel=0.01, parent=root, col=col)
    for i in range(3):
        a = R(90 + i * 120)
        leg = cyl(f"{name}_leg_{i}", 0.014, 0.50, (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.25), m.wood_dark, segments=12, parent=root, col=col)
        leg.rotation_euler = (R(8) * math.sin(a), -R(8) * math.cos(a), 0)
    mug(m, f"{name}_mug", (0.07, -0.05, 0.518), root, col, material=m.pots[2])
    books_root = empty(f"{name}_books", (-0.06, 0.06, 0.518), parent=root, col=col)
    box(f"{name}_book_a", (0.20, 0.14, 0.025), (0, 0, 0.0125), m.books[3], bevel=0.003, parent=books_root, col=col)
    box(f"{name}_book_b", (0.18, 0.13, 0.02), (0.005, 0, 0.035), m.books[1], bevel=0.003, parent=books_root, col=col).rotation_euler = (0, 0, R(12))
    return root


def rug(m, name, loc, col, w=1.7, d=1.15):
    root = _root(name, loc, 0, col)
    box(f"{name}_border", (w, d, 0.012), (0, 0, 0.006), m.rug_border, bevel=0.006, parent=root, col=col)
    box(f"{name}_field", (w - 0.12, d - 0.12, 0.014), (0, 0, 0.007), m.rug, bevel=0.006, parent=root, col=col)
    return root


def table_lamp(m, name, loc, col):
    root = _root(name, loc, 0, col)
    sphere(f"{name}_base", 0.07, (0, 0, 0.065), m.pots[0], scale=(1, 1, 0.95), segments=32, parent=root, col=col)
    cyl(f"{name}_neck", 0.008, 0.08, (0, 0, 0.16), m.brass, segments=12, parent=root, col=col)
    cone(f"{name}_shade", 0.11, 0.07, 0.12, (0, 0, 0.18), m.shade, segments=40, parent=root, col=col, caps=False)
    sphere(f"{name}_bulb", 0.025, (0, 0, 0.22), m.bulb, parent=root, col=col)
    return root


def floor_lamp(m, name, loc, col):
    root = _root(name, loc, 0, col)
    cyl(f"{name}_base", 0.14, 0.025, (0, 0, 0.0125), m.black_metal, segments=40, bevel=0.008, parent=root, col=col)
    cyl(f"{name}_pole", 0.012, 1.38, (0, 0, 0.71), m.brass, segments=16, parent=root, col=col)
    cone(f"{name}_shade", 0.22, 0.16, 0.28, (0, 0, 1.30), m.shade, segments=48, parent=root, col=col, caps=False)
    sphere(f"{name}_bulb", 0.04, (0, 0, 1.38), m.bulb, parent=root, col=col)
    return root


def cat(m, name, loc, rotz, col):
    """식빵 자세로 잠든 고양이."""
    root = _root(name, loc, rotz, col)
    sphere(f"{name}_body", 1.0, (0, 0.02, 0.075), m.cat, scale=(0.13, 0.19, 0.085), segments=32, parent=root, col=col)
    sphere(f"{name}_chest", 1.0, (0, -0.10, 0.06), m.cat_white, scale=(0.09, 0.06, 0.06), parent=root, col=col)
    sphere(f"{name}_head", 0.075, (0, -0.17, 0.11), m.cat, scale=(1.1, 0.95, 0.9), segments=32, parent=root, col=col)
    sphere(f"{name}_muzzle", 0.035, (0, -0.235, 0.095), m.cat_white, scale=(1.2, 0.8, 0.7), parent=root, col=col)
    for sx in (-1, 1):
        ear = cone(f"{name}_ear_{sx}", 0.028, 0.002, 0.05, (sx * 0.045, -0.165, 0.165), m.cat, segments=12, parent=root, col=col)
        ear.rotation_euler = (R(-10), R(sx * 22), 0)
        box(f"{name}_eye_{sx}", (0.022, 0.004, 0.003), (sx * 0.032, -0.236, 0.122), m.charcoal, parent=root, col=col).rotation_euler = (0, R(sx * -10), 0)
        sphere(f"{name}_paw_{sx}", 0.028, (sx * 0.05, -0.20, 0.02), m.cat_white, scale=(1, 1.4, 0.7), parent=root, col=col)
    cable(f"{name}_tail", [(0.08, 0.17, 0.04), (0.15, 0.05, 0.03), (0.13, -0.10, 0.025), (0.06, -0.17, 0.025)], 0.024, m.cat, parent=root, col=col)
    return root


# ---------------------------------------------------------------- 벽 요소

def wall_screen(m, name, loc, rotz, col, img, label, w=0.96, h=0.56):
    """벽걸이 화면 + 아래 이름표. 서버 밖 서비스(Grafana Cloud 등)를 나타낸다."""
    root = _root(name, loc, rotz, col)
    box(f"{name}_frame", (w + 0.04, 0.035, h + 0.04), (0, 0.0175, 0), m.charcoal, bevel=0.01, parent=root, col=col)
    smat = screen_mat(f"{name}_screen_mat", img, strength=m.screen_boost * 1.2)
    screen_plane(f"{name}_screen", w, h, (0, -0.0005, 0), smat, parent=root, col=col)
    box(f"{name}_label", (0.30, 0.012, 0.05), (0, 0.006, -h / 2 - 0.08), m.charcoal, bevel=0.008, parent=root, col=col)
    text(f"{name}_label_text", label, 0.024, (0, -0.0008, -h / 2 - 0.08), m.label, parent=root, col=col)
    return root


def tablet(m, name, loc, rotz, col, img, label):
    root = _root(name, loc, rotz, col)
    box(f"{name}_foot", (0.14, 0.10, 0.012), (0, 0.03, 0.006), m.black_metal, bevel=0.004, parent=root, col=col)
    t = empty(f"{name}_tilt", (0, 0.03, 0.03), parent=root, col=col)
    t.rotation_euler = (R(-15), 0, 0)
    box(f"{name}_body", (0.26, 0.016, 0.18), (0, 0.01, 0.09), m.charcoal, bevel=0.008, parent=t, col=col)
    smat = screen_mat(f"{name}_screen_mat", img, strength=m.screen_boost)
    screen_plane(f"{name}_screen", 0.24, 0.16, (0, 0.0015, 0.09), smat, parent=t, col=col)
    text(f"{name}_label", label, 0.016, (0, -0.045, 0.006), m.label, rot=(0, 0, 0), parent=root, col=col)
    return root


def wall_sign(m, name, loc, rotz, col, title, subtitle):
    root = _root(name, loc, rotz, col)
    box(f"{name}_plaque", (0.90, 0.03, 0.30), (0, 0.015, 0), m.wood_dark, bevel=0.02, parent=root, col=col)
    text(f"{name}_title", title, 0.11, (0, -0.002, 0.03), m.sign_glow, extrude=0.006, parent=root, col=col)
    text(f"{name}_sub", subtitle, 0.035, (0, -0.002, -0.085), m.label, extrude=0.002, parent=root, col=col)
    return root


def sconce(m, name, loc, rotz, col):
    root = _root(name, loc, rotz, col)
    box(f"{name}_plate", (0.08, 0.02, 0.14), (0, 0.01, 0), m.brass, bevel=0.008, parent=root, col=col)
    cone(f"{name}_shade", 0.06, 0.075, 0.10, (0, -0.07, -0.02), m.shade, segments=32, parent=root, col=col, caps=False)
    sphere(f"{name}_bulb", 0.025, (0, -0.07, 0.02), m.bulb, parent=root, col=col)
    return root


def cable_tray(m, name, x0, x1, y, z, col, cable_mats):
    """벽을 따라가는 사다리형 케이블 트레이와 케이블 다발."""
    root = _root(name, ((x0 + x1) / 2, y, z), 0, col)
    length = x1 - x0
    for sy in (-1, 1):
        box(f"{name}_rail_{sy}", (length, 0.008, 0.05), (0, sy * 0.07, 0), m.black_metal, bevel=0.002, parent=root, col=col)
    n = int(length / 0.14)
    for i in range(n + 1):
        box(f"{name}_rung_{i}", (0.012, 0.14, 0.008), (-length / 2 + i * length / n, 0, -0.02), m.black_metal, parent=root, col=col)
    for i in range(0, n + 1, 4):
        box(f"{name}_bracket_{i}", (0.02, 0.10, 0.02), (-length / 2 + i * length / n, 0.12, -0.02), m.black_metal, parent=root, col=col)
    for k in range(7):
        oy, oz = -0.045 + (k % 4) * 0.03, -0.008 + (k // 4) * 0.012
        pts = [(-length / 2, oy, oz), (-length / 4, oy + 0.004 * (k % 3), oz), (length / 4, oy - 0.003 * (k % 2), oz), (length / 2, oy, oz)]
        cable(f"{name}_cable_{k}", pts, 0.0055, cable_mats[k % len(cable_mats)], parent=root, col=col)
    return root
