"""서버 랙 생성. 정면은 -Y, 위는 +Z, 단위는 미터. 랙 원점은 바닥 중앙."""
import math

from lib import box, cable, collection, cyl, empty, mat, text

U = 0.0445
FACE_W = 0.4826  # 19인치 전면판
FACE_T = 0.012
W, D = 0.66, 0.66  # 랙 외곽 폭·깊이
PLINTH = 0.085
MARGIN = 0.04  # 장비 칸 위아래 여백
RAIL_Y = -D / 2 + 0.045  # 장비 전면판 뒷면 위치

STATUS_COLOR = {
    "ok": (0.25, 1.0, 0.45),
    "warn": (1.0, 0.62, 0.12),
    "error": (1.0, 0.16, 0.12),
    "unknown": (0.45, 0.47, 0.5),
}


class Palette:
    def __init__(self, led_boost=1.0, interior=0.0):
        self.interior = interior
        self.strip = mat("interior_strip", (0.9, 0.9, 0.9), rough=0.5, emit=(1.0, 0.82, 0.62), strength=interior)
        self.body = mat("rack_body", (0.030, 0.032, 0.037), rough=0.42, metal=0.55, coat=0.15)
        self.body_inset = mat("rack_inset", (0.022, 0.024, 0.028), rough=0.6, metal=0.4)
        self.frame = mat("rack_frame", (0.015, 0.016, 0.019), rough=0.5, metal=0.6)
        self.face = mat("face_graphite", (0.050, 0.054, 0.062), rough=0.38, metal=0.5, coat=0.2)
        self.face_alt = mat("face_anthracite", (0.085, 0.088, 0.095), rough=0.35, metal=0.55, coat=0.2)
        self.face_cream = mat("face_cream", (0.78, 0.74, 0.66), rough=0.45, coat=0.1)
        self.sled = mat("drive_sled", (0.11, 0.115, 0.125), rough=0.4, metal=0.45)
        self.slot = mat("slot_dark", (0.006, 0.006, 0.007), rough=0.8)
        self.port = mat("port_black", (0.004, 0.004, 0.005), rough=0.55)
        self.steel = mat("steel", (0.62, 0.63, 0.65), rough=0.28, metal=1.0)
        self.label = mat("label_cream", (0.86, 0.82, 0.72), rough=0.6)
        self.ink = mat("ink", (0.04, 0.04, 0.045), rough=0.7)
        self.sign_ink = mat("sign_ink", (0.93, 0.90, 0.83), rough=0.5)
        self.sage = mat("sage", (0.36, 0.48, 0.36), rough=0.5)
        self.lcd = mat("lcd", (0.02, 0.05, 0.06), rough=0.2, emit=(0.35, 0.75, 0.85), strength=0.7 * led_boost)
        self.cables = [
            mat("cable_blue", (0.02, 0.09, 0.42), rough=0.5),
            mat("cable_sky", (0.05, 0.22, 0.62), rough=0.5),
            mat("cable_yellow", (0.92, 0.70, 0.18), rough=0.55),
            mat("cable_cream", (0.85, 0.82, 0.74), rough=0.6),
        ]
        self.led = {
            k: mat(f"led_{k}", (0.02, 0.02, 0.02), rough=0.3, emit=c, strength=16.0 * led_boost)
            for k, c in STATUS_COLOR.items()
        }
        self.led_act = mat("led_activity", (0.02, 0.02, 0.02), rough=0.3, emit=(0.3, 0.6, 1.0), strength=12.0 * led_boost)
        self.led_port = mat("led_port", (0.02, 0.02, 0.02), rough=0.3, emit=(0.4, 1.0, 0.35), strength=10.0 * led_boost)
        self.led_port_amber = mat("led_port_amber", (0.02, 0.02, 0.02), rough=0.3, emit=(1.0, 0.65, 0.15), strength=10.0 * led_boost)


# ---------------------------------------------------------------- 공통 부품

