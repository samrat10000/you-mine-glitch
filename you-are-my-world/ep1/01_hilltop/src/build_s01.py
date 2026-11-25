"""Shot 01 builder: renders MakeHuman Girl & Boy 2x SSAA normal/silhouette passes on twos + meta.json.
Parallelizes unique odd poses across workers when >12 poses are requested.
Usage: python build_s01.py <out_dir> <scale> <frames|all>
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import shutil
import sys
import time
from typing import Dict, List, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rig_mh import build_cast, make_camera, pose_couple_frame, project_points, render_character_pass

N_FRAMES = 240
BASE_W, BASE_H = 1080, 1920
_WCTX: dict = {}


def _clamp_box(cx: float, cy: float, bw: int, bh: int, w: int, h: int) -> List[int]:
    x0 = max(0, min(w - bw, int(round(cx - bw * 0.5))))
    y0 = max(0, min(h - bh, int(round(cy - bh * 0.5))))
    return [x0, y0, min(bw, w - x0), min(bh, h - y0)]


def parse_frames(spec: str) -> List[int]:
    if spec.lower() == "all":
        return list(range(1, N_FRAMES + 1))
    out: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(f for f in out if 1 <= f <= N_FRAMES))


def _init_worker(out_dir: str, scale: float, w: int, h: int):
    global _WCTX
    girl, boy = build_cast()
    cam = make_camera(width=w, height=h)
    _WCTX = dict(out_dir=out_dir, scale=scale, w=w, h=h, girl=girl, boy=boy, cam=cam)


def _render_pose(fpose: int) -> Tuple[int, dict, float]:
    ctx = _WCTX
    tf0 = time.time()
    w, h, scale, cam = ctx["w"], ctx["h"], ctx["scale"], ctx["cam"]
    girl_res, boy_res, ik_diag = pose_couple_frame(ctx["girl"], ctx["boy"], fpose, N_FRAMES)
    Vg, Tg, Ng, dg = girl_res
    Vb, Tb, Nb, db = boy_res
    im_g = render_character_pass(Vg, Tg, Ng, cam, "girl", dg["chest_pos"], ssaa=2)
    im_b = render_character_pass(Vb, Tb, Nb, cam, "boy", dg["chest_pos"], ssaa=2)
    im_g.save(os.path.join(ctx["out_dir"], f"girl_{fpose:03d}.png"))
    im_b.save(os.path.join(ctx["out_dir"], f"boy_{fpose:03d}.png"))

    pts_proj = np.array([
        dg["chest_pos"],
        ik_diag["clasp_pos"],
        db["head_pos"] - np.array([0.0, 0.0, 0.14]),
        [0.0, 0.10, 0.90],
        [0.27, 0.18, 0.34],
    ], dtype=np.float64)
    uv, _ = project_points(cam, pts_proj)
    info = dict(
        fpose=fpose,
        girl_glow_uv=[float(uv[0, 0] / w), float(uv[0, 1] / h)],
        clasp_uv=[float(uv[1, 0] / w), float(uv[1, 1] / h)],
        ik_diag=ik_diag,
        crop_boxes=dict(
            couple_mid=_clamp_box(uv[3, 0], uv[3, 1], max(140, int(round(420 * scale))), max(160, int(round(480 * scale))), w, h),
            boy_closeup=_clamp_box(uv[2, 0], uv[2, 1], max(120, int(round(340 * scale))), max(140, int(round(380 * scale))), w, h),
            girl_legs=_clamp_box(uv[4, 0], uv[4, 1], max(120, int(round(340 * scale))), max(150, int(round(420 * scale))), w, h),
            hands_clasp=_clamp_box(uv[1, 0], uv[1, 1], max(100, int(round(280 * scale))), max(100, int(round(280 * scale))), w, h),
        ),
    )
    return fpose, info, time.time() - tf0


def main():
    if len(sys.argv) < 4:
        print("Usage: python build_s01.py <out_dir> <scale> <frames|all>")
        sys.exit(1)

    out_dir = os.path.abspath(sys.argv[1])
    scale = float(sys.argv[2])
    frames = parse_frames(sys.argv[3])
    os.makedirs(out_dir, exist_ok=True)

    w = int(round(BASE_W * scale))
    h = int(round(BASE_H * scale))
    unique_poses = sorted(set(f - ((f - 1) % 2) for f in frames))
    print(f"Building {len(frames)} frames ({len(unique_poses)} unique twos-poses) @ {w}x{h}")

    meta_path = os.path.join(out_dir, "meta.json")
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path, "r", encoding="utf-8"))
    else:
        meta = dict(
            width=w, height=h, scale=scale, n_frames=N_FRAMES, fps=24,
            frames={}, crops=dict(couple_mid={}, boy_closeup={}, girl_legs={}, hands_clasp={}),
        )
    meta["width"], meta["height"], meta["scale"] = w, h, scale

    pose_cache: Dict[int, dict] = {}
    t_start = time.time()
    if len(unique_poses) > 12:
        n_workers = min(len(unique_poses), max(1, min(6, os.cpu_count() or 4)))
        with mp.Pool(processes=n_workers, initializer=_init_worker, initargs=(out_dir, scale, w, h)) as pool:
            for fpose, info, dt in pool.imap_unordered(_render_pose, unique_poses):
                pose_cache[fpose] = info
                ik = info["ik_diag"]
                print(
                    f"pose {fpose:03d} ({dt:.2f}s) | IK gR={ik['err_girl_R_cm']} gL={ik['err_girl_L_cm']} "
                    f"bR={ik['err_boy_R_cm']} bL={ik['err_boy_L_cm']} legR={ik['err_leg_R_cm']} legL={ik['err_leg_L_cm']}",
                    flush=True,
                )
    else:
        _init_worker(out_dir, scale, w, h)
        for fpose in unique_poses:
            _, info, dt = _render_pose(fpose)
            pose_cache[fpose] = info
            ik = info["ik_diag"]
            print(
                f"pose {fpose:03d} ({dt:.2f}s) | IK gR={ik['err_girl_R_cm']} gL={ik['err_girl_L_cm']} "
                f"bR={ik['err_boy_R_cm']} bL={ik['err_boy_L_cm']} legR={ik['err_leg_R_cm']} legL={ik['err_leg_L_cm']}",
                flush=True,
            )

    for f in frames:
        fpose = f - ((f - 1) % 2)
        g_path = os.path.join(out_dir, f"girl_{f:03d}.png")
        b_path = os.path.join(out_dir, f"boy_{f:03d}.png")
        if f != fpose:
            shutil.copyfile(os.path.join(out_dir, f"girl_{fpose:03d}.png"), g_path)
            shutil.copyfile(os.path.join(out_dir, f"boy_{fpose:03d}.png"), b_path)
        info = pose_cache[fpose]
        meta["frames"][f"{f:03d}"] = dict(
            fpose=info["fpose"], girl_glow_uv=info["girl_glow_uv"],
            clasp_uv=info["clasp_uv"], ik_diag=info["ik_diag"],
        )
        for cname, cbox in info["crop_boxes"].items():
            meta["crops"].setdefault(cname, {})[str(f)] = cbox

    with open(meta_path, "w", encoding="utf-8") as fp:
        json.dump(meta, fp, indent=1)
    sorted_fs = sorted(int(k) for k in meta["frames"].keys())
    if len(sorted_fs) < N_FRAMES:
        probe_crops: Dict[str, Dict[str, List[int]]] = {}
        for pos_idx, fr_num in enumerate(sorted_fs, start=1):
            for cname, cmap in meta["crops"].items():
                if str(fr_num) in cmap:
                    probe_crops.setdefault(cname, {})[str(pos_idx)] = cmap[str(fr_num)]
        probe_path = os.path.join(out_dir, "probe_crops.json")
        with open(probe_path, "w", encoding="utf-8") as fp:
            json.dump(dict(crops=probe_crops), fp, indent=1)
        print(f"Saved probe_crops.json -> {probe_path}")
    print(f"Saved meta.json -> {meta_path} (total {time.time() - t_start:.2f}s)")


if __name__ == "__main__":
    main()
