"""5 O'CLOCK Ep1 v3 - shot 03 "Kiriyama" (3.5 s, 84 f @24). Built to SHOT_RULES (shot 01 v4 + 02 log).
Wide establishing shot from the hill road: tiled-roof town, the 1964 radio tower, railway + crossing, a two-car
diesel train, rice fields with the mountain's shadow creeping across them, laundry, power lines, a maple branch
in the foreground. Slow crane down. Sky, sun and mountains are painted (paint_bg03.py) and joined in comp_s03.py.
Local frame: x = right, y = into the frame (toward the sun), z = up. Everything is parented to TOWN.
usage: python3 build_s03.py <outdir> <scale> [frames|all]"""
import os, sys, json, random
OUT = sys.argv[1]; SCALE = float(sys.argv[2]); FR = sys.argv[3] if len(sys.argv) > 3 else 'all'
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, 'toonlib_v4.py')).read())
from bpy_extras.object_utils import world_to_camera_view

NF = 84
SUN = Vector(SUNV)
FWD = Vector((SUN.x, SUN.y, 0)).normalized()
YAW = math.atan2(FWD.y, FWD.x) - math.pi / 2
TOWN = empty('TOWN'); TOWN.rotation_euler = (0, 0, YAW)
TM = Matrix.Rotation(YAW, 4, 'Z')
rnd = random.Random(31)
rnd2 = random.Random(77)          # v2 detail uses its own stream so the v1 layout Sam approved stays identical
lin = lambda c: tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def W(p):
    return TM @ Vector(p)


def shade(lit, k=0.42, cool=(0.27, 0.25, 0.37)):
    """shadow tone for a lit colour: darker + pulled toward the violet paint shadow"""
    return tuple(l * k + c * (1 - k) * 0.75 for l, c in zip(lit, cool))


def T(name, lit, rim=None, tex=None, k=0.42, rf=0.40):
    return toon(name, shade(lit, k), lit, rim, tex, rf)


def tex_rows(spacing, dark=0.62, axis='Z'):
    """horizontal tile rows / siding boards: thin dark lines every `spacing` m along object Z"""
    def f(nt, ramp):
        N = nt.nodes; L = nt.links
        tc = N.new('ShaderNodeTexCoord'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sp.inputs[0])
        m = N.new('ShaderNodeMath'); m.operation = 'MULTIPLY'; m.inputs[1].default_value = 1 / spacing
        L.new(sp.outputs[axis], m.inputs[0])
        fr = N.new('ShaderNodeMath'); fr.operation = 'FRACT'; L.new(m.outputs[0], fr.inputs[0])
        g = N.new('ShaderNodeMath'); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = 0.80; L.new(fr.outputs[0], g.inputs[0])
        mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = dark
        L.new(g.outputs[0], mr.inputs['Value'])
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; L.new(tc.outputs['Object'], nz.inputs['Vector'])
        wm = N.new('ShaderNodeMapRange'); wm.inputs['From Min'].default_value = 0.35; wm.inputs['From Max'].default_value = 0.65
        wm.inputs['To Min'].default_value = 0.86; wm.inputs['To Max'].default_value = 1.06; L.new(nz.outputs['Fac'], wm.inputs['Value'])
        mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; L.new(mr.outputs[0], mm.inputs[0]); L.new(wm.outputs[0], mm.inputs[1])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        L.new(ramp.outputs[0], mx.inputs[6]); L.new(mm.outputs[0], mx.inputs[7])
        return mx.outputs[2]
    return f


def tex_paddies(nt, ramp):
    """rice paddies: brick pattern = levees (mortar) + per-field colour variation"""
    N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / 34, 1 / 15, 1)
    L.new(tc.outputs['Object'], mp.inputs[0])
    br = N.new('ShaderNodeTexBrick'); L.new(mp.outputs[0], br.inputs['Vector'])
    br.inputs['Color1'].default_value = (1.0, 1.0, 1.0, 1); br.inputs['Color2'].default_value = (0.78, 0.80, 0.70, 1)
    br.inputs['Mortar'].default_value = (0.55, 0.50, 0.55, 1); br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.035; br.inputs['Bias'].default_value = 0.0
    br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 1.0
    br.offset = 0.37; br.squash = 1.0
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    L.new(ramp.outputs[0], mx.inputs[6]); L.new(br.outputs['Color'], mx.inputs[7])
    return mx.outputs[2]


def tex_bands(period, c2):
    """aviation red/white bands up the tower (object Z)"""
    def f(nt, ramp):
        N = nt.nodes; L = nt.links
        tc = N.new('ShaderNodeTexCoord'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sp.inputs[0])
        m = N.new('ShaderNodeMath'); m.operation = 'MULTIPLY'; m.inputs[1].default_value = 1 / period; L.new(sp.outputs['Z'], m.inputs[0])
        fr = N.new('ShaderNodeMath'); fr.operation = 'FRACT'; L.new(m.outputs[0], fr.inputs[0])
        g = N.new('ShaderNodeMath'); g.operation = 'GREATER_THAN'; g.inputs[1].default_value = 0.5; L.new(fr.outputs[0], g.inputs[0])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
        L.new(g.outputs[0], mx.inputs[0]); L.new(ramp.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*c2, 1)
        return mx.outputs[2]
    return f


def _m(N, L, op, a, b=None, c=None):
    n = N.new('ShaderNodeMath'); n.operation = op
    for i, x in enumerate((a, b, c)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0]


def _mul_ramp(N, L, ramp_sock, fac):
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
    L.new(ramp_sock, mx.inputs[6])
    cb = N.new('ShaderNodeCombineXYZ')
    for i in range(3): L.new(fac, cb.inputs[i])
    L.new(cb.outputs[0], mx.inputs[7])
    return mx.outputs[2]


def tex_kawara(row=0.30, col=0.27, tin=False):
    """kawara roof: S-tile columns running down the slope (wavy shading + grooves), tile course lines, weathering"""
    def f(nt, ramp):
        N = nt.nodes; L = nt.links
        tc = N.new('ShaderNodeTexCoord')
        p = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], p.inputs[0])
        n = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Normal'], n.inputs[0])
        colc = _m(N, L, 'ADD', _m(N, L, 'MULTIPLY', p.outputs['X'], _m(N, L, 'ABSOLUTE', n.outputs['Y'])),
                  _m(N, L, 'MULTIPLY', p.outputs['Y'], _m(N, L, 'ABSOLUTE', n.outputs['X'])))
        wave = _m(N, L, 'MULTIPLY_ADD', _m(N, L, 'SINE', _m(N, L, 'MULTIPLY', colc, 2 * math.pi / col)), 0.10, 0.90)
        groove = _m(N, L, 'MULTIPLY_ADD', _m(N, L, 'LESS_THAN', _m(N, L, 'FRACT', _m(N, L, 'MULTIPLY', colc, 1 / col)), 0.10), -0.22, 1.0)
        course = _m(N, L, 'MULTIPLY_ADD', _m(N, L, 'GREATER_THAN', _m(N, L, 'FRACT', _m(N, L, 'MULTIPLY', p.outputs['Z'], 1 / row)), 0.84), -0.38, 1.0)
        nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.55; nz.inputs['Detail'].default_value = 4
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
        weath = _m(N, L, 'MULTIPLY_ADD', nz.outputs['Fac'], 0.45, 0.76)
        fac = _m(N, L, 'MULTIPLY', _m(N, L, 'MULTIPLY', wave if not tin else 1.0, groove), _m(N, L, 'MULTIPLY', course, weath))
        return _mul_ramp(N, L, ramp.outputs[0], fac)
    return f


