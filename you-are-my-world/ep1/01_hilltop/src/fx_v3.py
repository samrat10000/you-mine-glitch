"""Realism + glitter-grain + glitch compositor for 01_hilltop v3 (pure NumPy + PIL, zero scipy).

Usage: python fx_v3.py <cel_dir> <bg_v3_dir> <out_dir> [frames]
Reuses the v2 cel passes (girl_###.png / boy_###.png + meta.json) and the bg_v3 plates.
Seamless 240-frame loop: every periodic term uses integer multiples of phi; particles live on
integer cycles per loop; per-frame film grain is noise (no loop state).
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import json
import math
import multiprocessing as mp
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rig_mh import gauss_blur_f32
from comp_s01 import _crop_layer, _fast_blur_down, _hex
from paint_bg_v3 import STAR_TEMPS, STAR_TEMP_P, splat, sstep

N_FRAMES = 240
# (first frame, last frame, strength) - bursts land on the meteor terminal flares + mid-loop pulse
GLITCH_WINDOWS: List[Tuple[int, int, float]] = [(56, 63, 1.0), (112, 115, 0.42), (168, 174, 0.85)]
# (t_start, t_end, p0, p1, peak, train_tau) — high in upper Milky Way sky, above hero cloud crown
METEORS = [
    (0.145, 0.245, (0.07, 0.048), (0.76, 0.168), 1.15, 0.068),
    (0.650, 0.710, (0.96, 0.068), (0.74, 0.148), 0.68, 0.048),
]
_CTX: dict = {}


def _load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255.0


def _glitch_strength(f: int) -> float:
    for f0, f1, s in GLITCH_WINDOWS:
        if f0 <= f <= f1:
            p = (f - f0 + 0.5) / (f1 - f0 + 1)
            return s * math.sin(math.pi * p) ** 0.5
    return 0.0


def _init_worker(cel_dir: str, bg_dir: str, out_dir: str, meta: dict):
    global _CTX
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

    rng = np.random.default_rng(4242)
    # Bright stars that scintillate (fainter ones are baked into sky_base)
    n_st = 340
    stars = dict(
        u=rng.uniform(0.01, 0.99, n_st),
        v=rng.uniform(0.0, 1.0, n_st) ** 1.25 * 0.62,
        I=0.10 + 1.25 * rng.random(n_st) ** 6,
        temp=rng.choice(len(STAR_TEMPS), size=n_st, p=STAR_TEMP_P),
        k=rng.integers(5, 41, size=(n_st, 3)),
        ph=rng.uniform(0, 2 * math.pi, size=(n_st, 3)),
    )

    # Static per-pixel glitter hashes (integer twinkle rates -> loop-safe)
    gl_h1 = rng.random((h, w), dtype=np.float32)
    gl_h2 = rng.random((h, w), dtype=np.float32)
    gl_k = (4 + np.floor(rng.random((h, w), dtype=np.float32) * 15)).astype(np.float32)

    # Girl spawn pool (frame 1 silhouette); per-frame centroid shift tracks her sway
    g0 = _load_rgba(os.path.join(cel_dir, "girl_001.png"))[..., 3]
    g0b = gauss_blur_f32(g0, 4.0 * scale)
    ey, ex = np.where((g0 > 0.25) & (g0b < 0.88))
    iy, ix = np.where(g0 > 0.88)
    pool_edge = np.stack([ex, ey], axis=1).astype(np.float32)
    pool_all = np.stack([np.concatenate([ex, ix]), np.concatenate([ey, iy])], axis=1).astype(np.float32)
    ys0, xs0 = np.where(g0 > 0.5)
    cen0 = (float(xs0.mean()), float(ys0.mean()))
    downwind_mask = pool_edge[:, 0] >= (cen0[0] - 8.0)
    pool_downwind = pool_edge[downwind_mask] if np.any(downwind_mask) else pool_edge
    left_mask = pool_edge[:, 0] < (cen0[0] - 10.0)
    left_pool = pool_edge[left_mask] if np.any(left_mask) else pool_edge

    # ~3600 coherent twinkling surface glitters anchored directly ON the Girl's body
    n_surf = 3600
    # Weight 65% toward outer silhouette contour/hair/hem & 35% interior stardust core
    sel_e = rng.integers(0, len(pool_edge), size=int(n_surf * 0.55))
    sel_a = rng.integers(0, len(pool_all), size=n_surf - int(n_surf * 0.55))
    pts_surf = np.concatenate([pool_edge[sel_e], pool_all[sel_a]], axis=0)
    surf_pal = np.array([
        [1.00, 1.00, 1.00],  # diamond white
        [1.00, 0.58, 0.81],  # rose-pink #FF94CE
        [0.55, 0.94, 1.00],  # electric ice-cyan #8CF0FF
        [1.00, 0.89, 0.69],  # pale gold #FFE3B0
        [0.78, 0.64, 1.00],  # pale violet #C6A4FF
    ], dtype=np.float32)
    surf_probs = np.array([0.55, 0.22, 0.13, 0.05, 0.05])
    S_glit = dict(
        dx=(pts_surf[:, 0] - cen0[0] + rng.normal(0.0, 1.4 * scale, n_surf)).astype(np.float32),
        dy=(pts_surf[:, 1] - cen0[1] + rng.normal(0.0, 1.4 * scale, n_surf)).astype(np.float32),
        br=(1.20 + 8.30 * (rng.random(n_surf) ** 3.6)).astype(np.float32),
        k=rng.integers(6, 35, size=n_surf).astype(np.float32),
        ph=rng.uniform(0.0, 2.0 * math.pi, size=n_surf).astype(np.float32),
        col=rng.choice(len(surf_pal), size=n_surf, p=surf_probs),
        pal=surf_pal,
    )

    # Particle system: 0 curl-wind sparks | 1 aura grains | 2 strays onto Boy | 3 hero diamond glints
    counts = [5200, 2400, 420, 150]
    P: Dict[str, np.ndarray] = {}
    cls = np.concatenate([np.full(c, i, dtype=np.int32) for i, c in enumerate(counts)])
    n = cls.size
    P["cls"] = cls
    P["k"] = rng.choice(np.array([3, 4, 5, 6, 8, 10, 12], dtype=np.float32), size=n)
    P["off"] = rng.random(n).astype(np.float32)
    P["seed"] = rng.integers(0, 1_000_000, size=n)
    vx = rng.uniform(30, 165, n) + rng.normal(0, 22, n)
    vy = -rng.uniform(55, 225, n)
    vx[cls == 1] = rng.normal(8, 14, (cls == 1).sum())
    vy[cls == 1] = -rng.uniform(10, 48, (cls == 1).sum())
    vx[cls == 2] = -rng.uniform(95, 240, (cls == 2).sum())
    vy[cls == 2] = rng.uniform(-25, 85, (cls == 2).sum())
    vx[cls == 3] = rng.uniform(18, 90, (cls == 3).sum())
    vy[cls == 3] = -rng.uniform(45, 165, (cls == 3).sum())
    P["vx"] = (vx * scale).astype(np.float32)
    P["vy"] = (vy * scale).astype(np.float32)
    P["wob_a"] = (rng.uniform(5, 20, n) * scale).astype(np.float32)
    P["wob_k"] = rng.integers(1, 4, n).astype(np.float32)
    P["ph"] = rng.uniform(0, 2 * math.pi, n).astype(np.float32)
    P["tw_k"] = rng.integers(8, 34, n).astype(np.float32)
    P["tw_ph"] = rng.uniform(0, 2 * math.pi, n).astype(np.float32)
    P["halo_r"] = (rng.uniform(6, 75, n) * scale).astype(np.float32)
    br = 0.65 + 2.15 * rng.random(n) ** 2.4
    br[cls == 1] *= 0.55
    br[cls == 3] = rng.uniform(2.4, 5.2, (cls == 3).sum())
    P["br"] = br.astype(np.float32)
    # 0=diamond white, 1=rose pink, 2=ice cyan
    pt_r = rng.random(n)
    P["ctype"] = np.where(pt_r < 0.52, 0, np.where(pt_r < 0.86, 1, 2)).astype(np.int32)

    # Subtle out-of-focus meadow-air dust bokeh orbs floating mid-height around the couple (NOT dark dirt rings!)
    bokeh = []
    for _ in range(6):
        bokeh.append(dict(
            u=float(rng.uniform(0.18, 0.86)),
            v=float(rng.uniform(0.54, 0.82)),
            r=float(rng.uniform(14, 34)) * scale,
            I=float(rng.uniform(0.035, 0.085)),
            ph=float(rng.uniform(0, 2 * math.pi)),
            col=_hex("#FF9CCB") if rng.random() < 0.65 else _hex("#A6C4FF"),
        ))

    vig_d = (u - 0.5) ** 2 * 1.15 + (v - 0.5) ** 2
    vignette = (1.0 - 0.24 * np.clip(vig_d * 2.1, 0.0, 1.0))[..., None]

    _CTX = dict(
        cel_dir=cel_dir, out_dir=out_dir, meta=meta, w=w, h=h, scale=scale, aspect=w / float(h),
        layers=layers, xx=xx, yy=yy, u=u, v=v, stars=stars, gl_h1=gl_h1, gl_h2=gl_h2, gl_k=gl_k,
        pool_edge=pool_edge, pool_all=pool_all, pool_downwind=pool_downwind, left_pool=left_pool,
        cen0=cen0, S_glit=S_glit, P=P, bokeh=bokeh, vignette=vignette,
    )


def _render_stars(img: np.ndarray, ctx: dict, phi: float, cdx: float, cdy: float):
    w, h, scale = ctx["w"], ctx["h"], ctx["scale"]
    S = ctx["stars"]
    for i in range(S["u"].size):
        I0 = float(S["I"][i])
        k, ph = S["k"][i], S["ph"][i]
        scint = 1.0 + 0.40 * (0.5 * math.sin(k[0] * phi + ph[0]) + 0.3 * math.sin(k[1] * phi + ph[1]) + 0.2 * math.sin(k[2] * phi + ph[2]))
        I = I0 * scint
        cx = (S["u"][i] + cdx) * w
        cy = (S["v"][i] + cdy) * h
        span = int(4 + 14 * I0 * scale)
        x0, x1 = max(0, int(cx) - span), min(w, int(cx) + span + 1)
        y0, y1 = max(0, int(cy) - span), min(h, int(cy) + span + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        dx = ctx["xx"][y0:y1, x0:x1] - cx
        dy = ctx["yy"][y0:y1, x0:x1] - cy
        r = np.sqrt(dx * dx + dy * dy)
        sig = (0.55 + 0.75 * I0) * scale
        prof = np.exp(-(r / sig) ** 2) * 1.2 + np.exp(-r / ((2.0 + 5.0 * I0) * scale)) * 0.07 * I0
        if I0 > 0.95:  # faint lens diffraction on only the brightest few
            sw = 0.8 * scale
            sl = 10.0 * I0 * scale
            prof = prof + (np.exp(-(dy / sw) ** 2) * np.exp(-np.abs(dx) / sl) + np.exp(-(dx / sw) ** 2) * np.exp(-np.abs(dy) / sl)) * 0.10
        col = STAR_TEMPS[int(S["temp"][i])] * (0.9 + 0.1 * math.sin(k[0] * phi * 0.5 + ph[2]))
        img[y0:y1, x0:x1] += prof[..., None] * col * I


def _render_meteor(img: np.ndarray, ctx: dict, t: float, spec):
    ts, te, p0, p1, peak, tau_train = spec
    if t < ts or t > te + 6.0 * tau_train:
        return
    w, h, scale = ctx["w"], ctx["h"], ctx["scale"]
    x0, y0 = p0[0] * w, p0[1] * h
    x1, y1 = p1[0] * w, p1[1] * h
    L = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    p_head = min(1.0, (t - ts) / (te - ts))
    xh, yh = x0 + dx * L * p_head, y0 + dy * L * p_head
    pad = 48
    bx0, bx1 = max(0, int(min(x0, xh)) - pad), min(w, int(max(x0, xh)) + pad)
    by0, by1 = max(0, int(min(y0, yh)) - pad), min(h, int(max(y0, yh)) + pad)
    if bx1 <= bx0 or by1 <= by0:
        return
    px = ctx["xx"][by0:by1, bx0:bx1] - x0
    py = ctx["yy"][by0:by1, bx0:bx1] - y0
    s = px * dx + py * dy
    perp = -px * dy + py * dx
    valid = ((s >= 0.0) & (s <= L * p_head)).astype(np.float32)
    p_s = np.clip(s / L, 0.0, 1.0)
    age = np.maximum(t - (ts + p_s * (te - ts)), 0.0)

    def light_curve(p):
        return np.maximum(np.sin(np.pi * np.clip(p, 0.0, 1.0)), 0.0) ** 0.55 * (1.0 + 2.1 * np.exp(-((p - 0.85) / 0.036) ** 2))

    # Seamless decay to 0 before loop wrap t=1.0 for late meteor train
    loop_fade = 1.0 - float(np.clip((t - 0.93) / 0.05, 0.0, 1.0))
    lc = light_curve(p_s) * peak
    core_w = 0.90 * scale * (1.0 + 0.45 * lc)
    streak = np.exp(-(perp / core_w) ** 2) * np.exp(-age / 0.020) * lc * valid

    # Forbidden-oxygen green-cyan early wake -> incandescent white-gold ablation core & flare
    fresh = np.exp(-age / 0.012)[..., None]
    flare_w = np.exp(-((p_s - 0.85) / 0.07) ** 2)[..., None]
    hot_mix = np.clip(np.maximum(fresh, flare_w * 0.75), 0.0, 1.0)
    col_plasma = _hex("#58FFB8") * (1.0 - 0.45 * p_s[..., None]) + _hex("#8CF6FF") * (0.45 * p_s[..., None])
    col_ablate = _hex("#FFFDF5") * 0.72 + _hex("#FFC98B") * 0.45
    streak_col = col_plasma * (1.0 - hot_mix) + col_ablate * hot_mix

    # Persistent ionized wake twisted by upper-atmosphere wind shear
    wav = (2.5 * np.sin(s * 0.04 + age * 18.0) + 1.4 * np.cos(s * 0.09 - age * 11.0)) * scale * np.clip(age / 0.025, 0.0, 1.0)
    tw_ = (1.4 + 68.0 * age) * scale
    train = np.exp(-((perp - wav) / tw_) ** 2) * np.exp(-age / tau_train) * lc * valid * 0.24 * (1.4 / (1.4 + 68.0 * age)) * loop_fade
    train_col = 0.65 * _hex("#58FFB4") + 0.35 * _hex("#FFB478")

    add = streak[..., None] * streak_col * 1.95 + train[..., None] * train_col
    if t <= te:
        xx_r = ctx["xx"][by0:by1, bx0:bx1]
        yy_r = ctx["yy"][by0:by1, bx0:bx1]
        hd = np.sqrt((xx_r - xh) ** 2 + (yy_r - yh) ** 2)
        lch = float(light_curve(np.array(p_head))) * peak
        add += (np.exp(-(hd / (1.85 * scale)) ** 2) * 1.95 + np.exp(-hd / (9.5 * scale)) * 0.24)[..., None] * _hex("#FFF6E8") * lch
        # 3 tiny trailing ablation fragmentation micro-sparks behind head after p >= 0.78
        if p_head >= 0.78:
            frag_fade = min(1.0, (p_head - 0.78) / 0.06) * (1.0 - max(0.0, (p_head - 0.94) / 0.06))
            px_n, py_n = -dy, dx
            for idx_f, (lag_px, lat_px) in enumerate(((2.8, 0.7), (5.6, -1.1), (8.6, 0.5))):
                drift = 1.0 + (p_head - 0.78) * (4.0 + 1.5 * idx_f)
                fx_p = xh - dx * lag_px * scale * drift + px_n * lat_px * scale * drift
                fy_p = yh - dy * lag_px * scale * drift + py_n * lat_px * scale * drift
                fd2 = ((xx_r - fx_p) ** 2 + (yy_r - fy_p) ** 2) / ((0.95 * scale) ** 2)
                f_col = _hex("#FFFDF5") if idx_f == 0 else _hex("#FFC98B")
                add += np.exp(-fd2)[..., None] * f_col * (1.25 * frag_fade * lch * (1.0 - 0.22 * idx_f))
    img[by0:by1, bx0:bx1] += add


def _render_surface_glitters(
    ctx: dict, f: int, phi: float, dcx: float, dcy: float, ge: float,
    gy0: int, gy1: int, gx0: int, gx1: int, a_eff_r: np.ndarray,
) -> np.ndarray:
    """Render ~3600 twinkling prismatic stardust grains & top 55 4-point diamond glints directly on Girl."""
    scale = ctx["scale"]
    S = ctx["S_glit"]
    gx = S["dx"] + ctx["cen0"][0] + dcx - float(gx0)
    gy = S["dy"] + ctx["cen0"][1] + dcy - float(gy0)
    if ge > 0.0:
        rj = np.random.default_rng(8300 + f)
        gx = gx + rj.normal(0.0, 5.5 * ge, gx.size).astype(np.float32)
    tw = (0.5 + 0.5 * np.sin(S["k"] * phi + S["ph"])) ** 14
    val = S["br"] * tw
    active = val > 0.08
    rh, rw = gy1 - gy0, gx1 - gx0
    out = np.zeros((rh, rw, 3), dtype=np.float32)
    if not np.any(active):
        return out
    gx_a, gy_a, val_a, c_a = gx[active], gy[active], val[active], S["col"][active]
    # Keep stars strictly within active grain-mask ROI
    ix = np.clip(np.round(gx_a).astype(np.int32), 0, rw - 1)
    iy = np.clip(np.round(gy_a).astype(np.int32), 0, rh - 1)
    vis = a_eff_r[iy, ix] > 0.15
    gx_a, gy_a, val_a, c_a = gx_a[vis], gy_a[vis], val_a[vis], c_a[vis]
    if gx_a.size == 0:
        return out

    pal = S["pal"]
    for ci in range(len(pal)):
        mc = c_a == ci
        if not np.any(mc):
            continue
        buf = np.zeros((rh, rw), dtype=np.float32)
        splat(buf, gx_a[mc], gy_a[mc], val_a[mc])
        out += gauss_blur_f32(buf, 0.55 * scale)[..., None] * pal[ci]

    # Top ~65 brightest twinkling surface diamonds get crisp 4-point optical crosshairs
    n_top = min(65, val_a.size)
    if n_top > 0:
        top_idx = np.argpartition(val_a, -n_top)[-n_top:]
        sp_buf = np.zeros((rh, rw), dtype=np.float32)
        splat(sp_buf, gx_a[top_idx], gy_a[top_idx], val_a[top_idx] * 0.72)
        sp_core = gauss_blur_f32(sp_buf, 0.55 * scale)
        acc = np.zeros((rh, rw), dtype=np.float32)
        for d in range(1, int(round(13 * scale))):
            wgt = math.exp(-d / (3.8 * scale))
            acc[:, d:] += sp_core[:, :-d] * wgt
            acc[:, :-d] += sp_core[:, d:] * wgt
            acc[d:, :] += sp_core[:-d, :] * wgt
            acc[:-d, :] += sp_core[d:, :] * wgt
        out += acc[..., None] * np.array([1.0, 0.96, 0.99], dtype=np.float32) * 0.36
    return out


def _render_particles(ctx: dict, f: int, phi: float, dcx: float, dcy: float, ge: float):
    w, h, scale = ctx["w"], ctx["h"], ctx["scale"]
    P = ctx["P"]
    cyc_f = (f - 1) / float(N_FRAMES) * P["k"] + P["off"]
    age = (cyc_f - np.floor(cyc_f)).astype(np.float32)
    cyc = (np.floor(cyc_f) % P["k"]).astype(np.int64)
    hsh = P["seed"] + cyc * 7919
    cls = P["cls"]
    pd, pa, pl, pe = ctx["pool_downwind"], ctx["pool_all"], ctx["left_pool"], ctx["pool_edge"]
    sx = np.empty(cls.size, np.float32)
    sy = np.empty(cls.size, np.float32)
    # 70% downwind + 30% full contour on Class 0 so dust peels organically with the wind
    m0 = cls == 0
    if np.any(m0):
        use_dw = (P["seed"][m0] % 10) < 7
        idx0 = hsh[m0]
        sx0 = np.where(use_dw, pd[idx0 % len(pd), 0], pe[idx0 % len(pe), 0])
        sy0 = np.where(use_dw, pd[idx0 % len(pd), 1], pe[idx0 % len(pe), 1])
        sx[m0], sy[m0] = sx0, sy0
    for c, pool in ((1, pa), (2, pl), (3, pe)):
        m = cls == c
        idx = hsh[m] % len(pool)
        sx[m] = pool[idx, 0]
        sy[m] = pool[idx, 1]

    ang = 2 * np.pi * ((np.sin(P["seed"] * 12.9898 + cyc * 78.233) * 43758.5453) % 1.0)
    halo = (cls == 1).astype(np.float32) * P["halo_r"]
    tw1 = 2.0 * math.pi * age * P["wob_k"] + P["ph"]
    tw2 = 2.0 * math.pi * age * (P["wob_k"] * 2.0 + 1.0) - P["ph"] * 1.3
    wob1 = P["wob_a"] * np.sin(tw1)
    wob2 = (P["wob_a"] * 0.45) * np.cos(tw2)
    drift_x = np.where(cls == 0, (age ** 1.35) * P["vx"] * 1.25, P["vx"] * age)
    x = sx + dcx + np.cos(ang) * halo + drift_x + wob1 + wob2 * 0.6
    y = sy + dcy + np.sin(ang) * halo + P["vy"] * (age ** 1.05) + 0.55 * wob1 - wob2
    life = np.sin(np.pi * age) ** 0.75 * np.where(cls == 0, (1.0 - age) ** 0.45, 1.0)
    twk = 0.25 + 0.75 * (0.5 + 0.5 * np.sin(P["tw_k"] * phi + P["tw_ph"])) ** 6
    val = (P["br"] * life * twk * 2.9).astype(np.float32)
    if ge > 0.0:
        rj = np.random.default_rng(7000 + f)
        x = x + rj.normal(0, 16 * ge, x.size).astype(np.float32)
        y = y + rj.normal(0, 3.5 * ge, y.size).astype(np.float32)

    buf_w = np.zeros((h, w), np.float32)
    buf_p = np.zeros((h, w), np.float32)
    buf_c = np.zeros((h, w), np.float32)
    buf_h = np.zeros((h, w), np.float32)
    hero = cls == 3
    ct = P["ctype"]
    mw = (ct == 0) & ~hero
    mp_ = (ct == 1) & ~hero
    mc = (ct == 2) & ~hero
    splat(buf_w, x[mw], y[mw], val[mw])
    splat(buf_p, x[mp_], y[mp_], val[mp_])
    splat(buf_c, x[mc], y[mc], val[mc])
    splat(buf_h, x[hero], y[hero], val[hero])

    pts_w = gauss_blur_f32(buf_w, 0.65 * scale)
    pts_p = gauss_blur_f32(buf_p, 0.65 * scale)
    pts_c = gauss_blur_f32(buf_c, 0.65 * scale)
    pts_h = gauss_blur_f32(buf_h, 0.85 * scale)
    glow = _fast_blur_down(buf_w + buf_p + buf_c * 0.8 + buf_h * 2.2, 5.5 * scale, 2)

    # 4-point glints on hero diamond sparks (ROI only)
    ys, xs = np.nonzero(buf_h > 1e-4)
    spikes = np.zeros((h, w), np.float32)
    if ys.size:
        pad_s = int(round(20 * scale))
        y0, y1 = max(0, int(ys.min()) - pad_s), min(h, int(ys.max()) + pad_s + 1)
        x0, x1 = max(0, int(xs.min()) - pad_s), min(w, int(xs.max()) + pad_s + 1)
        roi = pts_h[y0:y1, x0:x1]
        acc = np.zeros_like(roi)
        for d in range(1, int(round(19 * scale))):
            wgt = math.exp(-d / (5.5 * scale))
            acc[:, d:] += roi[:, :-d] * wgt
            acc[:, :-d] += roi[:, d:] * wgt
            acc[d:, :] += roi[:-d, :] * wgt
            acc[:-d, :] += roi[d:, :] * wgt
        spikes[y0:y1, x0:x1] = acc * 0.17
    out = (
        pts_w[..., None] * _hex("#FFF8F5")
        + pts_p[..., None] * _hex("#FF8CCB")
        + pts_c[..., None] * _hex("#8CF0FF")
        + pts_h[..., None] * _hex("#FFFFFF")
        + spikes[..., None] * _hex("#FFE8F6")
        + glow[..., None] * _hex("#FF9ACD") * 0.45
    )
    return out


def _shift_x_clamp(arr: np.ndarray, dx: int) -> np.ndarray:
    """Shift 2D array horizontally with edge clamping (prevents wrap-around screen border artifacts)."""
    w = arr.shape[1]
    idx = np.clip(np.arange(w, dtype=np.int32) - dx, 0, w - 1)
    return arr[:, idx]


def _glitch(img: np.ndarray, f: int, e: float, gy_bounds: Tuple[int, int]) -> np.ndarray:
    """True 'Glitch in the Universe' burst: prismatic RGB split + razor scanline tears (ZERO wrap/macroblocks)."""
    h, w = img.shape[:2]
    rng = np.random.default_rng(31337 + f)
    out = img.copy()

    # 1. Radial + Girl-band horizontal prismatic RGB split
    s = int(round(3 + 10 * e * rng.uniform(0.65, 1.0)))
    r_sh = _shift_x_clamp(img[..., 0], s)
    b_sh = _shift_x_clamp(img[..., 2], -s)
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
    rad_w = np.clip(((xx - 0.52) ** 2 + (yy - 0.65) ** 2) * 3.2, 0.22, 1.0)
    gy0, gy1 = gy_bounds
    girl_band = np.exp(-(((yy * h) - 0.5 * (gy0 + gy1)) / max(120.0, 0.55 * (gy1 - gy0))) ** 2)
    split_w = np.clip(rad_w * 0.72 + girl_band * 0.48, 0.0, 1.0)
    out[..., 0] = img[..., 0] * (1.0 - split_w) + r_sh * split_w
    out[..., 2] = img[..., 2] * (1.0 - split_w) + b_sh * split_w

    # 2. 10-18 razor-thin dimensional scanline tears (70% Girl/meteor bands, 30% sky/clouds)
    n_slices = int(round(10 + 8 * e))
    for i in range(n_slices):
        r_pick = rng.random()
        if r_pick < 0.48:
            y0 = int(rng.integers(max(0, gy0 - 30), min(h - 10, gy1 + 30)))
        elif r_pick < 0.72:
            y0 = int(rng.integers(int(0.04 * h), int(0.24 * h)))
        else:
            y0 = int(rng.integers(0, h - 10))
        bh = int(rng.integers(1, 10))
        y1 = min(h, y0 + bh)
        sh = int(rng.choice([-1, 1]) * rng.uniform(10, 72) * e)
        stagger = int(round((2 + 8 * e) * rng.uniform(0.6, 1.2)))
        sl = out[y0:y1]
        r_s = _shift_x_clamp(sl[..., 0], sh + stagger)
        g_s = _shift_x_clamp(sl[..., 1], sh)
        b_s = _shift_x_clamp(sl[..., 2], sh - stagger)
        torn = np.stack([r_s, g_s, b_s], axis=-1)
        # Brief spectral scanline & cyan/magenta highlight inside torn strip
        if rng.random() < 0.45:
            tint = np.array([1.15, 0.85, 1.25], dtype=np.float32) if i % 2 == 0 else np.array([0.82, 1.18, 1.28], dtype=np.float32)
            torn = torn * tint
        if y1 - y0 >= 2:
            torn[::2] *= 1.0 - 0.16 * e
        out[y0:y1] = torn

    # 3. Subtle whole-frame temporal scanline flicker
    out[::2] *= 1.0 - 0.08 * e
    out *= 1.0 + 0.05 * e * float(rng.uniform(-1, 1))
    return np.clip(out, 0.0, 1.0)


def _process_frame(f: int) -> Tuple[int, float]:
    tf0 = time.time()
    ctx = _CTX
    w, h, scale, aspect = ctx["w"], ctx["h"], ctx["scale"], ctx["aspect"]
    u, v, xx, yy = ctx["u"], ctx["v"], ctx["xx"], ctx["yy"]
    L = ctx["layers"]
    f_info = ctx["meta"]["frames"][f"{f:03d}"]
    phi = 2.0 * math.pi * (f - 1) / float(N_FRAMES)
    t = (f - 1) / float(N_FRAMES)
    f12 = (f - 1) // 2
    ge = _glitch_strength(f)

    cam_dy = 0.0085 * math.sin(phi)
    cam_dx = 0.0030 * math.cos(phi)
    cam_zm = 1.0 + 0.007 * (0.5 - 0.5 * math.cos(phi))

    # 1. Sky + scintillating stars + meteors (behind clouds)
    img = _crop_layer(L["sky"], w, h, cam_dx * 0.5, cam_dy * 0.6, 1.0 + (cam_zm - 1.0) * 0.4)
    _render_stars(img, ctx, phi, cam_dx * 0.5, cam_dy * 0.6)
    for spec in METEORS:
        _render_meteor(img, ctx, t, spec)

    # 2. Clouds: far + hero, with the Girl-lit emission breathing (and a flash when meteor 1 flares)
    lay = _crop_layer(L["cfar"], w, h, cam_dx * 0.9 + 0.005 * math.sin(phi), cam_dy * 1.05, 1.0 + (cam_zm - 1.0) * 0.8)
    img = img * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4]
    dx_m = cam_dx * 1.3 + 0.009 * math.sin(phi - 0.4)
    lay = _crop_layer(L["cmid"], w, h, dx_m, cam_dy * 1.45, 1.0 + (cam_zm - 1.0) * 1.1)
    a_m = lay[..., 3:4]
    img = img * (1 - a_m) + (lay[..., :3] * 0.86) * a_m
    glow = _crop_layer(L["ccore"], w, h, dx_m, cam_dy * 1.45, 1.0 + (cam_zm - 1.0) * 1.1)
    flash = 0.45 * math.exp(-((t - 0.231) / 0.012) ** 2) + 0.25 * math.exp(-((t - 0.701) / 0.009) ** 2)
    pulse = 1.0 + 0.10 * math.sin(2.0 * phi) + flash
    img += glow[..., :3] * glow[..., 3:4] * pulse * 0.86

    # 3. Grass with wind ripple
    gmid = _crop_layer(L["gmid"], w, h, cam_dx, cam_dy, cam_zm)
    y_s = int(0.73 * h)
    tip_w = np.clip((0.865 - v[y_s:, :]) / 0.10, 0.0, 1.0)
    shear = 3.2 * np.sin(2.0 * phi + u[y_s:, :] * 10.0) * tip_w + 1.2 * np.sin(5.0 * phi + u[y_s:, :] * 31.0) * tip_w
    dx_i = np.clip(np.round(xx[y_s:, :] - shear), 0, w - 1).astype(np.int32)
    gmid[y_s:] = gmid[y_s:][np.arange(h - y_s)[:, None], dx_i]
    gm_a = gmid[..., 3:4]

    # 4. Girl made of grains: sculptural 0.44..0.76 pearlescent core + multi-scale stardust + eroded edge + surface glints
    g = _load_rgba(os.path.join(ctx["cel_dir"], f"girl_{f:03d}.png"))
    b = _load_rgba(os.path.join(ctx["cel_dir"], f"boy_{f:03d}.png"))
    ga = g[..., 3]
    ys_c, xs_c = np.where(ga > 0.5)
    dcx = float(xs_c.mean()) - ctx["cen0"][0]
    dcy = float(ys_c.mean()) - ctx["cen0"][1]
    gys, gxs = np.where(ga > 0.01)
    gy0, gy1 = max(0, int(gys.min()) - 14), min(h, int(gys.max()) + 15)
    gx0, gx1 = max(0, int(gxs.min()) - 14), min(w, int(gxs.max()) + 15)
    R = (slice(gy0, gy1), slice(gx0, gx1))
    a = ga[R]

    # Multi-scale granular stardust texture & wind-swept downwind erosion
    a_blur = gauss_blur_f32(a, 5.2 * scale)
    gx_a = np.gradient(a_blur, axis=1)
    downwind_w = np.clip(0.55 - gx_a * 2.2, 0.35, 1.0)
    interior = sstep(0.52, 0.96, a_blur)
    edge_amt = (1.0 - interior) * downwind_w

    rng_g12 = np.random.default_rng(5000 + f12)
    rng_gf = np.random.default_rng(9000 + f)
    clump_n = gauss_blur_f32(rng_g12.standard_normal(a.shape).astype(np.float32), 0.90 * scale)
    clump_u = 0.5 + 0.5 * np.tanh(clump_n * 1.45)
    # Eroded 10-22px outer stardust zone dissolves organically into multi-scale bright clusters
    keep_erode = np.where(clump_u > (edge_amt * 0.78), np.clip((clump_u - edge_amt * 0.65) * 2.2, 0.0, 1.0), 0.0).astype(np.float32)
    a_eff_r = a * (interior + (1.0 - interior) * keep_erode)

    g_fine = gauss_blur_f32(rng_gf.standard_normal(a.shape).astype(np.float32), 0.42 * scale) * 1.75
    g_med = gauss_blur_f32(rng_g12.standard_normal(a.shape).astype(np.float32), 1.25 * scale) * 2.4
    grain_mix = g_fine * 0.72 + g_med * 0.28

    depth = g[R][..., 1:2]
    rim_c = g[R][..., 2:3]
    base_col = (
        _hex("#F4B2D2") * (1.0 - (0.35 + 0.65 * depth))
        + _hex("#FFF8F4") * (0.35 + 0.65 * depth)
        + np.array([0.14, 0.11, 0.16], dtype=np.float32) * rim_c
    )
    # Luminous 0.70..0.94 pearlescent stardust core so she outshines clouds while HDR glints burst brighter!
    lum = (0.74 + 0.22 * np.clip(grain_mix[..., None], -1.4, 1.4)) * (1.0 - 0.16 * (1.0 - depth))
    em_r = base_col * lum

    # Twinkling static pixel micro-sparkles + 3600 coherent RGB surface glitters + hero optical star glints
    h1, h2, kk = ctx["gl_h1"][R], ctx["gl_h2"][R], ctx["gl_k"][R]
    tw = np.clip(np.sin(kk * phi + 6.2832 * h2), 0.0, 1.0)
    micro_sp = (h1 > 0.982) * (tw ** 14) * 3.8 + (h1 > 0.935) * (tw ** 7) * 0.85
    em_r = em_r * a_eff_r[..., None] + (micro_sp * a_eff_r)[..., None] * _hex("#FFF4FC")
    em_r += _render_surface_glitters(ctx, f, phi, dcx, dcy, ge, gy0, gy1, gx0, gx1, a_eff_r)

    # Ambient micro-glitch dimensional shimmer ON the Girl (every frame, 4-6 thin 1-2px slices)
    rng_mg = np.random.default_rng(14100 + f12)
    n_mg = int(rng_mg.integers(4, 7))
    sh_amp = 1.8 if ge <= 0.0 else 3.2
    for _ in range(n_mg):
        sy0 = int(rng_mg.integers(4, max(5, (gy1 - gy0) - 6)))
        shh = int(rng_mg.integers(1, 3))
        dx_r = int(rng_mg.choice([-1, 1]) * rng_mg.integers(1, max(2, int(round(sh_amp * 2.0)))))
        dx_b = -dx_r
        sl_e = em_r[sy0 : sy0 + shh]
        em_r[sy0 : sy0 + shh, :, 0] = np.roll(sl_e[..., 0], dx_r, axis=1)
        em_r[sy0 : sy0 + shh, :, 2] = np.roll(sl_e[..., 2], dx_b, axis=1)
        em_r[sy0 : sy0 + shh, :, 1] = np.roll(sl_e[..., 1], int(dx_r // 2), axis=1)

    g_em = np.zeros((h, w, 3), np.float32)
    g_a = np.zeros((h, w), np.float32)
    g_em[R] = np.maximum(em_r, 0.0)
    g_a[R] = np.clip(a_eff_r, 0.0, 1.0)

    # 5. Boy: dark grounded realistic silhouette + Chiaroscuro rose grazing rim + indigo crown rim + 35mm grain
    ba = b[..., 3:4]
    rng_bg = np.random.default_rng(2200 + f)
    boy_grain = 0.88 + 0.24 * np.clip(rng_bg.standard_normal((h, w, 1)).astype(np.float32) * 0.45, -1.0, 1.0)
    boy_col = (_hex("#070614") * (0.55 + 0.45 * b[..., 2:3]) + _hex("#0F0D24") * 0.35 * b[..., 2:3]) * boy_grain
    rim_g = np.clip(b[..., 0:1] * 1.65, 0.0, 1.0) ** 1.15
    top_edge = np.clip(ba[..., 0] - np.roll(ba[..., 0], 3, axis=0), 0.0, 1.0)[..., None]
    boy_col += rim_g * _hex("#FFC4DE") * (0.85 + 0.25 * (boy_grain - 0.88)) * 0.95
    boy_col += np.clip(b[..., 1:2] * 0.85 + top_edge * 0.45, 0.0, 1.0) * _hex("#7B8EFF") * 0.28
    wrap = _fast_blur_down(g_em, 15.0 * scale, 2)
    b_inner = sstep(0.62, 0.98, _fast_blur_down(ba[..., 0], 5.5 * scale, 2))[..., None]
    boy_col += wrap * ba * (1.0 - b_inner) * 0.55

    img = img * (1 - ba) + boy_col * ba
    img = img * (1 - gm_a) + gmid[..., :3] * gm_a

    img = img * (1 - g_a[..., None]) + g_em
    clasp_u, clasp_v = f_info["clasp_uv"]
    d_clasp = np.sqrt(((u - clasp_u) * aspect) ** 2 + (v - clasp_v) ** 2)
    cw = ba * np.exp(-(d_clasp / 0.022) ** 2)[..., None] * 0.92
    img = img * (1 - cw) + boy_col * cw
    clasp_spark = np.exp(-(d_clasp / 0.018) ** 2) * (0.14 + 0.08 * math.sin(6.0 * phi))
    img += clasp_spark[..., None] * _hex("#FFD4EA")

    # 6. Halation (kept off the solid hill)
    solid_hill = _fast_blur_down(gm_a[..., 0] * np.clip((v - 0.850) / 0.015, 0.0, 1.0), 5.0 * scale, 2)[..., None]
    hal = (_fast_blur_down(g_em, 3.2 * scale, 2) * 0.30
           + _fast_blur_down(g_a, 15.0 * scale, 2)[..., None] * _hex("#FF9CC8") * 0.40
           + _fast_blur_down(g_a, 56.0 * scale, 4)[..., None] * _hex("#E2589A") * 0.26)
    img += hal * (1.0 - 0.82 * solid_hill)

    # 7. Glitter particles shed from her silhouette
    img += _render_particles(ctx, f, phi, dcx, dcy, ge)

    foot_tuck = gm_a * np.clip((v - 0.838) / 0.012, 0.0, 1.0)[..., None]
    img = img * (1 - foot_tuck) + gmid[..., :3] * foot_tuck

    gfg = _crop_layer(L["gfg"], w, h, cam_dx * 1.4 + 0.005 * math.sin(2.0 * phi), cam_dy * 1.35, 1.0 + (cam_zm - 1.0) * 1.35)
    img = img * (1 - gfg[..., 3:4]) + gfg[..., :3] * gfg[..., 3:4]
    for bk in ctx["bokeh"]:
        cx = (bk["u"] + 0.010 * math.sin(phi + bk["ph"])) * w
        cy = (bk["v"] + 0.006 * math.cos(phi + bk["ph"])) * h
        r = bk["r"]
        x0, x1 = max(0, int(cx - r - 2)), min(w, int(cx + r + 3))
        y0, y1 = max(0, int(cy - r - 2)), min(h, int(cy + r + 3))
        if x1 <= x0 or y1 <= y0:
            continue
        rd = np.sqrt((xx[y0:y1, x0:x1] - cx) ** 2 + (yy[y0:y1, x0:x1] - cy) ** 2) / r
        disc = sstep(1.0, 0.40, rd)
        img[y0:y1, x0:x1] += disc[..., None] * bk["col"] * bk["I"] * (0.75 + 0.25 * math.sin(2 * phi + bk["ph"]))

    # 8. Lens: optical bloom -> ACES filmic tone map -> radial chromatic aberration
    img = np.maximum(img, 0.0)
    br = np.maximum(img - 0.82, 0.0)
    img += _fast_blur_down(br, 6.0 * scale, 2) * 0.42 + _fast_blur_down(br, 28.0 * scale, 4) * 0.28
    x = img * 1.0
    img = np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0)
    r_ch = np.asarray(Image.fromarray((img[..., 0] * 255).astype(np.uint8), mode="L").resize((w + 4, h + 6), Image.Resampling.BILINEAR).crop((2, 3, w + 2, h + 3)), dtype=np.float32) / 255.0
    b_ch = np.asarray(Image.fromarray((img[..., 2] * 255).astype(np.uint8), mode="L").resize((w - 4, h - 6), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    b_ch = np.pad(b_ch, ((3, 3), (2, 2)), mode="edge")
    edge_k = np.clip(((u - 0.5) ** 2 + (v - 0.5) ** 2) * 4.0, 0.0, 1.0)
    img[..., 0] = img[..., 0] * (1 - edge_k) + r_ch * edge_k
    img[..., 2] = img[..., 2] * (1 - edge_k) + b_ch * edge_k

    # 9. Glitch in the universe bursts (zero macroblock copy-paste!)
    if ge > 0.0:
        img = _glitch(img, f, ge, (gy0, gy1))

    # 10. Film: crisp fine 35mm optical grain + subtle chroma grain + vignette
    img *= ctx["vignette"]
    rng_f = np.random.default_rng(1000 + f)
    gr = gauss_blur_f32(rng_f.standard_normal((h, w)).astype(np.float32), 0.38) * 1.35
    Lm = img.mean(axis=-1, keepdims=True)
    amp = 0.007 + 0.036 * Lm * (1.0 - Lm)
    img += gr[..., None] * amp + rng_f.standard_normal((h, w, 3)).astype(np.float32) * 0.0035
    img += rng_f.uniform(-0.5, 0.5, (h, w, 1)).astype(np.float32) / 255.0
    img = np.clip(img, 0.0, 1.0)
    Image.fromarray((img * 255.0 + 0.5).astype(np.uint8)).save(os.path.join(ctx["out_dir"], f"{f:03d}.png"))
    return f, time.time() - tf0


def main():
    if len(sys.argv) < 4:
        print("Usage: python fx_v3.py <cel_dir> <bg_v3_dir> <out_dir> [frames]")
        sys.exit(1)
    cel_dir, bg_dir, out_dir = (os.path.abspath(p) for p in sys.argv[1:4])
    os.makedirs(out_dir, exist_ok=True)
    meta = json.load(open(os.path.join(cel_dir, "meta.json"), "r", encoding="utf-8"))
    if len(sys.argv) >= 5:
        want: List[int] = []
        for p in sys.argv[4].split(","):
            p = p.strip()
            if "-" in p:
                a0, b0 = p.split("-", 1)
                want.extend(range(int(a0), int(b0) + 1))
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
                print(f"fx {f:03d} ({dt:.2f}s)", flush=True)
    else:
        _init_worker(cel_dir, bg_dir, out_dir, meta)
        for f in frames:
            _, dt = _process_frame(f)
            print(f"fx {f:03d} ({dt:.2f}s)", flush=True)
    print(f"Composited {len(frames)} frames in {time.time() - t0:.2f}s -> {out_dir}")


if __name__ == "__main__":
    main()

