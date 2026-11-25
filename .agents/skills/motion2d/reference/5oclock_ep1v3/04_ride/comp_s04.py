"""Composite shot 04 (v4 recipe): painted bay sky -> sun -> far shore + sea -> cel street.
The shop window gets the mirror pass (rendered 12 frames late, flipped left-right) where the glass holdout lets it through.
Sea glitter under the sun, light wrap, bloom, dust motes, grade, vignette, grain.
usage: python3 comp_s04.py <celdir> <outdir> [frames]"""
import sys, os, glob, json, math, numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

CEL, OUT = sys.argv[1:3]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
META = json.load(open(os.path.join(CEL, 'meta.json')))
KEYS = sorted(META, key=int); NF = 96
BG = CEL if os.path.exists(os.path.join(CEL, 'sky04.png')) else HERE
sky0 = np.asarray(Image.open(os.path.join(BG, 'sky04.png'))).astype(np.float32) / 255
far0 = np.asarray(Image.open(os.path.join(BG, 'far04.png'))).astype(np.float32) / 255
bgH, bgW = sky0.shape[:2]
skyb = np.stack([gaussian_filter(sky0[..., c], 2.2) for c in range(3)], -1)
farb = np.stack([gaussian_filter(far0[..., c], 1.2) for c in range(4)], -1)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rng = np.random.default_rng(4); NM = 60
mote = dict(x=rng.uniform(0.3, 1.0, NM), y=rng.uniform(0.10, 0.70, NM), r=rng.uniform(1.2, 4.0, NM),
            vx=rng.uniform(-0.0030, -0.0012, NM), vy=rng.uniform(-0.0008, 0.0002, NM), ph=rng.uniform(0, 6.3, NM))
H1 = META[KEYS[0]]['hy']
grng = np.random.default_rng(11); NG = 220                       # sea glitter points along the sun path
glit = dict(u=grng.normal(0, 1, NG), v=grng.uniform(0.002, 0.10, NG) ** 1.3, ph=grng.uniform(0, 6.3, NG), s=grng.uniform(0.6, 1.6, NG))


