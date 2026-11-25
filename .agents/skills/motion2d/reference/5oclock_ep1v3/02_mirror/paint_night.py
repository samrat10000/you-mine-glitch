"""Painted NIGHT street seen in the curve mirror (before the convex warp). 1200x1200.
The crossroads at night: road to a vanishing point, block walls, poles, one streetlight pool,
a lone figure standing dead still in the light, faint stars, the far radio tower light.
draw(f, leaf_u) -> float RGB array. leaf_u in 0..1 = the reflected leaf crossing the OTHER way."""
import math, numpy as np, cairo
from scipy.ndimage import gaussian_filter

N = 1200
INK = (0.03, 0.03, 0.06)


def _np(s):
    s.flush()
    a = np.ndarray((N, N, 4), np.uint8, s.get_data()).astype(np.float32) / 255
    return a[..., [2, 1, 0]]


def base():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, N, N); c = cairo.Context(s)
    # sky
    g = cairo.LinearGradient(0, 0, 0, N * .55)
    g.add_color_stop_rgb(0, .02, .03, .09); g.add_color_stop_rgb(1, .07, .10, .22)
    c.set_source(g); c.paint()
    rng = np.random.default_rng(7)
    for _ in range(140):
        x, y, r = rng.uniform(0, N), rng.uniform(0, N * .45), rng.uniform(.6, 1.6)
        c.set_source_rgba(.85, .9, 1, rng.uniform(.3, .9)); c.arc(x, y, r, 0, 7); c.fill()
    # far mountains + tower light
    c.set_source_rgb(.04, .05, .11); c.move_to(0, N * .50)
    xs = np.linspace(0, N, 40)
    ys = N * .50 - 40 * np.abs(np.sin(xs / N * 5.1 + 1.3)) - 25 * np.abs(np.sin(xs / N * 13 + .2))
    for x, y in zip(xs, ys): c.line_to(x, y)
    c.line_to(N, N); c.line_to(0, N); c.close_path(); c.fill()
    vx, vy = N * .52, N * .52                       # vanishing point
    # road
    c.set_source_rgb(.05, .06, .12); c.move_to(vx - 6, vy); c.line_to(vx + 6, vy); c.line_to(N * 1.3, N); c.line_to(-N * .3, N); c.close_path(); c.fill()
    # centre line dashes
    for k in range(9):
        t0 = (k / 9) ** 1.8; t1 = ((k + .45) / 9) ** 1.8
        y0, y1 = vy + (N - vy) * t0, vy + (N - vy) * t1
        w0, w1 = 1 + 10 * t0, 1 + 10 * t1
        c.set_source_rgb(.30, .30, .34); c.move_to(vx - w0, y0); c.line_to(vx + w0, y0); c.line_to(vx + w1, y1); c.line_to(vx - w1, y1); c.fill()
    # block walls both sides + joints
    for side in (-1, 1):
        c.set_source_rgb(.07, .08, .15)
        x_far = vx + side * 30; x_near = vx + side * N * .75
        c.move_to(x_far, vy - 18); c.line_to(x_near, N * .40); c.line_to(x_near, N * .98); c.line_to(x_far, vy + 4); c.close_path(); c.fill()
        c.set_source_rgba(.02, .02, .05, .8); c.set_line_width(1.2)
        for j in range(1, 6):
            a = j / 6
            c.move_to(x_far, vy - 18 + 22 * a); c.line_to(x_near, N * .40 + (N * .58) * a); c.stroke()
    # utility poles receding on the left, with wires
    for k, t in enumerate([.12, .30, .55, .9]):
        x = vx - (N * .62) * t - 20; top = vy - (N * .62) * t - 40; bot = vy + (N * .48) * t + 10
        c.set_source_rgb(.02, .02, .05); c.rectangle(x - 3 - 9 * t, top, 6 + 18 * t, bot - top); c.fill()
    c.set_source_rgba(.02, .02, .05, .9); c.set_line_width(1.5)
    for i in range(3):
        c.move_to(vx - 25, vy - 50 - i * 6); c.curve_to(vx - 300, vy - 120 - i * 15, vx - 600, vy - 260 - i * 30, -50, vy - 420 - i * 40); c.stroke()
    img = _np(s)
    return img, (vx, vy)


