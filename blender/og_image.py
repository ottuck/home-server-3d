"""링크 미리보기 그림(web/og.png, 1200×630)을 밤 렌더에서 만든다. 방 전체가 들어가게 줄이고 좌우는 배경색으로 채운다.

blender -b --factory-startup --python blender/og_image.py
"""
import os

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 630

src = bpy.data.images.load(os.path.join(ROOT, "docs", "renders", "room_night.png"))
sw, sh = src.size
src.scale(round(sw * H / sh), H)
pw, ph = src.size
room = np.array(src.pixels[:], dtype=np.float32).reshape(ph, pw, 4)
out = np.empty((H, W, 4), dtype=np.float32)
out[:] = room[2, 2]  # 렌더 모서리의 배경색
x0 = (W - pw) // 2
out[:, x0:x0 + pw] = room
img = bpy.data.images.new("og", W, H, alpha=False)
img.pixels = out.ravel()
img.filepath_raw = os.path.join(ROOT, "web", "og.png")
img.file_format = "PNG"
img.save()
print("saved", img.filepath_raw)