def faceplate(p, root, h, material, name):
    box(f"{name}_face", (FACE_W, FACE_T, h), (0, -FACE_T / 2, h / 2), material, bevel=0.0025, parent=root, col=p.col)
    # 손잡이 귀와 나사
    for sx in (-1, 1):
        x = sx * (FACE_W / 2 - 0.011)
        for zi, z in enumerate((h * 0.25, h * 0.75) if h > 0.06 else (h / 2,)):
            cyl(f"{name}_screw_{sx}_{zi}", 0.0032, 0.003, (x, -FACE_T - 0.0012, z), p.steel, axis="Y", segments=12, parent=root, col=p.col)
    # 장비 몸체(뒤쪽, 대부분 가려짐)
    box(f"{name}_chassis", (0.44, 0.55, h - 0.003), (0, 0.275, h / 2), p.frame, parent=root, col=p.col)


def handles(p, root, h, name):
    if h < 0.08:
        return
    for sx in (-1, 1):
        x = sx * (FACE_W / 2 - 0.032)
        box(f"{name}_handle_{sx}", (0.007, 0.007, h * 0.62), (x, -FACE_T - 0.011, h / 2), p.steel, bevel=0.003, parent=root, col=p.col)
        for z in (h * 0.19, h * 0.81):
            box(f"{name}_handle_post_{sx}_{z:.3f}", (0.006, 0.011, 0.006), (x, -FACE_T - 0.005, z), p.steel, bevel=0.002, parent=root, col=p.col)


def vents(p, root, x0, x1, h, name, rows_per_u=3):
    n = max(2, round(h / U * rows_per_u))
    pitch = (h - 0.012) / n
    for i in range(n):
        z = 0.006 + pitch * (i + 0.5)
        box(f"{name}_vent_{i}", (x1 - x0, 0.002, pitch * 0.42), ((x0 + x1) / 2, -FACE_T - 0.0002, z), p.slot, bevel=0.0008, segments=2, parent=root, col=p.col)


def status_panel(p, root, unit, h, x0, name, states):
    """서비스 이름표와 컨테이너별 상태 LED. LED 이름은 led__<container>."""
    label = unit.get("label")
    if not label:
        return
    zc = h - 0.014 if h > 0.05 else h * 0.62
    pw = 0.078
    box(f"{name}_labelplate", (pw, 0.0015, 0.0135), (x0 + pw / 2, -FACE_T - 0.0008, zc), p.label, bevel=0.001, segments=2, parent=root, col=p.col)
    size = 0.0072 if len(label) <= 11 else 0.0058
    text(f"{name}_labeltext", label, size, (x0 + pw / 2, -FACE_T - 0.0018, zc), p.ink, parent=root, col=p.col)
    zl = zc - 0.0135 if h > 0.05 else h * 0.2
    for i, c in enumerate(unit.get("containers", [])):
        x = x0 + 0.006 + i * 0.013
        state = states.get(c, "ok")
        box(f"led__{c}", (0.009, 0.003, 0.005), (x + 0.004, -FACE_T - 0.001, zl), p.led[state], bevel=0.001, segments=2, parent=root, col=p.col)
    # 전원 버튼
    cyl(f"{name}_power", 0.0042, 0.003, (x0 + pw - 0.006, -FACE_T - 0.0015, zl), p.steel, axis="Y", segments=16, parent=root, col=p.col)
    cyl(f"{name}_power_ring", 0.0047, 0.002, (x0 + pw - 0.006, -FACE_T - 0.0008, zl), p.led_act, axis="Y", segments=16, parent=root, col=p.col)


def drive_bays(p, root, x0, x1, h, name, rows, cols):
    gap = 0.003
    bw = (x1 - x0 - gap * (cols - 1)) / cols
    bh = (h - 0.010 - gap * (rows - 1)) / rows
    for r in range(rows):
        for c in range(cols):
            x = x0 + bw / 2 + c * (bw + gap)
            z = 0.005 + bh / 2 + r * (bh + gap)
            n = f"{name}_bay_{r}_{c}"
            box(f"{n}_slot", (bw + 0.002, 0.002, bh + 0.002), (x, -FACE_T - 0.0002, z), p.slot, parent=root, col=p.col)
            box(f"{n}_sled", (bw - 0.002, 0.004, bh - 0.003), (x, -FACE_T - 0.0018, z), p.sled, bevel=0.0012, segments=2, parent=root, col=p.col)
            # 손잡이 홈과 작은 LED
            box(f"{n}_grip", (bw * 0.55, 0.002, bh * 0.16), (x - bw * 0.12, -FACE_T - 0.0040, z + bh * 0.22), p.slot, bevel=0.0006, segments=1, parent=root, col=p.col)
            led = p.led_act if (r + c) % 3 else p.led["ok"]
            box(f"{n}_led", (0.0028, 0.002, 0.0028), (x + bw * 0.36, -FACE_T - 0.0042, z - bh * 0.28), led, parent=root, col=p.col)


