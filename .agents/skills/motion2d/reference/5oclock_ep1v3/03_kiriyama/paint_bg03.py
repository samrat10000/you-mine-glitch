"""Painted far layers for shot 03 (v4 sky recipe, re-fitted to a horizon at mid-frame).
Writes sky03.png (RGB, no sun: the comp paints the sinking sun) and mts03.png (RGBA mountain ridges).
usage: python3 paint_bg03.py <meta.json>      canvas = 110% of 1080x1920, centred like comp crops"""
import sys, json, numpy as np
from scipy.ndimage import gaussian_filter, zoom
from PIL import Image

W, H = 1188, 2112
M = json.load(open(sys.argv[1])); m1 = M[sorted(M, key=int)[0]]
c2v = lambda y: 0.5 + (y - 0.5) / 1.1                       # screen -> canvas
VH = c2v(m1['hy'])                                           # horizon on the canvas
SX = 0.5 + (m1['sx'] - 0.5) / 1.1; SY = c2v(m1['sy'] + 0.04)  # mid-shot sun (it sinks during the shot)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = xx / W, yy / H
C = lambda *c: np.array(c, np.float32)


def grad(stops):
    img = np.zeros((H, W, 3), np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (v >= p0) & (v < p1)
        t = ((v - p0) / (p1 - p0))[m][:, None]
        img[m] = C(*c0) * (1 - t) + C(*c1) * t
    img[v >= stops[-1][0]] = C(*stops[-1][1])
    return img


def fbm(sx, sy, oct=5, seed=0):
    r = np.random.default_rng(seed); acc = np.zeros((H, W), np.float32); a = 1; tot = 0
    for o in range(oct):
        hh, ww = max(2, int(H / sy * 2 ** o / 64)), max(2, int(W / sx * 2 ** o / 64))
        n = r.standard_normal((hh, ww)).astype(np.float32)
        n = zoom(n, (H / hh, W / ww), order=3)[:H, :W]
        acc += n * a; tot += a; a *= 0.5
    acc /= tot
    return (acc - acc.mean()) / acc.std()


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


k = VH / 0.80                                                # v4 stops end (0.80) on the horizon
sky = grad([(0.0, (0.13, 0.12, 0.27)), (0.22 * k, (0.30, 0.20, 0.38)), (0.42 * k, (0.70, 0.36, 0.42)),
            (0.58 * k, (0.97, 0.55, 0.36)), (0.70 * k, (1.0, 0.76, 0.48)), (0.80 * k, (1.0, 0.86, 0.62))])
for (y0, y1, sx, sy, thr, col, seed, rimk) in [
        (0.04, 0.30, 7.0, 1.0, 0.25, (0.24, 0.17, 0.34), 1, 0.25),
        (0.22, 0.52, 9.0, 1.2, 0.45, (0.46, 0.25, 0.40), 2, 0.6),
        (0.48, 0.70, 12.0, 1.4, 0.75, (0.80, 0.42, 0.42), 3, 1.0)]:
    y0, y1 = y0 * k, y1 * k
    n = fbm(sx, sy, 6, seed)
    band = sstep(y0, y0 + 0.06 * k, v) * (1 - sstep(y1 - 0.08 * k, y1, v))
    m = sstep(thr, thr + 0.06, n * band + band * 0.4 - 0.4)
    below = np.roll(m, -int(0.010 * H), axis=0)
    under = np.clip(m - below, 0, 1)
    rim = gaussian_filter(np.clip(m - np.roll(m, -int(0.004 * H), axis=0), 0, 1), 0.8)
    near = np.exp(-np.abs(u - SX) / 0.35) * np.exp(-np.abs(v - SY) / 0.30)
    base = C(*col)[None, None] * (1 - 0.15 * gaussian_filter(n, 3)[..., None].clip(-1, 1))
    lit = C(1.0, 0.62, 0.42)
    cl = base + (lit - base) * (gaussian_filter(under, 6)[..., None] * 1.6 * near[..., None]).clip(0, 0.85)
    sky = sky * (1 - m[..., None]) + cl * m[..., None]
    sky += rim[..., None] * C(1.0, 0.85, 0.55) * (0.5 + 1.4 * near[..., None]) * rimk
Image.fromarray((np.clip(sky, 0, 1) * 255 + .5).astype(np.uint8)).save('sky03.png')


# --- mountain ridges (fbm, not sines): far haze ridge, middle ridge, and the near mountain the sun sets behind ---
def ridge(seed, base, amp, sm, peak=None):
    r = np.random.default_rng(seed); y = np.zeros(W)
    for o in range(7):
        n = 3 * 2 ** o
        y += np.interp(np.linspace(0, n, W), np.arange(n + 1), r.standard_normal(n + 1)) * 0.55 ** o
    y = gaussian_filter(y, max(1, sm / 4)); y = (y - y.min()) / (y.max() - y.min())
    if peak:                                                   # a dominant summit (px, width, height 0..1)
        px, pw, ph = peak
        xs = np.linspace(0, 1, W); dx = xs - px
        cone = np.where(dx < 0, np.exp(-(-dx) / (pw * 0.75)), np.exp(-dx / (pw * 1.5)))     # asymmetric, steeper sun-side
        y = np.maximum(y * 0.55, ph * cone * (0.88 + 0.12 * y))
        y = gaussian_filter(y, 7); y = y / y.max()
    return base - amp * y


ML = M[sorted(M, key=int)[-1]]
SUN_END = c2v(ML['sy'] - (ML['hy'] - m1['hy']) + 0.075 * 0.99)    # in frame-1 canvas coords (layers follow the tilt)
mts = np.zeros((H, W, 4), np.float32)
layers = [(11, VH + 0.004, 0.045, (0.66, 0.44, 0.52), 14, None, 0.9),
          (12, VH + 0.012, 0.060, (0.44, 0.27, 0.38), 9, None, 0.45),
          (13, VH + 0.030, VH + 0.030 - SUN_END + 0.004, (0.24, 0.15, 0.25), 5, (SX + 0.004, 0.16, 1.0), 0.25)]
for seed, base, amp, col, sm, peak, hz in layers:
    rl = ridge(seed, base, amp, sm, peak)
    m = gaussian_filter((v > rl[None, :]).astype(np.float32), 0.7)
    haze = np.exp(-np.abs(u - SX) / 0.3)[..., None] * C(0.25, 0.12, 0.05) * hz
    # sun-side slope: thin warm rim along the crest near the sun
    crest = np.clip(m - np.roll(m, int(0.003 * H), axis=0), 0, 1) * np.exp(-np.abs(u - SX) / 0.18)
    colr = C(*col) + haze + crest[..., None] * C(1.0, 0.70, 0.45) * 0.9
    # vertical shading: darker toward the foot (mist band at the foot comes from the comp)
    colr = colr * (1 - 0.18 * np.clip((v - rl[None, :]) / 0.05, 0, 1))[..., None]
    a = m[..., None]
    mts[..., :3] = mts[..., :3] * (1 - a) + colr * a
    mts[..., 3:] = np.maximum(mts[..., 3:], a)
Image.fromarray((np.clip(mts, 0, 1) * 255 + .5).astype(np.uint8), 'RGBA').save('mts03.png')
print('VH', VH, 'SUN', SX, SY, 'SUN_END', SUN_END)
