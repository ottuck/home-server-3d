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


def skyline(w=1600, h=700, night=False):
    a = np.zeros((h, w, 4), dtype=np.float32)
    a[..., 3] = 1.0
    t = np.linspace(0, 1, h)[:, None]
    if night:
        top, bottom = np.array([0.010, 0.016, 0.045]), np.array([0.06, 0.07, 0.14])
    else:
        top, bottom = np.array([0.42, 0.62, 0.88]), np.array([0.92, 0.88, 0.80])
    a[..., :3] = (bottom * (1 - t) + top * t)[:, None, :]
    rng = np.random.default_rng(11)
    # 먼 건물과 가까운 건물 두 겹
    for layer, (hmin, hmax, shade) in enumerate([(0.25, 0.55, 0.0), (0.12, 0.38, 1.0)]):
        x = 0
        while x < w:
            bw = int(rng.integers(50, 150))
            bh = int(h * rng.uniform(hmin, hmax))
            if night:
                col = np.array([0.025, 0.030, 0.060]) * (1 + shade * 0.4)
            else:
                col = np.array([0.70, 0.74, 0.80]) * (1 - shade * 0.12)
            a[:bh, x:x + bw, :3] = col
            # 창문
            for wy in range(12, bh - 10, 16):
                for wx in range(x + 8, x + bw - 10, 14):
                    if night and rng.random() < 0.38:
                        warm = rng.random() < 0.7
                        c = np.array([1.0, 0.78, 0.45]) if warm else np.array([0.75, 0.85, 1.0])
                        a[wy:wy + 7, wx:wx + 6, :3] = c * rng.uniform(0.5, 1.0)
                    elif not night and rng.random() < 0.5:
                        a[wy:wy + 7, wx:wx + 6, :3] = col * 0.85 + np.array([0.05, 0.07, 0.10])
            x += bw + int(rng.integers(0, 12))
    return a
