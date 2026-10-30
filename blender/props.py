"""방 소품. 모든 소품은 로컬 좌표에서 정면이 -Y이고, 바닥 중앙이 원점이다.
root 빈 객체를 돌려 배치하므로 rotz=90이면 정면이 +X를 본다.
"""
import math

import bmesh
import bpy

import numpy as np

import textures as tx
from lib import box, cable, cone, cyl, empty, fabric_mat, image, lathe, mat, mesh, screen_mat, screen_plane, sphere, text, uv_box

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
        # 북유럽풍: 검은 것은 랙과 Grafana 모니터 테두리뿐이고, 나머지 금속·플라스틱은 따뜻한 흰색, 작은 부분은 연회색이다
        self.chrome = mat("chrome", (0.86, 0.86, 0.87), rough=0.12, metal=1.0)
        self.white_metal = mat("white_metal", (0.86, 0.85, 0.82), rough=0.35)
        self.white_plastic = mat("white_plastic", (0.89, 0.88, 0.85), rough=0.45)
        self.light_gray = mat("light_gray", (0.58, 0.58, 0.56), rough=0.5)
        self.fabric_sage = mat("fabric_sage", (0.40, 0.50, 0.38), rough=0.95)
        self.rug = mat("rug", (0.66, 0.58, 0.46), rough=1.0)
        self.rug_border = mat("rug_border", (0.40, 0.30, 0.21), rough=1.0)
        self.leaf = [mat("leaf_a", (0.10, 0.28, 0.09), rough=0.55), mat("leaf_b", (0.20, 0.42, 0.14), rough=0.55),
                     mat("leaf_c", (0.30, 0.50, 0.20), rough=0.6)]
        self.stem = mat("stem", (0.18, 0.30, 0.10), rough=0.7)
        self.soil = mat("soil", (0.07, 0.045, 0.03), rough=1.0)
        self.pots = [mat("pot_terracotta", (0.62, 0.32, 0.19), rough=0.8), mat("pot_cream", (0.86, 0.83, 0.76), rough=0.6),
                     mat("pot_sage", (0.45, 0.55, 0.43), rough=0.6), mat("pot_white", (0.84, 0.83, 0.79), rough=0.55)]
        self.books = [mat(f"book_{i}", c, rough=0.7) for i, c in enumerate([
            (0.42, 0.52, 0.40), (0.82, 0.76, 0.62), (0.62, 0.30, 0.18), (0.12, 0.20, 0.35),
            (0.78, 0.58, 0.22), (0.25, 0.25, 0.27), (0.70, 0.66, 0.58), (0.35, 0.22, 0.15)])]
        self.stone = mat("pot_stone", (0.66, 0.60, 0.51), rough=0.75)
        self.dracaena = mat("dracaena_leaf", (0.05, 0.17, 0.045), rough=0.5)
        self.dracaena_stripe = mat("dracaena_stripe", (0.24, 0.40, 0.05), rough=0.5)
        self.cane = mat("cane", (0.17, 0.13, 0.07), rough=0.85)
        self.raffia = mat("raffia", (0.80, 0.72, 0.52), rough=0.95)
        self.basket = self._fabric("basket_seagrass", (0.55, 0.42, 0.24), "weave", 14, 6)
        self.basket_dark = self._fabric("basket_band", (0.30, 0.22, 0.13), "weave", 14, 7)
        self.ficus = [mat("ficus_leaf_a", (0.045, 0.15, 0.04), rough=0.45), mat("ficus_leaf_b", (0.08, 0.22, 0.06), rough=0.45),
                      mat("ficus_leaf_c", (0.13, 0.30, 0.08), rough=0.5)]
        self.bark = mat("bark", (0.26, 0.19, 0.12), rough=0.9)
        self.pages = mat("book_pages", (0.86, 0.82, 0.71), rough=0.85)
        self.armchair_fabric = self._fabric("armchair_fabric", (0.40, 0.50, 0.38), "weave", 8, 3)
        self.pillow_fabric = self._fabric("pillow_fabric", (0.66, 0.60, 0.50), "weave", 10, 4)
        self.chair_mesh = self._fabric("chair_mesh", (0.36, 0.36, 0.35), "mesh", 10, 5)
        self.vacuum = mat("vacuum_white", (0.88, 0.88, 0.86), rough=0.35, coat=0.3)
        self.vacuum_led = mat("vacuum_led", (0.30, 1.0, 0.55), rough=0.3, emit=(0.30, 1.0, 0.55), strength=4.0)
        self.blind = mat("blind", (0.93, 0.91, 0.86), rough=0.6)
        self.rattan = self._rattan(glow)
        self.cream_vinyl = mat("speaker_wood", (0.36, 0.21, 0.11), rough=0.5)
        self.speaker_grille = self._fabric("speaker_grille", (0.66, 0.59, 0.46), "weave", 28, 8)
        self.akari = mat("akari_paper", (0.95, 0.92, 0.84), rough=0.9, emit=(1.0, 0.82, 0.60), strength=0.55 * glow)
        self.linen_dark = self._fabric("lamp_linen", (0.17, 0.14, 0.11), "weave", 20, 9)
        # 켜면 짙은 리넨 사이로 빛이 은은하게 비친다(밤 렌더에서만 발광, 웹은 스위치가 켠다)
        b = self.linen_dark.node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Color"].default_value = (1.0, 0.62, 0.32, 1.0)
        b.inputs["Emission Strength"].default_value = 0.12 * glow
        self.lining = mat("arc_lining", (0.96, 0.94, 0.90), rough=0.7, emit=(1.0, 0.84, 0.62), strength=1.0 * glow)
        self.wire = mat("black_wire", (0.03, 0.03, 0.035), rough=0.4, metal=0.6)
        self.keycap = mat("keycap_ivory", (0.86, 0.83, 0.75), rough=0.5)
        self.keycap_mod = mat("keycap_gray", (0.48, 0.47, 0.44), rough=0.5)
        self.keycap_accent = mat("keycap_accent", (0.78, 0.20, 0.12), rough=0.5)
        self.keyboard_case = mat("keyboard_case", (0.80, 0.77, 0.69), rough=0.4)
        self.shade = mat("lamp_shade", (0.92, 0.86, 0.74), rough=0.9, emit=(1.0, 0.78, 0.50), strength=1.6 * glow)
        self.bulb = mat("bulb", (1.0, 0.95, 0.85), rough=0.3, emit=(1.0, 0.80, 0.55), strength=0.5 + 25.0 * glow)
        self.sign_glow = mat("sign_glow", (0.95, 0.88, 0.72), rough=0.5, emit=(1.0, 0.72, 0.40), strength=6.0 * glow)
        self.label = mat("label_ink", (0.90, 0.87, 0.80), rough=0.6)
        self.screen_boost = 1.0 if night else 0.6

    @staticmethod
    def _rattan(glow):
        """엮은 라탄 갓 재질: 바탕색 그림 + 틈만 빛나는 발광 그림(낮에도 그림이 GLB에 남도록 아주 약하게 켠다)."""
        from lib import node_mat
        col, light = tx.rattan()
        mt = node_mat("rattan_shade")
        nt = mt.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        c = nt.nodes.new("ShaderNodeTexImage")
        c.image = image("tex_rattan", 512, 512, col)
        e = nt.nodes.new("ShaderNodeTexImage")
        e.image = image("tex_rattan_glow", 512, 512, light)
        nt.links.new(c.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(e.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = max(2.5 * glow, 0.001)
        bsdf.inputs["Roughness"].default_value = 0.8
        return mt

    @staticmethod
    def _fabric(name, color, kind, cells, seed):
        col, nrm = tx.fabric(color, kind=kind, cells=cells, seed=seed)
        return fabric_mat(name, image(f"tex_{name}", 256, 256, col), image(f"tex_{name}_normal", 256, 256, nrm),
                          rough=0.95 if kind == "weave" else 0.8)


def _link_to(ob, parent, col):
    (col or bpy.context.scene.collection).objects.link(ob)
    ob.parent = parent
    return ob


def _root(name, loc, rotz, col):
    r = empty(name, loc, col=col)
    r.rotation_euler = (0, 0, R(rotz))
    return r


# ---------------------------------------------------------------- 식물

def _leaf(name, length, width, elev, droop, yaw, base, material, root, col, twist=0.0, n=14, stripe=None):
    """잎 한 장: 가장 넓은 곳이 아래쪽 40%쯤인 뾰족한 잎. 가운데 잎맥을 따라 살짝 V자로 접히고,
    가장자리는 아래로 말리며, 끝으로 갈수록 처지고 비틀린다."""
    across = (-1.0, -0.2, 0.0, 0.2, 1.0) if stripe else (-1.0, -0.5, 0.0, 0.5, 1.0)
    verts, faces = [], []
    for i in range(n + 1):
        t = i / n
        s = t * length
        y = s * math.cos(elev)
        z = s * math.sin(elev) - droop * s * s
        hw = width / 2 * math.sin(math.pi * t ** 0.75) ** 0.75 + 0.0015
        tw = twist * t
        for k in across:
            x, dz = k * hw, hw * (0.22 * abs(k) - 0.30 * k * k)
            verts.append((x * math.cos(tw) - dz * math.sin(tw), y, z + x * math.sin(tw) + dz * math.cos(tw)))
    w = len(across)
    for i in range(n):
        for k in range(w - 1):
            a = i * w + k
            faces.append((a, a + 1, a + w + 1, a + w))
    ob = mesh(name, verts, faces, base, material, rot=(0, 0, yaw), parent=root, col=col)
    if stripe:  # 가운데 두 칸(잎맥 양옆)은 밝은 줄무늬
        ob.data.materials.append(stripe)
        for f, poly in enumerate(ob.data.polygons):
            poly.material_index = 1 if f % (w - 1) in (1, 2) else 0
    return ob


def planter(m, name, style, pr, ph, root, col):
    """화분 네 가지(테라코타, 크림, 세이지, 차콜). 벽 두께와 테두리가 보이게 단면을 돌려 만든다. 흙 윗면 높이를 돌려준다."""
    mt = m.pots[style % len(m.pots)]
    s = style % 4
    if s == 0:  # 받침 접시 위의 테라코타: 위쪽에 두꺼운 띠
        lathe(f"{name}_saucer", [(0, 0), (pr * 0.92, 0), (pr * 0.97, 0.016), (pr * 0.93, 0.018), (pr * 0.86, 0.007), (0, 0.007)],
              (0, 0, 0), mt, parent=root, col=col)
        prof = [(0, 0.007), (pr * 0.70, 0.007), (pr * 0.73, 0.013), (pr * 0.86, ph * 0.76), (pr * 0.97, ph * 0.78), (pr, ph * 0.8),
                (pr, ph), (pr * 0.92, ph), (pr * 0.88, ph * 0.9), (0, ph * 0.9)]
        inner = pr * 0.88
    elif s == 1:  # 둥근 배와 좁은 입의 도자기
        prof = [(0, 0), (pr * 0.58, 0), (pr * 0.64, 0.008), (pr * 0.92, ph * 0.3), (pr, ph * 0.58), (pr * 0.93, ph * 0.86),
                (pr * 0.84, ph * 0.96), (pr * 0.86, ph), (pr * 0.78, ph), (pr * 0.76, ph * 0.9), (0, ph * 0.9)]
        inner = pr * 0.76
    elif s == 2:  # 굽이 있고 위로 살짝 벌어지는 원통
        prof = [(0, 0), (pr * 0.80, 0), (pr * 0.82, 0.01), (pr * 0.79, 0.014), (pr * 0.84, 0.02), (pr * 0.97, ph * 0.97), (pr, ph),
                (pr * 0.91, ph), (pr * 0.89, ph * 0.9), (0, ph * 0.9)]
        inner = pr * 0.89
    else:  # 곧은 원통, 얇은 테두리
        prof = [(0, 0), (pr * 0.86, 0), (pr * 0.93, 0.012), (pr * 0.95, ph), (pr * 0.90, ph), (pr * 0.89, ph * 0.9), (0, ph * 0.9)]
        inner = pr * 0.89
    lathe(f"{name}_pot", prof, (0, 0, 0), mt, parent=root, col=col)
    soil = ph * 0.9
    # 흙은 가운데가 살짝 볼록하다
    lathe(f"{name}_soil", [(0, soil - 0.004), (inner * 0.99, soil - 0.004), (inner * 0.99, soil + 0.002), (inner * 0.6, soil + 0.006),
                           (0, soil + 0.008)], (0, 0, 0), m.soil, parent=root, col=col)
    return soil


def plant(m, name, loc, col, height=1.0, pot=0, seed=1, rotz=0, reach=1.0):
    """화분 식물. height는 화분과 잎 크기, reach는 줄기가 뻗는 높이 배율이다(키 큰 식물은 reach를 키운다).
    웹에서 누르면 흔들리므로 화분 바닥 중심을 축으로 하는 부분(part__)이다."""
    rng = np.random.default_rng(seed)
    root = _root(f"part__{name}", loc, rotz, col)
    pr = 0.09 + 0.08 * height
    ph = 0.12 + 0.18 * height
    soil = planter(m, name, pot, pr, ph, root, col)
    count = int((8 + 10 * height) * (0.6 + 0.4 * reach))
    grow = height * reach
    for i in range(count):
        yaw = rng.uniform(0, 2 * math.pi)
        rise = rng.uniform(0.15, 1.0) ** 0.7  # 키 큰 줄기가 많고 짧은 줄기는 적게
        stem_h = ph + (0.05 + 0.5 * rise) * grow
        lean = rng.uniform(0.02, 0.07) * (1 + height) * (0.5 + 0.5 * reach) * (1.2 - 0.5 * rise)
        bx, by = -math.sin(yaw) * lean, math.cos(yaw) * lean
        # 줄기는 아래에서 곧게 오르다 끝에서 바깥으로 휜다
        cable(f"{name}_stem_{i}", [(0, 0, soil), (bx * 0.25, by * 0.25, ph + (stem_h - ph) * 0.6), (bx, by, stem_h)],
              0.0022 + 0.0018 * height * (0.7 + 0.3 * reach), m.stem, parent=root, col=col)
        size = 0.6 + 0.6 * height * (0.75 + 0.25 * reach)
        _leaf(f"{name}_leaf_{i}", rng.uniform(0.10, 0.17) * size, rng.uniform(0.045, 0.07) * (0.7 + 0.5 * height),
              R(rng.uniform(20, 60)), rng.uniform(1.0, 3.0) / (0.6 + height), yaw, (bx, by, stem_h),
              m.leaf[int(rng.integers(0, 3))], root, col, twist=rng.uniform(-0.5, 0.5))
    return root


def dracaena(m, name, loc, col, seed=1):
    """행운목(드라세나 마상게아나): 키가 다른 마디진 줄기 세 개 끝에 길고 휘어지는 줄무늬 잎 다발.
    해초를 엮은 배불뚝이 바구니(손잡이 둘, 아래쪽은 짙은 띠)에 담는다.
    웹에서 누르면 흔들리므로 바구니 바닥 중심을 축으로 하는 부분(part__)이다."""
    rng = np.random.default_rng(seed)
    root = _root(f"part__{name}", loc, 0, col)
    rb, hb = 0.19, 0.34  # 바구니 최대 반지름, 높이

    def wall(z):
        return rb * (0.80 + 0.20 * math.sin(math.pi * min(z / (hb * 0.95), 1.0) * 0.92))

    low = [(0, 0), (rb * 0.72, 0)] + [(wall(z), z) for z in np.linspace(0.01, hb * 0.32, 5)]
    up = [(wall(z), z) for z in np.linspace(hb * 0.32, hb, 9)]
    lathe(f"{name}_basket_low", low + [(wall(hb * 0.32) * 0.95, hb * 0.32), (0, hb * 0.32)], (0, 0, 0), m.basket_dark, parent=root, col=col)
    rim = [(wall(hb) * 0.94, hb), (wall(hb) * 0.92, hb * 0.86), (0, hb * 0.86)]
    upper = lathe(f"{name}_basket", [(0, hb * 0.32 - 0.001)] + up + rim, (0, 0, 0), m.basket, parent=root, col=col)
    uv_box(upper, 0.05)
    for ob in root.children:
        if ob.name.endswith("_basket_low"):
            uv_box(ob, 0.05)
    cable(f"{name}_basket_lip", [(wall(hb) * math.cos(a), wall(hb) * math.sin(a), hb) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)],
          0.008, m.basket, parent=root, col=col, cyclic=True)
    for sx in (-1, 1):  # 손잡이: 테두리 양옆에서 솟은 꼰 고리
        x = sx * wall(hb) * 0.98
        cable(f"{name}_handle_{sx}", [(x, -0.07, hb - 0.005), (x + sx * 0.02, -0.05, hb + 0.06), (x + sx * 0.02, 0.05, hb + 0.06), (x, 0.07, hb - 0.005)],
              0.006, m.basket, parent=root, col=col)
    soil = hb * 0.86
    cyl(f"{name}_soil", wall(hb) * 0.9, 0.01, (0, 0, soil + 0.005), m.soil, segments=32, parent=root, col=col)
    # 줄기 세 개: (밑동 위치, 높이, 기울기 방향). 방 안쪽(+X)과 창 쪽(+Y)으로 벌어진다.
    canes = [((0.02, 0.03), 1.25, (0.05, 0.06)), ((0.05, -0.04), 0.95, (0.12, -0.02)), ((-0.04, -0.01), 0.70, (0.06, -0.08))]
    for c, ((bx, by), tall, (lx, ly)) in enumerate(canes):
        tip = (bx + lx, by + ly, soil + tall)
        cable(f"{name}_cane_{c}", [(bx, by, soil), (bx + lx * 0.35, by + ly * 0.35, soil + tall * 0.5), tip], 0.019, m.cane, parent=root, col=col)
        for k in range(int(tall / 0.035)):  # 마디
            t = (k + 0.5) * 0.035 / tall
            ring = cyl(f"{name}_ring_{c}_{k}", 0.021, 0.004, (bx + lx * t * t, by + ly * t * t, soil + tall * t), m.cane, segments=12,
                       parent=root, col=col)
            ring.rotation_euler = (math.atan2(-ly, 1.0) * 0.5, math.atan2(lx, 1.0) * 0.5, 0)
        # 줄기 끝 잎 다발: 어린 잎은 위로 서고, 오래된 잎은 바깥으로 휘어 처진다
        count = 16 if tall > 1.0 else 13
        for i in range(count):
            age = i / (count - 1)
            yaw = i * 2.4 + rng.uniform(-0.3, 0.3)
            length = rng.uniform(0.26, 0.38) * (0.8 + 0.3 * age)
            _leaf(f"{name}_leaf_{c}_{i}", length, rng.uniform(0.065, 0.085), R(62 - 70 * age + rng.uniform(-8, 8)),
                  rng.uniform(0.8, 1.6) * (0.4 + 0.9 * age), yaw, (tip[0], tip[1], tip[2] - 0.05 * age),
                  m.dracaena, root, col, twist=rng.uniform(-0.4, 0.4), n=10, stripe=m.dracaena_stripe)
    return root


def ficus(m, name, loc, col, seed=1):
    """벤자민 고무나무(외대 수형): 키 큰 석재 화분, 곧은 줄기, 위쪽의 둥글고 촘촘한 잎 덩어리.
    웹에서 누르면 흔들리므로 화분 바닥 중심을 축으로 하는 부분(part__)이다."""
    rng = np.random.default_rng(seed)
    root = _root(f"part__{name}", loc, 0, col)
    pr, ph = 0.16, 0.42
    lathe(f"{name}_pot", [(0, 0), (pr * 0.82, 0), (pr * 0.9, 0.012), (pr * 0.97, ph * 0.5), (pr, ph), (pr * 0.92, ph), (pr * 0.91, ph * 0.93), (0, ph * 0.93)],
          (0, 0, 0), m.stone, parent=root, col=col)
    soil = ph * 0.93
    lathe(f"{name}_soil", [(0, soil - 0.004), (pr * 0.9, soil - 0.004), (pr * 0.9, soil + 0.004), (0, soil + 0.01)], (0, 0, 0), m.soil, parent=root, col=col)
    top = 1.22
    cable(f"{name}_trunk", [(0, 0, soil), (0.012, -0.006, 0.75), (-0.006, 0.008, 1.0), (0.004, 0.0, top)], 0.017, m.bark, parent=root, col=col)
    # 수관: 살짝 위로 긴 타원체(가로 반지름 0.30, 세로 0.36). 안쪽 가지 몇 개와 바깥 껍질 쪽에 몰린 작은 잎들.
    cx, cz, rx, rz = 0.0, top + 0.26, 0.30, 0.36
    for i in range(7):
        a = rng.uniform(0, 2 * math.pi)
        end = (math.cos(a) * rx * 0.55, math.sin(a) * rx * 0.55, cz + rng.uniform(-0.15, 0.2))
        cable(f"{name}_branch_{i}", [(0, 0, top - 0.04), (end[0] * 0.4, end[1] * 0.4, (top + end[2]) / 2), end], 0.006, m.bark, parent=root, col=col)
    for i in range(700):
        # 껍질 쪽에 몰리게 반지름을 고르고, 아래쪽은 조금 성기게
        u = rng.uniform(-1, 1) ** 1
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.5, 1.0) ** 0.6
        if u < -0.6 and rng.random() < 0.5:
            continue
        horiz = math.sqrt(max(0.0, 1 - u * u))
        dx, dy, dz = math.cos(a) * horiz, math.sin(a) * horiz, u
        base = (cx + dx * rx * r, dy * rx * r, cz + dz * rz * r)
        _leaf(f"{name}_leaf_{i}", rng.uniform(0.055, 0.085), rng.uniform(0.026, 0.036), R(rng.uniform(-25, 35) + 25 * dz),
              rng.uniform(1.5, 4.0), math.atan2(-dx, dy) + rng.uniform(-0.6, 0.6), base,
              m.ficus[int(rng.choice(3, p=[0.45, 0.4, 0.15]))], root, col, twist=rng.uniform(-0.6, 0.6), n=5)
    return root


