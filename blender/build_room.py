"""방 전체를 만들어 렌더링한다.

blender -b --factory-startup --python blender/build_room.py -- --theme day --out renders/room_day.png
"""
import argparse
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import export  # noqa: E402
import lib  # noqa: E402
import textures  # noqa: E402
import props  # noqa: E402
import rack  # noqa: E402
import room  # noqa: E402
import stage  # noqa: E402

ROOT = os.path.dirname(HERE)


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default="day", choices=list(room.THEMES))
    ap.add_argument("--out", default=None)
    ap.add_argument("--res", type=int, nargs=2, default=(1600, 1000))
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--blend", default=None)
    ap.add_argument("--glb", default=None, help="웹용 GLB 경로(낮 테마로 내보낸다)")
    ap.add_argument("--scale", type=float, default=6.5)
    ap.add_argument("--target", type=float, nargs=3, default=(0.0, 0.1, 1.08))
    ap.add_argument("--yaw", type=float, default=40)
    ap.add_argument("--tilt", type=float, default=58)
    return ap.parse_args(argv)


def main():
    args = parse()
    with open(os.path.join(ROOT, "shared", "infra.json"), encoding="utf-8") as f:
        infra = json.load(f)
    lib.reset()
    night = args.theme == "night"
    rt = stage.THEMES[args.theme]
    rack_root = rack.build_rack(infra, states={}, led_boost=rt["led_boost"], interior=rt["interior"])
    m = props.Mats(night=night)
    col = lib.collection("room")
    cable_mats = [bpy.data.materials["cable_blue"], bpy.data.materials["cable_sky"], bpy.data.materials["cable_yellow"]]
    room.shell(m, night, col)
    room.layout(m, night, col, rack_root, cable_mats)
    room.lights(args.theme)
    stage.camera(target=args.target, ortho_scale=args.scale, tilt=args.tilt, yaw=args.yaw)
    stage.render_settings(args.res[0], args.samples, res_y=args.res[1])
    stage.bloom(rt["bloom"])
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
    if args.out:
        out = os.path.abspath(args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print("rendered", out)
    if args.glb:
        glb = os.path.abspath(args.glb)
        n = export.optimize()
        size = export.export(glb, ["rack", "room"])
        # 밤 창밖 그림은 웹이 테마를 바꿀 때 갈아 끼운다
        tex_dir = os.path.join(os.path.dirname(glb), "textures")
        os.makedirs(tex_dir, exist_ok=True)
        night_sky = lib.image("skyline_night_export", 1600, 700, textures.skyline(night=True))
        night_sky.filepath_raw = os.path.join(tex_dir, "skyline_night.png")
        night_sky.file_format = "PNG"
        night_sky.save()
        print(f"exported {glb} meshes={n} bytes={size}")


main()