def tex_patchy(scale=0.06, fine=0.9, lo=0.80, hi=1.12):
    """grass / earth: big soft colour patches + fine speckle (painted look, not flat)"""
    def f(nt, ramp):
        N = nt.nodes; L = nt.links
        tc = N.new('ShaderNodeTexCoord')
        n1 = N.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale; n1.inputs['Detail'].default_value = 3
        L.new(tc.outputs['Object'], n1.inputs['Vector'])
        cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.interpolation = 'CONSTANT'
        e = cr.color_ramp.elements; e[0].position = 0; e[0].color = (lo, lo, lo, 1); e[1].position = 0.46; e[1].color = (1, 1, 1, 1)
        x = e.new(0.60); x.color = (hi, hi, hi, 1)
        L.new(n1.outputs['Fac'], cr.inputs[0])
        n2 = N.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = fine; L.new(tc.outputs['Object'], n2.inputs['Vector'])
        sp = _m(N, L, 'MULTIPLY_ADD', n2.outputs['Fac'], 0.25, 0.88)
        bw = N.new('ShaderNodeRGBToBW'); L.new(cr.outputs[0], bw.inputs[0])
        return _mul_ramp(N, L, ramp.outputs[0], _m(N, L, 'MULTIPLY', bw.outputs[0], sp))
    return f


def tex_rice(rows=0.7, stub=False):
    """paddy surface: planting rows (converge into the distance), per-field tint, soft noise"""
    def f(nt, ramp):
        N = nt.nodes; L = nt.links
        tc = N.new('ShaderNodeTexCoord'); p = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], p.inputs[0])
        r = _m(N, L, 'MULTIPLY_ADD', _m(N, L, 'GREATER_THAN', _m(N, L, 'FRACT', _m(N, L, 'MULTIPLY', p.outputs['X'], 1 / rows)), 0.70),
               -0.20 if stub else -0.12, 1.0)
        n1 = N.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 0.04; L.new(tc.outputs['Object'], n1.inputs['Vector'])
        t = _m(N, L, 'MULTIPLY_ADD', n1.outputs['Fac'], 0.40, 0.80)
        return _mul_ramp(N, L, ramp.outputs[0], _m(N, L, 'MULTIPLY', r, t))
    return f


# ---------------- materials ----------------
ROOF = [T('roof_kawara', (0.38, 0.40, 0.50), tex=tex_kawara()),
        T('roof_kawara2', (0.44, 0.44, 0.52), tex=tex_kawara()),
        T('roof_sekishu', (0.66, 0.33, 0.22), tex=tex_kawara()),
        T('roof_tin', (0.32, 0.45, 0.47), tex=tex_kawara(0.9, 0.45, tin=True))]
EAVE = T('eave_tile', (0.30, 0.31, 0.38))
ANT = T('antenna', (0.70, 0.70, 0.72), rim=(1.0, 0.85, 0.6), rf=0.5)
HEATER = T('heater_tank', (0.86, 0.86, 0.84))
WALLS = [T('wall_cream', (0.86, 0.80, 0.68)), T('wall_white', (0.90, 0.88, 0.84)),
         T('wall_wood', (0.42, 0.30, 0.24), tex=tex_rows(0.22, 0.75)), T('wall_grey', (0.66, 0.66, 0.66), tex=tex_rows(0.35, 0.85))]
GLASS = toon('glass', (0.10, 0.11, 0.17), (0.20, 0.22, 0.32), (1.0, 0.82, 0.55))
FRAME = T('frame', (0.62, 0.60, 0.58))
GROUND = T('ground', (0.48, 0.42, 0.36), rim=None)
ASPH = T('asphalt', (0.40, 0.38, 0.42), rim=None)
LINEW = T('roadpaint', (0.92, 0.90, 0.86), rim=None)
GRASS = T('grass', (0.52, 0.52, 0.28), tex=tex_patchy())
GRASS_D = T('grass_dry', (0.66, 0.60, 0.34), tex=tex_patchy(0.08, 1.4))
GRAVEL = T('gravel', (0.74, 0.66, 0.54), tex=tex_patchy(0.2, 3.0, 0.86, 1.08))
KERB = T('kerb', (0.74, 0.72, 0.70))
GUTTER = T('gutter', (0.56, 0.54, 0.54), tex=tex_rows(0.5, 0.45, 'Y'))
WOOD = T('rack_wood', (0.50, 0.38, 0.28))
BUNDLE = T('rice_bundles', (0.86, 0.66, 0.34), tex=tex_rows(0.22, 0.72, 'X'), rim=(1.0, 0.85, 0.55), rf=0.6)
FIELDS = [toon('paddy_gold', (0.42, 0.30, 0.36), (0.95, 0.70, 0.33), None, tex_rice()),
          toon('paddy_gold2', (0.42, 0.31, 0.34), (0.90, 0.64, 0.30), None, tex_rice()),
          toon('paddy_cut', (0.36, 0.27, 0.32), (0.74, 0.52, 0.32), None, tex_rice(0.5, True)),
          toon('paddy_late', (0.36, 0.32, 0.30), (0.80, 0.70, 0.36), None, tex_rice())]
FIELD = FIELDS[0]
LEVEE = T('levee', (0.66, 0.58, 0.34), tex=tex_patchy(0.08, 1.2), rim=(1.0, 0.86, 0.58), rf=0.55)
BALLAST = T('ballast', (0.50, 0.46, 0.46), rim=None)
RAIL = T('rail', (0.62, 0.60, 0.62))
SLEEPER = T('sleeper', (0.38, 0.32, 0.30), rim=None)
TREE = [T('tree', (0.30, 0.40, 0.22), rim=(0.95, 0.80, 0.45), rf=0.72), T('tree2', (0.24, 0.34, 0.24), rim=(0.95, 0.80, 0.45), rf=0.72),
        T('maple_tree', (0.80, 0.34, 0.14), rim=(1.0, 0.75, 0.45), rf=0.72)]
TOWER = toon('tower', shade((0.92, 0.90, 0.86)), (0.92, 0.90, 0.86), (1.0, 0.80, 0.55), tex_bands(7.0, lin((0.85, 0.22, 0.14))))
RED_ON = emis('tower_red_on', (1.0, 0.10, 0.06), 6.0); RED_OFF = emis('tower_red_off', (0.25, 0.04, 0.04))
TRAIN = T('train_cream', (0.93, 0.86, 0.70), rim=(1.0, 0.85, 0.6), rf=0.72)
TRAINR = T('train_red', (0.78, 0.17, 0.13))
DARK = T('underframe', (0.20, 0.18, 0.22), rim=(0.8, 0.6, 0.45))
YEL = T('yellow', (0.98, 0.80, 0.16)); BLK = T('black', (0.12, 0.11, 0.13))
LAMP_ON = emis('xlamp_on', (1.0, 0.12, 0.06), 5.0); LAMP_OFF = emis('xlamp_off', (0.22, 0.05, 0.05))
CLOTH = [toon('cloth_w', (0.80, 0.74, 0.70), (0.98, 0.96, 0.92), (1, 0.9, 0.7)), toon('cloth_b', (0.36, 0.46, 0.66), (0.55, 0.66, 0.86), (1, 0.85, 0.65)),
         toon('cloth_p', (0.80, 0.50, 0.55), (0.96, 0.70, 0.72), (1, 0.85, 0.65)), toon('cloth_y', (0.80, 0.66, 0.30), (0.98, 0.86, 0.46), (1, 0.9, 0.6))]
LEAF = toon('leaf', (0.74, 0.24, 0.07), (0.97, 0.52, 0.16), (1.0, 0.80, 0.45))
BARK = T('bark', (0.30, 0.22, 0.20))
VEND = emis('vending_face', (0.95, 0.96, 1.0), 1.6)


def obj(name, bm, mat, D, flat=True, extra=()):
    """mesh object in TOWN space; outline width scales with its distance D (about 1.5 px)"""
    ob = mesh_obj(name, bm, mat, TOWN, 0)
    for m in extra: ob.data.materials.append(m)
    if flat:
        for p in ob.data.polygons: p.use_smooth = False
    t = max(0.004, 0.00075 * D)
    nm = len(ob.data.materials)
    for _ in range(nm): ob.data.materials.append(ink)
    sm = ob.modifiers.new('ol', 'SOLIDIFY'); sm.thickness = t; sm.offset = 1; sm.use_flip_normals = True
    sm.material_offset = nm; sm.use_rim = False
    return ob