def ports(p, root, x0, rows, cols, h, name, with_cables, cable_side):
    pitch_x, port_w, port_h = 0.0165, 0.0115, 0.0088
    zs = [h / 2] if rows == 1 else [h * 0.30, h * 0.70]
    for r, z in enumerate(zs):
        for c in range(cols):
            x = x0 + c * pitch_x + (0.004 if c >= cols // 2 else 0.0)
            n = f"{name}_port_{r}_{c}"
            box(f"{n}", (port_w, 0.002, port_h), (x, -FACE_T - 0.0002, z), p.port, parent=root, col=p.col)
            led = p.led_port_amber if (c * 7 + r * 3) % 11 == 0 else p.led_port
            if rows == 1 or r == 1:
                box(f"{n}_led", (0.0026, 0.0015, 0.0018), (x - port_w * 0.3, -FACE_T - 0.0006, z + port_h / 2 + 0.0028), led, parent=root, col=p.col)
            if not with_cables((r, c)):
                continue
            cm = p.cables[2 if c % 5 == 4 else 0] if cable_side < 0 else p.cables[1 if (c + r) % 2 else 0]
            box(f"{n}_boot", (port_w * 0.85, 0.016, port_h * 0.8), (x, -FACE_T - 0.008, z), cm, bevel=0.0018, segments=2, parent=root, col=p.col)
            side_x = cable_side * (0.279 - 0.003 * (c % 4))
            # 앞으로 조금 나온 뒤 같은 높이로 옆 덕트까지 가서 덕트 안으로 내려간다
            drop = 0.10 + 0.006 * c
            fy = -FACE_T - 0.030 - 0.002 * (c % 4)
            pts = [
                (x, -FACE_T - 0.016, z),
                (x, fy, z - 0.004),
                (side_x - cable_side * 0.035, fy, z - 0.008),
                (side_x, fy + 0.012, z - 0.03),
                (side_x, 0.004, z - drop),
            ]
            cable(f"{n}_cable", pts, 0.0026, cm, parent=root, col=p.col)


# ---------------------------------------------------------------- 장비 종류

def unit_server(p, root, unit, h, name, states, face):
    faceplate(p, root, h, face, name)
    handles(p, root, h, name)
    n = round(h / U)
    rows = 1 if n == 1 else n
    drive_bays(p, root, -0.205, -0.035, h, name, rows=rows, cols=4)
    vents(p, root, -0.020, 0.105, h, name)
    status_panel(p, root, unit, h, 0.120, name, states)


def unit_switch(p, root, unit, h, name, states):
    faceplate(p, root, h, p.face_alt, name)
    ports(p, root, -0.200, 2, 16, h, name, with_cables=lambda rc: rc[1] % 3 != 2, cable_side=1)
    for i in range(4):
        box(f"{name}_sfp_{i}", (0.012, 0.003, 0.0095), (0.090 + i * 0.0145, -FACE_T - 0.0005, h / 2), p.steel, bevel=0.001, segments=2, parent=root, col=p.col)
    status_panel(p, root, unit, h, 0.155, name, states)


def unit_patch(p, root, unit, h, name, states):
    faceplate(p, root, h, p.face, name)
    ports(p, root, -0.200, 1, 20, h, name, with_cables=lambda rc: rc[1] % 2 == 0, cable_side=-1)
    status_panel(p, root, unit, h, 0.155, name, states)


def unit_storage(p, root, unit, h, name, states):
    faceplate(p, root, h, p.face_alt, name)
    handles(p, root, h, name)
    drive_bays(p, root, -0.205, 0.105, h, name, rows=2, cols=6)
    status_panel(p, root, unit, h, 0.120, name, states)


def unit_blank(p, root, unit, h, name, states):
    faceplate(p, root, h, p.face, name)
    vents(p, root, -0.200, 0.200, h, name, rows_per_u=4)


def unit_ups(p, root, unit, h, name, states):
    faceplate(p, root, h, p.face_cream, name)
    handles(p, root, h, name)
    vents(p, root, -0.200, -0.020, h, name, rows_per_u=3)
    box(f"{name}_lcd_bezel", (0.070, 0.002, 0.036), (0.040, -FACE_T - 0.0006, h * 0.55), p.frame, bevel=0.002, segments=2, parent=root, col=p.col)
    box(f"{name}_lcd", (0.060, 0.002, 0.026), (0.040, -FACE_T - 0.0016, h * 0.55), p.lcd, bevel=0.001, segments=1, parent=root, col=p.col)
    for i in range(3):
        cyl(f"{name}_btn_{i}", 0.0045, 0.004, (0.098 + i * 0.016, -FACE_T - 0.002, h * 0.55), p.frame, axis="Y", segments=16, parent=root, col=p.col)
    box(f"{name}_labelplate", (0.060, 0.0015, 0.012), (0.175, -FACE_T - 0.0008, h * 0.55), p.frame, bevel=0.001, segments=2, parent=root, col=p.col)
    text(f"{name}_labeltext", unit["label"], 0.0075, (0.175, -FACE_T - 0.0018, h * 0.55), p.sign_ink, parent=root, col=p.col)


BUILDERS = {
    "server": unit_server,
    "switch": unit_switch,
    "patch": unit_patch,
    "storage": unit_storage,
    "blank": unit_blank,
    "ups": unit_ups,
}


# ---------------------------------------------------------------- 랙 몸체

def frame(p, root, rack_u):
    col = p.col
    body_h = rack_u * U + 2 * MARGIN
    top_z = PLINTH + body_h
    # 다리와 받침
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"rack_foot_{sx}_{sy}", 0.022, 0.03, (sx * (W / 2 - 0.06), sy * (D / 2 - 0.07), 0.015), p.steel, segments=24, bevel=0.004, parent=root, col=col)
    box("rack_plinth", (W - 0.02, D - 0.02, PLINTH - 0.03), (0, 0, 0.03 + (PLINTH - 0.03) / 2), p.frame, bevel=0.006, parent=root, col=col)
    # 옆판: 바깥 판 + 안쪽으로 들어간 패널 + 통풍구
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.016)
        box(f"rack_side_{sx}", (0.032, D, body_h), (x, 0, PLINTH + body_h / 2), p.body, bevel=0.010, parent=root, col=col)
        box(f"rack_side_inset_{sx}", (0.002, D - 0.11, body_h - 0.11), (x + sx * 0.016, 0.0, PLINTH + body_h / 2), p.body_inset, bevel=0.0008, segments=2, parent=root, col=col)
        for i in range(10):
            z = top_z - 0.10 - i * 0.022
            box(f"rack_side_vent_{sx}_{i}", (0.002, 0.30, 0.007), (x + sx * 0.0172, -0.12, z), p.slot, bevel=0.0015, segments=2, parent=root, col=col)
    # 윗판, 뒤판, 앞 상하 프레임
    box("rack_top", (W, D, 0.045), (0, 0, top_z + 0.0225), p.body, bevel=0.012, parent=root, col=col)
    for i in range(6):
        box(f"rack_top_vent_{i}", (0.34, 0.012, 0.002), (0, -0.10 + i * 0.045, top_z + 0.0452), p.slot, bevel=0.002, segments=2, parent=root, col=col)
    box("rack_back", (W - 0.06, 0.02, body_h), (0, D / 2 - 0.02, PLINTH + body_h / 2), p.frame, parent=root, col=col)
    box("rack_front_top", (W - 0.05, 0.05, MARGIN), (0, -D / 2 + 0.035, top_z - MARGIN / 2), p.body, bevel=0.006, parent=root, col=col)
    box("rack_front_bottom", (W - 0.05, 0.05, MARGIN), (0, -D / 2 + 0.035, PLINTH + MARGIN / 2), p.body, bevel=0.006, parent=root, col=col)
    # 앞 윗프레임 밑에 숨긴 조명(밤에만 켠다)
    if p.interior > 0:
        box("rack_interior_strip", (W - 0.12, 0.012, 0.003), (0, -D / 2 + 0.03, top_z - MARGIN - 0.0005), p.strip, parent=root, col=col)
    # 장착 레일(전면판 뒤)
    for sx in (-1, 1):
        x = sx * 0.245
        box(f"rack_rail_{sx}", (0.03, 0.02, rack_u * U), (x, RAIL_Y + 0.010, PLINTH + MARGIN + rack_u * U / 2), p.frame, parent=root, col=col)
    # 양옆 케이블 덕트(손가락 모양 가이드)
    for sx in (-1, 1):
        x = sx * 0.279
        box(f"rack_duct_back_{sx}", (0.032, 0.006, rack_u * U), (x, RAIL_Y + 0.045, PLINTH + MARGIN + rack_u * U / 2), p.frame, parent=root, col=col)
        for i in range(rack_u):
            z = PLINTH + MARGIN + (i + 0.5) * U
            for ex in (-1, 1):
                box(f"rack_duct_finger_{sx}_{i}_{ex}", (0.006, 0.05, 0.016), (x + ex * 0.013, RAIL_Y + 0.020, z), p.frame, bevel=0.002, segments=2, parent=root, col=col)
    return top_z