def crop(layer, dy, f):
    cx = bgW // 2; cy = bgH // 2 - int(dy * H)
    c = layer[max(0, cy - H // 2):cy - H // 2 + H, cx - W // 2:cx - W // 2 + W]
    if c.shape[0] < H:
        c = np.concatenate([c, np.repeat(c[-1:], H - c.shape[0], 0)], 0)
    return c


def frame(f, celpath):
    m = META[str(f)]; fs = f - ((f - 1) % 2)
    dy = m['hy'] - H1
    bg = crop(skyb, dy, f).copy()
    sx, sy = m['sx'], m['sy']
    d = np.sqrt(((xx / W - sx) * W / H) ** 2 + (yy / H - sy) ** 2)
    bg = bg + np.exp(-d / 0.035)[..., None] * np.array([1.0, 0.85, 0.55]) * 0.38 + np.exp(-d / 0.20)[..., None] * np.array([1.0, 0.55, 0.30]) * 0.28
    disk = np.clip((0.019 - d) / 0.0022, 0, 1)
    bg = bg + (np.array([1.0, 0.97, 0.86]) - bg) * disk[..., None]
    beam = np.exp(-d / 0.32)
    fr = crop(farb, dy, f); fa = fr[..., 3:4]
    fcol = fr[..., :3] + np.exp(-d / 0.10)[..., None] * np.array([0.30, 0.14, 0.05]) * 0.5
    bg = bg * (1 - fa) + fcol * fa
    # glitter: tiny bright dashes on the sea in the sun's path, twinkling on twos
    hy = m['hy']
    for i in range(NG):
        vv = hy + 0.004 + glit['v'][i]; uu = sx + glit['u'][i] * (0.012 + 0.25 * glit['v'][i])
        tw = max(0.0, math.sin(fs * 0.9 + glit['ph'][i] * 5)) ** 4
        if tw < 0.05: continue
        px, py = uu * W, vv * H; ln = 2.0 + 9 * glit['v'][i] * 10 * glit['s'][i]
        x0, x1, y0, y1 = int(max(px - ln * 2, 0)), int(min(px + ln * 2, W)), int(max(py - 3, 0)), int(min(py + 3, H))
        if x1 <= x0 or y1 <= y0: continue
        g = np.exp(-((xx[y0:y1, x0:x1] - px) / ln) ** 2 - ((yy[y0:y1, x0:x1] - py) / 0.9) ** 2) * tw * 0.9
        bg[y0:y1, x0:x1] += g[..., None] * np.array([1.0, 0.86, 0.62])
    # haze band on the horizon
    bg = bg + np.exp(-((yy / H - (hy + 0.002)) / 0.012) ** 2)[..., None] * np.array([0.55, 0.38, 0.34]) * 0.30
    cel = np.asarray(Image.open(celpath).convert('RGBA').resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    a = cel[..., 3:4]; rgb = cel[..., :3]
    under = bg.copy()
    # shop window: where the glass holdout shows through, put the late reflection instead of the sky
    rp = os.path.join(CEL, 'refl_%03d.png' % f)
    if m.get('refl') and os.path.exists(rp):
        mk = Image.new('L', (W, H), 0)
        ImageDraw.Draw(mk).polygon([(u * W, v * H) for u, v in m['glass']], fill=255)
        mk = gaussian_filter(np.asarray(mk).astype(np.float32) / 255, 0.6)[..., None]
        rf = np.asarray(Image.open(rp).convert('RGBA').resize((W, H), Image.LANCZOS)).astype(np.float32)[:, ::-1] / 255
        ra = rf[..., 3:4]
        rsky = np.array([0.62, 0.52, 0.70]) * (1 - 0.35 * (yy / H)[..., None]) + np.array([0.10, 0.05, 0.0])   # the eastern sky behind the camera
        refl = rf[..., :3] * ra + rsky * (1 - ra)
        refl = refl * np.array([0.80, 0.84, 0.92]) + 0.03
        sheen = (np.clip(np.sin((xx + yy * 0.55) / 38.0), 0, 1) ** 12 * 0.10)[..., None]
        refl = refl + sheen
        under = under * (1 - mk) + refl * mk
    inner = np.clip(1 - gaussian_filter(a[..., 0], 7), 0, 1)[..., None] * a
    wrapsrc = np.stack([gaussian_filter(bg[..., c] * (1 - a[..., 0]), 10) for c in range(3)], -1)
    img = rgb * a + under * (1 - a)
    img = img + wrapsrc * inner * (0.45 * beam[..., None] + 0.08)
    # veiling glare: the low sun bleeds over everything near it, even when the shop roof hides the disc
    glare = np.exp(-d / 0.09)[..., None] * np.array([1.0, 0.78, 0.50]) * 0.30 + np.exp(-d / 0.35)[..., None] * np.array([1.0, 0.60, 0.35]) * 0.14
    img = img + glare
    mm = np.zeros((H, W), np.float32)
    for i in range(NM):
        x = ((mote['x'][i] + mote['vx'][i] * fs) % 1.0 + 0.004 * math.sin(fs * 0.12 + mote['ph'][i])) * W
        y = (mote['y'][i] + mote['vy'][i] * fs) * H
        r = mote['r'][i]
        x0, x1, y0, y1 = int(max(x - 3 * r, 0)), int(min(x + 3 * r, W)), int(max(y - 3 * r, 0)), int(min(y + 3 * r, H))
        if x1 <= x0 or y1 <= y0: continue
        tw = 0.6 + 0.4 * math.sin(fs * 0.4 + mote['ph'][i] * 3)
        mm[y0:y1, x0:x1] += np.exp(-((xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2) / (2 * (r * .6) ** 2)) * tw
    img = img + (mm * beam)[..., None] * np.array([1.0, 0.85, 0.6]) * 0.55
    hi = np.clip(img.max(-1, keepdims=True) - 0.74, 0, 1) / 0.26 * img
    bl = np.stack([gaussian_filter(hi[..., c], 28) for c in range(3)], -1)
    img = img + bl * 0.28 + beam[..., None] * np.array([0.10, 0.04, 0.0]) * 0.6
    img = np.clip(img * 1.07, 0, 1)
    img = img + (img * img * (3 - 2 * img) - img) * 0.55          # S-curve: deeper shadows, brighter sunlit highlights
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
