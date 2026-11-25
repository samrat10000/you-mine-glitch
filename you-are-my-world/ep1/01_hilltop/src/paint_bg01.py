"""Pure-NumPy + PIL multi-plane painted background generator for 01_hilltop v2 (zero scipy).
Sculpts volumetric dome-normal painterly coral cumulus thunderheads with deep indigo sky coves,
Beer-Lambert optical shadowing, twilight atmospheric hill, 1800 varied wispy grass blades,
45 slender meadow reeds, and foreground bokeh at 115% oversize (1242x2208).
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

BG_DIR = os.path.abspath(os.path.join(HERE, "..", "bg_v2"))
W_SCR, H_SCR = 1080, 1920
OVERSIZE = 1.15
W, H = int(round(W_SCR * OVERSIZE)), int(round(H_SCR * OVERSIZE))  # 1242 x 2208


def scr_to_bg(u_scr: float, v_scr: float) -> Tuple[float, float]:
    return 0.5 + (u_scr - 0.5) / OVERSIZE, 0.5 + (v_scr - 0.5) / OVERSIZE


def hex_rgb(hx: str) -> np.ndarray:
    hx = hx.lstrip("#")
    return np.array([int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)], dtype=np.float32) / 255.0


def sstep(a: float, b: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - a) / max(b - a, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def fbm_2d(h: int, w: int, base_cells: Tuple[int, int], octaves: int = 5, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh = max(3, int(base_cells[0] * (2 ** o)))
        gw = max(3, int(base_cells[1] * (2 ** o)))
        grid = rng.standard_normal((gh, gw)).astype(np.float32)
        up = np.asarray(Image.fromarray(grid, mode="F").resize((w, h), Image.Resampling.BICUBIC), dtype=np.float32)
        acc += up * amp
        tot += amp
        amp *= 0.50
    acc /= tot
    return (acc - acc.mean()) / max(float(acc.std()), 1e-6)


def make_sky_base(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    stops = [
        (0.00, hex_rgb("#17165A")),
        (0.28, hex_rgb("#231E7C")),
        (0.56, hex_rgb("#31238A")),
        (0.80, hex_rgb("#3A2172")),
        (1.00, hex_rgb("#1E1342")),
    ]
    sky = np.zeros((H, W, 3), dtype=np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (v >= p0) & (v <= p1)
        t = ((v - p0) / (p1 - p0))[m][:, None]
        sky[m] = c0 * (1.0 - t) + c1 * t

    # Subtle clean atmospheric twilight scatter around couple/cloud core (zero noisy blotches)
    lc_u, lc_v = scr_to_bg(0.58, 0.68)
    d_glow = np.sqrt(((u - lc_u) * (W / H)) ** 2 + ((v - lc_v) * 0.85) ** 2)
    sky += np.exp(-d_glow / 0.38)[..., None] * hex_rgb("#782069") * 0.24
    return np.clip(sky, 0.0, 1.0)


def sculpt_cumulus_layer(
    u: np.ndarray,
    v: np.ndarray,
    lobes_scr: List[Tuple[float, float, float, float, float]],
    seed: int,
    warp_amp: float,
    edge_soft: float,
    col_shadow: np.ndarray,
    col_deep_mid: np.ndarray,
    col_mid: np.ndarray,
    col_lit: np.ndarray,
    col_core: np.ndarray,
    light_scr: Tuple[float, float] = (0.58, 0.68),
    detail_amp: float = 0.22,
    alpha_mask: np.ndarray | None = None,
    reuse_fields: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None,
) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    """Sculpt volumetric cauliflower cumulus domes using true stacked 3D lobe normals + Beer-Lambert self-shadowing."""
    aspect = W / float(H)
    if reuse_fields is not None:
        dens, nx_field, ny_field, nz_field, puff1, puff2, puff3 = reuse_fields
    else:
        wx = fbm_2d(H, W, (6, 4), octaves=5, seed=seed)
        wy = fbm_2d(H, W, (6, 4), octaves=5, seed=seed + 13)
        puff1 = fbm_2d(H, W, (10, 6), octaves=5, seed=seed + 31)
        puff2 = fbm_2d(H, W, (24, 15), octaves=4, seed=seed + 71)
        puff3 = fbm_2d(H, W, (52, 32), octaves=3, seed=seed + 99)

        uw = u + wx * warp_amp
        vw = v + wy * warp_amp * aspect

        dens = np.zeros((H, W), dtype=np.float32)
        nx_acc = np.zeros((H, W), dtype=np.float32)
        ny_acc = np.zeros((H, W), dtype=np.float32)
        nz_acc = np.zeros((H, W), dtype=np.float32)

        for (cx_s, cy_s, rx_s, ry_s, wt) in lobes_scr:
            cx, cy = scr_to_bg(cx_s, cy_s)
            rx, ry = rx_s / OVERSIZE, ry_s / OVERSIZE
            lx = (uw - cx) / rx
            ly = (vw - cy) / ry
            d2 = lx * lx + ly * ly
            inside = np.maximum(0.0, 1.0 - d2)
            dome = (inside ** 0.72) * wt
            # Smooth-max blend (k=10) so overlapping lobes merge seamlessly without rubber creases
            dens = np.maximum(dens, dome) + 0.10 * np.minimum(dens, dome)

            lz = np.sqrt(inside)
            gn_x = -lx * aspect
            gn_y = -ly
            gn_z = lz * 0.90
            gn_len = np.sqrt(gn_x * gn_x + gn_y * gn_y + gn_z * gn_z) + 1e-5
            wl = np.exp(np.clip(dome, 0.0, 1.2) * 5.0) * np.where(d2 < 1.25, 1.0, 0.0)
            nx_acc += wl * (gn_x / gn_len)
            ny_acc += wl * (gn_y / gn_len)
            nz_acc += wl * (gn_z / gn_len)

        n_len = np.sqrt(nx_acc * nx_acc + ny_acc * ny_acc + nz_acc * nz_acc) + 1e-5
        # Soft-filter accumulated dome normals so internal puff overlaps read as unified painterly mass
        nx_field = gauss_blur_f32(nx_acc / n_len, 12.0)
        ny_field = gauss_blur_f32(ny_acc / n_len, 12.0)
        nz_field = np.maximum(0.10, gauss_blur_f32(nz_acc / n_len, 12.0))

    # Fade negative breakup smoothly inside solid cloud cores -> wispy edges, ZERO interior pinholes!
    cauli = 0.52 * puff1 + 0.34 * puff2 + 0.14 * puff3
    cauli_w = np.clip((0.52 - dens) / 0.36, 0.16, 1.0)
    density = dens + cauli * detail_amp * cauli_w * np.clip(dens * 2.4 + 0.06, 0.0, 1.0)
    alpha = sstep(0.11, 0.11 + edge_soft * 0.85, density)
    if alpha_mask is not None:
        alpha = alpha * alpha_mask

    # Directional 3D dome illumination toward couple/Girl + Beer-Lambert self-shadowing
    lu, lv = scr_to_bg(*light_scr)
    dx_l = (lu - u) * aspect
    dy_l = lv - v
    dist_l = np.sqrt(dx_l * dx_l + dy_l * dy_l) + 1e-4
    ldx, ldy, ldz = dx_l / dist_l, dy_l / dist_l, 0.45

    bump = 0.28 * puff1 + 0.22 * puff2 + 0.12 * puff3
    b_dx = np.roll(bump, -3, axis=1) - bump
    b_dy = np.roll(bump, -3, axis=0) - bump
    nxe = nx_field - b_dx * 2.0
    nye = ny_field - b_dy * 2.0
    nze = nz_field
    ne_len = np.sqrt(nxe * nxe + nye * nye + nze * nze) + 1e-5
    ndotl = np.clip((nxe * ldx + nye * ldy + nze * ldz) / ne_len, 0.0, 1.0)

    # 4-step Beer-Lambert forward optical shadowing toward light source
    step_x = np.clip((dx_l / dist_l) * (0.018 * W), -44, 44).astype(np.float32)
    step_y = np.clip((dy_l / dist_l) * (0.018 * H), -44, 44).astype(np.float32)
    d_blur = gauss_blur_f32(np.clip(density, 0.0, 1.3), 5.0)
    yy_i, xx_i = np.mgrid[0:H, 0:W]
    occ = np.zeros((H, W), dtype=np.float32)
    for k_step, wt_s in ((0.8, 0.35), (1.8, 0.30), (3.0, 0.22), (4.4, 0.13)):
        sx = np.clip(np.round(xx_i + step_x * k_step), 0, W - 1).astype(np.int32)
        sy = np.clip(np.round(yy_i + step_y * k_step), 0, H - 1).astype(np.int32)
        occ += d_blur[sy, sx] * wt_s

    forward_scatter = np.exp(-np.maximum(0.0, occ - density * 0.48) * 1.40)
    rad_glow = np.exp(-dist_l / 0.40)
    soft_billows = np.clip(0.5 + 0.34 * puff1 + 0.22 * puff2, 0.0, 1.0)

    rng_g = np.random.default_rng(seed + 555)
    fine_tooth = rng_g.standard_normal((H, W)).astype(np.float32) * 0.014
    shade = np.clip(
        0.42 * ndotl * (0.45 + 0.55 * forward_scatter)
        + 0.30 * forward_scatter
        + 0.24 * rad_glow
        + 0.16 * soft_billows
        - 0.10 * np.clip(density - 0.72, 0.0, 1.0)
        + fine_tooth,
        0.0,
        1.0,
    )

    stops_col = [(0.00, col_shadow), (0.24, col_deep_mid), (0.50, col_mid), (0.76, col_lit), (1.00, col_core)]
    rgb = np.zeros((H, W, 3), dtype=np.float32)
    for (s0, c0), (s1, c1) in zip(stops_col, stops_col[1:]):
        m = (shade >= s0) & (shade <= s1)
        t = ((shade - s0) / max(s1 - s0, 1e-5))[m][:, None]
        # Slightly stepped smoothstep for painted anime cel separation
        t_p = t * t * (3.0 - 2.0 * t)
        rgb[m] = c0 * (1.0 - t_p) + c1 * t_p

    soft_alpha = gauss_blur_f32(alpha, 1.2)
    rgba = np.concatenate([np.clip(rgb, 0.0, 1.0), np.clip(soft_alpha, 0.0, 1.0)[..., None]], axis=-1)
    return rgba, (dens, nx_field, ny_field, nz_field, puff1, puff2, puff3)


def ridge_v_scr(u_scr: np.ndarray) -> np.ndarray:
    # Left knoll at ~0.788 conceals Boy's lower hips cleanly; slopes organically to ~0.858 under Girl
    knoll = 0.070 / (1.0 + np.exp((u_scr - 0.44) / 0.08))
    gentle_undul = 0.004 * np.sin(u_scr * 7.5 + 0.6) + 0.002 * np.cos(u_scr * 16.0)
    return 0.858 - knoll + gentle_undul


def make_grass_layers() -> Tuple[Image.Image, Image.Image]:
    """Build 2x SSAA atmospheric twilight hill + 1800 varied wispy blades + 45 taller reeds + corner bokeh."""
    ss = 2
    Ws, Hs = W * ss, H * ss

    # Atmospheric twilight indigo-plum hill gradient (NEVER flat dead #000000 black!)
    yy_h, xx_h = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
    uh = 0.5 + (xx_h / float(Ws) - 0.5) * OVERSIZE
    vh = 0.5 + (yy_h / float(Hs) - 0.5) * OVERSIZE
    ridge_grid = ridge_v_scr(uh)
    below_ridge = vh >= ridge_grid
    depth_in_hill = np.clip((vh - ridge_grid) / 0.18, 0.0, 1.0)
    col_crest = hex_rgb("#1D133A")
    col_bottom = hex_rgb("#110B26")
    hill_rgb = col_crest * (1.0 - depth_in_hill[..., None]) + col_bottom * depth_in_hill[..., None]

    # Subtle ambient ground bounce directly under Girl (warm rose-plum) & Boy (deep indigo)
    d_g_gnd = np.sqrt(((uh - 0.59) * (W / H)) ** 2 + ((vh - 0.858) * 1.4) ** 2)
    d_b_gnd = np.sqrt(((uh - 0.36) * (W / H)) ** 2 + ((vh - 0.790) * 1.4) ** 2)
    hill_rgb += np.exp(-d_g_gnd / 0.14)[..., None] * hex_rgb("#5A1F58") * 0.22 * (1.0 - depth_in_hill[..., None])
    hill_rgb += np.exp(-d_b_gnd / 0.14)[..., None] * hex_rgb("#242470") * 0.16 * (1.0 - depth_in_hill[..., None])
    hill_rgba = np.zeros((Hs, Ws, 4), dtype=np.uint8)
    hill_rgba[..., :3] = (np.clip(hill_rgb, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    hill_rgba[..., 3] = np.where(below_ridge, 255, 0).astype(np.uint8)
    im_mid = Image.fromarray(hill_rgba, mode="RGBA")
    dr = ImageDraw.Draw(im_mid)

    rng = np.random.default_rng(77)
    girl_u, girl_v = scr_to_bg(0.595, 0.856)
    boy_u, boy_v = scr_to_bg(0.36, 0.788)

    # Pass 1: 1800 natural clumps of varied-height wispy curved grass blades (bases well anchored inside ridge)
    blade_specs = []
    for _ in range(360):
        # 360 organic tufts x 5 blades = 1800 blades
        tuft_u = float(rng.uniform(-0.07, 1.07))
        tuft_h_scale = float(rng.uniform(0.35, 1.45))
        tuft_lean_bias = float(rng.uniform(0.85, 1.15))
        for _b in range(5):
            u_s = tuft_u + float(rng.uniform(-0.010, 0.010))
            v_s = float(ridge_v_scr(np.array([u_s]))[0]) + float(rng.uniform(0.004, 0.012))
            ub, vb = scr_to_bg(u_s, v_s)
            bx, by = ub * Ws, vb * Hs
            near_girl_feet = math.exp(-((u_s - 0.595) / 0.036) ** 2)
            # Varied heights so ridge reads lush & chaotic instead of uniform buzzcut!
            h_blade = float(rng.uniform(18, 118)) * tuft_h_scale * (1.0 - 0.30 * near_girl_feet)
            w_base = float(rng.uniform(1.4, 4.4))
            lean = float(rng.uniform(0.22, 0.92)) * tuft_lean_bias * h_blade * 0.58 * (1 if rng.random() > 0.14 else -0.40)
            pts_l, pts_r = [], []
            for k in range(6):
                t = k / 5.0
                cx = bx + lean * (t ** 1.55)
                cy = by - h_blade * t
                hw = 0.5 * w_base * (1.0 - t) ** 0.90
                pts_l.append((cx - hw, cy))
                pts_r.append((cx + hw, cy))
            dr.polygon(pts_l + list(reversed(pts_r)), fill=(27, 17, 52, 255))

            d_g = math.hypot(ub - girl_u, vb - girl_v)
            d_b = math.hypot(ub - boy_u, vb - boy_v)
            if d_g < 0.15 or d_b < 0.13:
                tip_l, tip_r = [], []
                for k in range(3, 6):
                    t = k / 5.0
                    cx = bx + lean * (t ** 1.55)
                    cy = by - h_blade * t
                    hw = 0.36 * w_base * (1.0 - t) ** 0.90
                    tip_l.append((cx - hw, cy))
                    tip_r.append((cx + hw, cy))
                rose_k = math.exp(-d_g / 0.11)
                cyan_k = math.exp(-d_b / 0.10) * 0.55
                rc = int(np.clip(32 + rose_k * 110 + cyan_k * 18, 0, 255))
                gc = int(np.clip(18 + rose_k * 52 + cyan_k * 42, 0, 255))
                bc = int(np.clip(56 + rose_k * 76 + cyan_k * 88, 0, 255))
                blade_specs.append((tip_l + list(reversed(tip_r)), (rc, gc, bc, 210)))

    # Pass 2: ~45 tall slender wispy wild meadow grass stems tapering naturally (ZERO black lollipop ovals!)
    for _r in range(45):
        u_s = float(rng.uniform(-0.04, 1.04))
        if 0.48 < u_s < 0.68:
            u_s = float(rng.uniform(0.05, 0.42)) if rng.random() < 0.5 else float(rng.uniform(0.70, 0.98))
        v_s = float(ridge_v_scr(np.array([u_s]))[0]) + 0.008
        ub, vb = scr_to_bg(u_s, v_s)
        bx, by = ub * Ws, vb * Hs
        h_reed = float(rng.uniform(95, 175))
        w_reed = float(rng.uniform(1.8, 3.2))
        lean = float(rng.uniform(0.45, 0.95)) * h_reed * 0.52
        pts_l, pts_r = [], []
        for k in range(8):
            t = k / 7.0
            cx = bx + lean * (t ** 1.55) + 5.0 * math.sin(t * math.pi)
            cy = by - h_reed * t
            hw = 0.5 * w_reed * ((1.0 - t) ** 0.95)
            pts_l.append((cx - hw, cy))
            pts_r.append((cx + hw, cy))
        dr.polygon(pts_l + list(reversed(pts_r)), fill=(28, 17, 54, 240))

    for tip_poly, tip_col in blade_specs:
        dr.polygon(tip_poly, fill=tip_col)

    im_mid_ds = im_mid.resize((W, H), Image.Resampling.LANCZOS)

    # Foreground bokeh out-of-focus silhouette grass framing lower left & right corners
    im_fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr_fg = ImageDraw.Draw(im_fg)
    for idx in range(72):
        side = -1 if idx % 2 == 0 else 1
        u_s = float(rng.uniform(-0.06, 0.30)) if side < 0 else float(rng.uniform(0.74, 1.06))
        ub, vb = scr_to_bg(u_s, float(rng.uniform(0.95, 1.05)))
        bx, by = ub * W, vb * H
        h_blade = float(rng.uniform(80, 210))
        w_base = float(rng.uniform(5, 11))
        lean = float(rng.uniform(18, 80))
        pts_l, pts_r = [], []
        for k in range(6):
            t = k / 5.0
            cx = bx + lean * (t ** 1.45)
            cy = by - h_blade * t
            hw = 0.5 * w_base * (1.0 - t) ** 0.85
            pts_l.append((cx - hw, cy))
            pts_r.append((cx + hw, cy))
        dr_fg.polygon(pts_l + list(reversed(pts_r)), fill=(16, 10, 34, 230))
    fg_arr = np.asarray(im_fg, dtype=np.float32) / 255.0
    fg_blur = gauss_blur_f32(fg_arr, 5.5)
    im_fg_out = Image.fromarray((np.clip(fg_blur, 0, 1) * 255.0 + 0.5).astype(np.uint8), mode="RGBA")
    return im_mid_ds, im_fg_out


def save_rgba(arr: np.ndarray, path: str):
    Image.fromarray((np.clip(arr, 0, 1) * 255.0 + 0.5).astype(np.uint8), mode="RGBA").save(path)


def main():
    t0 = time.time()
    os.makedirs(BG_DIR, exist_ok=True)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / float(W), yy / float(H)

    print("1/5 Painting deep electric twilight indigo sky...")
    sky = make_sky_base(u, v)
    Image.fromarray((np.clip(sky, 0, 1) * 255.0 + 0.5).astype(np.uint8)).save(os.path.join(BG_DIR, "sky_base.png"))

    print("2/5 Sculpting far plum-indigo cumulus layer with clear sky coves...")
    lobes_far = [
        # Mass 1 (center-right rising hero thunderhead behind Girl, clear left bay & right cove!)
        (0.60, 0.25, 0.11, 0.068, 0.90), (0.66, 0.30, 0.12, 0.078, 0.94),
        (0.50, 0.33, 0.13, 0.082, 0.88), (0.44, 0.42, 0.15, 0.095, 0.92),
        (0.62, 0.41, 0.15, 0.100, 0.96), (0.55, 0.54, 0.22, 0.125, 0.98),
        # Mass 2 (separate lower-left billowing bank, keeping x=0..0.34 y=0.20..0.44 open sky!)
        (0.24, 0.50, 0.14, 0.088, 0.86), (0.09, 0.54, 0.16, 0.095, 0.84),
        (-0.04, 0.62, 0.17, 0.105, 0.80), (0.28, 0.65, 0.22, 0.125, 0.92),
        (0.14, 0.78, 0.28, 0.135, 0.90),
        # Mass 3 (separate lower-right puffs leaving mid-right indigo cove x=0.74..1.00 y=0.26..0.56!)
        (0.84, 0.65, 0.16, 0.100, 0.86), (0.94, 0.76, 0.19, 0.115, 0.88),
        (0.58, 0.78, 0.34, 0.145, 0.98), (0.86, 0.88, 0.24, 0.120, 0.88),
    ]
    c_far, _ = sculpt_cumulus_layer(
        u, v, lobes_far, seed=101, warp_amp=0.028, edge_soft=0.22,
        col_shadow=hex_rgb("#2E1A66"), col_deep_mid=hex_rgb("#482070"),
        col_mid=hex_rgb("#682878"), col_lit=hex_rgb("#9A3A7E"), col_core=hex_rgb("#C44E8C"),
        detail_amp=0.38,
    )
    save_rgba(c_far, os.path.join(BG_DIR, "cloud_far.png"))

    print("3/5 Sculpting dome-normal coral cumulus clouds with deep indigo sky coves...")
    lobes_mid = [
        # Mass 1: Asymmetric cauliflower cumulus rising center-right behind Girl (bridge puff seals pinhole!)
        (0.61, 0.26, 0.095, 0.062, 0.94), (0.68, 0.31, 0.095, 0.065, 0.90),
        (0.53, 0.31, 0.110, 0.072, 0.94), (0.47, 0.42, 0.135, 0.085, 0.95),
        (0.63, 0.42, 0.125, 0.088, 0.96), (0.56, 0.53, 0.195, 0.115, 1.02),
        (0.42, 0.59, 0.175, 0.105, 0.96),
        # Mass 2: Low-mid left coral bank (leaves upper-left bay clean starlight, seals left gap!)
        (0.22, 0.52, 0.125, 0.078, 0.90), (0.08, 0.56, 0.135, 0.084, 0.86),
        (0.14, 0.63, 0.150, 0.095, 0.94), (-0.04, 0.64, 0.145, 0.092, 0.80),
        (0.26, 0.67, 0.200, 0.115, 0.96), (0.14, 0.80, 0.250, 0.125, 0.92),
        # Mass 3: Lower-right billowing puffs (carves deep mid-right sky cove y=0.26..0.56!)
        (0.82, 0.66, 0.135, 0.088, 0.88), (0.94, 0.74, 0.165, 0.105, 0.90),
        (0.60, 0.74, 0.260, 0.135, 1.02), (0.85, 0.86, 0.215, 0.115, 0.90),
    ]
    c_mid, mid_fields = sculpt_cumulus_layer(
        u, v, lobes_mid, seed=205, warp_amp=0.032, edge_soft=0.18,
        col_shadow=hex_rgb("#371E6B"), col_deep_mid=hex_rgb("#6C2A78"),
        col_mid=hex_rgb("#DC4C82"), col_lit=hex_rgb("#FF94AE"), col_core=hex_rgb("#FFD4E0"),
        detail_amp=0.44,
    )
    save_rgba(c_mid, os.path.join(BG_DIR, "cloud_mid.png"))

    print("4/5 Sculpting seamless inner radiance glow through dome puffs...")
    gu_bg, gv_bg = scr_to_bg(0.58, 0.66)
    d_girl_glow = np.sqrt(((u - gu_bg) * (W / H)) ** 2 + (v - gv_bg) ** 2)
    core_mask = np.clip(np.exp(-d_girl_glow / 0.28) * 1.15, 0.0, 1.0).astype(np.float32)
    c_core, _ = sculpt_cumulus_layer(
        u, v, [], seed=205, warp_amp=0.032, edge_soft=0.18,
        col_shadow=hex_rgb("#BC3C78"), col_deep_mid=hex_rgb("#E2548A"),
        col_mid=hex_rgb("#FA7AA0"), col_lit=hex_rgb("#FFB4C8"), col_core=hex_rgb("#FFE4EC"),
        detail_amp=0.44, alpha_mask=core_mask, reuse_fields=mid_fields,
    )
    save_rgba(c_core, os.path.join(BG_DIR, "cloud_core.png"))

    print("5/5 Drawing twilight hill, 1800 wispy grass blades, 45 tall reeds & bokeh...")
    im_gmid, im_gfg = make_grass_layers()
    im_gmid.save(os.path.join(BG_DIR, "grass_mid.png"))
    im_gfg.save(os.path.join(BG_DIR, "grass_fg_bokeh.png"))

    comp = sky.copy()
    for cl in (c_far, c_mid, c_core):
        a = cl[..., 3:4]
        comp = comp * (1.0 - a) + cl[..., :3] * a
    gm = np.asarray(im_gmid, dtype=np.float32) / 255.0
    gf = np.asarray(im_gfg, dtype=np.float32) / 255.0
    comp = comp * (1.0 - gm[..., 3:4]) + gm[..., :3] * gm[..., 3:4]
    comp = comp * (1.0 - gf[..., 3:4]) + gf[..., :3] * gf[..., 3:4]

    ox, oy = (W - W_SCR) // 2, (H - H_SCR) // 2
    crop = comp[oy : oy + H_SCR, ox : ox + W_SCR]
    prev_path = os.path.join(BG_DIR, "bg_preview.png")
    Image.fromarray((np.clip(crop, 0, 1) * 255.0 + 0.5).astype(np.uint8)).save(prev_path)
    print(f"Done in {time.time() - t0:.2f}s -> {prev_path}")


if __name__ == "__main__":
    main()