def box(bm, c, s, mi=0, rotz=0.0):
    r = bmesh.ops.create_cube(bm, size=1)
    vs = r['verts']
    bmesh.ops.scale(bm, vec=s, verts=vs)
    if rotz: bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(rotz, 3, 'Z'))
    bmesh.ops.translate(bm, vec=c, verts=vs)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs


def beam(bm, p, q, t, mi=0):
    p, q = Vector(p), Vector(q); d = q - p; L = d.length
    r = bmesh.ops.create_cube(bm, size=1); vs = r['verts']
    bmesh.ops.scale(bm, vec=(t, t, L), verts=vs)
    rot = d.normalized().to_track_quat('Z', 'Y').to_matrix()
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, vec=(p + q) / 2, verts=vs)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi


# ---------------- ground ----------------
def plane(name, x0, x1, y0, y1, z, mat, D):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs)
    ob = mesh_obj(name, bm, mat, TOWN, 0)
    return ob


plane('town_ground', -90, 90, 8, 66, 0, GROUND, 40)
plane('grass_strip', -200, 200, 66, 100, -0.02, GRASS, 80)
plane('road_side', -200, 200, 68, 74, 0.03, ASPH, 70)
plane('main_street', 5.5, 10.5, 8, 100, 0.04, ASPH, 40)
for k in range(30):                                              # centre dashes on the main street
    y = 10 + k * 3.0
    plane('dash%d' % k, 7.92, 8.08, y, y + 1.5, 0.06, LINEW, 40)
for i in range(6):                                               # zebra crossing by the station road
    plane('zebra%d' % i, 5.8 + i * 0.8, 6.2 + i * 0.8, 64.5, 67.0, 0.06, LINEW, 64)
plane('stopline', 5.6, 8.0, 79.0, 79.45, 0.06, LINEW, 80)

for _ in range(5): rnd.uniform(-8, 8)            # v1 drew 5 numbers here (old farm tracks): keeps the approved layout