def sign(p, root, host, top_z):
    col = p.col
    y, z = -D / 2 + 0.16, top_z + 0.045 + 0.09
    for sx in (-1, 1):
        box(f"sign_post_{sx}", (0.012, 0.012, 0.08), (sx * 0.17, y + 0.02, top_z + 0.045 + 0.04), p.frame, bevel=0.003, parent=root, col=col)
    plate = box("sign_plate", (0.46, 0.016, 0.13), (0, y, z), p.frame, bevel=0.012, parent=root, col=col)
    plate.rotation_euler = (math.radians(-14), 0, 0)
    # 글자와 아이콘은 판에 붙여 같이 기운다
    icon = box("sign_icon", (0.085, 0.006, 0.085), (-0.165, -0.010, 0.0), p.sage, bevel=0.012, parent=plate, col=col)
    for i in range(3):
        box(f"sign_icon_bar_{i}", (0.050, 0.004, 0.012), (0, -0.004, 0.022 - i * 0.022), p.sign_ink, bevel=0.003, segments=2, parent=icon, col=col)
        box(f"sign_icon_dot_{i}", (0.006, 0.005, 0.006), (0.032, -0.004, 0.022 - i * 0.022), p.led["ok"], parent=icon, col=col)
    text("sign_title", host["title"], 0.042, (-0.105, -0.0085, 0.020), p.sign_ink, align="LEFT", extrude=0.0008, parent=plate, col=col)
    text("sign_subtitle", host["subtitle"], 0.021, (-0.105, -0.0085, -0.028), p.sign_ink, align="LEFT", extrude=0.0006, parent=plate, col=col)