# ---------------------------------------------------------------- 작업 공간

def monitor(m, name, loc, rotz, img, root, col, w=0.56, h=0.33):
    r = empty(name, loc, parent=root, col=col)
    r.rotation_euler = (0, 0, R(rotz))
    box(f"{name}_base", (0.22, 0.16, 0.012), (0, 0.04, 0.006), m.white_metal, bevel=0.005, parent=r, col=col)
    box(f"{name}_neck", (0.045, 0.025, 0.26), (0, 0.075, 0.13), m.white_metal, bevel=0.006, parent=r, col=col)
    zc = 0.12 + h / 2 + 0.03
    box(f"{name}_body", (w, 0.03, h), (0, 0.04, zc), m.white_plastic, bevel=0.008, parent=r, col=col)
    smat = screen_mat(f"{name}_screen_mat", img, strength=m.screen_boost)
    screen_plane(f"{name}_screen", w - 0.025, h - 0.035, (0, 0.0245, zc + 0.004), smat, parent=r, col=col)
    return r


def mouse(m, name, loc, root, col):
    """흰 무선 마우스(로지텍 M750 느낌): 뒤가 볼록하고 앞이 좁은 몸통, 가운데 버튼 홈, 회색 휠, 바닥은 평평하다."""
    r = empty(name, loc, parent=root, col=col)
    me = bpy.data.meshes.new(f"{name}_shell")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=1.0)
    L, W, H = 0.056, 0.032, 0.036  # 반길이, 반너비, 높이
    for vtx in bm.verts:
        x, y, z = vtx.co
        width = W * (1.0 - 0.16 * max(y, 0.0)) * (1.0 + 0.04 * min(y, 0.0))  # 앞(+Y)이 좁다
        hump = H * (1.0 - 0.28 * y) * 0.85  # 손바닥이 닿는 뒤쪽이 높다
        vtx.co = (x * width, y * L, max(z, 0.0) * hump + 0.0015)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    shell = bpy.data.objects.new(f"{name}_shell", me)
    _link_to(shell, r, col)
    shell.data.materials.append(m.white_plastic)
    # 왼쪽·오른쪽 버튼 사이 홈(몸통 윗면을 따라가는 가는 선)과 그 사이로 살짝 나온 휠
    def top(yn):
        return math.sqrt(max(0.0, 1 - yn * yn)) * H * (1.0 - 0.28 * yn) * 0.85 + 0.0015

    cable(f"{name}_split", [(0, yn * L, top(yn) + 0.0003) for yn in (0.30, 0.45, 0.60, 0.75)], 0.0007, m.light_gray, parent=r, col=col)
    cyl(f"{name}_wheel", 0.0055, 0.006, (0, 0.43 * L, top(0.43) - 0.0032), m.charcoal, axis="X", segments=20, bevel=0.0015, parent=r, col=col)
    return r


