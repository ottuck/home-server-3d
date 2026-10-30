"""numpy로 그리는 화면·창밖 그림. 배열은 (높이, 폭, RGBA)이고 첫 행이 맨 아래다.

화면 속 그래프는 장식이다. 실제 수치는 웹에서 데이터로 그린다.
"""
import numpy as np

RNG = np.random.default_rng(7)


def canvas(w, h, color):
    a = np.zeros((h, w, 4), dtype=np.float32)
    a[..., :3] = color
    a[..., 3] = 1.0
    return a


def rect(a, x0, y0, x1, y1, color, alpha=1.0):
    region = a[int(y0):int(y1), int(x0):int(x1), :3]
    region[:] = region * (1 - alpha) + np.array(color) * alpha


def series(n, base=0.5, amp=0.25, seed=0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 6, n)
    v = base + amp * (0.5 * np.sin(t * 1.3 + seed) + 0.3 * np.sin(t * 3.7 + seed * 2)) + rng.normal(0, amp * 0.18, n)
    return np.clip(v, 0.05, 0.95)


def chart(a, x0, y0, x1, y1, color, seed, bg):
    rect(a, x0, y0, x1, y1, bg)
    for gy in np.linspace(y0 + 8, y1 - 8, 4):
        rect(a, x0 + 6, gy, x1 - 6, gy + 1, np.array(bg) * 1.6 + 0.02)
    xs = np.arange(int(x0) + 8, int(x1) - 8)
    v = series(len(xs), seed=seed)
    ys = (y0 + 10 + v * (y1 - y0 - 20)).astype(int)
    for x, y in zip(xs, ys):
        rect(a, x, y0 + 8, x + 1, y, color, alpha=0.18)
        rect(a, x, y - 2, x + 1, y + 2, color)


