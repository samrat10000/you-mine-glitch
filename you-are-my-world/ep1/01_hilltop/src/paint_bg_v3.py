"""Photographic-realism background painter for 01_hilltop v3 (pure NumPy + PIL, zero scipy).

Builds, at 115% oversize (1242x2208), into ep1/01_hilltop/bg_v3/:
  sky_base.png        night-sky gradient + Milky Way (dust lanes, star clouds) + ~7000 faint stars
  cloud_far.png       distant thin cumulus + high cirrus wisps (RGBA)
  cloud_mid.png       hero volumetric cumulus, light-marched (sun afterglow + sky + silver lining) (RGBA)
  cloud_core.png      the Girl-glow contribution on the hero cloud (RGB emission, A = cloud coverage)
  grass_mid.png       dark hill + ~9500 curved blades in 3 depth rows + seed-head stems, back-lit rims (RGBA)
  grass_fg_bokeh.png  out-of-focus foreground blades (RGBA)
  bg_preview.png      1080x1920 flattened check
"""
from __future__ import annotations

import math
import os
import sys
import time
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rig_mh import gauss_blur_f32

BG_DIR = os.path.abspath(os.path.join(HERE, "..", "bg_v3"))
W_SCR, H_SCR = 1080, 1920
OVERSIZE = 1.15
W, H = int(round(W_SCR * OVERSIZE)), int(round(H_SCR * OVERSIZE))  # 1242 x 2208

GIRL_GLOW_SCR = (0.586, 0.614)
GIRL_FEET_SCR = (0.595, 0.856)
BOY_SCR = (0.36, 0.788)


def scr_to_bg(u_scr: float, v_scr: float) -> Tuple[float, float]:
    return 0.5 + (u_scr - 0.5) / OVERSIZE, 0.5 + (v_scr - 0.5) / OVERSIZE


def hex_rgb(hx: str) -> np.ndarray:
    hx = hx.lstrip("#")
    return np.array([int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)], dtype=np.float32) / 255.0