def keyboard(m, name, loc, root, col):
    """베이지 로우프로파일 키보드(75% 배열 다섯 줄): 아이보리 글자 키, 회색 기능 키, 빨간 Esc·Enter."""
    r = empty(name, loc, parent=root, col=col)
    u = 0.0185
    box(f"{name}_case", (15 * u + 0.012, 5 * u + 0.012, 0.012), (0, 0, 0.006), m.keyboard_case, bevel=0.004, segments=3, parent=r, col=col)
    rows = [  # 뒤(+Y)에서 앞 줄 순서. (너비 u 목록, 기능 키 위치, 강조 키 위치)
        ([1] * 13 + [2], {13}, {0}),
        ([1.5] + [1] * 12 + [1.5], {0, 13}, set()),
        ([1.75] + [1] * 11 + [2.25], {0}, {12}),
        ([2.25] + [1] * 10 + [2.75], {0, 11}, set()),
        ([1.25] * 3 + [6.25] + [1.25] * 4, {0, 1, 2, 4, 5, 6, 7}, set()),
    ]
    for ri, (widths, mods, accents) in enumerate(rows):
        x = -7.5 * u
        y = (2 - ri) * u
        for k, w in enumerate(widths):
            mt = m.keycap_accent if k in accents else m.keycap_mod if k in mods else m.keycap
            box(f"{name}_key_{ri}_{k}", (w * u - 0.0025, u - 0.0025, 0.0065), (x + w * u / 2, y, 0.0145), mt, bevel=0.0018, segments=2,
                parent=r, col=col)
            x += w * u
    return r

