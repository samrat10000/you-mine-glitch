"""Composite shot 02 (v4 recipe): painted day sky + cel layer; inside the curve-mirror glass the painted NIGHT street,
mapped through the glass UV with a convex warp. Then light wrap, dust motes, bloom, grade, vignette, grain.
usage: python3 comp_s02.py <celdir> <bg.png> <outdir> [frames]"""
import sys, os, glob, json, math, numpy as np, png
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
import paint_night as PN

CEL, BGP, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
META = json.load(open(os.path.join(CEL, 'meta.json')))
m1 = META[sorted(META, key=int)[0]]
SX, SY = m1['sx'], m1['sy']
bg0 = np.asarray(Image.open(BGP)).astype(np.float32) / 255
RED = np.load(BGP.replace('.png', '_red.npy'))
bgH, bgW = bg0.shape[:2]
bgb = np.stack([gaussian_filter(bg0[..., c], 2.2) for c in range(3)], -1)
rng = np.random.default_rng(3)
NM = 70
mote = dict(x=rng.uniform(0.35, 1.0, NM), y=rng.uniform(0.25, 0.95, NM), r=rng.uniform(1.2, 4.5, NM),
            vx=rng.uniform(-0.0006, 0.0004, NM), vy=rng.uniform(-0.0012, -0.0002, NM), ph=rng.uniform(0, 6.3, NM))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dsun = np.sqrt(((xx / W - SX) * W / H) ** 2 + (yy / H - SY) ** 2)
beam = np.exp(-dsun / 0.32)
# fixed glass dirt (specks + a faint water-spot film), in glass UV space
drng = np.random.default_rng(11)
DIRT = drng.uniform(-1, 1, (90, 2)); DIRT_R = drng.uniform(0.004, 0.018, 90); DIRT_A = drng.uniform(0.04, 0.16, 90)


def ease(t):
    t = min(max(t, 0), 1); return t * t * (3 - 2 * t)


def s2l(x):
    return np.where(x > 0.04045, ((x + 0.055) / 1.055) ** 2.4, x / 12.92)


def read16(p):
    w, h, rows, _ = png.Reader(p).asDirect()
    return (np.vstack(list(rows)).reshape(h, w, -1).astype(np.float32) / 65535.0)


def up(a):
    """resize a float HxWxC array to W,H (bilinear per channel)"""
    if a.shape[0] == H: return a
    return np.stack([np.asarray(Image.fromarray(a[..., c]).resize((W, H), Image.BILINEAR)) for c in range(a.shape[2])], -1)