BASE, VP = base()
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
LX, LY = N * .40, N * .30                  # the streetlight head (left pole)
POOL_X, POOL_Y = N * .50, N * .74


def figure(c, x, y, h):
    """lone figure in a hoodie, 7.5 heads, standing dead still, head a little down, weight on the left leg"""
    hd = h / 7.5
    c.set_source_rgb(*INK)
    c.save(); c.translate(x, y)
    T = lambda u: -h + hd * u                     # height in heads from the top
    # hood + head (hood is slightly bigger than the head and peaks back)
    c.move_to(-hd * .52, T(1.05)); c.curve_to(-hd * .62, T(.45), -hd * .38, T(.02), hd * .02, T(.0))
    c.curve_to(hd * .42, T(.02), hd * .60, T(.40), hd * .50, T(1.05)); c.close_path(); c.fill()
    # torso: sloped shoulders, hoodie hangs loose, hem at the hips
    c.move_to(-hd * .45, T(1.0))
    c.curve_to(-hd * .80, T(1.15), -hd * 1.02, T(1.30), -hd * 1.00, T(1.65))
    c.curve_to(-hd * .98, T(2.4), -hd * .90, T(3.2), -hd * .86, T(3.55))
    c.line_to(hd * .86, T(3.55))
    c.curve_to(hd * .90, T(3.2), hd * .98, T(2.4), hd * 1.00, T(1.65))
    c.curve_to(hd * 1.02, T(1.30), hd * .80, T(1.15), hd * .45, T(1.0)); c.close_path(); c.fill()
    # arms hang a hair away from the body, hands at the upper thigh
    for s_ in (-1, 1):
        c.move_to(s_ * hd * .92, T(1.45))
        c.curve_to(s_ * hd * 1.22, T(2.1), s_ * hd * 1.20, T(3.0), s_ * hd * 1.10, T(3.62))
        c.curve_to(s_ * hd * 1.12, T(3.85), s_ * hd * .95, T(3.95), s_ * hd * .88, T(3.75))
        c.curve_to(s_ * hd * .92, T(3.0), s_ * hd * .86, T(2.2), s_ * hd * .70, T(1.7)); c.close_path(); c.fill()
    # legs: left straight (weight), right slightly relaxed, gap between, shoes
    for s_, kx in ((-1, 0.0), (1, .06)):
        c.move_to(s_ * hd * .06, T(3.5)); c.line_to(s_ * hd * .80, T(3.5))
        c.curve_to(s_ * hd * .74, T(4.6), s_ * hd * (.58 + kx), T(5.6), s_ * hd * (.52 + kx), T(7.2))
        c.line_to(s_ * hd * (.62 + kx), T(7.38)); c.curve_to(s_ * hd * (.66 + kx), T(7.5), s_ * hd * (.30 + kx), T(7.52), s_ * hd * (.16 + kx), T(7.5))
        c.line_to(s_ * hd * (.20 + kx), T(7.2)); c.curve_to(s_ * hd * (.18 + kx), T(5.6), s_ * hd * .12, T(4.5), s_ * hd * .06, T(3.9)); c.close_path(); c.fill()
    c.restore()


def leaf_shape(c, R):
    """maple outline (same 7-lobe shape as the 3D leaf)"""
    NV = 140
    for k in range(NV):
        th = 2 * math.pi * k / NV; ph = (th - math.pi) / math.pi
        tri = ((ph + 1) * 3.5) % 1.0; lobe = (1 - abs(tri * 2 - 1)) ** 0.75
        env = 0.35 + 0.65 * abs(math.cos(ph * math.pi / 2.25)) ** 0.7
        rr = R * env * (0.58 + 0.42 * lobe) * (1 - 0.04 * abs(math.sin(th * 44)))
        if abs(ph) > 0.93: rr *= 0.35
        (c.move_to if k == 0 else c.line_to)(rr * math.sin(th), -rr * math.cos(th))
    c.close_path(); c.fill()
    c.set_line_width(R * 0.06); c.move_to(0, 0); c.line_to(0, R * 0.75); c.stroke()