def mug(m, name, loc, root, col, material=None):
    """속이 빈 머그. 굽, 둥근 아래쪽, 테두리 두께가 보이고 커피는 테두리보다 조금 아래에 있다."""
    r = empty(name, loc, parent=root, col=col)
    mt = material or m.ivory
    lathe(f"{name}_cup", [(0, 0.004), (0.026, 0.0), (0.030, 0.0), (0.033, 0.005), (0.035, 0.016), (0.036, 0.080), (0.0355, 0.085),
                          (0.0325, 0.085), (0.032, 0.080), (0.031, 0.020), (0.026, 0.012), (0, 0.011)], (0, 0, 0), mt, parent=r, col=col)
    lathe(f"{name}_coffee", [(0, 0.064), (0.0315, 0.064), (0.0315, 0.068), (0, 0.068)], (0, 0, 0), m.wood_dark, parent=r, col=col)
    cable(f"{name}_handle", [(0.033, 0, 0.068), (0.057, 0, 0.064), (0.059, 0, 0.036), (0.034, 0, 0.026)], 0.0065, mt, parent=r, col=col)


def desk_lamp(m, name, loc, rotz, root, col):
    """크롬 관절 스탠드: 둥근 받침, 두 가닥 막대로 된 아래·위 팔과 관절, 앞(-Y) 아래를 보는 반구 갓."""
    r = empty(name, loc, parent=root, col=col)
    r.rotation_euler = (0, 0, R(rotz))
    lathe(f"{name}_base", [(0, 0), (0.075, 0), (0.075, 0.012), (0.06, 0.02), (0.02, 0.024), (0, 0.024)], (0, 0, 0), m.chrome, parent=r, col=col)
    hinge0, elbow, head = (0.0, 0.03, 0.035), (0.0, 0.10, 0.33), (0.0, -0.12, 0.40)

    def arm(part, a, b):
        for sx in (-1, 1):  # 두 가닥 막대
            cable(f"{name}_{part}_{sx}", [(a[0] + sx * 0.009, a[1], a[2]), (b[0] + sx * 0.009, b[1], b[2])], 0.0045, m.chrome, parent=r, col=col)
        # 가닥 사이의 스프링 대신 가는 막대 하나
        mid = tuple((p + q) / 2 for p, q in zip(a, b))
        cable(f"{name}_{part}_spring", [a, mid, b], 0.0025, m.chrome, parent=r, col=col)

    arm("lower", hinge0, elbow)
    arm("upper", elbow, head)
    for k, at in enumerate((hinge0, elbow, head)):  # 관절 나사
        cyl(f"{name}_joint_{k}", 0.012, 0.03, at, m.chrome, axis="X", segments=16, parent=r, col=col)
    # 반구 갓: 꼭대기가 위·뒤(+Y)로 25° 기울어 머리 관절에 붙고, 입은 앞 아래를 본다
    tilt, rad = R(-25), 0.07
    up = (0.0, -math.sin(tilt), math.cos(tilt))
    c = tuple(h - rad * u for h, u in zip(head, up))
    prof = [(rad * math.sin(math.pi / 2 * k / 8), rad * math.cos(math.pi / 2 * k / 8)) for k in range(9)]
    inner = [(x * 0.96, z * 0.96) for x, z in reversed(prof)]
    dome = lathe(f"{name}_shade", [(0, rad)] + prof[1:] + inner[:-1] + [(0, rad * 0.96)], c, m.chrome, segments=40, parent=r, col=col)
    dome.rotation_euler = (tilt, 0, 0)
    sphere(f"{name}_bulb", 0.022, tuple(p + 0.025 * u for p, u in zip(c, up)), m.bulb, parent=r, col=col)


def desk(m, name, loc, rotz, col, screen):
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
        box(f"{name}_leg_{sy}", (0.035, 0.035, top_z), (0.62, sy * 0.27, top_z / 2), m.white_metal, bevel=0.006, parent=root, col=col)
    box(f"{name}_leg_bar", (0.03, 0.54, 0.03), (0.62, 0, 0.08), m.white_metal, bevel=0.006, parent=root, col=col)
    z = top_z + 0.035
    # 정면을 보는 와이드 모니터 한 대(34인치급, 21:9)
    monitor(m, f"{name}_mon", (0.0, 0.10, z), 0, screen, root, col, w=0.84, h=0.36)
    keyboard(m, f"{name}_kbd", (0.0, -0.16, z), root, col)
    mouse(m, f"{name}_mouse", (0.30, -0.17, z), root, col)
    mug(m, f"{name}_mug", (-0.42, -0.16, z), root, col)
    # 스탠드는 오른쪽 뒤에서 키보드·마우스 쪽 책상을 비춘다(갓이 모니터에 닿지 않게 조금 앞으로 둔다)
    desk_lamp(m, f"{name}_lamp", (0.60, 0.20, z), -30, root, col)
    plant(m, f"{name}_plant", (-0.58, 0.18, z), col, height=0.15, pot=1, seed=5).parent = root
    return root


