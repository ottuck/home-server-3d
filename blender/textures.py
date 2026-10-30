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


def _blur(img, r):
    """가로·세로 상자 흐림을 세 번 겹친 부드러운 흐림(가우스에 가깝다). img는 (h, w) 또는 (h, w, c)."""
    out = img.astype(np.float32)
    for _ in range(3):
        for axis in (0, 1):
            c = np.cumsum(np.pad(out, [(r + 1, r) if k == axis else (0, 0) for k in range(out.ndim)], mode="edge"), axis=axis)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            out = (hi - lo) / (2 * r + 1)
    return out


def skyline(w=1200, h=1280, night=False):
    """창밖. 그림판처럼 보이지 않도록 건물 같은 또렷한 형태는 그리지 않고, 사진의 배경 흐림처럼
    부드러운 하늘 그라데이션과 아주 흐린 구름·나무(낮), 도시 불빛이 번진 지평선과 달무리(밤)만 둔다.
    그림 비율은 창 뒤 평면(1.5 × 1.6m)과 같고, 0번 줄이 아래다."""
    a = np.ones((h, w, 4), dtype=np.float32)
    t = np.linspace(0, 1, h)[:, None]
    yy, xx = np.mgrid[0:h, 0:w]
    rng = np.random.default_rng(11)
    if not night:
        top, horizon = np.array([0.50, 0.68, 0.90]), np.array([0.90, 0.93, 0.96])
        a[..., :3] = (horizon * (1 - t ** 0.7) + top * t ** 0.7)[:, None, :]
        # 흐린 구름: 흰 덩어리를 찍고 크게 흐린다
        cloud = np.zeros((h, w), dtype=np.float32)
        for _ in range(9):
            cx, cy = rng.uniform(0, w), rng.uniform(h * 0.45, h * 0.95)
            rx, ry = rng.uniform(120, 260), rng.uniform(40, 80)
            cloud = np.maximum(cloud, np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)))
        cloud = _blur(cloud, 30) * 0.55
        a[..., :3] += (np.array([0.99, 0.99, 1.0]) - a[..., :3]) * cloud[..., None]
        # 아래쪽 흐린 나뭇잎(초점이 나간 바깥 나무)
        tree = np.zeros((h, w), dtype=np.float32)
        for _ in range(40):
            cx, cy, r = rng.uniform(-50, w + 50), rng.uniform(0, h * 0.16), rng.uniform(60, 130)
            tree = np.maximum(tree, (np.hypot(xx - cx, yy - cy) < r).astype(np.float32))
        tree = np.maximum(tree, (yy < h * 0.08).astype(np.float32))  # 맨 아래는 빈틈 없이
        tree = _blur(tree, 45)
        green = np.array([0.42, 0.56, 0.38])
        a[..., :3] = a[..., :3] * (1 - 0.8 * tree[..., None]) + green * 0.8 * tree[..., None]
        return np.clip(a, 0, 1)

    # 밤: 위는 짙은 남색, 아래는 도시 불빛이 번진 따뜻한 지평선, 오른쪽 위에 흐린 달무리
    top, horizon = np.array([0.012, 0.018, 0.050]), np.array([0.090, 0.085, 0.140])
    a[..., :3] = (horizon * (1 - t ** 0.5) + top * t ** 0.5)[:, None, :]
    glow = np.exp(-yy / (h * 0.10)) * (0.8 + 0.2 * np.sin(xx / w * 9.0 + 1.3))
    a[..., :3] += np.array([0.16, 0.09, 0.04]) * glow[..., None]
    moon = np.exp(-np.hypot(xx - w * 0.74, yy - h * 0.80) / 90.0)
    a[..., :3] += np.array([0.30, 0.31, 0.36]) * 0.35 * moon[..., None]
    # 흐린 불빛 몇 점(초점이 나간 먼 창들)
    lights = np.zeros((h, w), dtype=np.float32)
    for _ in range(60):
        cx, cy = int(rng.uniform(0, w)), int(rng.uniform(0, h * 0.22))
        lights[max(cy - 3, 0):cy + 3, max(cx - 3, 0):cx + 3] = rng.uniform(0.5, 1.0)
    lights = _blur(lights, 10) * 6.0
    a[..., :3] += np.array([1.0, 0.75, 0.45]) * 0.12 * np.clip(lights, 0, 1)[..., None]
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
    glow[..., :3] = np.where(strip[..., None], np.array([0.03, 0.02, 0.01]), np.array([1.0, 0.62, 0.30]))
    return col, glow