# ---------------- houses ----------------
def house(cx, cy, w, d, h, roofmat, wallmat, kind, D, balcony=False, r=None):
    r = r or rnd
    bm = bmesh.new()
    box(bm, (0, 0, h / 2), (w, d, h), 0)
    # windows on all four sides: dark glass with a light frame, sliding-door style (two panes)
    floors = 2 if h > 4.5 else 1
    for fl_ in range(floors):
        z = 1.5 + fl_ * 2.8
        for side in (-1, 1):
            n = max(1, int(w / 3.2))
            for i in range(n):
                x = -w / 2 + (i + 0.5) * w / n + r.uniform(-0.3, 0.3)
                if r.random() < 0.25: continue
                ww = r.choice((1.2, 1.6, 0.8))
                box(bm, (x, side * (d / 2 + 0.03), z), (ww + 0.16, 0.05, 1.26), 3)
                box(bm, (x, side * (d / 2 + 0.06), z), (ww, 0.05, 1.1), 2)
                box(bm, (x, side * (d / 2 + 0.085), z), (0.06, 0.02, 1.1), 3)
                if r.random() < 0.5:                         # rain shutter box above some windows
                    box(bm, (x - ww / 2 - 0.25, side * (d / 2 + 0.08), z), (0.35, 0.15, 1.2), 0)
        for side in (-1, 1):
            if r.random() < 0.6:
                box(bm, (side * (w / 2 + 0.03), r.uniform(-d / 4, d / 4), z), (0.05, 1.0, 1.1), 2)
    if floors == 2:                                              # little eave between floors
        box(bm, (0, 0, 2.9), (w + 0.7, d + 0.7, 0.10), 1)
    if balcony:
        box(bm, (0, -d / 2 - 0.55, 2.95), (w * 0.6, 1.1, 0.12), 3)
        box(bm, (0, -d / 2 - 1.07, 3.45), (w * 0.6, 0.05, 0.9), 3)
    # roof
    o = 0.55; rh = 1.6 + 0.12 * w
    x0, x1, y0, y1 = -w / 2 - o, w / 2 + o, -d / 2 - o, d / 2 + o
    zt = h + 0.05
    if kind == 'hip':
        ins = min(w, d) / 2 + o
        a, b, c, e = (bm.verts.new((x0, y0, zt)), bm.verts.new((x1, y0, zt)), bm.verts.new((x1, y1, zt)), bm.verts.new((x0, y1, zt)))
        if w >= d:
            r0, r1 = bm.verts.new((x0 + ins, 0, zt + rh)), bm.verts.new((x1 - ins, 0, zt + rh))
            fs = [(a, b, r1, r0), (c, e, r0, r1), (b, c, r1), (e, a, r0)]
        else:
            r0, r1 = bm.verts.new((0, y0 + ins, zt + rh)), bm.verts.new((0, y1 - ins, zt + rh))
            fs = [(b, c, r1, r0), (e, a, r0, r1), (c, e, r1), (a, b, r0)]
        for fv in fs: bm.faces.new(fv).material_index = 1
        beam(bm, r0.co, r1.co, 0.28, 1)
        RA, RB = r0.co.copy(), r1.co.copy()
    else:   # gable: ridge along the long axis
        if w >= d:
            ra, rb = bm.verts.new((x0, 0, zt + rh)), bm.verts.new((x1, 0, zt + rh))
            q = [bm.verts.new(v) for v in ((x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt))]
            bm.faces.new((q[0], q[1], rb, ra)).material_index = 1; bm.faces.new((q[2], q[3], ra, rb)).material_index = 1
            for sx in (-1, 1):
                g = [bm.verts.new((sx * w / 2, -d / 2, h)), bm.verts.new((sx * w / 2, d / 2, h)), bm.verts.new((sx * w / 2, 0, zt + rh - 0.1))]
                bm.faces.new(g).material_index = 0
        else:
            ra, rb = bm.verts.new((0, y0, zt + rh)), bm.verts.new((0, y1, zt + rh))
            q = [bm.verts.new(v) for v in ((x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt))]
            bm.faces.new((q[1], q[2], rb, ra)).material_index = 1; bm.faces.new((q[3], q[0], ra, rb)).material_index = 1
            for sy in (-1, 1):
                g = [bm.verts.new((-w / 2, sy * d / 2, h)), bm.verts.new((w / 2, sy * d / 2, h)), bm.verts.new((0, sy * d / 2, zt + rh - 0.1))]
                bm.faces.new(g).material_index = 0
        beam(bm, ra.co, rb.co, 0.26, 1)
        RA, RB = ra.co.copy(), rb.co.copy()
    # eave tile edge (round tile ends) all round + ridge end tiles (onigawara) + ridge cap
    for (pa, pb) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        if kind != 'hip' and ((w >= d and pa[0] == pb[0]) or (w < d and pa[1] == pb[1])): continue
        beam(bm, (pa[0], pa[1], zt + 0.02), (pb[0], pb[1], zt + 0.02), 0.17, 4)
    for e_ in (RA, RB):
        box(bm, (e_.x, e_.y, e_.z + 0.22), (0.42, 0.42, 0.5), 4)
    beam(bm, RA + Vector((0, 0, 0.17)), RB + Vector((0, 0, 0.17)), 0.20, 4)
    if kind != 'hip':                                            # gable barge boards
        for e_, sgn in ((RA, -1), (RB, 1)):
            for side in (-1, 1):
                if w >= d: q0 = Vector((e_.x, side * (d / 2 + o), zt))
                else: q0 = Vector((side * (w / 2 + o), e_.y, zt))
                beam(bm, q0, e_, 0.12, 3)
    # TV antenna (Yagi) on about half the roofs, solar water heater on some
    if rnd2.random() < 0.55 and cy > 22:          # none on the front row: it would stand in front of the laundry
        mc = (RA + RB) / 2 + Vector((rnd2.uniform(-1, 1), 0, 0.2))
        top = mc + Vector((0, 0, rnd2.uniform(1.8, 2.8)))
        beam(bm, mc, top, 0.05, 5)
        yaw = rnd2.uniform(-0.4, 0.4); dvec = Vector((math.sin(yaw), math.cos(yaw), 0))
        beam(bm, top - dvec * 0.9, top + dvec * 0.9, 0.04, 5)
        for j in range(7):
            q = top - dvec * 0.85 + dvec * (j * 0.28); pv = Vector((dvec.y, -dvec.x, 0)) * (0.42 - j * 0.03)
            beam(bm, q - pv, q + pv, 0.022, 5)
        beam(bm, mc, mc + Vector((0.9, -0.6, -1.0)), 0.015, 5)   # guy wire
    if w >= d and rnd2.random() < 0.22:
        ang = math.atan2(rh, abs(y0))
        vs = box(bm, (0, 0, 0), (2.2, 1.3, 0.10), 2)
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(-ang, 3, 'X'))
        hx = rnd2.uniform(-w / 4, w / 4)
        bmesh.ops.translate(bm, vec=(hx, y0 * 0.45, zt + rh * 0.55 + 0.25), verts=vs)
        beam(bm, (hx - 1.1, y0 * 0.22, zt + rh * 0.78 + 0.35), (hx + 1.1, y0 * 0.22, zt + rh * 0.78 + 0.35), 0.38, 6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj('house', bm, wallmat, D, extra=(roofmat, GLASS, FRAME, EAVE, ANT, HEATER))
    ob.location = (cx, cy, 0)
    ob.rotation_euler = (0, 0, math.radians(r.uniform(-2, 2)))
    return ob


HOUSES = []
LAUNDRY_HOUSE = None
for row, y in enumerate((17, 26, 35.5, 45, 55)):
    x = -0.40 * y - 6 + rnd.uniform(-2, 2)
    while x < 0.40 * y + 6:
        w = rnd.uniform(6.5, 9.5); d = rnd.uniform(6.5, 8.5)
        if x + w / 2 > 4.5 and x - w / 2 < 11.5:             # keep the main street open
            x = 12.0 + w / 2; continue
        h = rnd.choice((5.6, 5.8, 6.0, 3.2)) if rnd.random() > 0.15 else 3.0
        bal = (row == 1 and LAUNDRY_HOUSE is None and -9 < x < -2)
        hz = house(x + w / 2, y + rnd.uniform(-0.8, 0.8), w, d, 5.8 if bal else h, rnd.choice(ROOF[:3] * 2 + ROOF[3:]),
                   rnd.choice(WALLS), rnd.choice(('hip', 'hip', 'gable')), y, balcony=bal)
        HOUSES.append(hz)
        if bal: LAUNDRY_HOUSE = (hz, w, d)
        x += w + rnd.uniform(1.6, 3.5)

# garden trees (clumped ellipsoids) between houses + a few red maples
for i in range(26):
    y = rnd.uniform(14, 62); x = rnd.uniform(-0.38 * y, 0.38 * y)
    if 4 < x < 12: continue
    bm = bmesh.new(); s = rnd.uniform(1.6, 2.8)
    for k in range(4):
        e = ellipsoid(s * rnd.uniform(.7, 1.0), s * rnd.uniform(.7, 1.0), s * rnd.uniform(.55, .8), 14, 8)
        bmesh.ops.translate(e, vec=(rnd.uniform(-s, s) * .6, rnd.uniform(-s, s) * .6, s * 1.4 + rnd.uniform(0, s * .8)), verts=e.verts)
        me = bpy.data.meshes.new('t'); e.to_mesh(me); e.free(); bm.from_mesh(me)
    beam(bm, (0, 0, 0), (0, 0, s * 1.3), 0.3)
    ob = obj('tree', bm, rnd.choice(TREE), y, flat=False)
    for p in ob.data.polygons: p.use_smooth = True
    ob.location = (x, y, 0)

# vending machine (glowing) on the main street
vm = bmesh.new(); box(vm, (0, 0, 0.92), (1.0, 0.75, 1.84), 0); box(vm, (0, -0.39, 1.05), (0.86, 0.04, 1.2), 1)
vo = obj('vending', vm, T('vend_body', (0.92, 0.92, 0.94)), 30, extra=(VEND,)); vo.location = (4.9, 31.0, 0)

# utility poles along the main street + wires, and the big near pole on the hill (foreground layer)
def upole(x, y, z0, hgt, D):
    bm = lathe([(0, 0.17), (hgt, 0.12), (hgt + 0.02, 0)], 16)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    for k, zz in enumerate((hgt - 0.5, hgt - 1.4)):
        box(bm, (0, 0, zz), (1.8, 0.12, 0.12), 0)
    box(bm, (0.32, 0, hgt - 2.6), (0.45, 0.45, 0.8), 0)        # transformer
    ob = obj('upole', bm, CONC, D, flat=False); ob.location = (x, y, z0)
    return ob


def wire(a, b, sag, thick):
    c = bpy.data.curves.new('wire', 'CURVE'); c.dimensions = '3D'; c.bevel_depth = thick
    sp = c.splines.new('POLY'); n = 40; sp.points.add(n - 1)
    a, b = Vector(a), Vector(b)
    for k in range(n):
        t = k / (n - 1); q = a.lerp(b, t); q.z -= sag * 4 * t * (1 - t)
        sp.points[k].co = (*q, 1)
    co = bpy.data.objects.new('wire', c); sc.collection.objects.link(co); c.materials.append(WIRE); co.parent = TOWN
    return co


PP = [(4.4, 12 + 28 * k) for k in range(4)]
for x, y in PP: upole(x, y, 0, 10.5, y)
for (xa, ya), (xb, yb) in zip(PP, PP[1:]):
    for dz, dx in ((10.0, -0.8), (10.0, 0.8), (9.1, -0.8), (9.1, 0.8)):
        wire((xa + dx, ya, dz), (xb + dx, yb, dz), 0.45, 0.025)
NEAR = (-3.0, 10.0, 9.6)                                         # near pole stands on the hill road beside the camera
upole(NEAR[0], NEAR[1], NEAR[2], 12.0, 10)
for i, (dz, dx) in enumerate(((11.5, -0.8), (11.5, 0.8), (10.6, 0.0))):
    wire((NEAR[0] + dx, NEAR[1], NEAR[2] + dz), (PP[1][0] + dx * .8, PP[1][1], dz - 0.9), 1.4 + 0.2 * i, 0.022)
    wire((NEAR[0] + dx, NEAR[1], NEAR[2] + dz), (-60 + dx, 70, 9.0 + dz * 0.1), 2.6 + 0.2 * i, 0.022)

# main street: kerbs, covered side drains (grated lids), white edge lines, two manholes
kb = bmesh.new(); gb = bmesh.new()
for xk in (5.35, 10.65):
    box(kb, (xk, 54, 0.09), (0.18, 92, 0.18))
    box(gb, (xk + (-0.45 if xk < 8 else 0.45), 54, 0.05), (0.6, 92, 0.06))
obj('kerbs', kb, KERB, 40); obj('drains', gb, GUTTER, 40)
for xl in (5.85, 10.15): plane('edgeline', xl - 0.07, xl + 0.07, 8, 86, 0.06, LINEW, 40)
for ym in (22.0, 47.0):
    mh = lathe([(0, 0.32), (0.02, 0.32), (0.025, 0)], 24)
    bmesh.ops.rotate(mh, verts=mh.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    obj('manhole', mh, T('manhole', (0.46, 0.44, 0.46), tex=tex_rows(0.06, 0.6, 'X')), ym).location = (7.0, ym, 0.05)
# hedge + grass tufts along the station road and the railway embankment
hb = bmesh.new()
for k in range(56):
    x = -70 + k * 2.5 + rnd2.uniform(-0.5, 0.5)
    if 4 < x < 12: continue
    e = ellipsoid(1.5, 0.8, 0.75, 12, 6); bmesh.ops.translate(e, vec=(x, 75.2, 0.7), verts=e.verts)
    me = bpy.data.meshes.new('h'); e.to_mesh(me); e.free(); hb.from_mesh(me)
ho = obj('hedge', hb, T('hedge', (0.34, 0.44, 0.24), tex=tex_patchy(0.5, 3), rim=(0.95, 0.82, 0.5), rf=0.72), 75, flat=False)
tb_ = bmesh.new()
for k in range(260):
    x = rnd2.uniform(-60, 60); y = rnd2.choice((rnd2.uniform(76, 85), rnd2.uniform(91, 99), rnd2.uniform(66.2, 67.8)))
    if 4.5 < x < 11.5: continue
    for b_ in range(5):
        a_ = rnd2.uniform(0, 6.3); hh_ = rnd2.uniform(0.35, 0.8)
        v0 = tb_.verts.new((x + 0.08 * math.cos(a_), y + 0.08 * math.sin(a_), 0)); v1 = tb_.verts.new((x - 0.08 * math.cos(a_), y - 0.08 * math.sin(a_), 0))
        v2 = tb_.verts.new((x + 0.25 * math.cos(a_ + 1.2), y + 0.25 * math.sin(a_ + 1.2), hh_)); tb_.faces.new((v0, v1, v2))
mesh_obj('tufts', tb_, T('tuft', (0.62, 0.62, 0.30), rim=(1.0, 0.86, 0.5), rf=0.5), TOWN, 0)
plane('embank_grass', -200, 200, 85.6, 86.0, 0.3, GRASS_D, 88)

# paddies: real fields (cells) with raised levees, four crop states, rows that converge into the distance
fb = bmesh.new(); lb = bmesh.new()
y = 101.0; rowi = 0
while y < 480:
    dy_ = rnd2.uniform(13, 19); x = -260 + rnd2.uniform(-10, 0)
    while x < 260:
        dx_ = rnd2.uniform(26, 40)
        vs = [fb.verts.new(v) for v in ((x, y, -0.1), (x + dx_, y, -0.1), (x + dx_, y + dy_, -0.1), (x, y + dy_, -0.1))]
        fc = fb.faces.new(vs); fc.material_index = rnd2.choice((0, 0, 1, 1, 2, 2, 3))
        box(lb, (x, y + dy_ / 2, 0.08), (0.55, dy_, 0.36))           # side levee
        x += dx_
    box(lb, (0, y, 0.08), (520, 0.7, 0.36))                          # long levee (farm walkway)
    y += dy_; rowi += 1
fo = mesh_obj('paddies', fb, FIELDS[0], TOWN, 0)
for m_ in FIELDS[1:]: fo.data.materials.append(m_)
for p_ in fo.data.polygons: p_.use_smooth = False
lo_ = obj('levees', lb, LEVEE, 220)
# farm tracks: gravel with two wheel ruts and grass verges, slightly raised so they catch the light
for k in range(4):
    x = -130 + k * 72 + rnd2.uniform(-8, 8)
    tr = bmesh.new(); box(tr, (x, 290, 0.10), (2.6, 380, 0.4), 0)
    for rx in (-0.55, 0.55): box(tr, (x + rx, 290, 0.31), (0.32, 380, 0.02), 1)
    for vx in (-1.6, 1.6): box(tr, (x + vx, 290, 0.06), (0.7, 380, 0.3), 2)
    obj('farmtrack', tr, GRAVEL, 250, extra=(T('rut', (0.56, 0.48, 0.40)), GRASS_D))
# a road with utility poles running straight away into the distance (strong depth cue)
FARX = -58.0
plane('farm_road', FARX - 2.5, FARX + 2.5, 100, 480, 0.02, ASPH, 250)
prev = None
for k in range(13):
    yk = 104 + k * 29.0
    pole_ = upole(FARX + 3.2, yk, 0, 9.0, yk)
    if prev:
        for dz, dx in ((8.6, -0.8), (8.6, 0.8), (7.7, 0.0)):
            wire((FARX + 3.2 + dx, prev, dz), (FARX + 3.2 + dx, yk, dz), 0.35, 0.03)
    prev = yk
# rice-drying racks (hasa-gake): poles + bars with golden bundles hanging, scattered over the cut fields
for k in range(18):
    yk = rnd2.uniform(108, 420); xk = rnd2.uniform(-200, 200)
    if abs(xk - 44) < 22 and abs(yk - 175) < 20: continue
    if abs(xk - FARX) < 8: continue
    Lr = rnd2.uniform(9, 18); rk = bmesh.new()
    for j in range(int(Lr / 2) + 1):
        px = -Lr / 2 + j * 2.0
        beam(rk, (px, 0, 0), (px, 0, 2.4), 0.12, 0)
        beam(rk, (px, 0, 2.2), (px - 0.6, -0.5, 0), 0.07, 0)
    for zb in (1.25, 2.05):
        beam(rk, (-Lr / 2, 0, zb), (Lr / 2, 0, zb), 0.08, 0)
        box(rk, (0, 0, zb - 0.33), (Lr - 0.2, 0.45, 0.62), 1)
    ro = obj('hasa', rk, WOOD, yk, extra=(BUNDLE,)); ro.location = (xk, yk, 0); ro.rotation_euler = (0, 0, rnd2.uniform(-0.25, 0.25))
# small farm sheds with tin roofs + a few field trees
for k in range(7):
    yk = rnd2.uniform(115, 380); xk = rnd2.uniform(-180, 180)
    if abs(xk - 44) < 20 and abs(yk - 175) < 20: continue
    house(xk, yk, rnd2.uniform(3, 5), rnd2.uniform(3, 4), 2.4, ROOF[3], WALLS[2], 'gable', yk, r=rnd2)
FIELD_TREES = [(rnd2.uniform(-170, 170), rnd2.uniform(130, 420)) for _ in range(9)]
for (xt, yt) in FIELD_TREES:
    bm = bmesh.new(); sz = rnd2.uniform(2.5, 4.0)
    for k in range(5):
        e = ellipsoid(sz * rnd2.uniform(.7, 1.0), sz * rnd2.uniform(.7, 1.0), sz * rnd2.uniform(.6, .85), 14, 8)
        bmesh.ops.translate(e, vec=(rnd2.uniform(-sz, sz) * .6, rnd2.uniform(-sz, sz) * .6, sz * 1.6 + rnd2.uniform(0, sz * .9)), verts=e.verts)
        me = bpy.data.meshes.new('t'); e.to_mesh(me); e.free(); bm.from_mesh(me)
    beam(bm, (0, 0, 0), (0, 0, sz * 1.5), 0.4)
    ob = obj('fieldtree', bm, rnd2.choice(TREE[:2]), yt, flat=False); ob.location = (xt, yt, 0)

# ---------------- railway + crossing ----------------
RY = 88.0
bl = bmesh.new(); box(bl, (0, RY, 0.25), (420, 4.2, 0.5), 0)
obj('ballast', bl, BALLAST, RY)
rl = bmesh.new()
for sx in (-0.53, 0.53): box(rl, (0, RY + sx, 0.62), (420, 0.08, 0.16), 0)
obj('rails', rl, RAIL, RY)
sl = bmesh.new()
for k in range(-330, 330):
    box(sl, (k * 0.62, RY, 0.53), (0.22, 2.1, 0.08), 0)
mesh_obj('sleepers', sl, SLEEPER, TOWN, 0)
plane('crossing_deck', 5.5, 10.5, RY - 2.2, RY + 2.2, 0.56, ASPH, RY)


def crossing_post(x, y, facing):
    bm = bmesh.new()
    box(bm, (0, 0, 2.0), (0.14, 0.14, 4.0), 1)                  # post (black/yellow bands added below)
    for k in range(8):
        box(bm, (0, 0, 0.25 + k * 0.5), (0.16, 0.16, 0.25), 2)
    for a in (0.6, -0.6):                                        # crossbuck X
        vs = box(bm, (0, -0.1, 3.6), (1.5, 0.04, 0.22), 2)
        bmesh.ops.rotate(bm, verts=vs, cent=(0, -0.1, 3.6), matrix=Matrix.Rotation(a, 3, 'Y'))
    box(bm, (0, -0.05, 2.9), (1.0, 0.1, 0.12), 1)
    box(bm, (0.42, 0.04, 1.2), (0.38, 0.3, 0.38), 1)             # bar motor box
    ob = obj('xpost', bm, YEL, RY, extra=(BLK, YEL)); ob.location = (x, y, 0.5); ob.rotation_euler = (0, 0, facing)
    lamps = []
    for sx in (-0.45, 0.45):
        lb = ellipsoid(0.15, 0.06, 0.15, 12, 8)
        lo = obj('xlamp', lb, LAMP_OFF, RY, flat=False); lo.parent = ob; lo.location = (sx, -0.14, 2.9)
        lamps.append(lo)
    bar = bmesh.new()
    for k in range(10):
        box(bar, (0.3 + k * 0.38 + 0.19, 0, 0), (0.38, 0.07, 0.07), k % 2)
    piv = empty('barpivot', ob, (0.42, -0.2, 1.2))
    bo = obj('xbar', bar, YEL, RY, extra=(BLK,)); bo.parent = piv
    return ob, lamps, piv


X1 = crossing_post(5.0, RY - 2.8, 0.0)
X2 = crossing_post(11.0, RY + 2.8, math.pi)


# ---------------- the two-car diesel train ----------------
def railcar(L, front):
    bm = bmesh.new()
    vs = box(bm, (0, 0, 2.55), (L, 2.9, 2.7), 0)
    edges = [e for e in bm.edges if all(v in vs for v in e.verts) and all(v.co.z > 3.8 for v in e.verts) and abs(e.verts[0].co.x - e.verts[1].co.x) > 1]
    bmesh.ops.bevel(bm, geom=edges, offset=0.45, segments=3, affect='EDGES', profile=0.5)
    for f in bm.faces: f.material_index = 0
    for sy in (-1, 1):
        box(bm, (0, sy * 1.465, 1.72), (L - 0.4, 0.04, 0.22), 1)           # red band
        box(bm, (0, sy * 1.465, 3.42), (L - 0.4, 0.04, 0.08), 1)           # thin roof-line band
        n = int(L / 1.45)
        for i in range(n):
            x = -L / 2 + 1.3 + i * (L - 2.6) / (n - 1)
            if i in (2, n - 3): continue
            box(bm, (x, sy * 1.47, 2.7), (1.05, 0.04, 0.95), 2)             # window
        for x in (-L / 2 + 3.2, L / 2 - 3.2):
            box(bm, (x, sy * 1.47, 2.2), (1.15, 0.05, 2.0), 3)              # doors (grey)
            box(bm, (x - 0.28, sy * 1.49, 2.7), (0.4, 0.04, 0.8), 2); box(bm, (x + 0.28, sy * 1.49, 2.7), (0.4, 0.04, 0.8), 2)
    for sx in (-1, 1):
        ex = sx * (L / 2 + 0.02)
        if (sx == 1) == front:
            box(bm, (ex, -0.65, 2.75), (0.04, 1.0, 0.9), 2); box(bm, (ex, 0.65, 2.75), (0.04, 1.0, 0.9), 2)
            box(bm, (ex, 0, 3.75), (0.05, 0.9, 0.25), 2)                    # destination board
            for yy in (-1.0, 1.0): box(bm, (ex + sx * 0.02, yy, 1.75), (0.05, 0.28, 0.2), 4)
        box(bm, (ex, 0, 1.72), (0.05, 2.9, 0.22), 1)
    box(bm, (0, 0, 0.95), (L - 4.0, 2.4, 0.55), 3)                         # underfloor equipment
    for x in (-L / 2 + 3.0, L / 2 - 3.0):
        box(bm, (x, 0, 0.75), (2.4, 2.5, 0.55), 3)                         # bogies
        for wx in (-0.85, 0.85):
            for sy in (-1, 1):
                wb = lathe([(-0.05, 0.43), (0.05, 0.43)], 14); bmesh.ops.translate(wb, vec=(x + wx, sy * 0.53 / 1.0, 0.68), verts=wb.verts)
                me = bpy.data.meshes.new('w'); wb.to_mesh(me); wb.free(); bm.from_mesh(me)
    for x in (-L / 4, L / 4):
        box(bm, (x, 0, 4.0), (2.2, 1.6, 0.35), 3)                          # roof units
    box(bm, (L / 2 - 4.5, 0.6, 4.2), (0.25, 0.25, 0.6), 3)                 # exhaust
    for f in bm.faces:
        if f.material_index > 4: f.material_index = 3
    ob = obj('railcar', bm, TRAIN, RY, extra=(TRAINR, GLASS, DARK, emis('headlight', (1.0, 0.95, 0.8), 3.0)))
    return ob


TR = empty('train', TOWN)
c1 = railcar(20.0, True); c1.parent = TR; c1.location = (0, 0, 0)
c2 = railcar(20.0, False); c2.parent = TR; c2.location = (-20.8, 0, 0)

# ---------------- the 1964 radio tower ----------------
TX, TYT = 44.0, 175.0
tb = bmesh.new()
lv = [(0, 7.0), (8, 5.6), (16, 4.4), (24, 3.4), (32, 2.6), (40, 1.9), (48, 1.4), (54, 1.1)]
corn = lambda z, r: [(r, r, z), (-r, r, z), (-r, -r, z), (r, -r, z)]
for (za, ra), (zb, rb) in zip(lv, lv[1:]):
    A, B = corn(za, ra), corn(zb, rb)
    for i in range(4):
        j = (i + 1) % 4
        beam(tb, A[i], B[i], 0.45)
        beam(tb, A[i], B[j], 0.18); beam(tb, A[j], B[i], 0.18)
        beam(tb, B[i], B[j], 0.22)
for zp, rp in ((24, 4.2), (48, 2.2)):
    box(tb, (0, 0, zp + 0.1), (rp * 2.0, rp * 2.0, 0.35))
beam(tb, (0, 0, 54), (0, 0, 66), 0.35)
for zz in (57, 61):
    box(tb, (0.6, 0, zz), (0.9, 0.5, 1.4))
tob = obj('radio_tower', tb, TOWER, TYT); tob.location = (TX, TYT, 0)
mound = ellipsoid(16, 14, 2.6, 24, 10); mo = obj('tower_hill', mound, T('tower_hill', (0.62, 0.50, 0.30)), TYT, flat=False); mo.location = (TX, TYT, -1.6)
tl = ellipsoid(0.55, 0.55, 0.55, 12, 8)
TL = obj('tower_light', tl, RED_ON, TYT, flat=False); TL.parent = tob; TL.location = (0, 0, 66.5)

# ---------------- laundry on the balcony ----------------
LAUNDRY = []
CLOTH += [toon('jeans', (0.22, 0.28, 0.46), (0.36, 0.46, 0.70), (1, 0.85, 0.65)),
          toon('print_red', (0.62, 0.16, 0.14), (0.88, 0.28, 0.22), (1, 0.8, 0.6)),
          toon('stripe_navy', (0.18, 0.20, 0.34), (0.26, 0.30, 0.52), (1, 0.85, 0.65))]
PEGM = [T('peg_pink', (0.98, 0.56, 0.66)), T('peg_green', (0.50, 0.86, 0.60)), T('peg_blue', (0.50, 0.70, 0.98))]
GARMENT = {   # outlines in (x across, v down) units of (W, H); hung from v = 0
    'tshirt': ([(-0.13, 0.0), (0.0, 0.07), (0.13, 0.0), (0.30, 0.03), (0.50, 0.19), (0.42, 0.33), (0.30, 0.27), (0.31, 0.62),
                (0.30, 1.0), (-0.30, 1.0), (-0.31, 0.62), (-0.30, 0.27), (-0.42, 0.33), (-0.50, 0.19), (-0.30, 0.03)], 0.78, 0.74),
    'towel': ([(-0.5, 0.0), (0.5, 0.0), (0.5, 1.0), (-0.5, 1.0)], 0.40, 0.86),
    'jeans': ([(-0.5, 0.0), (0.5, 0.0), (0.53, 0.35), (0.47, 1.0), (0.07, 1.0), (0.0, 0.31), (-0.07, 1.0), (-0.47, 1.0), (-0.53, 0.35)], 0.40, 0.98),
    'sock': ([(-0.5, 0.0), (0.5, 0.0), (0.5, 0.64), (1.25, 0.80), (1.32, 0.93), (1.2, 1.0), (0.25, 1.0), (-0.45, 0.88)], 0.085, 0.27),
    'cloth': ([(-0.5, 0.0), (0.5, 0.0), (0.5, 1.0), (-0.5, 1.0)], 0.22, 0.20),
}


def garment(kind, seed, mat, mat2=None):
    """real garment cut: resampled outline -> scanfill -> subdivided, static vertical folds; mat2 = print / hem bands"""
    pts, Wd, Hd = GARMENT[kind]; r = random.Random(seed)
    bm = bmesh.new(); ring = []
    P = [Vector((x * Wd, 0, -v * Hd)) for x, v in pts]
    for a, b in zip(P, P[1:] + P[:1]):
        n = max(1, int((b - a).length / 0.02))
        for j in range(n): ring.append(bm.verts.new(a.lerp(b, j / n)))
    es = [bm.edges.new((ring[i], ring[(i + 1) % len(ring)])) for i in range(len(ring))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    ph = r.uniform(0, 6)
    for v in bm.verts:
        dn = -v.co.z / Hd
        v.co.y += 0.016 * math.sin(v.co.x * 38 + ph) * min(1, dn * 2.5) + 0.010 * math.sin(v.co.x * 71 + ph * 2) * dn
        if kind == 'tshirt' and dn < 0.08: v.co.y -= 0.02 * (0.08 - dn) / 0.08     # collar curls toward us
    if mat2 is not None:
        for f in bm.faces:
            c = f.calc_center_median(); u, dn = c.x / Wd, -c.z / Hd
            if kind == 'tshirt' and (u * u + ((dn - 0.40) * 0.9) ** 2) < 0.012: f.material_index = 1      # chest print
            if kind == 'towel' and (dn < 0.06 or dn > 0.94 or 0.70 < dn < 0.76): f.material_index = 1     # hem bands + woven stripe
    ob = obj('cloth_' + kind, bm, mat, 26, flat=False, extra=((mat2,) if mat2 else ()))
    for p_ in ob.data.polygons: p_.use_smooth = True
    sm = ob.modifiers.new('th', 'SOLIDIFY'); sm.thickness = 0.008; ob.modifiers.move(1, 0)
    return ob


def peg(bmp, x, z, mi, y=-0.015):
    box(bmp, (x, y, z - 0.025), (0.018, 0.022, 0.07), mi)


if LAUNDRY_HOUSE:
    hz, w, d = LAUNDRY_HOUSE
    PY = -d / 2 - 0.8; PZ = 4.6
    pole = bmesh.new(); beam(pole, (-w * 0.30, PY, PZ), (w * 0.30, PY, PZ), 0.05)
    for sx in (-1, 1): beam(pole, (sx * w * 0.30, PY, PZ), (sx * w * 0.30, -d / 2 - 0.02, PZ + 0.1), 0.04)   # pole brackets
    obj('laundry_pole', pole, STEEL, 26).parent = hz
    pegs = bmesh.new()
    line = [('tshirt', 0, 5), ('towel', 0, 6), ('jeans', 4, None), ('towel', 1, 0), ('tshirt', 2, 6), ('hanger', None, None)]
    span = w * 0.54; x = -span / 2
    for i, (kind, mi, m2) in enumerate(line):
        if kind == 'hanger':                                     # pinch hanger (角ハンガー) with socks and small cloths
            hx = x + 0.30; hb_ = bmesh.new()
            beam(hb_, (hx, PY, PZ + 0.03), (hx, PY, PZ - 0.10), 0.012)
            for a_, b_ in (((-0.25, -0.16), (0.25, -0.16)), ((0.25, -0.16), (0.25, 0.16)), ((0.25, 0.16), (-0.25, 0.16)), ((-0.25, 0.16), (-0.25, -0.16))):
                beam(hb_, (hx + a_[0], PY + a_[1], PZ - 0.22), (hx + b_[0], PY + b_[1], PZ - 0.22), 0.02)
            for a_ in (-0.25, 0.25):
                beam(hb_, (hx, PY, PZ - 0.10), (hx + a_, PY - 0.16, PZ - 0.22), 0.01); beam(hb_, (hx, PY, PZ - 0.10), (hx + a_, PY + 0.16, PZ - 0.22), 0.01)
            obj('pinch_hanger', hb_, PEGM[2], 26).parent = hz
            for j in range(6):
                k_ = 'sock' if j % 3 != 2 else 'cloth'
                ob = garment(k_, 50 + j, CLOTH[(j + 1) % 4]); ob.parent = hz
                ob.location = (hx - 0.22 + j * 0.088, PY - 0.16, PZ - 0.22)
                peg(pegs, hx - 0.22 + j * 0.088, PZ - 0.22, j % 3, -0.175)
                LAUNDRY.append((ob, [v.co.copy() for v in ob.data.vertices], 10 + j))
            continue
        Wd = GARMENT[kind][1]
        if kind == 'tshirt':                                     # on a plastic hanger
            hb_ = bmesh.new(); cx_ = x + Wd / 2
            beam(hb_, (cx_, PY, PZ + 0.03), (cx_, PY, PZ - 0.06), 0.012)
            beam(hb_, (cx_, PY, PZ - 0.06), (cx_ - 0.24, PY, PZ - 0.14), 0.02); beam(hb_, (cx_, PY, PZ - 0.06), (cx_ + 0.24, PY, PZ - 0.14), 0.02)
            obj('hanger', hb_, PEGM[i % 3], 26).parent = hz
            z0 = PZ - 0.10
        else:
            z0 = PZ - 0.03
            for px in (x + 0.04, x + Wd - 0.04): peg(pegs, px, PZ + 0.02, i % 3)
        ob = garment(kind, i, CLOTH[mi], CLOTH[m2] if m2 is not None else None); ob.parent = hz
        ob.location = (x + Wd / 2, PY, z0)
        LAUNDRY.append((ob, [v.co.copy() for v in ob.data.vertices], i))
        x += Wd + 0.07
    po_ = obj('pegs', pegs, PEGM[0], 26, extra=(PEGM[1], PEGM[2])); po_.parent = hz; po_.location = (0, PY, 0)

# ---------------- foreground maple branch (top-left, out of focus) ----------------
BR = empty('branch', TOWN, (-3.9, 6.0, 21.0)); BR.scale = (1.8, 1.8, 1.8)
TWIGS = [[(0, 0, 0), (0.45, -0.05, -0.20), (0.92, 0.04, -0.44), (1.35, 0.0, -0.58), (1.75, 0.05, -0.66)],
         [(0.45, -0.05, -0.20), (0.62, -0.10, -0.02), (0.80, -0.08, 0.10)],
         [(0.92, 0.04, -0.44), (1.02, 0.02, -0.66), (1.08, 0.0, -0.86)],
         [(1.35, 0.0, -0.58), (1.52, -0.05, -0.45), (1.68, -0.06, -0.38)]]
TIPS = []
for i, tw in enumerate(TWIGS):
    cu = bpy.data.curves.new('twig', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.032 if i == 0 else 0.016
    cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(tw) - 1)
    for j, (bp, p_) in enumerate(zip(sp.bezier_points, tw)):
        bp.co = p_; bp.handle_left_type = bp.handle_right_type = 'AUTO'; bp.radius = 1.0 - 0.75 * j / (len(tw) - 1)
    co = bpy.data.objects.new('twig', cu); sc.collection.objects.link(co); cu.materials.append(BARK); co.parent = BR
    cu.materials.append(ink)
    TIPS += [Vector(tw[-1]), Vector(tw[-2]).lerp(Vector(tw[-1]), 0.5)]


def maple(bm, R):
    NV = 140; ring = []
    for k in range(NV):
        th = 2 * math.pi * k / NV; ph = (th - math.pi) / math.pi
        tri = ((ph + 1) * 3.5) % 1.0; lobe = (1 - abs(tri * 2 - 1)) ** 0.75
        env = 0.35 + 0.65 * abs(math.cos(ph * math.pi / 2.25)) ** 0.7
        rr = R * env * (0.58 + 0.42 * lobe) * (1 - 0.04 * abs(math.sin(th * 44)))
        if abs(ph) > 0.93: rr *= 0.35
        x, y = rr * math.sin(th), -rr * math.cos(th)
        ring.append(bm.verts.new((x, y, 3.0 * (x * x + y * y) / R * 0.06)))
    c = bm.verts.new((0, 0.004, 0))
    for i in range(NV): bm.faces.new((c, ring[i], ring[(i + 1) % NV]))


LEAVES = []
for i in range(34):
    base = rnd.choice(TIPS)
    bm = bmesh.new(); maple(bm, rnd.uniform(0.085, 0.12))
    lo = obj('fgleaf', bm, LEAF, 6, flat=False)
    lo.parent = BR; lo.location = base + Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.15, 0.1), rnd.uniform(-0.25, 0.08)))
    lo.rotation_euler = (math.radians(rnd.uniform(55, 115)), rnd.uniform(-0.7, 0.7), rnd.uniform(0, 6.3))
    LEAVES.append((lo, lo.rotation_euler.copy(), rnd.uniform(0, 6.3)))