def _chair_back(m, name, parent, col, z0=0.52, height=0.54, y0=0.272):
    """메시 등판: 허리는 좁고 어깨는 넓으며 위는 둥근 돔이다. 가로로 몸을 감싸게 휘고, 허리께가 앞으로 살짝 나오며,
    뒤로 10° 눕는다. 메시 판은 두께를 주고, 가장자리는 검은 틀(닫힌 관)이 두른다."""
    nu, nv = 14, 24

    def half_width(v):
        if v <= 0.78:  # 허리(0.19) → 어깨(0.235)
            return 0.19 + 0.045 * (0.5 - 0.5 * math.cos(math.pi * max(0.0, v - 0.3) / 0.48)) if v > 0.3 else 0.19
        t = min((v - 0.78) / 0.22, 0.985)
        return 0.235 * (1 - t ** 4) ** 0.25  # 둥근 모서리의 돔

    def point(u, v):
        x = u * half_width(v)
        y = y0 + v * height * math.tan(R(10)) - 0.04 * u * u - 0.022 * math.exp(-((v - 0.32) / 0.14) ** 2)
        return (x, y, z0 + v * height)

    verts = [point(-1 + 2 * i / nu, j / nv) for j in range(nv + 1) for i in range(nu + 1)]
    faces = [(j * (nu + 1) + i, j * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i) for j in range(nv) for i in range(nu)]
    panel = mesh(f"{name}_back", verts, faces, (0, 0, 0), m.chair_mesh, parent=parent, col=col)
    uv_box(panel, 0.06)
    md = panel.modifiers.new("Solidify", "SOLIDIFY")
    md.thickness = 0.012
    md.offset = 0
    rim = [point(1, j / nv) for j in range(0, nv + 1, 2)] + [point(-1, j / nv) for j in range(nv, -1, -2)]
    cable(f"{name}_back_rim", rim, 0.011, m.white_plastic, parent=parent, col=col, cyclic=True)
    return panel


def chair(m, name, loc, rotz, col):
    """메시 등판 사무용 의자. 팔걸이는 좌판 아래에서 나온 L자 받침 위에 패드를 얹는다."""
    root = _root(name, loc, rotz, col)
    for i in range(5):
        a = R(90 + i * 72)
        x, y = math.cos(a) * 0.24, math.sin(a) * 0.24
        b = box(f"{name}_leg_{i}", (0.26, 0.04, 0.03), (x / 2, y / 2, 0.065), m.white_metal, bevel=0.01, parent=root, col=col)
        b.rotation_euler = (0, 0, a)
        sphere(f"{name}_caster_{i}", 0.028, (x, y, 0.03), m.light_gray, parent=root, col=col)
    cyl(f"{name}_gas", 0.022, 0.30, (0, 0, 0.23), m.white_metal, segments=20, parent=root, col=col)
    cyl(f"{name}_gas_cover", 0.032, 0.12, (0, 0, 0.14), m.light_gray, segments=24, bevel=0.004, parent=root, col=col)
    # 좌판 위쪽은 웹에서 빙글 돌리는 부분이다(축은 의자 중심)
    top = empty(f"part__{name}_top", (0, 0, 0), parent=root, col=col)
    box(f"{name}_mech", (0.20, 0.22, 0.04), (0, 0.02, 0.37), m.light_gray, bevel=0.01, parent=top, col=col)
    uv_box(box(f"{name}_seat", (0.50, 0.48, 0.08), (0, 0, 0.43), m.chair_mesh, bevel=0.04, segments=5, parent=top, col=col), 0.06)
    # 등받이: 좌판 뒤 아래에서 올라오는 받침대가 등판 허리께를 붙잡는다
    cable(f"{name}_spine", [(0, 0.10, 0.38), (0, 0.27, 0.41), (0, 0.29, 0.60)], 0.018, m.white_metal, parent=top, col=col)
    _chair_back(m, name, top, col)
    for sx in (-1, 1):
        cable(f"{name}_arm_{sx}", [(sx * 0.10, 0.03, 0.385), (sx * 0.27, 0.03, 0.40), (sx * 0.285, 0.03, 0.61)], 0.012, m.white_metal, parent=top, col=col)
        box(f"{name}_arm_pad_{sx}", (0.07, 0.24, 0.028), (sx * 0.285, 0.01, 0.628), m.light_gray, bevel=0.012, segments=3, parent=top, col=col)
    return root


# ---------------------------------------------------------------- 수납·가구

def _shelf_book(m, name, loc, size, rng, root, col, lean=0.0, lying=False):
    """양장본 한 권: 앞뒤 표지, 등(-Y), 그 사이 크림색 책장 덩어리. 등에는 띠나 제목 칸을 둔다.
    size는 (가로, 깊이, 높이)이고, lying이면 눕혀서 등이 앞을 본다(가로가 책 높이, 높이가 두께)."""
    w, d, h = size
    cover = m.books[int(rng.integers(0, len(m.books)))]
    r = empty(name, loc, parent=root, col=col)
    r.rotation_euler = (0, lean, 0)
    t = 0.0025  # 표지 두께
    if lying:
        for z in (t / 2, h - t / 2):
            box(f"{name}_board_{z:.3f}", (w, d, t), (0, 0, z), cover, bevel=0.0008, segments=1, parent=r, col=col)
        box(f"{name}_pages", (w - 0.008, d - 0.006, h - 2 * t), (0.002, 0.002, h / 2), m.pages, parent=r, col=col)
    else:
        for x in (-w / 2 + t / 2, w / 2 - t / 2):
            box(f"{name}_board_{x:.3f}", (t, d, h), (x, 0, h / 2), cover, bevel=0.0008, segments=1, parent=r, col=col)
        box(f"{name}_pages", (w - 2 * t, d - 0.006, h - 0.008), (0, 0.002, h / 2 - 0.001), m.pages, parent=r, col=col)
    box(f"{name}_spine", (w, 0.003, h), (0, -d / 2 + 0.0015, h / 2), cover, bevel=0.001, segments=1, parent=r, col=col)
    roll = rng.random()
    across, tall = (w, h) if not lying else (h, w)
    if roll < 0.55:  # 위아래 띠 두 줄
        band = m.brass if rng.random() < 0.5 else m.ivory
        for k in (0.12, 0.88):
            z = h * k if not lying else h / 2
            x = 0 if not lying else w * (k - 0.5)
            box(f"{name}_band_{k}", (w + 0.0004, 0.0012, 0.004) if not lying else (0.004, 0.0012, h + 0.0004),
                (x, -d / 2 - 0.0002, z), band, parent=r, col=col)
    elif roll < 0.85:  # 제목 칸
        if not lying:
            box(f"{name}_label", (w * 0.62, 0.0012, tall * 0.16), (0, -d / 2 - 0.0002, h * 0.66), m.ivory, parent=r, col=col)
        else:
            box(f"{name}_label", (tall * 0.3, 0.0012, across * 0.55), (0, -d / 2 - 0.0002, h / 2), m.ivory, parent=r, col=col)
    return r


def books(m, name, x0, x1, z, depth, col, root, seed):
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1 - 0.03:
        roll = rng.random()
        if roll < 0.08 and x < x1 - 0.22:  # 눕혀 쌓은 두세 권
            w = rng.uniform(0.15, 0.19)
            zz = z
            for k in range(int(rng.integers(2, 4))):
                th = rng.uniform(0.022, 0.034)
                _shelf_book(m, f"{name}_{x:.3f}_{k}", (x + w / 2, 0, zz), (w * rng.uniform(0.86, 1.0), depth * rng.uniform(0.75, 0.9), th),
                            rng, root, col, lying=True)
                zz += th
            x += w + 0.012
            continue
        if roll < 0.18 and x < x1 - 0.18:
            x += rng.uniform(0.06, 0.12)  # 빈 틈
            continue
        bw = rng.uniform(0.022, 0.045)
        bh = rng.uniform(0.15, 0.25)
        bd = depth * rng.uniform(0.75, 0.95)
        lean = R(-12) if rng.random() < 0.08 else 0.0
        _shelf_book(m, f"{name}_{x:.3f}", (x + bw / 2, 0, z + (0.01 if lean else 0)), (bw, bd, bh), rng, root, col, lean=lean)
        x += bw + 0.002


