"""Composite shot 01: painted BG (push-in, DOF) + cel layer, light wrap, sun bloom, dust motes in the beam,
tower light blink, film grain, vignette.  usage: python3 comp_s01.py <celdir> <bg.png> <outdir> [frames]"""
import sys, os, glob, math, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom, binary_erosion

CEL, BGP, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
SX, SY = 0.576, 0.692
bg0 = np.asarray(Image.open(BGP)).astype(np.float32) / 255
RED = np.load(BGP.replace('.png', '_red.npy'))
bgH, bgW = bg0.shape[:2]
bgb = np.stack([gaussian_filter(bg0[..., c], 2.2) for c in range(3)], -1)   # DOF: background is far behind the ECU prop
rng = np.random.default_rng(3)
NM = 70
mote = dict(x=rng.uniform(0.35, 1.0, NM), y=rng.uniform(0.25, 0.95, NM), r=rng.uniform(1.2, 4.5, NM),
            vx=rng.uniform(-0.0006, 0.0004, NM), vy=rng.uniform(-0.0012, -0.0002, NM), ph=rng.uniform(0, 6.3, NM))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dsun = np.sqrt(((xx / W - SX) * W / H) ** 2 + (yy / H - SY) ** 2)
beam = np.exp(-dsun / 0.32)


def ease(t):
    t = min(max(t, 0), 1); return t * t * (3 - 2 * t)


def frame(f, celpath):
    k = ease((f - 1) / 71)
    s = 1.0 + 0.012 * k                                  # BG pushes less than the cel layer -> parallax
    cw, ch = int(W * 1.1 / s), int(H * 1.1 / s)
    cx, cy = bgW // 2 + int(6 * math.sin(f * 0.05)), bgH // 2
    crop = bgb[cy - ch // 2:cy + ch // 2, cx - cw // 2:cx + cw // 2]
    bg = np.asarray(Image.fromarray((crop * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255
    # radio-tower light: slow blink
    if (f // 12) % 2 == 0:
        rx = int((RED[0] - (bgW // 2 - cw // 2 + (cx - bgW // 2))) * W / cw); ry = int((RED[1] - (cy - ch // 2)) * H / ch)
        g = np.exp(-((xx - rx) ** 2 + (yy - ry) ** 2) / (2 * 3.0 ** 2))
        bg = bg + g[..., None] * np.array([1.0, 0.15, 0.1]) * 1.2
    cel = np.asarray(Image.open(celpath).convert('RGBA').resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    a = cel[..., 3:4]; rgb = cel[..., :3]
    # light wrap: the bright sky bleeds over the cel edges (backlit look)
    lum = bg.max(-1, keepdims=True)
    wrapsrc = np.stack([gaussian_filter(bg[..., c] * (1 - a[..., 0]), 10) for c in range(3)], -1)
    edge = np.clip(a[..., 0] - gaussian_filter(a[..., 0], 6), 0, 1)[..., None] * 0 + (a * (1 - np.clip(gaussian_filter(a[..., 0], 9)[..., None] * 1.25, 0, 1)) * 0 )
    inner = np.clip(1 - gaussian_filter(a[..., 0], 7), 0, 1)[..., None] * a
    img = rgb * a + bg * (1 - a)
    img = img + wrapsrc * inner * (0.45 * beam[..., None] + 0.08)
    # dust motes drifting through the sun beam (on twos)
    fs = f - ((f - 1) % 2)
    m = np.zeros((H, W), np.float32)
    for i in range(NM):
        x = (mote['x'][i] + mote['vx'][i] * fs + 0.004 * math.sin(fs * 0.12 + mote['ph'][i])) * W
        y = (mote['y'][i] + mote['vy'][i] * fs) * H
        r = mote['r'][i]
        x0, x1, y0, y1 = int(max(x - 3 * r, 0)), int(min(x + 3 * r, W)), int(max(y - 3 * r, 0)), int(min(y + 3 * r, H))
        if x1 <= x0 or y1 <= y0: continue
        tw = 0.6 + 0.4 * math.sin(fs * 0.4 + mote['ph'][i] * 3)
        m[y0:y1, x0:x1] += np.exp(-((xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2) / (2 * (r * .6) ** 2)) * tw
    img = img + (m * beam)[..., None] * np.array([1.0, 0.85, 0.6]) * 0.55
    # bloom from the sun + warm haze over everything near it
    hi = np.clip(img.max(-1, keepdims=True) - 0.82, 0, 1) / 0.18 * img
    bl = np.stack([gaussian_filter(hi[..., c], 28) for c in range(3)], -1)
    img = img + bl * 0.28 + beam[..., None] * np.array([0.10, 0.04, 0.0]) * 0.6
    # grade: lift shadows toward violet, gentle S
    img = np.clip(img, 0, 1)
    img = img * 1.04 + np.array([0.035, 0.02, 0.05])
    # vignette + grain
    d = ((xx / W - .5) ** 2 * 1.4 + (yy / H - .5) ** 2)
    img = img * (1 - 0.30 * np.clip(d * 2.4, 0, 1))[..., None]
    n = gaussian_filter(np.random.default_rng(f).standard_normal((H, W)).astype(np.float32), 0.6)
    img = img + n[..., None] * 0.018 * (0.7 + 0.6 * (1 - img.mean(-1, keepdims=True)))
    Image.fromarray((np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(OUT, '%03d.png' % f))


cels = sorted(glob.glob(os.path.join(CEL, 'cel_*.png')))
want = None if len(sys.argv) < 5 else set(int(x) for x in sys.argv[4].split(','))
for c in cels:
    f = int(os.path.basename(c)[4:7])
    if want and f not in want: continue
    frame(f, c); print('comp', f, flush=True)