# ---------------- the mountain's shadow: invisible occluder far beyond the fields ----------------
oc = bmesh.new(); box(oc, (0, 0, 0), (900, 2, 1))
OCC = mesh_obj('occluder', oc, GROUND, TOWN, 0)
OCC.visible_camera = False
try:
    OCC.visible_diffuse = False; OCC.visible_glossy = False
except Exception:
    pass

# ---------------- aerial perspective: every material fades toward the warm horizon colour with camera depth ----------------
HAZE = lin((0.98, 0.68, 0.50))
for mat in list(bpy.data.materials):
    if not mat.use_nodes: continue
    nt = mat.node_tree
    em = next((n for n in nt.nodes if n.type == 'EMISSION'), None)
    if em is None or em.inputs[1].default_value > 2.0 or mat.name.startswith('cloth'): continue
    src = em.inputs[0].links[0].from_socket if em.inputs[0].links else None
    cd = nt.nodes.new('ShaderNodeCameraData')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 85; mr.inputs['From Max'].default_value = 430
    mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = 0.48; mr.interpolation_type = 'SMOOTHSTEP'
    nt.links.new(cd.outputs['View Z Depth'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    nt.links.new(mr.outputs[0], mx.inputs[0])
    if src: nt.links.new(src, mx.inputs[6])
    else: mx.inputs[6].default_value = tuple(em.inputs[0].default_value)
    mx.inputs[7].default_value = (*HAZE, 1)
    nt.links.new(mx.outputs[2], em.inputs[0])

# ---------------- lights + camera ----------------
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 5.0; sun.data.color = (1.0, 0.78, 0.55); sun.data.angle = math.radians(0.6)
sun.rotation_euler = (-SUN).to_track_quat('-Z', 'Y').to_euler()
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); sc.collection.objects.link(fill)
fill.data.energy = 0.35; fill.data.color = (0.55, 0.55, 0.85); fill.data.use_shadow = False
fill.rotation_euler = (Vector((0.4, -1.0, 0.35))).to_track_quat('-Z', 'Y').to_euler()

camd = bpy.data.cameras.new('cam'); camd.lens = 30; camd.sensor_fit = 'VERTICAL'; camd.sensor_height = 36
camd.clip_start = 0.1; camd.clip_end = 3000
camd.dof.use_dof = True; camd.dof.focus_distance = 45.0; camd.dof.aperture_fstop = 0.7
cam = bpy.data.objects.new('cam', camd); sc.collection.objects.link(cam); sc.camera = cam


def ease(t):
    t = max(0, min(1, t)); return t * t * (3 - 2 * t)


def cam_at(f):
    k = ease((f - 1) / (NF - 1))
    pos = Vector((0.0, 0.0 + 1.5 * k, 19.5 - 2.0 * k)) + Vector((0.03 * math.sin(f * 0.06), 0, 0.02 * math.sin(f * 0.045)))
    pitch = math.radians(-7.0 + 1.8 * k)
    d = Vector((0, math.cos(pitch), math.sin(pitch)))
    return W(pos), (TM.to_3x3() @ d)


META = {}


def pose(f):
    fs = f - ((f - 1) % 2)                                        # props on twos, camera + train on ones
    p, d = cam_at(f)
    cam.location = p; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    k = (f - 1) / (NF - 1)
    # shadow edge creeps from y~360 to y~170 across the paddies: occluder at y=520 rising (sun sinking)
    tan_e = SUN.z / Vector((SUN.x, SUN.y)).length
    edge = 360 - 190 * ease(k * 1.05)
    hgt = (520 - edge) * tan_e
    OCC.location = (0, 520, hgt / 2 - 20); OCC.scale = (1, 1, hgt + 40)
    # train: front from x=-42 to x=+18 (about 60 km/h), on ones
    TR.location = (-42 + 62 * k, RY, 0.45)          # lowest wheel rim sits on the rail top (z 0.70)
    # crossing: lamps alternate at ~1.7 Hz from the first frame; bars lower over f1-f30
    on = (f // 7) % 2
    for (post, lamps, piv) in (X1, X2):
        lamps[0].material_slots[0].material = LAMP_ON if on else LAMP_OFF
        lamps[1].material_slots[0].material = LAMP_OFF if on else LAMP_ON
        b = ease((fs - 1) / 30); ang = math.radians(82 * (1 - b))
        bounce = math.radians(2.5) * math.sin(max(0, fs - 31) * 0.9) * math.exp(-max(0, fs - 31) * 0.25) if fs > 31 else 0
        piv.rotation_euler = (0, -(ang + bounce), 0)
    TL.material_slots[0].material = RED_ON if (f // 12) % 2 == 0 else RED_OFF
    # laundry sways (on twos): wind from the right, lag down the cloth
    for ob, base, i in LAUNDRY:
        for v, b0 in zip(ob.data.vertices, base):
            dn = -b0.z
            sw = (0.10 + 0.05 * math.sin(fs * 0.31 + i * 1.7 - dn * 2.0)) * dn
            fl = 0.035 * math.sin(fs * 0.55 + i + b0.x * 6 - dn * 4) * dn
            v.co = (b0.x + sw * 0.35, b0.y - sw + fl, b0.z + abs(sw) * 0.15)
        ob.data.update()
    # branch + leaves: slow sway, leaves flutter with lag
    BR.rotation_euler = (0.035 * math.sin(fs * 0.13), 0.02 * math.sin(fs * 0.09 + 1), 0.03 * math.sin(fs * 0.11))
    for lo, r0, ph in LEAVES:
        lo.rotation_euler = (r0.x + 0.18 * math.sin(fs * 0.35 + ph), r0.y + 0.10 * math.sin(fs * 0.27 + ph * 2), r0.z)


frames = range(1, NF + 1) if FR == 'all' else [int(x) for x in FR.split(',')]
for f in frames:
    sc.frame_set(f); pose(f)
    bpy.context.view_layer.update()
    s_ = world_to_camera_view(sc, cam, cam.location + SUN * 1000)
    h_ = world_to_camera_view(sc, cam, cam.location + FWD * 5000)
    t_ = world_to_camera_view(sc, cam, TL.matrix_world.translation)
    fe = world_to_camera_view(sc, cam, W((0, 480, 0)))
    META[f] = dict(sx=s_.x, sy=1 - s_.y, hy=1 - h_.y, tx=t_.x, ty=1 - t_.y, fy=1 - fe.y, tower_on=(f // 12) % 2 == 0)
    sc.render.filepath = os.path.join(OUT, 'cel_%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)
json.dump(META, open(os.path.join(OUT, 'meta.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 's03.blend'))
print('META', META[frames[0]])