def wall_shelf(m, name, loc, rotz, col, length=1.1, seed=1, decor=True):
    root = _root(name, loc, rotz, col)
    box(f"{name}_board", (length, 0.24, 0.03), (0, 0, 0.015), m.wood, bevel=0.006, parent=root, col=col)
    for sx in (-1, 1):
        box(f"{name}_bracket_{sx}", (0.02, 0.18, 0.08), (sx * (length / 2 - 0.12), 0.02, -0.04), m.white_metal, bevel=0.004, parent=root, col=col)
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
    """굵은 평직 천을 씌운 안락의자. 모양은 단순한 상자형 그대로 두고 질감만 입힌다."""
    root = _root(name, loc, rotz, col)
    f = m.armchair_fabric

    def soft(part, size, at, bevel, rot=None, material=f, parent=root):
        return uv_box(box(f"{name}_{part}", size, at, material, bevel=bevel, parent=parent, col=col, rot=rot), 0.05)

    soft("base", (0.86, 0.80, 0.22), (0, 0, 0.21), 0.05)
    soft("cushion", (0.62, 0.66, 0.13), (0, -0.04, 0.38), 0.055)
    soft("back", (0.86, 0.20, 0.50), (0, 0.31, 0.50), 0.07, rot=(R(-6), 0, 0))
    for sx in (-1, 1):
        soft(f"arm_{sx}", (0.14, 0.78, 0.36), (sx * 0.37, 0.0, 0.40), 0.06)
        for sy in (-1, 1):
            cone(f"{name}_leg_{sx}_{sy}", 0.016, 0.022, 0.10, (sx * 0.34, sy * 0.30, 0), m.wood_dark, segments=12, parent=root, col=col)
    pillow = empty(f"part__{name}_pillow", (0.08, 0.17, 0.58), parent=root, col=col)
    soft("pillow_body", (0.36, 0.12, 0.30), (0, 0, 0), 0.06, rot=(R(-15), 0, R(8)), material=m.pillow_fabric, parent=pillow)
    return root


def _bent_leg(name, material, angle, parent, col, reach=0.17, inner=0.06, top=0.4725, bend=0.06, w=0.045, t=0.02):
    """구부린 합판 다리 하나(알토 스툴): 바닥에서 곧게 올라가 좌판 아래에서 둥글게 꺾여 가운데로 들어간다.
    납작한 직사각형 단면(폭 w, 두께 t)을 경로를 따라 쓸어 만든다. angle은 다리가 놓이는 방향."""
    path = [(reach, 0.0, 1.0, 0.0), (reach, top - bend, 1.0, 0.0)]  # (반지름, 높이, 바깥쪽 법선 r, z)
    for k in range(1, 9):
        a = math.pi / 2 * k / 8
        path.append((reach - bend + bend * math.cos(a), top - bend + bend * math.sin(a), math.cos(a), math.sin(a)))
    path.append((inner, top, 0.0, 1.0))
    ca, sa = math.cos(angle), math.sin(angle)
    verts, faces = [], []
    for r, z, nr, nz in path:
        for dn, dw in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            rr, zz, side = r + nr * dn * t / 2, z + nz * dn * t / 2, dw * w / 2
            verts.append((rr * ca - side * sa, rr * sa + side * ca, zz))
    n = len(path)
    for i in range(n - 1):
        for k in range(4):
            a0, a1 = i * 4 + k, i * 4 + (k + 1) % 4
            faces.append((a0, a1, a1 + 4, a0 + 4))
    faces += [(3, 2, 1, 0), ((n - 1) * 4, (n - 1) * 4 + 1, (n - 1) * 4 + 2, (n - 1) * 4 + 3)]
    ob = mesh(name, verts, faces, (0, 0, 0), material, smooth=False, parent=parent, col=col)
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width, md.segments, md.limit_method = 0.004, 2, "ANGLE"
    return ob


def side_table(m, name, loc, col):
    """책과 컵을 올린 알토 스툴: 둥근 좌판과 구부린 합판 다리 네 개."""
    root = _root(name, loc, 0, col)
    cyl(f"{name}_top", 0.21, 0.035, (0, 0, 0.50), m.wood, segments=48, bevel=0.01, parent=root, col=col)
    for i in range(4):
        _bent_leg(f"{name}_leg_{i}", m.wood, R(45 + 90 * i), root, col)
    mug(m, f"{name}_mug", (0.10, -0.10, 0.518), root, col, material=m.pots[2])
    books_root = empty(f"{name}_books", (-0.09, 0.04, 0.518), parent=root, col=col)
    box(f"{name}_book_a", (0.20, 0.14, 0.025), (0, 0, 0.0125), m.books[3], bevel=0.003, parent=books_root, col=col)
    book(m, f"{name}_book_b", (0, 0, 0.025), (0.17, 0.125, 0.022), m.books[1], books_root, col)
    return root


def book(m, name, loc, size, material, root, col):
    """덮개를 펼칠 수 있는 책. 등은 +X 모서리이고, 덮개는 등을 축으로 도는 부분(part__)이다."""
    w, d, h = size
    r = empty(name, loc, parent=root, col=col)
    box(f"{name}_back", (w, d, 0.003), (0, 0, 0.0015), material, bevel=0.001, parent=r, col=col)
    box(f"{name}_pages", (w - 0.008, d - 0.008, h - 0.006), (-0.003, 0, h / 2), m.ivory, parent=r, col=col)
    box(f"{name}_spine", (0.004, d, h), (w / 2 - 0.002, 0, h / 2), material, bevel=0.001, parent=r, col=col)
    hinge = empty(f"part__{name}_cover", (w / 2, 0, h), parent=r, col=col)
    box(f"{name}_cover_slab", (w, d, 0.003), (-w / 2, 0, -0.0015), material, bevel=0.001, parent=hinge, col=col)


def rug(m, name, loc, col, w=1.7, d=1.15, seed=4):
    """짠 러그: 윗면 그림 한 장(크림 바탕, 마름모 격자, 갈색 테두리와 선 두 줄, 고리 파일 질감)과 짧은 쪽 끝의 술."""
    rng = np.random.default_rng(seed)
    root = _root(name, loc, 0, col)
    color, normal = tx.rug(w, d, seed=seed)
    h, wp = color.shape[:2]
    material = fabric_mat("rug_woven", image("tex_rug", wp, h, color), image("tex_rug_normal", wp, h, normal), rough=1.0, strength=0.6)
    body = box(f"{name}_body", (w, d, 0.014), (0, 0, 0.007), material, bevel=0.004, segments=2, parent=root, col=col)
    me = body.data
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x + w / 2) / w, (co.y + d / 2) / d)
    for sx in (-1, 1):  # 술: 짧은 쪽 끝에 1.5cm 간격
        for k in range(int(d / 0.015)):
            y = -d / 2 + 0.01 + k * 0.015
            length = rng.uniform(0.04, 0.055)
            tassel = box(f"{name}_fringe_{sx}_{k}", (length, 0.004, 0.002), (sx * (w / 2 + length / 2 - 0.004), y, 0.001), m.raffia,
                         parent=root, col=col)
            tassel.rotation_euler = (0, 0, rng.uniform(-0.12, 0.12))
    return root