def draw(f, leaf_u=None, flicker=1.0):
    img = BASE.copy()
    # streetlight: pole arm + cone + pool
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, N, N); c = cairo.Context(s)
    c.set_source_rgb(*INK); c.set_line_width(7); c.move_to(N * .33, N * .95); c.line_to(N * .335, LY); c.line_to(LX, LY - 8); c.stroke()
    lamp = _np(s); la = lamp.max(-1, keepdims=True) * 0 + (np.asarray(s.get_data()).reshape(N, N, 4)[..., 3:4] / 255.0)
    img = img * (1 - la) + np.array(INK) * la
    cone = np.clip(1 - np.abs(xx - (LX + (yy - LY) * .25)) / (30 + (yy - LY) * .55), 0, 1) * (yy > LY) * np.exp(-(yy - LY) / (N * .6))
    pool = np.exp(-(((xx - POOL_X) / (N * .20)) ** 2 + ((yy - POOL_Y) / (N * .06)) ** 2))
    warm = np.array([1.0, .86, .55])
    img = img + (cone[..., None] * .18 + pool[..., None] * .55) * warm * flicker
    img = img + np.exp(-((xx - LX) ** 2 + (yy - LY - 6) ** 2) / (2 * 9 ** 2))[..., None] * warm * 1.2 * flicker
    # tower light far away (blinks)
    if (f // 12) % 2 == 0:
        img = img + np.exp(-((xx - N * .71) ** 2 + (yy - N * .455) ** 2) / (2 * 2.5 ** 2))[..., None] * np.array([1, .15, .1]) * 1.5
    # the figure, dead still in the pool of light, with a thin rim from the lamp
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, N, N); c = cairo.Context(s)
    figure(c, POOL_X + 6, POOL_Y + 10, N * .135)
    a = (np.asarray(s.get_data()).reshape(N, N, 4)[..., 3] / 255.0).astype(np.float32)
    rim = np.clip(a - np.roll(np.roll(a, 3, 1), 3, 0), 0, 1) * .6
    img = img * (1 - a[..., None]) + np.array(INK) * a[..., None] + rim[..., None] * warm * .5 * flicker
    # soft contact shadow + long shadow toward the viewer (lamp is behind-left of the figure)
    sh = np.exp(-(((xx - (POOL_X + 6 + (yy - POOL_Y - 10) * .18)) / 18) ** 2)) * np.clip((yy - POOL_Y - 6) / 4, 0, 1) * np.exp(-np.clip(yy - POOL_Y - 10, 0, None) / 120)
    cs = np.exp(-(((xx - POOL_X - 6) / 26) ** 2 + ((yy - POOL_Y - 10) / 5) ** 2))
    img = img * (1 - np.clip(sh * .55 + cs * .6, 0, .8))[..., None]
    # reflected leaf, crossing the other way
    if leaf_u is not None and 0 <= leaf_u <= 1:
        lx = N * (0.95 - 0.9 * leaf_u); ly = N * (0.66 + 0.05 * math.sin(leaf_u * 6))
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, N, N); c = cairo.Context(s)
        c.translate(lx, ly); c.rotate(f * 0.4); c.set_source_rgb(.18, .07, .05)
        c.scale(1.0, 0.55 + 0.45 * abs(math.sin(f * 0.16)))          # tumbling: foreshortens as it turns
        leaf_shape(c, 30)
        la = (np.asarray(s.get_data()).reshape(N, N, 4)[..., 3:4] / 255.0)
        img = img * (1 - la) + np.array([.18, .07, .05]) * la
    img = gaussian_filter(img, (1.0, 1.0, 0))      # slight softness: it's a reflection
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    from PIL import Image
    Image.fromarray((draw(1, .5) * 255).astype(np.uint8)).save('night_test.png')