def dashboard(w=640, h=360):
    bg = (0.035, 0.040, 0.050)
    panel = (0.065, 0.072, 0.088)
    a = canvas(w, h, bg)
    rect(a, 0, h - 26, w, h, (0.08, 0.09, 0.11))
    rect(a, 12, h - 18, 120, h - 9, (0.85, 0.85, 0.85))
    rect(a, w - 70, h - 18, w - 14, h - 9, (0.30, 0.80, 0.45))
    colors = [(0.30, 0.85, 0.45), (1.0, 0.62, 0.20), (0.30, 0.60, 1.0), (0.70, 0.45, 1.0)]
    pw, ph = (w - 36) / 2, (h - 26 - 36) / 2
    for i, c in enumerate(colors):
        cx, cy = 12 + (i % 2) * (pw + 12), 12 + (1 - i // 2) * (ph + 12)
        chart(a, cx, cy, cx + pw, cy + ph, c, seed=i + 1, bg=panel)
        rect(a, cx + 10, cy + ph - 16, cx + 60, cy + ph - 9, (0.75, 0.75, 0.78))
    return a


def code(w=480, h=300, seed=3):
    rng = np.random.default_rng(seed)
    a = canvas(w, h, (0.055, 0.062, 0.078))
    rect(a, 0, 0, 44, h, (0.045, 0.05, 0.065))
    palette = [(0.55, 0.75, 1.0), (0.95, 0.75, 0.45), (0.65, 0.90, 0.60), (0.85, 0.60, 0.90), (0.80, 0.82, 0.86)]
    y = h - 16
    while y > 10:
        indent = 56 + 18 * int(rng.integers(0, 4))
        x = indent
        for _ in range(int(rng.integers(1, 5))):
            ln = int(rng.integers(18, 90))
            if x + ln > w - 12:
                break
            rect(a, x, y, x + ln, y + 5, palette[int(rng.integers(0, len(palette)))], alpha=0.9)
            x += ln + 8
        rect(a, 14, y, 30, y + 5, (0.35, 0.37, 0.42))
        y -= 12 if rng.random() > 0.15 else 24
    return a


def wood_planks(room_w, room_d, ppm=420, row=0.15, seed=5):
    """나무 바닥 판자(sRGB). 폭 room_w·깊이 room_d(m) 전체를 한 장에 그린다."""
    rng = np.random.default_rng(seed)
    w, h = int(room_w * ppm), int(room_d * ppm)
    a = canvas(w, h, (0.70, 0.52, 0.35))
    rh = int(row * ppm)
    xs = np.arange(w)
    for r in range(h // rh + 1):
        y0, y1 = r * rh, min((r + 1) * rh, h)
        if y0 >= h:
            break
        x = -int(rng.uniform(0, 1.2) * ppm)
        while x < w:
            ln = int(rng.uniform(0.7, 1.4) * ppm)
            x0, x1 = max(x, 0), min(x + ln, w)
            if x1 > x0:
                tone = rng.uniform(0.88, 1.10)
                base = np.array([0.74, 0.56, 0.38]) * tone
                # 결: 판자마다 다른 위상의 가는 줄무늬
                phase = rng.uniform(0, 6.28)
                yy = np.arange(y0, y1)[:, None]
                grain = 1 + 0.035 * np.sin(yy * 0.9 + np.sin(xs[None, x0:x1] * 0.01 + phase) * 3)
                a[y0:y1, x0:x1, :3] = base * grain[..., None]
                a[y0:y1, x0:min(x0 + 2, x1), :3] *= 0.72  # 판자 끝 이음매
            x += ln
        a[y0:min(y0 + 2, h), :, :3] *= 0.70  # 줄 사이 틈
    return np.clip(a, 0, 1)


def skyline(w=1200, h=1280, night=False):
    """창밖 풍경. 그림 비율을 창 뒤 평면(1.5 × 1.6m)과 맞춰 창문이 늘어나지 않게 한다. 0번 줄이 아래다."""
    a = np.zeros((h, w, 4), dtype=np.float32)
    a[..., 3] = 1.0
    t = np.linspace(0, 1, h)[:, None]
    rng = np.random.default_rng(11)
    # 건물 배치를 먼저 정해 낮과 밤이 같은 거리를 보게 한다: 먼 줄, 가까운 줄
    layers = []
    for hmin, hmax in [(0.30, 0.52), (0.16, 0.36)]:
        row, x = [], 0
        while x < w:
            bw = int(rng.integers(60, 150))
            row.append((x, bw, int(h * rng.uniform(hmin, hmax))))
            x += bw + int(rng.integers(0, 10))
        layers.append(row)
    if not night:
        # 맑은 낮: 위는 짙은 파랑, 지평선은 옅은 하늘색, 옅은 구름 몇 점
        top, bottom = np.array([0.22, 0.45, 0.80]), np.array([0.72, 0.82, 0.92])
        sky = bottom * (1 - t ** 0.6) + top * t ** 0.6
        a[..., :3] = sky[:, None, :]
        yy, xx = np.mgrid[0:h, 0:w]
        crng = np.random.default_rng(3)
        for _ in range(5):
            cx, cy = crng.uniform(0, w), crng.uniform(h * 0.62, h * 0.92)
            for _ in range(6):  # 작은 덩어리 여럿을 겹친 뭉게구름
                bx, by = cx + crng.uniform(-90, 90), cy + crng.uniform(-18, 18)
                rx, ry = crng.uniform(40, 90), crng.uniform(16, 30)
                m = 0.55 * np.exp(-(((xx - bx) / rx) ** 2 + ((yy - by) / ry) ** 2))
                a[..., :3] += (np.array([0.98, 0.98, 0.99]) - a[..., :3]) * m[..., None]
        haze = bottom * 0.95
        palette = [np.array(c) for c in ((0.80, 0.76, 0.70), (0.88, 0.87, 0.84), (0.68, 0.64, 0.60), (0.76, 0.66, 0.55),
                                         (0.60, 0.64, 0.68), (0.84, 0.80, 0.72))]
        glass = np.array([0.34, 0.45, 0.56])
        for k, row in enumerate(layers):
            far = k == 0
            for x, bw, bh in row:
                base = palette[int(rng.integers(0, len(palette)))]
                if far:  # 먼 건물은 공기에 묻혀 하늘색으로 옅다
                    base = base * 0.45 + haze * 0.55
                # 해는 왼쪽 위: 앞면은 밝고 오른쪽 옆면은 그늘
                split = x + int(bw * 0.74)
                a[:bh, x:split, :3] = base
                a[:bh, split:x + bw, :3] = base * 0.74
                a[bh - 5:bh, x:x + bw, :3] = base * 0.88  # 옥상 난간
                ribbon = rng.random() < 0.35  # 띠 창(통유리)인 건물
                step = 22 if far else 28
                for wy in range(18, bh - 16, step):
                    refl = 0.85 + 0.3 * (wy / max(bh, 1))  # 위층일수록 하늘이 비쳐 밝다
                    g = glass * refl if not far else glass * 0.5 + haze * 0.5
                    if ribbon:
                        a[wy:wy + (8 if far else 12), x + 6:x + bw - 6, :3] = g
                        continue
                    for wx in range(x + 9, x + bw - 13, 16 if far else 19):
                        side = 0.8 if wx >= split else 1.0
                        a[wy:wy + (8 if far else 12), wx:wx + (6 if far else 9), :3] = g * side
        # 맨 아래 가로수: 둥근 초록 덩어리를 겹친다
        trng = np.random.default_rng(9)
        for _ in range(70):
            cx, cy, r = trng.uniform(0, w), trng.uniform(0, h * 0.08), trng.uniform(26, 48)
            m = np.clip(1 - np.hypot(xx - cx, (yy - cy) * 1.1) / r, 0, 1) ** 0.4
            leaf = np.array([0.20, 0.36, 0.16]) * trng.uniform(0.8, 1.2) * (0.85 + 0.25 * (yy - cy) / r).clip(0.6, 1.2)[..., None]
            a[..., :3] = a[..., :3] * (1 - m[..., None]) + leaf * m[..., None]
        return a

    # 밤: 지평선 쪽이 도시 불빛으로 옅게 밝은 하늘, 달 하나, 별 조금, 불 켜진 창은 드문드문
    top, bottom = np.array([0.008, 0.012, 0.035]), np.array([0.075, 0.075, 0.140])
    sky = bottom * (1 - t ** 0.55) + top * t ** 0.55
    sky = sky + np.array([0.09, 0.05, 0.03]) * np.exp(-t / 0.10)
    a[..., :3] = sky[:, None, :]
    yy, xx = np.mgrid[0:h, 0:w]
    mx, my, mr = w * 0.74, h * 0.80, 30
    d = np.hypot(xx - mx, yy - my)
    a[..., :3] += np.array([0.55, 0.55, 0.62]) * (0.18 * np.exp(-np.maximum(d - mr, 0) / 70))[..., None]
    disc = np.clip(mr + 1 - d, 0, 1)[..., None]
    a[..., :3] = a[..., :3] * (1 - disc) + np.array([0.96, 0.93, 0.84]) * disc
    for _ in range(60):
        sx, sy = int(rng.integers(2, w - 2)), int(rng.integers(int(h * 0.55), h - 2))
        if np.hypot(sx - mx, sy - my) < mr * 3:
            continue
        b = rng.uniform(0.35, 0.9)
        a[sy, sx, :3] = np.array([0.85, 0.88, 1.0]) * b
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a[sy + oy, sx + ox, :3] = np.maximum(a[sy + oy, sx + ox, :3], np.array([0.85, 0.88, 1.0]) * b * 0.3)
    for k, row in enumerate(layers):
        far = k == 0
        base = np.array([0.050, 0.058, 0.105]) if far else np.array([0.022, 0.026, 0.050])
        for x, bw, bh in row:
            # 아래쪽이 거리 불빛을 받아 조금 밝다
            shade = 1 + 0.6 * (1 - np.arange(bh) / bh) ** 3
            a[:bh, x:x + bw, :3] = base * shade[:, None, None]
            for wy in range(16, bh - 16, 26 if not far else 22):
                if rng.random() < (0.55 if far else 0.45):
                    continue  # 불 꺼진 층
                for wx in range(x + 10, x + bw - 14, 18 if not far else 16):
                    if rng.random() < 0.45:
                        c = np.array([1.0, 0.76, 0.42]) if rng.random() < 0.8 else np.array([0.72, 0.82, 1.0])
                        c = c * rng.uniform(0.45, 0.85) * (0.55 if far else 1.0)
                        ww, wh = (6, 8) if far else (8, 11)
                        a[wy - 1:wy + wh + 1, wx - 1:wx + ww + 1, :3] = np.maximum(a[wy - 1:wy + wh + 1, wx - 1:wx + ww + 1, :3], c * 0.25)
                        a[wy:wy + wh, wx:wx + ww, :3] = c
        tall = max(row, key=lambda r: r[2])
        lx, ly = tall[0] + tall[1] // 2, tall[2] + 4
        a[ly - 2:ly + 3, lx - 2:lx + 3, :3] = np.array([1.0, 0.25, 0.18]) * (0.5 if far else 0.9)
    return np.clip(a, 0, 1)


def _srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def fabric(color, kind="weave", n=256, cells=8, strength=4.0, seed=1):
    """이어 붙여도 이음매가 없는 직물 한 장: (바탕색 RGBA, 노멀 맵 RGBA).
    weave는 굵은 평직(안락의자), mesh는 엇갈린 구멍이 있는 사무용 의자 메시다. color는 재질과 같은 선형 값이다."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:n, 0:n] / n * cells
    ix, iy = x.astype(int), y.astype(int)
    fx, fy = x % 1, y % 1
    if kind == "weave":
        # 칸마다 세로실과 가로실이 번갈아 위로 올라온다
        warp = np.sin(np.pi * fx) ** 0.7 * (0.75 + 0.25 * np.sin(np.pi * fy))
        weft = np.sin(np.pi * fy) ** 0.7 * (0.75 + 0.25 * np.sin(np.pi * fx))
        h = np.where((ix + iy) % 2 == 0, warp, weft)
    else:
        # 줄마다 반 칸씩 어긋난 구멍
        gx = (x + 0.5 * (iy % 2)) % 1
        h = np.clip((np.hypot(gx - 0.5, fy - 0.5) - 0.16) / 0.2, 0, 1)
    # 보풀: 흐린 잡음(가장자리를 감아 계산해 타일 이음매가 없다)
    r = rng.random((n, n))
    for _ in range(2):
        r = (r + np.roll(r, 1, 0) + np.roll(r, -1, 0) + np.roll(r, 1, 1) + np.roll(r, -1, 1)) / 5
    h = h + 0.35 * (r - 0.5)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2 * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2 * strength
    nrm = np.stack([-gx, -gy, np.ones_like(h)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    normal = np.ones((n, n, 4), dtype=np.float32)
    normal[..., :3] = nrm * 0.5 + 0.5
    col = np.ones((n, n, 4), dtype=np.float32)
    lo = 0.72 if kind == "weave" else 0.45  # 메시는 구멍이 더 어둡게 보인다
    col[..., :3] = _srgb(np.array(color)[None, None, :] * (lo + (1.12 - lo) * np.clip(h, 0, 1))[..., None])
    return col, normal


def rug(w_m, d_m, ppm=400, seed=4):
    """러그 윗면 한 장(바탕색, 노멀 맵): 크림색 바탕에 은은한 마름모 격자, 가장자리에 갈색 띠와 가는 선 두 줄,
    고리 파일 질감. 그림 한 장이 러그 전체를 덮는다(0번 줄이 앞쪽)."""
    w, h = int(w_m * ppm), int(d_m * ppm)
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w] / ppm  # 미터
    edge = np.minimum(np.minimum(x, w_m - x), np.minimum(y, d_m - y))
    field, band, line = np.array([0.80, 0.74, 0.62]), np.array([0.40, 0.30, 0.21]), np.array([0.52, 0.40, 0.28])
    col = np.broadcast_to(field, (h, w, 3)).copy()
    # 바탕의 마름모 격자(아주 옅게)
    cx, cy = x - w_m / 2, y - d_m / 2
    lattice = np.abs(((cx + cy) / 0.16) % 1 - 0.5) + np.abs(((cx - cy) / 0.16) % 1 - 0.5)
    col = np.where((lattice < 0.10)[..., None], col * 0.9 + line * 0.1 * 0.9, col)
    # 테두리: 바깥 갈색 띠, 그 안쪽에 가는 선 두 줄
    col[edge < 0.06] = band
    for d0 in (0.085, 0.105):
        col[(edge > d0) & (edge < d0 + 0.008)] = line
    # 고리 파일: 실 한 가닥 크기의 잡음과 가로 줄(직조 방향)
    r = rng.random((h, w))
    r = (r + np.roll(r, 1, 0) + np.roll(r, 1, 1)) / 3
    rows = 0.5 + 0.5 * np.sin(y * ppm * np.pi / 2.2)
    pile = 0.55 * r + 0.45 * rows
    col *= (0.88 + 0.2 * pile)[..., None]
    out = np.ones((h, w, 4), dtype=np.float32)
    out[..., :3] = _srgb(col)
    gx = (np.roll(pile, -1, 1) - np.roll(pile, 1, 1)) * 1.5
    gy = (np.roll(pile, -1, 0) - np.roll(pile, 1, 0)) * 1.5
    nrm = np.stack([-gx, -gy, np.ones_like(pile)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    normal = np.ones((h, w, 4), dtype=np.float32)
    normal[..., :3] = nrm * 0.5 + 0.5
    return out, normal


def rattan(n=512, around=26, up=13):
    """대나무 살을 마름모로 엮은 갓 한 장(바탕색, 발광): 살은 밝은 대나무색, 사이 틈은 어둡다.
    발광 그림은 반대로 틈이 밝아, 불을 켜면 엮은 틈 사이로 빛이 새어 나온다. u는 둘레, v는 높이다."""
    v, u = np.mgrid[0:n, 0:n] / n
    a = (u * around + v * up) % 1
    b = (u * around - v * up) % 1
    sa, sb = np.abs(a - 0.5) < 0.30, np.abs(b - 0.5) < 0.30
    over = ((np.floor(u * around + v * up) + np.floor(u * around - v * up)) % 2) == 0  # 위로 지나가는 살
    strip = sa | sb
    shade = np.where(sa & sb, np.where(over, 1.0, 0.82), 0.92) * (0.9 + 0.1 * np.cos(np.pi * (np.where(sa, a, b) - 0.5) * 2))
    col = np.ones((n, n, 4), dtype=np.float32)
    bamboo, gap = np.array([0.74, 0.55, 0.32]), np.array([0.10, 0.07, 0.04])
    col[..., :3] = _srgb(np.where(strip[..., None], bamboo * shade[..., None], gap))
    glow = np.ones((n, n, 4), dtype=np.float32)
    glow[..., :3] = np.where(strip[..., None], np.array([0.03, 0.02, 0.01]), np.array([1.0, 0.72, 0.40]))
    return col, glow