def arc_lamp(m, name, loc, reach, col):
    """아크 플로어 스탠드: 황동 원형 받침, 곧게 올라가다 앞으로 휘어 넘어가는 검은 기둥,
    끝에 매달린 짙은 토프색 리넨 드럼 갓. 갓은 위아래가 열려 있고 안쪽은 흰 안감이라, 켜면 위아래로 빛이 나오고
    바깥 리넨으로도 빛이 은은하게 샌다. reach는 받침에서 갓 중심까지의 (dx, dy)다."""
    root = _root(name, loc, 0, col)
    dx, dy = reach
    lathe(f"{name}_base", [(0, 0), (0.12, 0), (0.12, 0.012), (0.11, 0.026), (0.04, 0.036), (0.016, 0.042), (0, 0.042)], (0, 0, 0), m.brass,
          parent=root, col=col)
    top, shade_z, r, h = 1.70, 1.22, 0.16, 0.18  # 아치 꼭대기 높이, 갓 아래 끝 높이, 갓 반지름·높이
    tip = (dx, dy, top - 0.08)
    cable(f"{name}_pole", [(0, 0, 0.04), (0, 0, 1.10), (dx * 0.12, dy * 0.12, top - 0.10), (dx * 0.55, dy * 0.55, top), tip], 0.010,
          m.black_metal, parent=root, col=col)
    cyl(f"{name}_joint", 0.015, 0.025, (0, 0, 1.10), m.brass, segments=16, parent=root, col=col)
    cable(f"{name}_drop", [tip, (dx, dy, shade_z + h - 0.02)], 0.005, m.black_metal, parent=root, col=col)
    cyl(f"{name}_socket", 0.018, 0.05, (dx, dy, shade_z + h - 0.045), m.brass, segments=16, parent=root, col=col)
    # 갓 위쪽 고정 살: 소켓에서 갓 테두리로 가는 가는 막대 셋
    for k in range(3):
        a = R(90 + 120 * k)
        cable(f"{name}_spoke_{k}", [(dx, dy, shade_z + h - 0.02), (dx + (r - 0.004) * math.cos(a), dy + (r - 0.004) * math.sin(a), shade_z + h - 0.006)],
              0.0018, m.brass, parent=root, col=col)
    shade = cone(f"{name}_shade", r, r, h, (dx, dy, shade_z), m.linen_dark, segments=56, parent=root, col=col, caps=False)
    uv_box(shade, 0.05)
    cone(f"{name}_lining", r - 0.004, r - 0.004, h - 0.004, (dx, dy, shade_z + 0.002), m.lining, segments=56, parent=root, col=col, caps=False)
    for z in (shade_z - 0.003, shade_z + h - 0.003):  # 위아래 테두리 띠(속이 빈 고리라 빛을 막지 않는다)
        cone(f"{name}_rim_{z:.2f}", r + 0.002, r + 0.002, 0.006, (dx, dy, z), m.brass, segments=56, parent=root, col=col, caps=False)
    sphere(f"{name}_bulb", 0.028, (dx, dy, shade_z + 0.12), m.bulb, parent=root, col=col)  # 빛(점 조명)은 전구 아래 갓 안쪽
    return root


# ---------------------------------------------------------------- 보관: 지금 방에는 두지 않는 소품
# 다시 쓰려면 room.layout에 한 줄 넣는다. 예) props.akari(m, "akari", (1.50, 0.10, 0), col)
# (웹에서 켜고 끄려면 web/main.js SWITCHES·lamps·GLOW에 akari_paper를 다시 넣는다.) 모습은 docs/archive/akari.png.

