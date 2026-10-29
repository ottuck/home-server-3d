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


def issues(w=300, h=200):
    """오류 추적 화면 느낌의 목록(장식)."""
    a = canvas(w, h, (0.10, 0.08, 0.14))
    rect(a, 0, h - 28, w, h, (0.20, 0.14, 0.30))
    rect(a, 12, h - 19, 90, h - 10, (0.92, 0.90, 0.95))
    for i in range(5):
        y = h - 52 - i * 30
        rect(a, 12, y, w - 12, y + 22, (0.15, 0.12, 0.20))
        rect(a, 20, y + 8, 28, y + 16, (0.35, 0.85, 0.45))
        rect(a, 38, y + 9, 38 + 60 + 25 * (i % 3), y + 15, (0.80, 0.78, 0.86))
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
        top, bottom = np.array([0.42, 0.62, 0.88]), np.array([0.92, 0.88, 0.80])
        a[..., :3] = (bottom * (1 - t) + top * t)[:, None, :]
        for k, row in enumerate(layers):
            col = np.array([0.70, 0.74, 0.80]) * (1 - k * 0.12)
            for x, bw, bh in row:
                a[:bh, x:x + bw, :3] = col
                for wy in range(14, bh - 14, 24):
                    for wx in range(x + 10, x + bw - 14, 18):
                        if rng.random() < 0.5:
                            a[wy:wy + 11, wx:wx + 8, :3] = col * 0.85 + np.array([0.05, 0.07, 0.10])
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
