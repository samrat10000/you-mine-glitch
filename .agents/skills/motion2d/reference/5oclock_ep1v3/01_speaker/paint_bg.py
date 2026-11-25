"""Painted sunset sky for shot 01 (anime BG layer). usage: python3 paint_bg.py out.png sunx suny"""
import sys, numpy as np
from scipy.ndimage import gaussian_filter, zoom
from PIL import Image

W, H = 1188, 2112          # 10% oversize so the BG can push in / drift
out, SX, SY = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
rng = np.random.default_rng(5)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = xx / W, yy / H


def C(*c):
    return np.array(c, np.float32)


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


sky = grad([(0.0, (0.13, 0.12, 0.27)), (0.22, (0.30, 0.20, 0.38)), (0.42, (0.70, 0.36, 0.42)),
            (0.58, (0.97, 0.55, 0.36)), (0.70, (1.0, 0.76, 0.48)), (0.80, (1.0, 0.86, 0.62))])
d = np.sqrt(((u - SX) * W / H) ** 2 + (v - SY) ** 2)
glow = np.exp(-d / 0.05)[..., None] * C(1.0, 0.85, 0.55) * 0.9 + np.exp(-d / 0.22)[..., None] * C(1.0, 0.55, 0.30) * 0.45
sky = sky + glow

# --- clouds: three stratus layers, crisp anime edges, sun-lit undersides + gold rims ---
for (y0, y1, sx, sy, thr, col, seed, rimk) in [
        (0.04, 0.30, 7.0, 1.0, 0.25, (0.24, 0.17, 0.34), 1, 0.25),
        (0.22, 0.52, 9.0, 1.2, 0.45, (0.46, 0.25, 0.40), 2, 0.6),
        (0.48, 0.70, 12.0, 1.4, 0.75, (0.80, 0.42, 0.42), 3, 1.0)]:
    n = fbm(sx, sy, 6, seed)
    band = sstep(y0, y0 + 0.06, v) * (1 - sstep(y1 - 0.08, y1, v))
    m = sstep(thr, thr + 0.06, n * band + band * 0.4 - 0.4)
    # lit underside: where the cloud ends just below (light from the low sun below the clouds)
    below = np.roll(m, -int(0.010 * H), axis=0)
    under = np.clip(m - below, 0, 1)
    rim = gaussian_filter(np.clip(m - np.roll(m, -int(0.004 * H), axis=0), 0, 1), 0.8)
    near = np.exp(-np.abs(u - SX) / 0.35) * np.exp(-np.abs(v - SY) / 0.30)
    base = C(*col)[None, None] * (1 - 0.15 * gaussian_filter(n, 3)[..., None].clip(-1, 1))
    lit = C(1.0, 0.62, 0.42)
    cl = base + (lit - base) * (gaussian_filter(under, 6)[..., None] * 1.6 * near[..., None]).clip(0, 0.85)
    sky = sky * (1 - m[..., None]) + cl * m[..., None]
    sky += rim[..., None] * C(1.0, 0.85, 0.55) * (0.5 + 1.4 * near[..., None]) * rimk

# sun disk (crisp) + tiny halo ring
sky = sky + (C(1.0, 0.97, 0.86) - sky) * sstep(0.024, 0.020, d)[..., None]


# --- mountains + town silhouettes along the bottom ---
def ridge(seed, base, amp, sm):
    r = np.random.default_rng(seed)
    y = np.zeros(W)
    for o in range(7):
        n = 3 * 2 ** o
        y += np.interp(np.linspace(0, n, W), np.arange(n + 1), r.standard_normal(n + 1)) * 0.55 ** o
    y = gaussian_filter(y, max(1, sm / 4))
    return base - amp * (y - y.min()) / (y.max() - y.min())


for seed, base, amp, col, sm in [(11, 0.83, 0.075, (0.62, 0.40, 0.50), 14), (12, 0.885, 0.06, (0.38, 0.24, 0.36), 9),
                                 (13, 0.93, 0.035, (0.20, 0.13, 0.22), 5)]:
    rl = ridge(seed, base, amp, sm)
    m = (v > rl[None, :]).astype(np.float32)
    m = gaussian_filter(m, 0.7)
    haze = np.exp(-np.abs(u - SX) / 0.3)[..., None] * C(0.25, 0.12, 0.05) * (0.9 if seed == 11 else 0.3)
    sky = sky * (1 - m[..., None]) + (C(*col) + haze) * m[..., None]
    if seed == 12:   # the 1964 radio tower on the middle ridge, red light
        tx = 0.18; ty = rl[int(tx * W)]
        for k in range(-2, 3):
            pass
        tw = (np.abs(u - tx) < (0.0012 + 0.006 * np.clip((v - (ty - 0.07)) / 0.07, 0, 1))) & (v > ty - 0.07) & (v < ty + 0.01)
        sky[tw] = C(0.30, 0.19, 0.30)
        RED = (int(tx * W), int((ty - 0.072) * H))
# rooftops
r = np.random.default_rng(21); x = 0
roof = np.full(W, 1.0)
while x < W:
    w = int(r.uniform(60, 160)); hgt = r.uniform(0.935, 0.97)
    roof[x:x + w] = hgt; x += w
m = gaussian_filter((v > roof[None, :]).astype(np.float32), 0.6)
sky = sky * (1 - m[..., None]) + C(0.14, 0.09, 0.15) * m[..., None]

np.save(out.replace('.png', '_red.npy'), np.array(RED))
img = np.clip(sky, 0, 1)
Image.fromarray((img * 255 + .5).astype(np.uint8)).save(out)
print('bg', out, 'red', RED)