def akari(m, name, loc, col):
    """이사무 노구치 아카리풍 종이 조명: 가로 살이 비치는 달걀형 한지 갓, 가는 검은 철사 다리 셋과 위 손잡이.
    다리는 짧게 해 갓 아래가 바닥에서 28cm 뜬다."""
    root = _root(name, loc, 0, col)
    z0, h, seg, rows, ribs = 0.28, 0.34, 48, 60, 14
    verts, faces = [], []
    for j in range(rows + 1):
        t = j / rows
        # 아래 입은 넓게 열리고(반지름 0.11), 가장 넓은 곳 0.135, 위는 둥글게 좁아진다(0.025)
        rr = (0.11 + 0.025 * math.sin(math.pi * min(t / 0.45, 1) / 2)) * (1 - t ** 3 * 0.82)
        rr = max(rr, 0.025) * (1 + 0.018 * math.cos(2 * math.pi * ribs * t))  # 대나무 살 자국
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((rr * math.cos(a), rr * math.sin(a), z0 + h * t))
    for j in range(rows):
        for i in range(seg):
            a, b = j * seg + i, j * seg + (i + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    mesh(f"{name}_shade", verts, faces, (0, 0, 0), m.akari, parent=root, col=col)
    sphere(f"{name}_bulb", 0.03, (0, 0, z0 + 0.12), m.bulb, parent=root, col=col)
    for k in range(3):  # 갓 아래 테두리에서 바닥으로 벌어지는 다리
        a = R(90 + k * 120)
        top = (0.105 * math.cos(a), 0.105 * math.sin(a), z0 + 0.005)
        foot = (0.20 * math.cos(a), 0.20 * math.sin(a), 0.0)
        cable(f"{name}_leg_{k}", [top, foot], 0.003, m.wire, parent=root, col=col)
        sphere(f"{name}_foot_{k}", 0.006, foot, m.wire, parent=root, col=col)
    cable(f"{name}_handle", [(-0.02, 0, z0 + h - 0.005), (-0.02, 0, z0 + h + 0.05), (0.02, 0, z0 + h + 0.05), (0.02, 0, z0 + h - 0.005)],
          0.0022, m.wire, parent=root, col=col)
    return root


def table_lamp(m, name, loc, col):
    """수납장 탁상등(이케아 뵈야 느낌): 니켈 원판 위의 달걀 모양 라탄 갓. 갓 위아래는 뚫려 있고, 켜면 엮은 틈으로 빛이 샌다."""
    root = _root(name, loc, 0, col)
    lathe(f"{name}_base", [(0, 0), (0.055, 0), (0.055, 0.01), (0.04, 0.026), (0.012, 0.03), (0, 0.03)], (0, 0, 0), m.chrome, parent=root, col=col)
    cyl(f"{name}_stem", 0.006, 0.07, (0, 0, 0.06), m.chrome, segments=12, parent=root, col=col)
    sphere(f"{name}_bulb", 0.025, (0, 0, 0.16), m.bulb, parent=root, col=col)
    # 달걀형 갓: 아래 입 반지름 0.05, 가장 넓은 곳 0.10(높이 60%), 위 입 0.035. 둘레(u)·높이(v) UV를 직접 준다.
    z0, h, seg, rows = 0.032, 0.32, 48, 24
    verts, faces, uvs = [], [], []
    for j in range(rows + 1):
        t = j / rows
        rr = 0.035 + 0.065 * math.sin(math.pi * min(t ** 0.85 * 1.02, 1.0)) ** 0.75 + 0.015 * (1 - t)
        for i in range(seg + 1):
            a = 2 * math.pi * i / seg
            verts.append((rr * math.cos(a), rr * math.sin(a), z0 + h * t))
    for j in range(rows):
        for i in range(seg):
            a = j * (seg + 1) + i
            faces.append((a, a + 1, a + seg + 2, a + seg + 1))
    shade = mesh(f"{name}_shade", verts, faces, (0, 0, 0), m.rattan, parent=root, col=col)
    uv = shade.data.uv_layers.new(name="UVMap")
    for poly in shade.data.polygons:
        for li in poly.loop_indices:
            vi = shade.data.loops[li].vertex_index
            uv.data[li].uv = ((vi % (seg + 1)) / seg, (vi // (seg + 1)) / rows)
    return root

def _pleated_shade(name, r_bottom, r_top, height, z0, material, parent, col, pleats=36, segments=144):
    """주름진 원뿔대 갓(위아래가 뚫린 한 겹 면)."""
    verts, faces = [], []
    for z, rr in ((z0, r_bottom), (z0 + height, r_top)):
        for i in range(segments):
            a = 2 * math.pi * i / segments
            k = rr * (1 + 0.035 * math.cos(pleats * a))
            verts.append((k * math.cos(a), k * math.sin(a), z))
    faces = [(i, (i + 1) % segments, segments + (i + 1) % segments, segments + i) for i in range(segments)]
    return mesh(name, verts, faces, (0, 0, 0), material, parent=parent, col=col)


def floor_lamp(m, name, loc, col):
    """황동 플로어 스탠드: 둥글게 솟은 받침, 가는 기둥과 마디, 위가 좁은 주름 흰 갓, 당김줄."""
    root = _root(name, loc, 0, col)
    lathe(f"{name}_base", [(0, 0), (0.13, 0), (0.13, 0.012), (0.11, 0.03), (0.06, 0.05), (0.025, 0.065), (0.02, 0.08), (0, 0.08)],
          (0, 0, 0), m.brass, parent=root, col=col)
    cyl(f"{name}_pole", 0.011, 1.22, (0, 0, 0.08 + 0.61), m.brass, segments=16, parent=root, col=col)
    for z in (0.50, 0.95):  # 기둥 마디
        cyl(f"{name}_ring_{z}", 0.016, 0.02, (0, 0, z), m.brass, segments=16, bevel=0.004, parent=root, col=col)
    cyl(f"{name}_socket", 0.024, 0.06, (0, 0, 1.33), m.brass, segments=16, parent=root, col=col)
    _pleated_shade(f"{name}_shade", 0.20, 0.11, 0.36, 1.24, m.shade, root, col)
    sphere(f"{name}_bulb", 0.035, (0, 0, 1.38), m.bulb, parent=root, col=col)
    cable(f"{name}_chain", [(0.06, 0, 1.33), (0.07, 0, 1.24), (0.07, 0, 1.13)], 0.0012, m.brass, parent=root, col=col)
    sphere(f"{name}_chain_bead", 0.006, (0.07, 0, 1.125), m.brass, parent=root, col=col)
    return root


def vacuum(m, loc, col):
    """흰 로봇 청소기(에코백스 느낌): 흰 몸통과 윗면, 옆을 두른 짙은 범퍼 띠, 흰 라이다. 정면(-Y)에 상태 LED.
    웹에서 통째로 움직이므로 중심을 축으로 둔다(part__)."""
    root = empty("part__vacuum", loc, col=col)
    cyl("vacuum_body", 0.165, 0.062, (0, 0, 0.041), m.vacuum, segments=48, bevel=0.012, parent=root, col=col)
    cyl("vacuum_bumper", 0.168, 0.026, (0, 0, 0.028), m.charcoal, segments=48, bevel=0.005, parent=root, col=col)
    cyl("vacuum_seam", 0.135, 0.002, (0, 0, 0.0725), m.light_gray, segments=48, parent=root, col=col)
    cyl("vacuum_lid", 0.132, 0.003, (0, 0, 0.0735), m.vacuum, segments=48, parent=root, col=col)
    cyl("vacuum_lidar", 0.042, 0.022, (0, 0.05, 0.084), m.vacuum, segments=32, bevel=0.006, parent=root, col=col)
    cyl("vacuum_lidar_band", 0.0425, 0.006, (0, 0.05, 0.08), m.charcoal, segments=32, parent=root, col=col)
    cyl("vacuum_button", 0.013, 0.004, (0, -0.07, 0.076), m.light_gray, segments=20, parent=root, col=col)
    cyl("vacuum_led", 0.007, 0.004, (0, -0.105, 0.076), m.vacuum_led, segments=16, parent=root, col=col)
    return root

def dock(m, name, loc, rotz, col):
    """자동 먼지 비움 스테이션: 흰 기둥형 몸통, 연회색 뚜껑 아래 물통 두 개, 앞쪽 아래는 청소기가 들어가는 짙은 입구.
    뒤(+Y)를 벽에 붙인다."""
    root = _root(name, loc, rotz, col)
    w, d, h = 0.34, 0.24, 0.42
    box(f"{name}_body", (w, d, h - 0.02), (0, 0, (h - 0.02) / 2), m.vacuum, bevel=0.03, segments=4, parent=root, col=col)
    box(f"{name}_lid", (w - 0.01, d - 0.01, 0.025), (0, 0, h - 0.012), m.light_gray, bevel=0.01, segments=3, parent=root, col=col)
    for sx in (-1, 1):  # 깨끗한 물·더러운 물 통
        box(f"{name}_tank_{sx}", (w / 2 - 0.03, 0.006, 0.12), (sx * w / 4, -d / 2 - 0.002, h - 0.10), m.light_gray, bevel=0.004, parent=root, col=col)
    box(f"{name}_mouth", (0.24, 0.006, 0.10), (0, -d / 2 - 0.002, 0.06), m.charcoal, bevel=0.01, segments=3, parent=root, col=col)
    cyl(f"{name}_logo", 0.008, 0.003, (0, -d / 2 - 0.004, 0.20), m.light_gray, axis="Y", segments=16, parent=root, col=col)
    return root

def blinds(m, name, x0, x1, z_top, y, col, count=27, stack=0.0055):
    """창 위에 걷어 올린 블라인드. 살과 아래 막대는 웹에서 내리고 기울이는 부분(part__)이다."""
    root = _root(name, (0, 0, 0), 0, col)
    w, cx = x1 - x0, (x0 + x1) / 2
    box(f"{name}_rail", (w + 0.03, 0.045, 0.035), (cx, y, z_top + 0.0175), m.blind, bevel=0.006, parent=root, col=col)
    cable(f"{name}_cord", [(x1 - 0.04, y - 0.02, z_top), (x1 - 0.04, y - 0.025, z_top - 0.35), (x1 - 0.04, y - 0.025, z_top - 0.62)],
          0.002, m.blind, parent=root, col=col)
    for i in range(count):
        box(f"part__blind_{i:02d}", (w, 0.045, 0.003), (cx, y, z_top - 0.006 - i * stack), m.blind, col=col)
    box("part__blind_bottom", (w + 0.01, 0.05, 0.012), (cx, y, z_top - 0.012 - count * stack), m.blind, bevel=0.004, col=col)
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


def speaker(m, loc, rotz, col):
    """수납장 위 가로형 블루투스 스피커(마셜 스탠모어 브라운 느낌): 호두나무 빛 몸통, 베이지 짠 그릴, 테두리 띠,
    윗면 앞쪽 황동 조작판과 손잡이 넷. 웹에서 누르면 음악에 맞춰 들썩이는 부분(part__)이다."""
    root = empty("part__speaker", loc, col=col)
    root.rotation_euler = (0, 0, R(rotz))
    w, d, h = 0.265, 0.15, 0.15
    box("speaker_body", (w, d, h), (0, 0, h / 2 + 0.006), m.cream_vinyl, bevel=0.018, segments=4, parent=root, col=col)
    grille = box("speaker_grille", (w - 0.03, 0.006, h - 0.04), (0, -d / 2 - 0.001, h / 2 + 0.002), m.speaker_grille, bevel=0.003,
                 parent=root, col=col)
    uv_box(grille, 0.03)
    box("speaker_piping", (w - 0.022, 0.004, h - 0.032), (0, -d / 2 + 0.001, h / 2 + 0.002), m.brass, bevel=0.004, parent=root, col=col)
    box("speaker_badge", (0.05, 0.003, 0.012), (0, -d / 2 - 0.0045, h * 0.72), m.brass, bevel=0.001, parent=root, col=col)
    box("speaker_panel", (w * 0.62, 0.035, 0.004), (0, -d / 2 + 0.025, h + 0.007), m.brass, bevel=0.0015, parent=root, col=col)
    for k in range(4):
        x = -w * 0.25 + k * w * 0.125 + (0.02 if k == 3 else 0)
        if k < 3:
            cyl(f"speaker_knob_{k}", 0.009, 0.012, (x, -d / 2 + 0.025, h + 0.014), m.brass, segments=20, bevel=0.002, parent=root, col=col)
        else:  # 전원 토글
            cyl(f"speaker_toggle", 0.0025, 0.016, (x, -d / 2 + 0.025, h + 0.016), m.brass, segments=10, parent=root, col=col)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"speaker_foot_{sx}_{sy}", 0.008, 0.006, (sx * (w / 2 - 0.03), sy * (d / 2 - 0.03), 0.003), m.charcoal, segments=16,
                parent=root, col=col)
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
        box(f"{name}_rail_{sy}", (length, 0.008, 0.05), (0, sy * 0.07, 0), m.white_metal, bevel=0.002, parent=root, col=col)
    n = int(length / 0.14)
    for i in range(n + 1):
        box(f"{name}_rung_{i}", (0.012, 0.14, 0.008), (-length / 2 + i * length / n, 0, -0.02), m.white_metal, parent=root, col=col)
    for i in range(0, n + 1, 4):
        box(f"{name}_bracket_{i}", (0.02, 0.10, 0.02), (-length / 2 + i * length / n, 0.12, -0.02), m.white_metal, parent=root, col=col)
    for k in range(7):
        oy, oz = -0.045 + (k % 4) * 0.03, -0.008 + (k // 4) * 0.012
        pts = [(-length / 2, oy, oz), (-length / 4, oy + 0.004 * (k % 3), oz), (length / 4, oy - 0.003 * (k % 2), oz), (length / 2, oy, oz)]
        cable(f"{name}_cable_{k}", pts, 0.0055, cable_mats[k % len(cable_mats)], parent=root, col=col)
    return root