def frame(f, celpath):
    k = ease((f - 1) / 71)
    fs = f - ((f - 1) % 2)
    s = 1.0 + 0.012 * k
    cw, ch = int(W * 1.1 / s), int(H * 1.1 / s)
    cx, cy = bgW // 2 + int(6 * math.sin(f * 0.05)), bgH // 2
    crop = bgb[cy - ch // 2:cy + ch // 2, cx - cw // 2:cx + cw // 2]
    bg = np.asarray(Image.fromarray((crop * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    if (f // 12) % 2 == 0:
        rx = int((RED[0] - (cx - cw // 2)) * W / cw); ry = int((RED[1] - (cy - ch // 2)) * H / ch)
        g = np.exp(-((xx - rx) ** 2 + (yy - ry) ** 2) / (2 * 3.0 ** 2))
        bg = bg + g[..., None] * np.array([1.0, 0.15, 0.1]) * 1.2
    cel = up(read16(celpath))
    a = cel[..., 3:4]; rgb = cel[..., :3]
    # ---- glass: emission UV (R = local x, G = local z, B = 1) ----
    lin = s2l(np.clip(rgb, 0, 1))
    blue = (rgb[..., 2] > 0.80) & (a[..., 0] > 0.5)
    gm = np.clip(gaussian_filter(blue.astype(np.float32), 0.6) * 1.3, 0, 1) * (a[..., 0] > .5)
    ring = np.clip(gm - np.clip(gaussian_filter(gm, 1.6) * 1.6 - 0.6, 0, 1), 0, 1)   # thin ink seat where glass meets rim
    d = (lin[..., 0] - 0.5) * 2; e = (lin[..., 1] - 0.5) * 2
    # fill UV across the antialiased rim so the warp never samples garbage
    rho = np.clip(np.sqrt(d * d + e * e), 0, 1)
    TH = 1.18
    sr = np.tan(rho * TH) / math.tan(TH)                        # convex mirror: middle magnified, edges squeezed
    sc_ = np.where(rho > 1e-5, sr / np.maximum(rho, 1e-5), 1 / math.tan(TH) * TH)
    nx = PN.N / 2 + d * sc_ * PN.N * 0.49
    ny = PN.N * 0.54 - e * sc_ * PN.N * 0.49
    lu = (fs - 24) / 36.0                                         # mirror leaf crosses the other way
    night = PN.draw(fs, lu, flicker=1.0 - 0.04 * (math.sin(fs * 1.7) > 0.6))
    gy, gx = np.nonzero(gm > 0)
    ins = np.zeros((H, W, 3), np.float32)
    for c in range(3):
        ins[gy, gx, c] = map_coordinates(night[..., c], [ny[gy, gx], nx[gy, gx]], order=1, mode='nearest')
    # glass: edge falloff, a thin cool sheen of the day sky on the top-left, dirt specks
    ins *= (1 - 0.45 * rho ** 5)[..., None]
    band = np.exp(-((d * 0.75 - e * 0.65 + 0.62) ** 2) / 0.012) * np.clip(1 - rho, 0, 1) ** 0.5
    ins += band[..., None] * np.array([1.0, 0.80, 0.62]) * 0.07
    dirt = np.zeros((H, W), np.float32)
    for (px, py), r, al in zip(DIRT, DIRT_R, DIRT_A):
        dirt += al * np.exp(-((d - px) ** 2 + (e - py) ** 2) / (2 * r * r))
    ins += (np.clip(dirt, 0, .3) * gm)[..., None] * np.array([1.0, 0.82, 0.6]) * 0.5
    ins = ins * (1 - 0.85 * ring[..., None]) + np.array([0.10, 0.06, 0.08]) * 0.85 * ring[..., None]
    rgb = rgb * (1 - gm[..., None]) + ins * gm[..., None]
    # ---- v4 post ----
    inner = np.clip(1 - gaussian_filter(a[..., 0], 7), 0, 1)[..., None] * a * (1 - gm[..., None])
    wrapsrc = np.stack([gaussian_filter(bg[..., c] * (1 - a[..., 0]), 10) for c in range(3)], -1)
    img = rgb * a + bg * (1 - a)
    img = img + wrapsrc * inner * (0.45 * beam[..., None] + 0.08)
    mm = np.zeros((H, W), np.float32)
    for i in range(NM):
        x = (mote['x'][i] + mote['vx'][i] * fs + 0.004 * math.sin(fs * 0.12 + mote['ph'][i])) * W
        y = (mote['y'][i] + mote['vy'][i] * fs) * H
        r = mote['r'][i]
        x0, x1, y0, y1 = int(max(x - 3 * r, 0)), int(min(x + 3 * r, W)), int(max(y - 3 * r, 0)), int(min(y + 3 * r, H))
        if x1 <= x0 or y1 <= y0: continue
        tw = 0.6 + 0.4 * math.sin(fs * 0.4 + mote['ph'][i] * 3)
        mm[y0:y1, x0:x1] += np.exp(-((xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2) / (2 * (r * .6) ** 2)) * tw
    img = img + (mm * beam * (1 - gm))[..., None] * np.array([1.0, 0.85, 0.6]) * 0.55
    hi = np.clip(img.max(-1, keepdims=True) - 0.82, 0, 1) / 0.18 * img
    bl = np.stack([gaussian_filter(hi[..., c], 28) for c in range(3)], -1)
    img = img + bl * 0.28 + (beam * (1 - 0.7 * gm))[..., None] * np.array([0.10, 0.04, 0.0]) * 0.6
    img = np.clip(img, 0, 1)
    img = img * 1.04 + np.array([0.035, 0.02, 0.05])
    dv = ((xx / W - .5) ** 2 * 1.4 + (yy / H - .5) ** 2)
    img = img * (1 - 0.30 * np.clip(dv * 2.4, 0, 1))[..., None]
    n = gaussian_filter(np.random.default_rng(f).standard_normal((H, W)).astype(np.float32), 0.6)
    img = img + n[..., None] * 0.018 * (0.7 + 0.6 * (1 - img.mean(-1, keepdims=True)))
    Image.fromarray((np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(OUT, '%03d.png' % f))


cels = sorted(glob.glob(os.path.join(CEL, 'cel_*.png')))
want = None if len(sys.argv) < 5 else set(int(x) for x in sys.argv[4].split(','))
for c in cels:
    f = int(os.path.basename(c)[4:7])
    if want and f not in want: continue
    frame(f, c); print('comp', f, flush=True)