def build_rack(infra, states=None, led_boost=1.0, interior=0.0, name="rack"):
    states = states or {}
    p = Palette(led_boost, interior)
    p.col = collection(name)
    root = empty(name, (0, 0, 0), col=p.col)
    host = infra["host"]
    rack_u = host["rackUnits"]
    top_z = frame(p, root, rack_u)

    used = sum(u["u"] for u in infra["units"])
    # 남는 칸은 빈 패널로 채우되 UPS는 맨 아래에 둔다
    units = list(infra["units"])
    at = next((i for i, u in enumerate(units) if u["kind"] == "ups"), len(units))
    units[at:at] = [{"id": f"blank-fill-{i}", "kind": "blank", "u": 1, "decor": True} for i in range(rack_u - used)]
    z = PLINTH + MARGIN + rack_u * U
    for idx, unit in enumerate(units):
        h = unit["u"] * U
        z -= h
        uroot = empty(f"unit__{unit['id']}", (0, RAIL_Y, z), parent=root, col=p.col)
        uroot["kind"] = unit["kind"]
        uroot["decor"] = bool(unit.get("decor"))
        face = p.face if idx % 2 else p.face_alt
        builder = BUILDERS[unit["kind"]]
        if unit["kind"] == "server":
            builder(p, uroot, unit, h - 0.0015, unit["id"], states, face)
        else:
            builder(p, uroot, unit, h - 0.0015, unit["id"], states)
    sign(p, root, host, top_z)
    return root
