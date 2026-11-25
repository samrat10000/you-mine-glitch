"""Composite shot 03 (v4 recipe): painted sky -> sinking sun -> painted mountains -> cel town.
Far layers follow the camera tilt (meta hy); the cel layer carries the crane parallax itself.
Aerial haze over the far fields, light wrap, tower light glow, bloom, dust motes, grade, vignette, grain.
usage: python3 comp_s03.py <celdir> <outdir> [frames]"""
import sys, os, glob, json, math, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

CEL, OUT = sys.argv[1:3]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
META = json.load(open(os.path.join(CEL, 'meta.json')))
KEYS = sorted(META, key=int); NF = 84
sky0 = np.asarray(Image.open(os.path.join(HERE, 'sky03.png'))).astype(np.float32) / 255
mts0 = np.asarray(Image.open(os.path.join(HERE, 'mts03.png'))).astype(np.float32) / 255
bgH, bgW = sky0.shape[:2]
skyb = np.stack([gaussian_filter(sky0[..., c], 2.2) for c in range(3)], -1)
mtsb = np.stack([gaussian_filter(mts0[..., c], 1.6) for c in range(4)], -1)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rng = np.random.default_rng(3); NM = 70
mote = dict(x=rng.uniform(0.15, 0.85, NM), y=rng.uniform(0.10, 0.75, NM), r=rng.uniform(1.2, 4.5, NM),
            vx=rng.uniform(-0.0006, 0.0004, NM), vy=rng.uniform(-0.0012, -0.0002, NM), ph=rng.uniform(0, 6.3, NM))
H1 = META[KEYS[0]]['hy']


def ease(t):
    t = min(max(t, 0), 1); return t * t * (3 - 2 * t)


def crop(layer, dy, f):
    """110% canvas -> screen; shifted by dy (screen units) so the far layers follow the tilt"""
    cw, ch = int(W * 1.1), int(H * 1.1)
    cx = bgW // 2 + int(4 * math.sin(f * 0.04)); cy = bgH // 2 - int(dy * H)
    c = layer[max(0, cy - H // 2):cy - H // 2 + H, cx - W // 2:cx - W // 2 + W]
    if c.shape[0] < H:
        c = np.concatenate([c, np.repeat(c[-1:], H - c.shape[0], 0)], 0)
    return c


def frame(f, celpath):
    m = META[str(f)]; k = (f - 1) / (NF - 1); fs = f - ((f - 1) % 2)
    dy = m['hy'] - H1
    bg = crop(skyb, dy, f).copy()
    # the sun sinks a little below its lighting position over the shot, behind the near summit
    sx, sy = m['sx'], m['sy'] + 0.075 * ease(k * 1.1)
    d = np.sqrt(((xx / W - sx) * W / H) ** 2 + (yy / H - sy) ** 2)
    glow = np.exp(-d / 0.035)[..., None] * np.array([1.0, 0.85, 0.55]) * 0.38 + np.exp(-d / 0.20)[..., None] * np.array([1.0, 0.55, 0.30]) * 0.28
    bg = bg + glow
    disk = np.clip((0.019 - d) / 0.0022, 0, 1)
    bg = bg + (np.array([1.0, 0.97, 0.86]) - bg) * disk[..., None]
    beam = np.exp(-np.sqrt(((xx / W - sx) * W / H) ** 2 + (yy / H - sy) ** 2) / 0.32)
    mt = crop(mtsb, dy, f)
    ma = mt[..., 3:4]
    mcol = mt[..., :3] + np.exp(-d / 0.10)[..., None] * np.array([0.30, 0.14, 0.05]) * 0.5   # sun haze over the crest
    bg = bg * (1 - ma) + mcol * ma
    # mist band along the mountain feet (behind the fields)
    foot = np.exp(-((yy / H - (m['fy'] - 0.006)) / 0.018) ** 2)
    bg = bg + foot[..., None] * np.array([0.55, 0.36, 0.34]) * 0.35
    cel = np.asarray(Image.open(celpath).convert('RGBA').resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    a = cel[..., 3:4]; rgb = cel[..., :3]
    # aerial perspective: far fields + tower fade toward the horizon colour
    hz = np.clip(1 - (yy / H - m['fy']) / 0.11, 0, 1) ** 1.6 * (yy / H > m['hy'] - 0.25)
    hcol = np.array([0.98, 0.66, 0.48])
    pass   # aerial haze now happens in the Blender materials (by camera depth)
    inner = np.clip(1 - gaussian_filter(a[..., 0], 7), 0, 1)[..., None] * a
    wrapsrc = np.stack([gaussian_filter(bg[..., c] * (1 - a[..., 0]), 10) for c in range(3)], -1)
    img = rgb * a + bg * (1 - a)
    img = img + wrapsrc * inner * (0.45 * beam[..., None] + 0.08)
    if m['tower_on']:
        tx, ty = m['tx'] * W, m['ty'] * H
        g = np.exp(-((xx - tx) ** 2 + (yy - ty) ** 2) / (2 * 4.0 ** 2)) + 0.25 * np.exp(-((xx - tx) ** 2 + (yy - ty) ** 2) / (2 * 16.0 ** 2))
        img = img + g[..., None] * np.array([1.0, 0.15, 0.1]) * 1.1
    mm = np.zeros((H, W), np.float32)
    for i in range(NM):
        x = (mote['x'][i] + mote['vx'][i] * fs + 0.004 * math.sin(fs * 0.12 + mote['ph'][i])) * W
        y = (mote['y'][i] + mote['vy'][i] * fs) * H
        r = mote['r'][i]
        x0, x1, y0, y1 = int(max(x - 3 * r, 0)), int(min(x + 3 * r, W)), int(max(y - 3 * r, 0)), int(min(y + 3 * r, H))
        if x1 <= x0 or y1 <= y0: continue
        tw = 0.6 + 0.4 * math.sin(fs * 0.4 + mote['ph'][i] * 3)
        mm[y0:y1, x0:x1] += np.exp(-((xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2) / (2 * (r * .6) ** 2)) * tw
    img = img + (mm * beam)[..., None] * np.array([1.0, 0.85, 0.6]) * 0.55
    hi = np.clip(img.max(-1, keepdims=True) - 0.82, 0, 1) / 0.18 * img
    bl = np.stack([gaussian_filter(hi[..., c], 28) for c in range(3)], -1)
    img = img + bl * 0.28 + beam[..., None] * np.array([0.10, 0.04, 0.0]) * 0.6
    img = np.clip(img, 0, 1)
    img = img * 1.04 + np.array([0.035, 0.02, 0.05])
    dv = ((xx / W - .5) ** 2 * 1.4 + (yy / H - .5) ** 2)
    img = img * (1 - 0.30 * np.clip(dv * 2.4, 0, 1))[..., None]
    n = gaussian_filter(np.random.default_rng(f).standard_normal((H, W)).astype(np.float32), 0.6)
    img = img + n[..., None] * 0.018 * (0.7 + 0.6 * (1 - img.mean(-1, keepdims=True)))
    Image.fromarray((np.clip(img, 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(OUT, '%03d.png' % f))


cels = sorted(glob.glob(os.path.join(CEL, 'cel_*.png')))
want = None if len(sys.argv) < 4 else set(int(x) for x in sys.argv[3].split(','))
for c in cels:
    f = int(os.path.basename(c)[4:7])
    if want and f not in want: continue
    frame(f, c); print('comp', f, flush=True)
