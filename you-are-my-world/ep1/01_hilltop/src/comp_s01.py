"""Optical HDR + CRT Phosphor Halftone Compositor for 01_hilltop (zero scipy).
Usage: python comp_s01.py <cel_dir> <bg_dir> <out_dir> [frames]
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import glob
import json
import math
import multiprocessing as mp
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rig_mh import gauss_blur_f32

N_FRAMES = 240
OVERSIZE = 1.15
_WORKER_CTX: dict = {}


def _hex(hx: str) -> np.ndarray:
    hx = hx.lstrip("#")
    return np.array([int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)], dtype=np.float32) / 255.0


def _fast_blur_down(arr: np.ndarray, sigma: float, div: int) -> np.ndarray:
    """Fast multi-scale float32 Gaussian blur via PIL bilinear downsample -> separable 1D blur -> upscale (100x faster)."""
    if div <= 1 or sigma < 3.0:
        return gauss_blur_f32(arr, sigma)
    h, w = arr.shape[:2]
    sw, sh = max(4, w // div), max(4, h // div)
    if arr.ndim == 2:
        small = np.asarray(Image.fromarray(arr, mode="F").resize((sw, sh), Image.Resampling.BILINEAR), dtype=np.float32)
        bl = gauss_blur_f32(small, sigma / float(div))
        return np.asarray(Image.fromarray(bl, mode="F").resize((w, h), Image.Resampling.BILINEAR), dtype=np.float32)
    chans = []
    for c in range(arr.shape[2]):
        small = np.asarray(Image.fromarray(arr[..., c], mode="F").resize((sw, sh), Image.Resampling.BILINEAR), dtype=np.float32)
        bl = gauss_blur_f32(small, sigma / float(div))
        chans.append(np.asarray(Image.fromarray(bl, mode="F").resize((w, h), Image.Resampling.BILINEAR), dtype=np.float32))
    return np.stack(chans, axis=-1)


def _crop_layer(im: Image.Image, w: int, h: int, dx_scr: float, dy_scr: float, zoom: float) -> np.ndarray:
    """Crop & zoom from 115% oversize BG layer into (h, w) float32 array in ~5ms via PIL C engine."""
    bw, bh = im.size
    crop_w = (bw / OVERSIZE) / zoom
    crop_h = (bh / OVERSIZE) / zoom
    cx = bw * 0.5 - dx_scr * w
    cy = bh * 0.5 - dy_scr * h
    box = (cx - crop_w * 0.5, cy - crop_h * 0.5, cx + crop_w * 0.5, cy + crop_h * 0.5)
    cropped = im.crop(box).resize((w, h), Image.Resampling.BILINEAR)
    return np.asarray(cropped, dtype=np.float32) / 255.0


def _init_worker(cel_dir: str, bg_dir: str, out_dir: str, meta: dict):
    global _WORKER_CTX
    w, h = int(meta["width"]), int(meta["height"])
    scale = float(meta["scale"])

    layers = {
        "sky": Image.open(os.path.join(bg_dir, "sky_base.png")).convert("RGB"),
        "cfar": Image.open(os.path.join(bg_dir, "cloud_far.png")).convert("RGBA"),
        "cmid": Image.open(os.path.join(bg_dir, "cloud_mid.png")).convert("RGBA"),
        "ccore": Image.open(os.path.join(bg_dir, "cloud_core.png")).convert("RGBA"),
        "gmid": Image.open(os.path.join(bg_dir, "grass_mid.png")).convert("RGBA"),
        "gfg": Image.open(os.path.join(bg_dir, "grass_fg_bokeh.png")).convert("RGBA"),
    }

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / float(w), yy / float(h)
    aspect = w / float(h)

    # Organic staggered hexagonal analog CRT phosphor stipple (finer 4.4x5.0 pitch, ZERO square Lego grid!)
    row_p = 4.4 * scale
    col_p = 5.0 * scale
    best_d2 = np.full((h, w), 1e12, dtype=np.float32)
    best_cy = np.zeros((h, w), dtype=np.float32)
    best_cx = np.zeros((h, w), dtype=np.float32)
    best_r = np.zeros((h, w), dtype=np.float32)
    best_c = np.zeros((h, w), dtype=np.float32)

    r_base = np.round(yy / row_p)
    for dr_i in (-1.0, 0.0, 1.0):
        ri = r_base + dr_i
        cy_cand = ri * row_p
        x_sh = (np.mod(ri, 2.0) > 0.5).astype(np.float32) * (0.5 * col_p)
        c_base = np.round((xx - x_sh) / col_p)
        for dc_i in (-1.0, 0.0, 1.0):
            ci = c_base + dc_i
            cx_cand = ci * col_p + x_sh
            d2_c = (xx - cx_cand) ** 2 + (yy - cy_cand) ** 2
            better = d2_c < best_d2
            best_d2 = np.where(better, d2_c, best_d2)
            best_cy = np.where(better, cy_cand, best_cy)
            best_cx = np.where(better, cx_cand, best_cx)
            best_r = np.where(better, ri, best_r)
            best_c = np.where(better, ci, best_c)

    # Deterministic per-hex-site hash -> organic spatial jitter & dot-radius variance
    def _hash2(ri: np.ndarray, ci: np.ndarray, k1: float, k2: float) -> np.ndarray:
        hv = np.sin(ri * k1 + ci * k2) * 43758.5453
        return hv - np.floor(hv)

    h1 = _hash2(best_r, best_c, 12.9898, 78.233)
    h2 = _hash2(best_r, best_c, 39.3468, 11.135)
    h3 = _hash2(best_r, best_c, 73.1560, 52.235)
    jx = (h1 - 0.5) * 1.10 * scale
    jy = (h2 - 0.5) * 1.10 * scale
    d_hex = np.sqrt((xx - (best_cx + jx)) ** 2 + (yy - (best_cy + jy)) ** 2)
    rad_jitter = 0.85 + 0.30 * h3
    yc = np.clip(np.round(best_cy), 0, h - 1).astype(np.int32)
    xc = np.clip(np.round(best_cx), 0, w - 1).astype(np.int32)
    cell_hash = h1

    # Periodic 12-fps hand-drawn organic contour boil spatial basis (precomputed cos/sin modes)
    boil_x_a = np.sin(v * 24.0 + u * 11.0) + 0.6 * np.cos(v * 41.0 - u * 19.0)
    boil_x_b = np.cos(v * 24.0 + u * 11.0) - 0.6 * np.sin(v * 41.0 - u * 19.0)
    boil_y_a = np.cos(u * 22.0 - v * 13.0) + 0.6 * np.sin(u * 38.0 + v * 17.0)
    boil_y_b = -np.sin(u * 22.0 - v * 13.0) + 0.6 * np.cos(u * 38.0 + v * 17.0)

    # Restrained CRT aperture-grille + gentle analog horizontal scanlines
    triad_x = xx % 3.0
    grille = np.ones((h, w, 3), dtype=np.float32)
    grille[:, :, 0] = np.where(triad_x < 1.0, 1.028, 0.986)
    grille[:, :, 1] = np.where((triad_x >= 1.0) & (triad_x < 2.0), 1.028, 0.986)
    grille[:, :, 2] = np.where(triad_x >= 2.0, 1.028, 0.986)
    scan_pitch = max(2.2, 3.0 * scale)
    scanlines = 1.0 - 0.042 * (0.5 - 0.5 * np.cos(2.0 * math.pi * yy / scan_pitch))

    # Soft Vignette
    vig_d = ((u - 0.5) ** 2 * 1.15 + (v - 0.5) ** 2)
    vignette = (1.0 - 0.18 * np.clip(vig_d * 2.1, 0.0, 1.0))[..., None]

    # Natural starry sky: 100 delicate varied pinpoint stars + ONLY 3 subtle asymmetric soft hero glints
    rng = np.random.default_rng(42)
    bg_stars = []
    for _ in range(100):
        sx = float(rng.uniform(0.02, 0.98))
        sy = float(rng.uniform(0.02, 0.46))
        bg_stars.append((
            sx, sy,
            float(rng.uniform(0.65, 1.55)) * scale,
            int(rng.integers(1, 5)),
            float(rng.uniform(0, 6.28)),
            float(rng.uniform(0.22, 0.78)),
            int(rng.integers(0, 3)),
        ))

    hero_stars = [
        # (u, v, size_scale, k_twinkle, phase, tint_idx, is_crescendo) - max 3 subtle soft hero glints
        (0.84, 0.125, 0.82, 1, 0.4, 0, True),
        (0.18, 0.145, 0.68, 2, 2.2, 1, False),
        (0.66, 0.065, 0.64, 2, 1.1, 2, False),
    ]

    # 22 sparse, delicate wind-swept stardust motes
    embers = []
    for _ in range(22):
        embers.append((
            float(rng.uniform(0.55, 0.63)),
            float(rng.uniform(0.50, 0.80)),
            float(rng.uniform(0.0, 1.0)),
            float(rng.uniform(0.12, 0.24)),
            float(rng.uniform(-0.12, -0.04)),
            float(rng.uniform(1.0, 2.2)) * scale,
            float(rng.uniform(0.0, 6.28)),
        ))

    _WORKER_CTX = dict(
        cel_dir=cel_dir,
        out_dir=out_dir,
        meta=meta,
        w=w,
        h=h,
        scale=scale,
        aspect=aspect,
        layers=layers,
        xx=xx,
        yy=yy,
        u=u,
        v=v,
        xc=xc,
        yc=yc,
        d_hex=d_hex,
        rad_jitter=rad_jitter,
        cell_hash=cell_hash,
        boil_x_a=boil_x_a,
        boil_x_b=boil_x_b,
        boil_y_a=boil_y_a,
        boil_y_b=boil_y_b,
        grille=grille,
        scanlines=scanlines,
        vignette=vignette,
        bg_stars=bg_stars,
        hero_stars=hero_stars,
        embers=embers,
    )


def _draw_aurora_palette(theta: np.ndarray) -> np.ndarray:
    """Smooth cyclic 4-stop aurora palette: Cyan -> Cobalt -> Violet -> Hot Magenta -> Cyan."""
    t = (theta / (2.0 * math.pi)) % 1.0
    stops = [
        _hex("#24D4FF"),  # Luminous cyan
        _hex("#3B5BFF"),  # Deep electric cobalt
        _hex("#9B2CFF"),  # Rich neon violet
        _hex("#FF2AE0"),  # Hot magenta
        _hex("#24D4FF"),  # Wrap seamlessly
    ]
    seg = t * 4.0
    idx = np.floor(seg).astype(np.int32).clip(0, 3)
    frac = (seg - idx)[..., None]
    out = np.zeros((*theta.shape, 3), dtype=np.float32)
    for k in range(4):
        m = idx == k
        if np.any(m):
            out[m] = stops[k] * (1.0 - frac[m]) + stops[k + 1] * frac[m]
    return out


def _apply_boil(pass_arr: np.ndarray, ctx: dict, ph_boil: float, amp_px: float) -> np.ndarray:
    """Apply subtle 12-fps hand-drawn organic contour boil via bilinear fractional sampling on alpha ROI."""
    h, w = pass_arr.shape[:2]
    a_mask = pass_arr[..., 3] > 0.002
    if not np.any(a_mask):
        return pass_arr
    ys, xs = np.where(a_mask)
    y0, y1 = max(0, int(ys.min()) - 4), min(h, int(ys.max()) + 5)
    x0, x1 = max(0, int(xs.min()) - 4), min(w, int(xs.max()) + 5)

    dx = (math.cos(ph_boil) * ctx["boil_x_a"][y0:y1, x0:x1] + math.sin(ph_boil) * ctx["boil_x_b"][y0:y1, x0:x1]) * (amp_px * 0.62)
    dy = (math.cos(ph_boil) * ctx["boil_y_a"][y0:y1, x0:x1] + math.sin(ph_boil) * ctx["boil_y_b"][y0:y1, x0:x1]) * (amp_px * 0.62)
    sx = np.clip(ctx["xx"][y0:y1, x0:x1] + dx, 0.0, w - 1.001)
    sy = np.clip(ctx["yy"][y0:y1, x0:x1] + dy, 0.0, h - 1.001)
    ix = np.floor(sx).astype(np.int32)
    iy = np.floor(sy).astype(np.int32)
    fx = (sx - ix)[..., None]
    fy = (sy - iy)[..., None]
    ix1 = np.minimum(ix + 1, w - 1)
    iy1 = np.minimum(iy + 1, h - 1)

    sampled = (
        pass_arr[iy, ix] * (1.0 - fx) * (1.0 - fy)
        + pass_arr[iy, ix1] * fx * (1.0 - fy)
        + pass_arr[iy1, ix] * (1.0 - fx) * fy
        + pass_arr[iy1, ix1] * fx * fy
    )
    out = pass_arr.copy()
    out[y0:y1, x0:x1] = sampled
    return out


def _render_shooting_star(
    img: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    w: int,
    h: int,
    aspect: float,
    t_norm: float,
    t_start: float,
    t_end: float,
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    tail_len: float,
    thickness: float,
    tint_head: np.ndarray,
    tint_tail: np.ndarray,
    strength: float,
):
    if not (t_start <= t_norm <= t_end):
        return
    p = (t_norm - t_start) / (t_end - t_start)
    env = math.sin(min(1.0, p / 0.14) * math.pi * 0.5) * math.sin(min(1.0, (1.0 - p) / 0.18) * math.pi * 0.5)
    hx = p0[0] + (p1[0] - p0[0]) * p
    hy = p0[1] + (p1[1] - p0[1]) * p
    dx = (p1[0] - p0[0]) * aspect
    dy = p1[1] - p0[1]
    dlen = math.hypot(dx, dy) + 1e-6
    dir_x, dir_y = dx / dlen, dy / dlen

    # Local ROI bounds check on normalized screen coordinates
    px = (u - hx) * aspect
    py = v - hy
    proj = -(px * dir_x + py * dir_y)  # positive behind head along trail
    perp = np.abs(px * dir_y - py * dir_x)

    in_trail = (proj >= -0.015) & (proj <= tail_len)
    if not np.any(in_trail):
        return
    t_along = np.clip(proj / tail_len, 0.0, 1.0)
    w_line = thickness * (1.0 - 0.72 * t_along)
    line_glow = np.exp(-((perp / np.maximum(w_line, 1e-4)) ** 1.6)) * ((1.0 - t_along) ** 1.8) * (proj >= 0.0)
    head_d = np.sqrt(px * px + py * py)
    head_core = np.exp(-((head_d / (thickness * 2.2)) ** 2))
    head_halo = np.exp(-(head_d / (thickness * 10.0)))

    trail_col = tint_head * (1.0 - t_along[..., None]) + tint_tail * t_along[..., None]
    add = (
        head_core[..., None] * np.array([1.0, 0.98, 1.0], dtype=np.float32) * 1.45
        + head_halo[..., None] * tint_head * 0.55
        + line_glow[..., None] * trail_col * 1.05
    ) * (env * strength)
    img += add


def _process_frame(f: int) -> Tuple[int, float]:
    tf0 = time.time()
    ctx = _WORKER_CTX
    w, h, scale, aspect = ctx["w"], ctx["h"], ctx["scale"], ctx["aspect"]
    u, v, xx, yy = ctx["u"], ctx["v"], ctx["xx"], ctx["yy"]
    layers = ctx["layers"]
    meta = ctx["meta"]
    f_info = meta["frames"][f"{f:03d}"]

    phi = 2.0 * math.pi * (f - 1) / float(N_FRAMES)
    t_norm = (f - 1) / float(N_FRAMES)
    f12 = (f - 1) // 2

    # 1. Cyclic floating camera & 3-plane cloud parallax (mathematically seamless at f=240 -> f=1)
    cam_dy = 0.0085 * math.sin(phi)
    cam_dx = 0.0030 * math.cos(phi)
    cam_zm = 1.0 + 0.007 * (0.5 - 0.5 * math.cos(phi))

    img = _crop_layer(layers["sky"], w, h, cam_dx * 0.5, cam_dy * 0.6, 1.0 + (cam_zm - 1.0) * 0.4)

    # 2. Delicate pinpoint night stars + max 3 subtle soft hero glints + 2 sleek needle meteors
    pin_tints = [
        np.array([0.88, 0.92, 1.00], dtype=np.float32),
        np.array([0.74, 0.88, 1.00], dtype=np.float32),
        np.array([0.94, 0.82, 1.00], dtype=np.float32),
    ]
    for (sx, sy, rad, k_tw, ph, base_br, tid) in ctx["bg_stars"]:
        sx_p = sx + cam_dx * 0.5
        sy_p = sy + cam_dy * 0.6
        tw = base_br * (0.70 + 0.30 * math.sin(k_tw * phi + ph))
        x0, x1 = max(0, int(sx_p * w - rad * 4)), min(w, int(sx_p * w + rad * 4) + 1)
        y0, y1 = max(0, int(sy_p * h - rad * 4)), min(h, int(sy_p * h + rad * 4) + 1)
        if x1 > x0 and y1 > y0:
            d2 = ((xx[y0:y1, x0:x1] - sx_p * w) ** 2 + (yy[y0:y1, x0:x1] - sy_p * h) ** 2) / (rad ** 2)
            img[y0:y1, x0:x1] += np.exp(-d2)[..., None] * pin_tints[tid] * tw

    star_tints = [_hex("#7BE8FF"), _hex("#B29BFF"), _hex("#FF82F0")]
    crescendo = math.exp(-((t_norm - 0.89) / 0.085) ** 2)
    for (sx, sy, sz, k_tw, ph, tidx, is_cr) in ctx["hero_stars"]:
        sx_p = sx + cam_dx * 0.5
        sy_p = sy + cam_dy * 0.6
        tw = 0.72 + 0.28 * math.sin(k_tw * phi + ph)
        boost = (1.0 + 0.45 * crescendo) if is_cr else 1.0
        span = int(round(30 * sz * boost * scale))
        x0, x1 = max(0, int(sx_p * w) - span), min(w, int(sx_p * w) + span + 1)
        y0, y1 = max(0, int(sy_p * h) - span), min(h, int(sy_p * h) + span + 1)
        if x1 > x0 and y1 > y0:
            dxp = xx[y0:y1, x0:x1] - sx_p * w
            dyp = yy[y0:y1, x0:x1] - sy_p * h
            r_px = np.sqrt(dxp * dxp + dyp * dyp)
            spike_len = 13.0 * sz * boost * scale
            spike_w = 1.65 * scale
            sp_h = np.exp(-((dyp / spike_w) ** 2)) * np.exp(-np.abs(dxp) / spike_len) * 0.26
            sp_v = np.exp(-((dxp / spike_w) ** 2)) * np.exp(-np.abs(dyp) / spike_len) * 0.26
            core = np.exp(-((r_px / (1.9 * sz * scale)) ** 2))
            halo = np.exp(-(r_px / (8.5 * sz * boost * scale)))
            tint = star_tints[(tidx + (1 if (f12 % 2 and not is_cr) else 0)) % 3]
            glow = (core[..., None] * np.array([1.0, 0.99, 1.0]) * 0.95
                    + (sp_h + sp_v)[..., None] * (0.6 * np.array([1.0, 1.0, 1.0]) + 0.4 * tint)
                    + halo[..., None] * tint * 0.26) * (tw * (0.85 + 0.35 * is_cr * crescendo))
            img[y0:y1, x0:x1] += glow

    # Sleek needle Meteor #1 (0.05-0.35) + subtle distant Meteor #2 (0.60-0.81)
    _render_shooting_star(
        img, u, v, w, h, aspect, t_norm, 0.05, 0.35,
        (0.22, 0.02), (0.98, 0.25), tail_len=0.26, thickness=0.0011,
        tint_head=_hex("#7BE2FF"), tint_tail=_hex("#EB48EA"), strength=0.95,
    )
    _render_shooting_star(
        img, u, v, w, h, aspect, t_norm, 0.60, 0.81,
        (0.05, 0.12), (0.58, 0.25), tail_len=0.15, thickness=0.0008,
        tint_head=_hex("#B0D4FF"), tint_tail=_hex("#D85CE8"), strength=0.55,
    )

    # 3. 3-plane dome-sculpted cumulus clouds (occludes behind-cloud stars naturally!)
    meteor_flash = math.exp(-((t_norm - 0.20) / 0.10) ** 2) * 0.06
    pulse = 1.16 + 0.06 * math.sin(2.0 * phi) + meteor_flash
    for key, px_m, py_m, z_m, drift_x, boost in [
        ("cfar", 0.9, 1.05, 0.80, 0.005 * math.sin(phi), 1.02),
        ("cmid", 1.3, 1.45, 1.10, 0.009 * math.sin(phi - 0.4), 1.10 + 0.05 * math.sin(2.0 * phi)),
        ("ccore", 1.6, 1.75, 1.25, 0.011 * math.sin(phi - 0.7), pulse),
    ]:
        lay = _crop_layer(layers[key], w, h, cam_dx * px_m + drift_x, cam_dy * py_m, 1.0 + (cam_zm - 1.0) * z_m)
        a = lay[..., 3:4]
        img = img * (1.0 - a) + np.clip(lay[..., :3] * boost, 0.0, 1.05) * a

    # 4. Midground backlit meadow grass with continuous cyclic wind-wave ripple
    gmid = _crop_layer(layers["gmid"], w, h, cam_dx * 1.0, cam_dy * 1.0, cam_zm)
    y_band = slice(int(0.73 * h), h)
    tip_w = np.clip((0.865 - v[y_band, :]) / 0.10, 0.0, 1.0)
    shear_px = 2.6 * np.sin(2.0 * phi + u[y_band, :] * 10.0) * tip_w
    dx_i = np.clip(np.round(xx[y_band, :] - shear_px), 0, w - 1).astype(np.int32)
    yy_i = np.arange(int(0.73 * h), h)[:, None]
    gmid[y_band] = gmid[y_band][yy_i - int(0.73 * h), dx_i]

    # 5. Character passes (on twos) + 12-fps hand-drawn organic contour boil
    g_raw = np.asarray(Image.open(os.path.join(ctx["cel_dir"], f"girl_{f:03d}.png")).convert("RGBA"), dtype=np.float32) / 255.0
    b_raw = np.asarray(Image.open(os.path.join(ctx["cel_dir"], f"boy_{f:03d}.png")).convert("RGBA"), dtype=np.float32) / 255.0
    ph_boil = 2.0 * math.pi * float(f12 % 120) / 120.0
    g_pass = _apply_boil(g_raw, ctx, ph_boil, 0.65 * scale)
    b_pass = _apply_boil(b_raw, ctx, ph_boil + 1.2, 0.65 * scale)

    clasp_u, clasp_v = f_info["clasp_uv"]
    d_clasp = np.sqrt(((u - clasp_u) * aspect) ** 2 + (v - clasp_v) ** 2)

    # Organic staggered-hexagonal analog CRT phosphor stipple with Chiaroscuro shadow preservation
    b_alpha = b_pass[..., 3:4]
    rad_raw = np.clip(0.95 * b_pass[..., 0] + 0.85 * b_pass[..., 1], 0.0, 1.35)
    rad_cell = rad_raw[ctx["yc"], ctx["xc"]]
    rad_thr = np.power(np.clip((rad_cell - 0.10) / 0.90, 0.0, 1.0), 1.18)

    r_dot = (0.55 + 1.55 * np.clip(rad_thr, 0.0, 1.0)) * ctx["rad_jitter"] * scale
    dot_spot = np.exp(-((ctx["d_hex"] / np.maximum(r_dot, 0.32)) ** 2.2)) * np.clip(rad_thr * 2.1, 0.0, 1.0)
    bleed = 0.22 * (np.roll(dot_spot, -1, axis=1) + np.roll(dot_spot, 1, axis=1))
    dot_mask = np.clip(dot_spot + bleed * 0.55, 0.0, 1.25)

    aurora_theta = phi + 0.15 - d_clasp * 3.8
    aurora_col = _draw_aurora_palette(aurora_theta)
    ph12 = 2.0 * math.pi * ((f12 % 60) / 60.0)
    sparkle = 0.90 + 0.20 * np.sin(ph12 * 3.0 + ctx["cell_hash"] * 6.283 + d_clasp * 10.0)

    # Shadowed left back stays deep velvet midnight-indigo; lit right shoulder/folds/curls sparkle!
    boy_base = _hex("#110E36") * (1.0 - 0.32 * b_pass[..., 2:3]) + _hex("#1B1750") * (0.42 * b_pass[..., 2:3])
    dot_amp = (dot_mask * np.clip(rad_thr * 1.35, 0.0, 1.35) * sparkle)[..., None]
    peak_white = np.clip((rad_thr - 0.72) / 0.28, 0.0, 1.0)[..., None] * dot_spot[..., None] * 0.35
    boy_lit = boy_base + aurora_col * dot_amp * 1.28 + aurora_col * (b_pass[..., 1:2] * 0.24) + peak_white
    boy_lit_c = np.clip(boy_lit, 0.0, 1.32)
    img = img * (1.0 - b_alpha) + boy_lit_c * b_alpha

    # Draw midground grassy knoll, tall meadow reeds & blades OVER boy's seated hips/legs!
    gm_a = gmid[..., 3:4]
    img = img * (1.0 - gm_a) + gmid[..., :3] * gm_a

    # 6. Girl Refined Pearl-Ivory Silhouette + Interlocking Clasp + Restrained Optical Halation
    g_alpha = g_pass[..., 3:4]
    g_depth = g_pass[..., 1:2]
    g_rim = g_pass[..., 2:3]
    girl_col = (
        _hex("#F5D6E6") * (1.0 - (0.76 + 0.24 * g_depth))
        + _hex("#FFF8F2") * (0.76 + 0.24 * g_depth)
        + np.array([0.14, 0.12, 0.14], dtype=np.float32) * g_rim
    )
    img = img * (1.0 - g_alpha) + np.clip(girl_col, 0.0, 1.22) * g_alpha

    # Blend Boy's phosphor-lit fingers crisply OVER Girl's palm right at clasp before halation!
    clasp_wrap = b_alpha * np.exp(-(d_clasp / 0.025) ** 2)[..., None] * 0.88
    img = img * (1.0 - clasp_wrap) + boy_lit_c * clasp_wrap

    clasp_flare = (np.exp(-(d_clasp / 0.025) ** 2) * 0.08 + np.exp(-(d_clasp / 0.085)) * 0.05) * (1.0 - 0.75 * b_alpha[..., 0])
    img += clasp_flare[..., None] * _hex("#FFD4E6")

    # Mask Girl's halation off solid earth ridge so foreground hill stays rich twilight indigo (ZERO milky neon floor leak!)
    solid_hill = _fast_blur_down(gm_a[..., 0] * np.clip((v - 0.850) / 0.015, 0.0, 1.0), 5.0 * scale, 2)[..., None]
    g_emit = girl_col * g_alpha
    h1 = _fast_blur_down(g_emit, 3.6 * scale, 2) * 0.28
    h2 = _fast_blur_down(g_alpha[..., 0], 18.0 * scale, 2)[..., None] * _hex("#FF90C4") * 0.44
    h3 = _fast_blur_down(g_alpha[..., 0], 58.0 * scale, 4)[..., None] * _hex("#E85094") * 0.28
    img += (h1 + h2 + h3) * (1.0 - 0.82 * solid_hill)

    # 22 sparse delicate wind-swept stardust light motes
    ember_buf = np.zeros((h, w), dtype=np.float32)
    for (ex0, ey0, eph, edx, edy, er, eosc) in ctx["embers"]:
        tau = (t_norm + eph) % 1.0
        life = math.sin(min(1.0, tau / 0.18) * math.pi * 0.5) * math.sin(min(1.0, (1.0 - tau) / 0.25) * math.pi * 0.5)
        ex = (ex0 + edx * (tau ** 1.15) + 0.008 * math.sin(tau * 6.28 + eosc)) * w
        ey = (ey0 + edy * tau + 0.006 * math.cos(tau * 6.28 + eosc)) * h
        x0, x1 = max(0, int(ex - 3.5 * er)), min(w, int(ex + 3.5 * er) + 1)
        y0, y1 = max(0, int(ey - 3.5 * er)), min(h, int(ey + 3.5 * er) + 1)
        if x1 > x0 and y1 > y0:
            d2 = ((xx[y0:y1, x0:x1] - ex) ** 2 + (yy[y0:y1, x0:x1] - ey) ** 2) / (2.0 * (er * 0.55) ** 2)
            ember_buf[y0:y1, x0:x1] += np.exp(-d2) * life * (0.65 + 0.35 * math.sin(2.0 * phi + eosc))
    img += ember_buf[..., None] * _hex("#FFE8F4") * 0.48

    # Tuck bottom of Girl's shoes cleanly behind wispy meadow grass tips so feet sit inside grass
    foot_tuck = gm_a * np.clip((v - 0.838) / 0.012, 0.0, 1.0)[..., None]
    img = img * (1.0 - foot_tuck) + gmid[..., :3] * foot_tuck

    # Foreground bokeh grass swaying softly in bottom corners
    gfg = _crop_layer(layers["gfg"], w, h, cam_dx * 1.4 + 0.005 * math.sin(2.0 * phi), cam_dy * 1.35, 1.0 + (cam_zm - 1.0) * 1.35)
    img = img * (1.0 - gfg[..., 3:4]) + gfg[..., :3] * gfg[..., 3:4]

    # 7. Analog / CRT Dreamcore Finish (clip >= 0 before Reinhard so zero divide warning!)
    img = np.maximum(img, 0.0)
    img = np.where(img > 0.92, 0.92 + (img - 0.92) / (1.0 + np.maximum(img - 0.92, 0.0) * 1.35), img)
    img = np.clip(img, 0.0, 1.0)

    # Subtle ~0.8px optical radial chromatic dispersion
    r_ch = np.asarray(Image.fromarray((img[..., 0] * 255.0).astype(np.uint8), mode="L").resize((w + 2, h + 3), Image.Resampling.BILINEAR).crop((1, 1, w + 1, h + 1)), dtype=np.float32) / 255.0
    b_ch = np.asarray(Image.fromarray((img[..., 2] * 255.0).astype(np.uint8), mode="L").resize((max(4, w - 2), max(4, h - 3)), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    b_pad = np.pad(b_ch, ((1, 2), (1, 1)), mode="edge")[:h, :w]
    img[..., 0] = 0.55 * img[..., 0] + 0.45 * r_ch
    img[..., 2] = 0.55 * img[..., 2] + 0.45 * b_pad

    img *= ctx["grille"] * ctx["scanlines"][..., None]
    img *= ctx["vignette"]
    rng_f = np.random.default_rng(1000 + f)
    gr = rng_f.standard_normal((h, w)).astype(np.float32)
    n_grain = (gr + np.roll(gr, 1, axis=0) + np.roll(gr, 1, axis=1)) * 0.35
    img += n_grain[..., None] * 0.015 * (0.65 + 0.70 * (1.0 - img.mean(axis=-1, keepdims=True)))
    dither = (rng_f.uniform(-0.5, 0.5, (h, w, 1)).astype(np.float32)) / 255.0
    img = np.clip(img + dither, 0.0, 1.0)

    out_path = os.path.join(ctx["out_dir"], f"{f:03d}.png")
    Image.fromarray((img * 255.0 + 0.5).astype(np.uint8)).save(out_path)
    return f, time.time() - tf0


def main():
    if len(sys.argv) < 4:
        print("Usage: python comp_s01.py <cel_dir> <bg_dir> <out_dir> [frames]")
        sys.exit(1)

    cel_dir = os.path.abspath(sys.argv[1])
    bg_dir = os.path.abspath(sys.argv[2])
    out_dir = os.path.abspath(sys.argv[3])
    os.makedirs(out_dir, exist_ok=True)

    meta = json.load(open(os.path.join(cel_dir, "meta.json"), "r", encoding="utf-8"))
    if len(sys.argv) >= 5:
        want = []
        for p in sys.argv[4].split(","):
            p = p.strip()
            if "-" in p:
                a, b = p.split("-", 1)
                want.extend(range(int(a), int(b) + 1))
            elif p:
                want.append(int(p))
        frames = sorted(set(want))
    else:
        frames = sorted(int(k) for k in meta["frames"].keys())

    t0 = time.time()
    n_workers = min(len(frames), max(1, min(4, os.cpu_count() or 4)))
    if n_workers > 1:
        with mp.Pool(processes=n_workers, initializer=_init_worker, initargs=(cel_dir, bg_dir, out_dir, meta)) as pool:
            for f, dt in pool.imap_unordered(_process_frame, frames):
                print(f"comp {f:03d} ({dt:.2f}s)", flush=True)
    else:
        _init_worker(cel_dir, bg_dir, out_dir, meta)
        for f in frames:
            _, dt = _process_frame(f)
            print(f"comp {f:03d} ({dt:.2f}s)", flush=True)
    print(f"Composited {len(frames)} frames in {time.time() - t0:.2f}s -> {out_dir}")


if __name__ == "__main__":
    main()

