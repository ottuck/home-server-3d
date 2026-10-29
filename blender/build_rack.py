"""랙 한 대를 만들어 렌더링하고 GLB로 내보낸다.

blender -b --factory-startup --python blender/build_rack.py -- --theme day --out renders/rack_day.png [--glb assets/rack.glb]
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
import rack  # noqa: E402
import stage  # noqa: E402

ROOT = os.path.dirname(HERE)


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default="day", choices=list(stage.THEMES))
    ap.add_argument("--out", default=None)
    ap.add_argument("--glb", default=None)
    ap.add_argument("--res", type=int, default=1200)
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--blend", default=None, help="확인용 .blend 저장 경로")
    ap.add_argument("--scale", type=float, default=2.1, help="정사영 카메라 화면 폭(m)")
    ap.add_argument("--target", type=float, nargs=3, default=(0.0, 0.0, 0.72))
    return ap.parse_args(argv)


def main():
    args = parse()
    with open(os.path.join(ROOT, "shared", "infra.json"), encoding="utf-8") as f:
        infra = json.load(f)
    lib.reset()
    theme = stage.THEMES[args.theme]
    # 렌더용 예시 상태. 실제 상태는 웹에서 데이터로 칠한다.
    rack.build_rack(infra, states={}, led_boost=theme["led_boost"], interior=theme["interior"])
    stage.room()
    stage.lights(args.theme)
    stage.camera(target=args.target, ortho_scale=args.scale)
    stage.render_settings(args.res, args.samples)
    stage.bloom(theme["bloom"])
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
    if args.out:
        out = os.path.abspath(args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print("rendered", out)
    if args.glb:
        n = export.optimize()
        size = export.export(os.path.abspath(args.glb), ["rack"])
        print(f"exported {args.glb} meshes={n} bytes={size}")


main()