def sstep(a: float, b: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _resize_f(arr: np.ndarray, w: int, h: int, resample=Image.Resampling.BILINEAR) -> np.ndarray:
    return np.asarray(Image.fromarray(arr.astype(np.float32), mode="F").resize((w, h), resample), dtype=np.float32)


def _octave(h: int, w: int, gy: int, gx: int, rng: np.random.Generator) -> np.ndarray:
    gy, gx = max(2, min(gy, h)), max(2, min(gx, w))
    grid = rng.standard_normal((gy + 3, gx + 3)).astype(np.float32)
    up = _resize_f(grid, w + int(3 * w / gx), h + int(3 * h / gy), Image.Resampling.BICUBIC)
    oy, ox = int(1.5 * h / gy), int(1.5 * w / gx)
    up = up[oy : oy + h, ox : ox + w]
    return (up - up.mean()) / (up.std() + 1e-6)


def fbm(h: int, w: int, base: Tuple[int, int], octaves: int, seed: int, mode: str = "plain", gain: float = 0.5) -> np.ndarray:
    """Multi-octave value noise. mode: plain | billow (cauliflower) | ridged (filaments)."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = _octave(h, w, int(base[0] * 2 ** o), int(base[1] * 2 ** o), rng)
        if mode == "billow":
            n = 1.0 - np.abs(n) * 0.9
        elif mode == "ridged":
            n = (1.0 - np.minimum(np.abs(n), 1.6) / 1.6) ** 2
        acc += n * amp
        tot += amp
        amp *= gain
    acc /= tot
    return (acc - acc.mean()) / (acc.std() + 1e-6)


def bilerp(arr: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    x = np.clip(x, 0.0, w - 1.001)
    y = np.clip(y, 0.0, h - 1.001)
    ix = x.astype(np.int32)
    iy = y.astype(np.int32)
    fx = x - ix
    fy = y - iy
    a = arr[iy, ix] * (1 - fx) + arr[iy, ix + 1] * fx
    b = arr[iy + 1, ix] * (1 - fx) + arr[iy + 1, ix + 1] * fx
    return a * (1 - fy) + b * fy


def splat(buf: np.ndarray, x: np.ndarray, y: np.ndarray, val: np.ndarray):
    """Bilinear sub-pixel splat of point lights into a 2D buffer (in place)."""
    h, w = buf.shape
    m = (x >= 0) & (x < w - 1) & (y >= 0) & (y < h - 1)
    x, y, val = x[m], y[m], val[m]
    ix = x.astype(np.int32)
    iy = y.astype(np.int32)
    fx = x - ix
    fy = y - iy
    np.add.at(buf, (iy, ix), val * (1 - fx) * (1 - fy))
    np.add.at(buf, (iy, ix + 1), val * fx * (1 - fy))
    np.add.at(buf, (iy + 1, ix), val * (1 - fx) * fy)
    np.add.at(buf, (iy + 1, ix + 1), val * fx * fy)


STAR_TEMPS = [hex_rgb(c) for c in ("#9DB4FF", "#C6D4FF", "#F4F6FF", "#FFF3E6", "#FFD9AE", "#FFBC7A")]
STAR_TEMP_P = np.array([0.10, 0.20, 0.30, 0.20, 0.13, 0.07])


# ----------------------------------------------------------------------------------------------- sky
def make_sky(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    stops = [
        (0.00, hex_rgb("#030514")),
        (0.22, hex_rgb("#070C28")),
        (0.45, hex_rgb("#101740")),
        (0.68, hex_rgb("#221D4E")),
        (0.86, hex_rgb("#382252")),
        (1.00, hex_rgb("#241438")),
    ]
    sky = np.zeros((H, W, 3), dtype=np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (v >= p0) & (v <= p1)
        t = ((v - p0) / (p1 - p0))[m][:, None]
        t = t * t * (3 - 2 * t)
        sky[m] = c0 * (1 - t) + c1 * t

    # Faint airglow banding (real night skies are never a clean gradient)
    air = fbm(H, W, (3, 2), 4, seed=311)
    sky += (air * 0.5 + 0.5)[..., None] * hex_rgb("#1B2A3A") * 0.08 * sstep(0.15, 0.75, v)[..., None]
    # Warm afterglow low on the right horizon (the light that colours the clouds from below)
    sun_u, sun_v = scr_to_bg(0.92, 0.86)
    d_sun = np.sqrt(((u - sun_u) * (W / H)) ** 2 + ((v - sun_v) * 1.6) ** 2)
    sky += np.exp(-d_sun / 0.30)[..., None] * hex_rgb("#7A3048") * 0.28

    # ---- Milky Way band (diagonal, upper sky — smooth gaseous star-clouds + Great Rift dust lanes) ----
    aspect = W / float(H)
    p0 = np.array([-0.12, 0.46])
    p1 = np.array([1.12, 0.03])
    dp = np.array([(p1[0] - p0[0]) * aspect, p1[1] - p0[1]])
    dvec = dp / np.linalg.norm(dp)
    nvec = np.array([-dvec[1], dvec[0]])
    rel_x = (u - p0[0]) * aspect
    rel_y = v - p0[1]
    along = rel_x * dvec[0] + rel_y * dvec[1]
    perp = rel_x * nvec[0] + rel_y * nvec[1]
    wob = 0.022 * np.sin(along * 7.0 + 1.3) + 0.010 * np.sin(along * 17.0)
    d = perp - wob
    core = np.exp(-(d / 0.052) ** 2)
    outer = np.exp(-(d / 0.145) ** 2)
    clumps_a = sstep(-0.3, 0.9, fbm(H, W, (5, 3), 6, seed=402))
    clumps_b = sstep(-0.2, 1.0, fbm(H, W, (14, 9), 5, seed=409))
    nebulosity = gauss_blur_f32(clumps_a * (0.65 + 0.50 * clumps_b), 1.2)
    dust = sstep(0.05, 0.80, fbm(H, W, (7, 5), 6, seed=405, mode="ridged") * 0.5 + 0.35)
    dust_lane = np.exp(-((d + 0.005) / 0.032) ** 2)
    mw = (core * 0.88 + outer * 0.36) * nebulosity
    mw *= 1.0 - 0.85 * np.clip(dust * (0.50 + 0.95 * dust_lane), 0.0, 1.0) * outer
    horizon_ext = sstep(0.76, 0.34, v)
    mw *= horizon_ext
    mw_col = hex_rgb("#F2D9BC")[None, None] * core[..., None] + hex_rgb("#88A2E4")[None, None] * (1.0 - core[..., None])
    sky += mw_col * (mw * 0.34)[..., None]

    rng = np.random.default_rng(417)
    # 6 soft H-alpha pink emission knots inside the galactic band
    for _ in range(6):
        a_t = float(rng.uniform(0.08, 0.92))
        cu = p0[0] + (p1[0] - p0[0]) * a_t + float(rng.normal(0, 0.012))
        cv = p0[1] + (p1[1] - p0[1]) * a_t + float(rng.normal(0, 0.012))
        r = float(rng.uniform(0.014, 0.028))
        dd = np.sqrt(((u - cu) * aspect) ** 2 + (v - cv) ** 2)
        sky += (np.exp(-(dd / r) ** 2) * horizon_ext)[..., None] * hex_rgb("#E85888") * 0.075

    # ---- ~5500 resolved background stars (2200 all-sky + 3300 Milky Way, sharp PSF + bright halos) ----
    n_st = 2200
    su = rng.uniform(0.0, 1.0, n_st)
    sv = rng.uniform(0.0, 0.80, n_st) ** 1.25
    extra = 3300
    t_b = rng.uniform(0.0, 1.0, extra)
    off = rng.normal(0.0, 0.052, extra)
    bu = p0[0] + (p1[0] - p0[0]) * t_b + (nvec[0] / aspect) * off
    bv = p0[1] + (p1[1] - p0[1]) * t_b + nvec[1] * off
    su = np.concatenate([su, bu])
    sv = np.concatenate([sv, bv])
    mag = rng.random(su.size) ** 5.2
    inten = (0.008 + 0.42 * mag) * sstep(0.82, 0.48, sv)
    temp_idx = rng.choice(len(STAR_TEMPS), size=su.size, p=STAR_TEMP_P)
    bright_m = mag > 0.35
    for c in range(3):
        cols = np.array([STAR_TEMPS[i][c] for i in temp_idx], dtype=np.float32)
        w_all = (inten * cols).astype(np.float32)
        buf_c = np.zeros((H, W), dtype=np.float32)
        splat(buf_c, su * W, sv * H, w_all)
        sky[..., c] += gauss_blur_f32(buf_c, 0.52) * 2.6
        if np.any(bright_m):
            buf_h = np.zeros((H, W), dtype=np.float32)
            splat(buf_h, su[bright_m] * W, sv[bright_m] * H, w_all[bright_m])
            sky[..., c] += gauss_blur_f32(buf_h, 2.2) * 0.9
    return np.clip(sky, 0.0, 1.0)


# ------------------------------------------------------------------------------------------- clouds
LOBES_MID = [
    # Towering cumulus congestus crown (center-right behind Girl; leaves upper-left Milky Way & right cove open!)
    (0.60, 0.25, 0.115, 0.070, 0.96), (0.67, 0.31, 0.110, 0.072, 0.94),
    (0.53, 0.31, 0.125, 0.080, 0.96), (0.48, 0.42, 0.155, 0.095, 0.98),
    (0.63, 0.42, 0.145, 0.095, 1.00), (0.56, 0.53, 0.210, 0.125, 1.06),
    # Continuous solid horizon-anchored base behind hill ridge (ZERO skull-eye sky holes!)
    (0.42, 0.59, 0.210, 0.120, 1.00), (0.38, 0.68, 0.220, 0.130, 1.00),
    (0.62, 0.63, 0.230, 0.140, 1.04), (0.49, 0.74, 0.250, 0.145, 1.04),
    # Left & right billowing horizon banks
    (0.24, 0.54, 0.145, 0.088, 0.92), (0.10, 0.58, 0.155, 0.092, 0.88),
    (0.18, 0.66, 0.185, 0.110, 0.98), (-0.04, 0.66, 0.165, 0.105, 0.84),
    (0.26, 0.74, 0.240, 0.135, 1.00), (0.12, 0.82, 0.270, 0.135, 0.96),
    (0.80, 0.67, 0.160, 0.100, 0.92), (0.94, 0.75, 0.185, 0.115, 0.94),
    (0.72, 0.78, 0.260, 0.145, 1.04), (0.86, 0.87, 0.235, 0.125, 0.94),
]
LOBES_FAR = [
    (0.66, 0.30, 0.12, 0.070, 0.80), (0.44, 0.40, 0.15, 0.090, 0.78),
    (0.30, 0.47, 0.16, 0.080, 0.74), (0.04, 0.52, 0.17, 0.090, 0.72),
    (0.90, 0.60, 0.17, 0.090, 0.76), (0.76, 0.50, 0.12, 0.060, 0.70),
]


def cloud_density(u: np.ndarray, v: np.ndarray, lobes, seed: int, erosion: float) -> Tuple[np.ndarray, np.ndarray]:
    wx = fbm(H, W, (3, 2), 4, seed=seed + 1) * 0.028
    wy = fbm(H, W, (3, 2), 4, seed=seed + 2) * 0.020
    uw, vw = u + wx, v + wy
    # C-infinity smooth-max via Lp-7 norm melts lobes seamlessly (ZERO Voronoi crease lines!)
    S_p = np.zeros((H, W), dtype=np.float32)
    for (cu, cv, rx, ry, wgt) in lobes:
        cu_b, cv_b = scr_to_bg(cu, cv)
        q = ((uw - cu_b) / (rx / OVERSIZE)) ** 2 + ((vw - cv_b) / (ry / OVERSIZE)) ** 2
        g_i = wgt * np.exp(-q * 0.88)
        S_p += g_i ** 7
    S = np.power(np.maximum(S_p, 1e-12), 1.0 / 7.0)
    billow = fbm(H, W, (9, 5), 7, seed=seed + 3, mode="billow", gain=0.52)
    fine = fbm(H, W, (40, 22), 4, seed=seed + 4, gain=0.55)
    b01 = np.clip(0.5 + 0.24 * billow, 0.0, 1.0)
    # Minimal interior erosion so the solid lower cumulus bank stays continuous, while outer wisps fray naturally
    edge_w = np.clip(1.06 - S, 0.06, 1.0)
    D = S - 0.50 + erosion * (b01 - 0.5) * 1.55 * edge_w + 0.015 * fine
    D = np.clip(D / 0.44, 0.0, None)
    D = (np.minimum(D, 1.4) ** 0.90).astype(np.float32)
    # Suppress tiny detached single-pixel floating micro-specks outside main lobes
    d_supp = _resize_f(gauss_blur_f32(_resize_f(D, W // 2, H // 2), 3.0), W, H)
    D = (D * sstep(0.018, 0.095, d_supp)).astype(np.float32)

    # 3D camera-facing smooth rounded cauliflower relief heightfield (soft-abs removes sharp V-crease lines!)
    n_c = fbm(H, W, (6, 4), 4, seed=seed + 10)
    n_m = fbm(H, W, (13, 8), 4, seed=seed + 11)
    n_f = fbm(H, W, (28, 16), 4, seed=seed + 12)
    b_coarse = 1.0 - np.sqrt(n_c * n_c + 0.16) * 0.72
    b_med = 1.0 - np.sqrt(n_m * n_m + 0.16) * 0.72
    Z_relief = np.clip(D, 0.0, 1.4) * (0.54 + 0.28 * b_coarse + 0.15 * b_med + 0.04 * n_f)
    return D, np.clip(Z_relief, 0.0, 2.0).astype(np.float32)


def _march_3d(
    Dh: np.ndarray,
    Zh_px: np.ndarray,
    ldx: np.ndarray,
    ldy: np.ndarray,
    ldz: np.ndarray,
    length_px: np.ndarray,
    n_steps: int,
    sigma: float,
) -> np.ndarray:
    """3D heightfield ray-march: lifts in +Z toward the light so convex cauliflower turrets shine."""
    hh, ww = Dh.shape
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    step = length_px / float(n_steps)
    acc = np.zeros((hh, ww), dtype=np.float32)
    for k in range(1, n_steps + 1):
        t = step * float(k)
        xs = xx + ldx * t
        ys = yy + ldy * t
        zs = Zh_px + ldz * t
        z_at = bilerp(Zh_px, xs, ys)
        d_at = bilerp(Dh, xs, ys)
        overhang = np.clip((z_at - zs) / 16.0, 0.0, 1.4)
        acc += overhang * d_at
    return acc * step * sigma


def light_cloud(D: np.ndarray, Z_relief: np.ndarray, u: np.ndarray, v: np.ndarray, palette: dict, emit_scale: float):
    hh, ww = H // 2, W // 2
    Dh = gauss_blur_f32(_resize_f(D, ww, hh), 1.6)
    Zh = gauss_blur_f32(_resize_f(Z_relief, ww, hh), 2.4)
    z_px_scale = 110.0
    Zh_px = Zh * z_px_scale
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)

    # 3D surface normals (Nx, Ny, Nz) from cauliflower heightfield gradient
    gy, gx = np.gradient(Zh_px)
    inv_n = 1.0 / np.sqrt(1.0 + gx * gx + gy * gy)
    nx, ny, nz = -gx * inv_n, -gy * inv_n, inv_n

    def wrapped_ndotl(lx, ly, lz, wrap: float = 0.45):
        dot = nx * lx + ny * ly + nz * lz
        return np.clip((dot + wrap) / (1.0 + wrap), 0.06, 1.0)

    # 1) Horizon twilight sun afterglow from below-right + front-Z (warm sunset coral-amber)
    svec = np.array([0.52, 0.55, 0.65], dtype=np.float32)
    svec /= float(np.linalg.norm(svec))
    tau_s = _march_3d(Dh, Zh_px, svec[0], svec[1], svec[2], np.full((hh, ww), 160.0, np.float32), 28, 0.032)
    ndotl_s = wrapped_ndotl(svec[0], svec[1], svec[2], 0.48)

    # 2) Cool night-sky ambient dome from above + front-Z (slate-indigo shadow crevices)
    uvec = np.array([-0.15, -0.75, 0.64], dtype=np.float32)
    uvec /= float(np.linalg.norm(uvec))
    tau_u = _march_3d(Dh, Zh_px, uvec[0], uvec[1], uvec[2], np.full((hh, ww), 140.0, np.float32), 24, 0.028)
    ndotl_u = wrapped_ndotl(uvec[0], uvec[1], uvec[2], 0.58)

    # 3) Girl point light standing in FRONT of cloud at z_girl = 1.35 * z_px_scale
    gu, gv = scr_to_bg(*GIRL_GLOW_SCR)
    lx_g, ly_g, lz_g = gu * ww, gv * hh, 1.35 * z_px_scale
    vx, vy, vz = lx_g - xx, ly_g - yy, lz_g - Zh_px
    dist3d = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-3
    dist2d = np.sqrt(vx * vx + vy * vy) / float(hh)
    tau_g = _march_3d(
        Dh, Zh_px, vx / dist3d, vy / dist3d, vz / dist3d,
        np.minimum(dist3d, 260.0), 28, 0.026,
    )
    ndotl_g = wrapped_ndotl(vx / dist3d, vy / dist3d, vz / dist3d, 0.50)

    up = lambda a: _resize_f(a, W, H)
    tau_s, tau_u, tau_g = up(tau_s), up(tau_u), up(tau_g)
    ndotl_s, ndotl_u, ndotl_g = up(ndotl_s), up(ndotl_u), up(ndotl_g)
    dist2d_f = up(dist2d)

    def ms(t):
        return (np.exp(-t) + 0.48 * np.exp(-0.34 * t) + 0.24 * np.exp(-0.11 * t)) / 1.72

    powder = 1.0 - np.exp(-2.4 * D)
    # Gentle turret crest contrast (keeps interior luminous and sculptural, NEVER black!)
    crevice_ao = 0.58 + 0.42 * np.clip(up(Zh) / np.maximum(_resize_f(gauss_blur_f32(Zh, 7.0), W, H), 0.18), 0.3, 1.2)
    edge = (1.0 - np.exp(-6.0 * D)) * np.exp(-3.4 * D)

    L_sun = ms(tau_s) * ndotl_s * (0.45 + 0.55 * powder)
    L_sky = (0.30 + 0.70 * ms(tau_u) * ndotl_u) * crevice_ao
    L_sil = edge * np.exp(-tau_s * 0.45)

    rgb = (
        palette["sun"] * L_sun[..., None]
        + palette["sky"] * L_sky[..., None]
        + palette["silver"] * L_sil[..., None]
        + palette["base"] * crevice_ao[..., None]
    )
    scatter = np.exp(-dist2d_f / 0.26) + 0.35 * np.exp(-dist2d_f / 0.48)
    girl_field = ms(tau_g) * ndotl_g * scatter * (0.45 + 0.55 * powder)
    glow = (palette["glow"] * (0.65 + 0.35 * ndotl_g)[..., None]) * girl_field[..., None] * emit_scale
    alpha = 1.0 - np.exp(-D * 4.4)
    return np.clip(rgb, 0.0, 1.25).astype(np.float32), np.clip(glow, 0.0, 1.25).astype(np.float32), alpha.astype(np.float32)


def make_cirrus(u: np.ndarray, v: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    streak = fbm(H, W, (16, 2), 4, seed=611, mode="plain", gain=0.48)
    shear_u = u + 0.08 * v
    band = sstep(0.05, 0.14, v) * sstep(0.40, 0.18, v) * (0.55 + 0.45 * np.sin(shear_u * 4.5 + 0.7))
    a = sstep(0.55, 1.35, streak) * band * 0.10
    col = hex_rgb("#7A5898")[None, None] * (1 - v[..., None]) + hex_rgb("#B66890")[None, None] * v[..., None]
    return col.astype(np.float32), a.astype(np.float32)


# -------------------------------------------------------------------------------------------- grass
def ridge_v_scr(u_scr: np.ndarray) -> np.ndarray:
    knoll = 0.070 / (1.0 + np.exp((u_scr - 0.44) / 0.08))
    gentle_undul = 0.004 * np.sin(u_scr * 7.5 + 0.6) + 0.002 * np.cos(u_scr * 16.0)
    return 0.858 - knoll + gentle_undul


def _blade(
    dr: ImageDraw.ImageDraw,
    bx: float,
    by: float,
    h: float,
    w0: float,
    th0: float,
    bend: float,
    fill,
    n: int = 8,
    min_hw: float = 0.22,
    taper_pow: float = 0.85,
):
    seg = h / (n - 1)
    x, y, th = bx, by, th0
    left, right = [], []
    for k in range(n):
        t = k / (n - 1)
        hw = max(min_hw, 0.5 * w0 * (1.0 - t) ** taper_pow + 0.15)
        nx, ny = math.cos(th), math.sin(th)
        left.append((x - nx * hw, y - ny * hw))
        right.append((x + nx * hw, y + ny * hw))
        th = th0 + bend * (t ** 1.4)
        x += math.sin(th) * seg
        y -= math.cos(th) * seg
    dr.polygon(left + right[::-1], fill=fill)
    return x, y, th


def _seed_head(dr, x, y, th, ss, rng, fill):
    """Oat/fescue-like nodding panicle with connected central rachis (ZERO floating dots)."""
    n = int(rng.integers(5, 10))
    seg = float(rng.uniform(2.2, 3.2)) * ss
    rach_w = 0.85 * ss
    pts = [(x, y)]
    ths = [th]
    for _ in range(n):
        th = th + 0.10
        x += math.sin(th) * seg
        y -= math.cos(th) * seg
        pts.append((x, y))
        ths.append(th)
    # Continuous connected rachis spine so panicle never detaches after downsampling
    rl, rr = [], []
    for i, ((px, py), pth) in enumerate(zip(pts, ths)):
        w_i = rach_w * (1.0 - 0.35 * (i / max(1, n)))
        nx, ny = math.cos(pth) * w_i, math.sin(pth) * w_i
        rl.append((px - nx, py - ny))
        rr.append((px + nx, py + ny))
    dr.polygon(rl + rr[::-1], fill=fill)
    for i in range(1, len(pts)):
        px, py = pts[i]
        pth = ths[i]
        side = 1 if i % 2 == 0 else -1
        ang = pth + side * float(rng.uniform(0.35, 0.65))
        ln = float(rng.uniform(4.0, 7.2)) * ss * (1.0 - 0.35 * i / n)
        wb = max(0.85 * ss, float(rng.uniform(0.95, 1.45)) * ss)
        wt = 0.45 * ss
        tx, ty = px + math.sin(ang) * ln, py - math.cos(ang) * ln
        mx, my = (px + tx) * 0.5, (py + ty) * 0.5
        nx_a, ny_a = math.cos(ang), math.sin(ang)
        dr.polygon([
            (px - nx_a * wb * 0.5, py - ny_a * wb * 0.5),
            (mx + nx_a * wb, my + ny_a * wb),
            (tx + nx_a * wt, ty + ny_a * wt),
            (tx - nx_a * wt, ty - ny_a * wt),
            (mx - nx_a * wb, my - ny_a * wb),
            (px + nx_a * wb * 0.5, py + ny_a * wb * 0.5),
        ], fill=fill)


def make_grass_layers() -> Tuple[Image.Image, Image.Image]:
    ss = 2
    Ws, Hs = W * ss, H * ss
    rng = np.random.default_rng(907)

    def base_y(u_s: float, dv: float) -> float:
        _, vb = scr_to_bg(u_s, float(ridge_v_scr(np.array([u_s]))[0]) + dv)
        return vb * Hs

    def bx_of(u_s: float) -> float:
        ub, _ = scr_to_bg(u_s, 0.5)
        return ub * Ws

    layers = []
    # (count, dv range, height range px@ss, width, colour, tall-stem count)
    rows = [
        (3400, (-0.002, 0.003), (6, 30), (0.9, 2.0), (24, 20, 52, 255), 30),
        (6000, (0.003, 0.012), (8, 62), (1.0, 2.6), (12, 10, 26, 255), 70),
        (1200, (0.012, 0.030), (30, 110), (1.4, 3.4), (6, 5, 14, 255), 24),
    ]
    for ri, (count, dvr, hr, wr, col, n_stems) in enumerate(rows):
        im = Image.new("RGBA", (Ws, Hs), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        if ri == 1:
            # Ground mass drawn with the mid row
            yy_h, xx_h = np.mgrid[0:Hs:4, 0:Ws:4].astype(np.float32)
            uh = 0.5 + (xx_h / float(Ws) - 0.5) * OVERSIZE
            vh = 0.5 + (yy_h / float(Hs) - 0.5) * OVERSIZE
            rig = ridge_v_scr(uh)
            below = (vh >= rig).astype(np.float32)
            dep = np.clip((vh - rig) / 0.16, 0.0, 1.0)
            g_arr = np.zeros((yy_h.shape[0], yy_h.shape[1], 4), dtype=np.uint8)
            g_arr[..., 0] = (6.0 + 5.0 * dep).astype(np.uint8)
            g_arr[..., 1] = (5.0 + 4.0 * dep).astype(np.uint8)
            g_arr[..., 2] = (18.0 + 11.0 * dep).astype(np.uint8)
            g_arr[..., 3] = (below * 255.0).astype(np.uint8)
            ground = Image.fromarray(g_arr, mode="RGBA").resize((Ws, Hs), Image.Resampling.BILINEAR)
            im.paste(ground, (0, 0), ground.split()[3])
        for _ in range(count):
            u_s = float(rng.uniform(-0.08, 1.08))
            near_girl = math.exp(-((u_s - GIRL_FEET_SCR[0]) / 0.034) ** 2)
            h = float(rng.lognormal(math.log((hr[0] + hr[1]) * 0.42), 0.45))
            h = min(max(h, hr[0]), hr[1]) * ss * (1.0 - 0.55 * near_girl)
            w0 = float(rng.uniform(*wr)) * ss
            th0 = float(rng.normal(0.18, 0.28))
            bend = float(rng.normal(0.35, 0.45)) * (1.0 + h / (hr[1] * ss))
            if rng.random() < 0.18:
                bend = float(rng.uniform(1.1, 1.9)) * (1 if rng.random() < 0.8 else -1)  # arching / drooping blades
            _blade(dr, bx_of(u_s), base_y(u_s, float(rng.uniform(*dvr))), h, w0, th0, bend, col, n=9)
        for _ in range(n_stems):
            u_s = float(rng.uniform(-0.04, 1.04))
            if 0.30 < u_s < 0.68:
                continue
            h = float(rng.uniform(hr[1] * 0.9, hr[1] * 1.55)) * ss
            th0 = float(rng.normal(0.22, 0.12))
            x, y, th = _blade(
                dr, bx_of(u_s), base_y(u_s, float(rng.uniform(*dvr))), h, 2.0 * ss, th0,
                float(rng.uniform(0.6, 1.35)), col, n=10, min_hw=0.95 * ss, taper_pow=0.55,
            )
            _seed_head(dr, x, y, th, ss, rng, col)
        arr = np.asarray(im.resize((W, H), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
        if ri == 0:
            arr = gauss_blur_f32(arr, 1.4)  # atmospheric softness on far row
        elif ri == 2:
            arr = gauss_blur_f32(arr, 1.6)  # shallow DOF softness near lens
        layers.append(arr)

    # Flatten rows back->front
    out = layers[0].copy()
    for lay in layers[1:]:
        a = lay[..., 3:4]
        out[..., :3] = out[..., :3] * (1 - a) + lay[..., :3] * a
        out[..., 3:4] = out[..., 3:4] * (1 - a) + a

    # Back-lit rims: strictly thin individual grass tips near Girl & horizon catch rose-gold light
    A = out[..., 3]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u_bg, v_bg = xx / W, yy / H
    fu, fv = scr_to_bg(*GIRL_FEET_SCR)
    d_feet = np.sqrt(((u_bg - fu) * (W / H)) ** 2 + ((v_bg - fv) * 1.3) ** 2)
    k = 2
    rim_r = A * (1.0 - np.roll(A, -k, axis=1))   # lit from the right
    rim_l = A * (1.0 - np.roll(A, k, axis=1))    # lit from the left
    rim_t = A * (1.0 - np.roll(A, k, axis=0))    # lit from above
    side = np.clip((fu - u_bg) / 0.03, -1.0, 1.0) * 0.5 + 0.5
    rim_side = rim_r * side + rim_l * (1 - side)
    glow_fall = np.exp(-d_feet / 0.11)
    horizon_fall = sstep(0.4, 1.0, u_bg) * 0.35
    rim = (rim_side * glow_fall)[..., None] * hex_rgb("#FFB8D6") * 0.92
    rim += (rim_r * horizon_fall)[..., None] * hex_rgb("#C46A7E") * 0.42
    rim += (rim_t * (0.22 + glow_fall * 0.45))[..., None] * hex_rgb("#6E66C8") * 0.32
    # Thin-blade translucency strictly above solid ridge mass (no milky band under her soles)
    thin = A * (1.0 - gauss_blur_f32(A, 2.5)) * sstep(0.004, -0.008, (v_bg - 0.5) * OVERSIZE + 0.5 - ridge_v_scr((u_bg - 0.5) * OVERSIZE + 0.5))
    rim += (thin * glow_fall)[..., None] * hex_rgb("#963868") * 0.55
    # Ground micro texture + minimal subtle contact bounce
    tex = fbm(H, W, (60, 34), 3, seed=919) * 0.010
    out[..., :3] = np.clip(out[..., :3] + rim + tex[..., None] * A[..., None], 0.0, 1.0)
    bounce = np.exp(-d_feet / 0.05) * A * 0.03
    out[..., :3] += bounce[..., None] * hex_rgb("#5A2050")
    im_mid = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), mode="RGBA")

    # Foreground out-of-focus blades (bottom corners) - real f/1.4 lens blur
    im_fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr_fg = ImageDraw.Draw(im_fg)
    for idx in range(90):
        side_s = -1 if idx % 2 == 0 else 1
        u_s = float(rng.uniform(-0.08, 0.26)) if side_s < 0 else float(rng.uniform(0.76, 1.08))
        ub, vb = scr_to_bg(u_s, float(rng.uniform(0.96, 1.06)))
        _blade(dr_fg, ub * W, vb * H, float(rng.uniform(90, 260)), float(rng.uniform(5, 12)),
               float(rng.normal(0.15 * -side_s, 0.25)), float(rng.normal(0.5, 0.5)) * -side_s, (5, 4, 12, 235))
    fg = gauss_blur_f32(np.asarray(im_fg, dtype=np.float32) / 255.0, 10.0)
    im_fg_out = Image.fromarray((np.clip(fg, 0, 1) * 255 + 0.5).astype(np.uint8), mode="RGBA")
    return im_mid, im_fg_out


def save_rgba(rgb: np.ndarray, a: np.ndarray, path: str):
    arr = np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)[..., None]], axis=-1)
    Image.fromarray((arr * 255.0 + 0.5).astype(np.uint8), mode="RGBA").save(path)


def main():
    t0 = time.time()
    os.makedirs(BG_DIR, exist_ok=True)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / float(W), yy / float(H)

    print("1/5 Night sky, Milky Way, faint stars...", flush=True)
    sky = make_sky(u, v)
    Image.fromarray((sky * 255.0 + 0.5).astype(np.uint8)).save(os.path.join(BG_DIR, "sky_base.png"))

    print("2/5 Distant cumulus + cirrus...", flush=True)
    pal_far = dict(
        sun=hex_rgb("#B0506A") * 0.65,
        sky=hex_rgb("#262D6C") * 0.62,
        silver=hex_rgb("#D88A8E") * 0.45,
        base=hex_rgb("#16153C") * 0.65,
        glow=hex_rgb("#FF9CC8") * 0.35,
    )
    D_far, Z_far = cloud_density(u, v, LOBES_FAR, seed=1201, erosion=0.45)
    D_far = D_far * 0.65
    Z_far = Z_far * 0.65
    rgb_f, glow_f, a_f = light_cloud(D_far, Z_far, u, v, pal_far, 0.4)
    ci_rgb, ci_a = make_cirrus(u, v)
    rgb_f = rgb_f + glow_f
    a_tot = a_f + ci_a * (1 - a_f)
    rgb_f = (rgb_f * a_f[..., None] + ci_rgb * (ci_a * (1 - a_f))[..., None]) / np.maximum(a_tot, 1e-4)[..., None]
    save_rgba(rgb_f, a_tot * 0.85, os.path.join(BG_DIR, "cloud_far.png"))

    print("3/5 Hero volumetric cumulus (3D relief light-marched)...", flush=True)
    pal_mid = dict(
        sun=hex_rgb("#EB5E72") * 0.88,
        sky=hex_rgb("#222B68") * 0.62,
        silver=hex_rgb("#FFD6CA") * 0.80,
        base=hex_rgb("#11153A") * 0.68,
        glow=hex_rgb("#FF92BE") * 0.60,
    )
    D_mid, Z_mid = cloud_density(u, v, LOBES_MID, seed=2205, erosion=0.52)
    rgb_m, glow_m, a_m = light_cloud(D_mid, Z_mid, u, v, pal_mid, 1.0)
    save_rgba(rgb_m, a_m, os.path.join(BG_DIR, "cloud_mid.png"))
    save_rgba(glow_m, a_m, os.path.join(BG_DIR, "cloud_core.png"))

    print("4/5 Grass rows, seed heads, back-lit rims...", flush=True)
    im_gmid, im_gfg = make_grass_layers()
    im_gmid.save(os.path.join(BG_DIR, "grass_mid.png"))
    im_gfg.save(os.path.join(BG_DIR, "grass_fg_bokeh.png"))

    print("5/5 Preview...", flush=True)
    comp = sky.copy()
    a = a_tot[..., None] * 0.85
    comp = comp * (1 - a) + np.clip(rgb_f, 0, 1) * a
    a = a_m[..., None]
    comp = comp * (1 - a) + np.clip(rgb_m + glow_m, 0, 1) * a
    for im in (im_gmid, im_gfg):
        g = np.asarray(im, dtype=np.float32) / 255.0
        comp = comp * (1 - g[..., 3:4]) + g[..., :3] * g[..., 3:4]
    ox, oy = (W - W_SCR) // 2, (H - H_SCR) // 2
    crop = comp[oy : oy + H_SCR, ox : ox + W_SCR]
    prev = os.path.join(BG_DIR, "bg_preview.png")
    Image.fromarray((np.clip(crop, 0, 1) * 255 + 0.5).astype(np.uint8)).save(prev)
    print(f"Done in {time.time() - t0:.2f}s -> {prev}", flush=True)


if __name__ == "__main__":
    main()
