"""5 O'CLOCK Ep1 v3 - shot 04 "Sam rides home" (4 s, 96 f @24). Built to SHOT_RULES (01 v4 + 02/03 log).
Low side-on tracking shot: Sam coasts downhill on his mamachari along the hill road above the bay, headphones on,
mouthing the lyrics, konbini bag swinging off the bar, hair and hoodie strings in the wind, pole shadows flicking
over him. He passes the Yamada shop: its window reflection runs half a second late (a mirrored camera rendered
12 frames behind, joined in comp_s04.py). At the end the camera eases off and he overtakes it.
Road frame ROAD: x = downhill along the road, y = away from camera (toward the sun / bay), z = up from the road.
usage: python3 build_s04.py <outdir> <scale> [frames|all]      (or blender -b --python build_s04.py -- <args>)"""
import os, sys, json, random
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
OUT = ARGV[0]; SCALE = float(ARGV[1]); FR = ARGV[2] if len(ARGV) > 2 else 'all'
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__)); D = HERE
S03 = os.path.join(HERE, '..', '..', '03_kiriyama', 'src_v2')
_tl = os.path.join(HERE, 'toonlib_v4.py'); _tl = _tl if os.path.exists(_tl) else os.path.join(S03, 'toonlib_v4.py')
if not os.path.exists(os.path.join(HERE, 'lib04.py')):           # shared materials/helpers: extracted from the shot 03 build
    import ast
    _s = open(os.path.join(S03, 'build_s03.py'), encoding='utf-8').read(); _keep = []
    for n in ast.parse(_s).body:
        if n.lineno > 760: break
        seg = ast.get_source_segment(_s, n)
        if isinstance(n, ast.FunctionDef) and n.name not in ('W', 'plane'): _keep.append(seg)
        elif isinstance(n, ast.Assign) and n.lineno > 150:
            nm = [x.id for x in n.targets if isinstance(x, ast.Name)]
            if nm and nm[0].isupper() and nm[0] not in ('HOUSES', 'LAUNDRY_HOUSE', 'PP', 'META', 'LAUNDRY', 'LEAVES', 'X1', 'X2', 'TR', 'TL', 'BR', 'OCC', 'HAZE', 'SUN', 'FWD', 'YAW', 'TM', 'NF'): _keep.append(seg)
    _t = '\n\n\n'.join(_keep); _t = _t[:_t.index('NEAR = ')]
    open(os.path.join(HERE, 'lib04.py'), 'w', encoding='utf-8').write(_t)
src = open(_tl).read()
src = src.replace("SUNV = tuple(Vector((-0.62, 1.0, 0.24)).normalized())", "SUNV = tuple(Vector((0.20, 1.0, 0.21)).normalized())")
exec(src)
from bpy_extras.object_utils import world_to_camera_view
NF = 96; DELAY = 12
SUN = Vector(SUNV)
SLOPE = math.radians(3.5)
ROAD = empty('ROAD'); ROAD.rotation_euler = (0, SLOPE, 0)       # +x runs downhill
TOWN = ROAD
rnd = random.Random(404); rnd2 = random.Random(405)
lin = lambda c: tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
exec(open(os.path.join(HERE, 'lib04.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE, 'bike.py')).read())
exec(open(os.path.join(HERE, 'rider.py')).read())
FONT = bpy.data.fonts.load(next(p for p in (os.path.join(HERE, 'ipag.ttf'), 'C:/Windows/Fonts/YuGothM.ttc', 'C:/Windows/Fonts/msgothic.ttc', '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf') if os.path.exists(p)))

SHOP0, SHOP1 = 4.0, 12.6
WY = 5.0                       # shop window plane (road-local y); the mirror camera reflects across it
FAR = []                       # objects behind the window plane: hidden from the mirror camera (they still cast shadows)


def plane(name, x0, x1, y0, y1, z, mat, D=10, far=False):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs)
    ob = mesh_obj(name, bm, mat, ROAD, 0)
    if far: FAR.append(ob)
    return ob


def text(s, size, mat, loc, rot=(math.radians(90), 0, 0), align='CENTER', far=True):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = s; cu.font = FONT; cu.size = size
    cu.align_x = align; cu.align_y = 'CENTER'; cu.extrude = 0.004
    ob = bpy.data.objects.new('txt', cu); sc.collection.objects.link(ob); cu.materials.append(mat)
    ob.parent = ROAD; ob.location = loc; ob.rotation_euler = rot
    if far: FAR.append(ob)
    return ob


# ---------------- materials (new for this shot) ----------------
def tex_asphalt(nt, ramp):
    """old hill-road asphalt: soft tonal patches, fine aggregate speckle, darker tar-sealed crack lines"""
    N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord')
    n1 = N.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 0.18; n1.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    big = _m(N, L, 'MULTIPLY_ADD', n1.outputs['Fac'], 0.30, 0.85)
    n2 = N.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 38.0; L.new(tc.outputs['Object'], n2.inputs['Vector'])
    sp = _m(N, L, 'MULTIPLY_ADD', _m(N, L, 'GREATER_THAN', n2.outputs['Fac'], 0.62), 0.10, 0.95)
    vo = N.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 0.30
    L.new(tc.outputs['Object'], vo.inputs['Vector'])
    n3 = N.new('ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = 0.4; L.new(tc.outputs['Object'], n3.inputs['Vector'])
    cr = _m(N, L, 'MULTIPLY_ADD', _m(N, L, 'MULTIPLY', _m(N, L, 'LESS_THAN', vo.outputs['Distance'], 0.006), _m(N, L, 'GREATER_THAN', n3.outputs['Fac'], 0.56)), -0.30, 1.0)
    return _mul_ramp(N, L, ramp.outputs[0], _m(N, L, 'MULTIPLY', _m(N, L, 'MULTIPLY', big, sp), cr))


def tex_plaster(nt, ramp):
    """aged shop plaster: rain streaks running down from the eave + soft grime toward the base"""
    N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sp.inputs[0])
    st = N.new('ShaderNodeCombineXYZ'); L.new(_m(N, L, 'MULTIPLY', sp.outputs['X'], 7.0), st.inputs[0]); L.new(_m(N, L, 'MULTIPLY', sp.outputs['Z'], 0.35), st.inputs[1])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 2
    L.new(st.outputs[0], nz.inputs['Vector'])
    streak = _m(N, L, 'MULTIPLY_ADD', _m(N, L, 'GREATER_THAN', nz.outputs['Fac'], 0.60), -0.10, 1.0)
    base = _m(N, L, 'MINIMUM', _m(N, L, 'MULTIPLY_ADD', sp.outputs['Z'], 0.35, 0.80), 1.0)
    return _mul_ramp(N, L, ramp.outputs[0], _m(N, L, 'MULTIPLY', streak, base))


def tex_stripes(period, c2):
    """awning canvas: vertical stripes along object X"""
    def f(nt, ramp):
        N = nt.nodes; L = nt.links
        tc = N.new('ShaderNodeTexCoord'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sp.inputs[0])
        g = _m(N, L, 'GREATER_THAN', _m(N, L, 'FRACT', _m(N, L, 'MULTIPLY', sp.outputs['X'], 1 / period)), 0.5)
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; L.new(g, mx.inputs[0])
        L.new(ramp.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*c2, 1)
        return mx.outputs[2]
    return f


ASPH4 = T('asphalt4', (0.43, 0.40, 0.45), tex=tex_asphalt)
PATCH = T('asph_patch', (0.33, 0.31, 0.36), tex=tex_patchy(0.5, 9.0, 0.9, 1.05))
PAINTW = T('roadpaint4', (0.90, 0.88, 0.84), tex=tex_patchy(1.2, 14.0, 0.82, 1.04))
KERB4 = T('kerb4', (0.70, 0.68, 0.68), tex=tex_patchy(0.6, 6.0, 0.86, 1.05))
GRATE = T('grate', (0.26, 0.24, 0.27), tex=tex_rows(0.035, 0.35, 'X'))
CONCW = T('blockwall', (0.66, 0.64, 0.62), tex=tex_rows(0.20, 0.80))
RAILW = T('guardrail', (0.88, 0.88, 0.86), rim=(1.0, 0.86, 0.6), rf=0.6)
POST = T('gr_post', (0.80, 0.80, 0.80))
POLE = T('pole4', (0.62, 0.60, 0.60), rim=(1.0, 0.84, 0.58), rf=0.6)
PLASTER = T('shop_plaster', (0.86, 0.80, 0.66), tex=tex_plaster)
ALU = T('alu_sash', (0.72, 0.72, 0.74), rim=(1.0, 0.9, 0.7), rf=0.55)
AWN = T('awning', (0.92, 0.90, 0.86), tex=tex_stripes(0.32, lin((0.62, 0.20, 0.16))), rim=(1.0, 0.85, 0.6), rf=0.6)
SIGNB = T('signboard', (0.94, 0.92, 0.86))
INKR = T('sign_red', (0.78, 0.16, 0.12))
INKK = T('sign_black', (0.14, 0.12, 0.14), rim=None)
TABAKO = T('tabako_red', (0.84, 0.14, 0.10), rim=(1.0, 0.8, 0.6), rf=0.6)
TABAKOW = T('tabako_white', (0.98, 0.96, 0.92))
VBODY = T('vend_body4', (0.90, 0.90, 0.92), rim=(1.0, 0.86, 0.62), rf=0.6)
VFACE = emis('vend_face4', (0.92, 0.95, 1.0), 1.3)
CRATE = T('beer_crate', (0.96, 0.74, 0.16))
POT = T('pot', (0.58, 0.32, 0.24))
SHRUB = T('shrub', (0.30, 0.42, 0.22), rim=(0.95, 0.82, 0.45), rf=0.72)
SUSUKI = toon('susuki', shade((0.86, 0.74, 0.52)), (0.86, 0.74, 0.52), (1.0, 0.90, 0.66), None, 0.55)
WEED = T('weed', (0.50, 0.54, 0.28), rim=(0.95, 0.85, 0.5), rf=0.6)
VERGE = T('verge4', (0.54, 0.52, 0.30), tex=tex_patchy(0.12, 2.2))
SHOPIN = None   # built below (holdout glass)
BAGM = toon('konbini_bag', (0.70, 0.66, 0.70), (0.97, 0.96, 0.94), (1.0, 0.95, 0.82), None, 0.55)
BAGP1 = T('bag_print_teal', (0.16, 0.56, 0.58)); BAGP2 = T('bag_print_orange', (0.96, 0.52, 0.18))
BAGIN = toon('bag_contents', (0.46, 0.44, 0.50), (0.78, 0.76, 0.80), None)
BLURM = emis('spoke_blur', (0.80, 0.80, 0.86), 0.55)


def glass_mat():
    """shop glass = holdout (the comp puts the late reflection there) mixed with the dim interior: shelves, a lit fridge"""
    m = bpy.data.materials.new('shop_glass'); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial'); ho = N.new('ShaderNodeHoldout'); em = N.new('ShaderNodeEmission')
    tc = N.new('ShaderNodeTexCoord'); sp = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sp.inputs[0])
    shelf = _m(N, L, 'GREATER_THAN', _m(N, L, 'FRACT', _m(N, L, 'MULTIPLY', sp.outputs['Z'], 1 / 0.42)), 0.78)
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    goods = _m(N, L, 'MULTIPLY', nz.outputs['Fac'], 0.08)
    fridge = _m(N, L, 'MULTIPLY', _m(N, L, 'GREATER_THAN', sp.outputs['X'], SHOP1 - 2.4), _m(N, L, 'LESS_THAN', sp.outputs['Z'], 1.6))
    v = _m(N, L, 'ADD', _m(N, L, 'ADD', 0.035, _m(N, L, 'MULTIPLY', shelf, 0.05)), _m(N, L, 'ADD', goods, _m(N, L, 'MULTIPLY', fridge, 0.16)))
    cb = N.new('ShaderNodeCombineXYZ'); L.new(_m(N, L, 'MULTIPLY', v, 0.95), cb.inputs[0]); L.new(v, cb.inputs[1]); L.new(_m(N, L, 'MULTIPLY', v, 1.25), cb.inputs[2])
    L.new(cb.outputs[0], em.inputs[0])
    mx = N.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.42          # 0.42 interior, 0.58 reflection
    L.new(ho.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m


SHOPGLASS = glass_mat()

# ---------------- the road ----------------
X0, X1 = -30, 60
plane('road', X0, X1, -2.6, 2.6, 0.0, ASPH4)
for y in (-2.35, 2.35):                                            # outer white lines, worn
    plane('edgeline', X0, X1, y - 0.06, y + 0.06, 0.004, PAINTW)
for x0, x1, y0, y1 in ((3.0, 5.6, -1.4, 0.2), (14.0, 15.1, 0.4, 2.0), (-6.0, -2.5, -2.2, -0.9), (24.0, 27.5, -0.6, 1.2), (33, 34.2, -2.1, -1.0)):
    plane('patch', x0, x1, y0, y1, 0.002, PATCH)                     # tar repair patches
plane('joint', 6.25, 6.37, -2.6, 2.6, 0.003, GRATE)
YELLOW = T('roadpaint_yellow', (0.94, 0.72, 0.20), tex=tex_patchy(1.2, 14.0, 0.80, 1.04))
plane('centreline', X0, X1, -0.06, 0.06, 0.004, YELLOW)                      # solid yellow: no overtaking on the hill
for x in (-12.0, 7.5, 41.0):                                                # 徐行 (slow) painted in the near lane, read by uphill traffic
    tx = text('徐行', 1.25, PAINTW, (x, -1.25, 0.006), rot=(0, 0, math.radians(90)), far=False)
    tx.data.extrude = 0.0
for k in range(int((X1 - X0) / 1.0)):                                      # far-kerb drain grates every few metres
    if k % 5: continue
    plane('fgrate', X0 + k, X0 + k + 0.5, 2.38, 2.58, 0.005, GRATE)
LEAFC = [T('leaf_r', (0.80, 0.30, 0.14)), T('leaf_o', (0.90, 0.55, 0.20)), T('leaf_b', (0.55, 0.36, 0.22))]
for k in range(3):                                                          # fallen maple leaves drifted along both kerbs
    bm = bmesh.new()
    for i in range(140):
        x = rnd.uniform(X0, X1); y = rnd.choice((rnd.uniform(-2.55, -1.9), rnd.uniform(1.9, 2.58), rnd.uniform(-2.5, 2.5)))
        s = rnd.uniform(0.05, 0.09); a = rnd.uniform(0, 6.28)
        pts = [Vector((x + math.cos(a + j * 2.094) * s * (1.0 if j % 2 == 0 else 0.7), y + math.sin(a + j * 2.094) * s, 0.008)) for j in range(5)]
        bm.faces.new([bm.verts.new(p) for p in pts])
    mesh_obj('leaves', bm, LEAFC[k], ROAD, 0)
bm = bmesh.new()                                                            # dark tyre streaks (braking on the hill)
for i in range(9):
    x = rnd.uniform(X0, X1); y = rnd.uniform(-2.0, 2.0); L_ = rnd.uniform(2.5, 7.0)
    for dy in (0.0, 1.45):
        vs = [bm.verts.new(v) for v in ((x, y + dy, 0.003), (x + L_, y + dy + 0.05, 0.003), (x + L_, y + dy + 0.2, 0.003), (x, y + dy + 0.16, 0.003))]
        bm.faces.new(vs)
mesh_obj('tyre_marks', bm, T('tyre_mark', (0.33, 0.31, 0.36), tex=tex_patchy(0.8, 6.0, 0.9, 1.05)), ROAD, 0)               # steel expansion joint: the bump at f40
for k, x in enumerate((-1.5, 18.5, 37.0)):                          # manholes (ring + cast pattern)
    bm = lathe([(0, 0.32), (0.012, 0.32), (0.012, 0.0)], 32)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, 'X'))
    ob = mesh_obj('manhole', bm, T('manhole%d' % k, (0.34, 0.32, 0.34), tex=tex_rows(0.05, 0.55, 'X')), ROAD, 0)
    ob.location = (x, -0.9 + k * 0.7, 0.0)
# near side: kerb, U-gutter with grated covers, verge, block wall + houses (only seen in the reflection)
bm = bmesh.new()
box(bm, ((X0 + X1) / 2, -2.68, 0.06), (X1 - X0, 0.16, 0.12), 0)
for k in range(int((X1 - X0) / 1.0)):
    x = X0 + 0.5 + k * 1.0
    box(bm, (x, -2.98, 0.03), (0.96, 0.42, 0.04), 1 if k % 4 == 0 else 0)
obj('near_kerb', bm, KERB4, 5, extra=(GRATE,))
plane('near_verge', X0, X1, -3.2, -6.0, 0.05, VERGE)
bm = bmesh.new()
for k in range(int((X1 - X0) / 2.0)):
    box(bm, (X0 + 1 + k * 2.0, -6.2, 0.75), (1.98, 0.15, 1.5), 0)
obj('near_wall', bm, CONCW, 12)
x = X0
while x < X1:
    w = rnd.uniform(6, 9)
    house(x + w / 2, -11.5 + rnd.uniform(-1, 1), w, rnd.uniform(6, 8), rnd.choice((3.2, 5.8, 6.0)), rnd.choice(ROOF), rnd.choice(WALLS),
          rnd.choice(('hip', 'gable')), 16)
    x += w + rnd.uniform(1.5, 3)
# far side: kerb, a narrow verge, white W-beam guardrail (breaks for the shop forecourt), then the drop to the bay
pass
bm = bmesh.new(); box(bm, ((X0 + X1) / 2, 2.68, 0.06), (X1 - X0, 0.16, 0.12), 0); FAR.append(obj('far_kerb', bm, KERB4, 7))
plane('forecourt', SHOP0 - 1.0, SHOP1 + 1.0, 2.76, WY + 0.3, 0.02, T('forecourt', (0.62, 0.60, 0.60), tex=tex_patchy(0.4, 5.0, 0.85, 1.06)), far=False)
plane('far_verge', X0, X1, 2.76, 3.6, 0.03, VERGE, far=True)
bm = bmesh.new()                                                    # the verge falls away steeply beyond the rail
vs = [bm.verts.new(v) for v in ((X0, 3.6, 0.03), (X1, 3.6, 0.03), (X1, 7.5, -4.5), (X0, 7.5, -4.5))]; bm.faces.new(vs)
FAR.append(obj('drop', bm, VERGE, 9))
for seg0, seg1 in ((X0, SHOP0 - 1.2), (SHOP1 + 1.2, X1)):
    bm = bmesh.new()
    n = int((seg1 - seg0) / 2.0)
    for k in range(n + 1):
        x = seg0 + k * (seg1 - seg0) / n
        box(bm, (x, 3.2, 0.42), (0.07, 0.07, 0.84), 1)
    L_ = seg1 - seg0; xm = (seg0 + seg1) / 2
    box(bm, (xm, 3.14, 0.70), (L_, 0.03, 0.30), 0)                    # W-beam: face + two folds
    box(bm, (xm, 3.11, 0.64), (L_, 0.03, 0.05), 0); box(bm, (xm, 3.11, 0.76), (L_, 0.03, 0.05), 0)
    for xe in (seg0, seg1): box(bm, (xe, 3.18, 0.70), (0.25, 0.12, 0.28), 0)   # rounded end pieces
    FAR.append(obj('guardrail', bm, RAILW, 7, extra=(POST,)))
# susuki pampas + weeds along the rail top: silhouettes against the sky catch the warm rim
for i in range(70):
    x = rnd.uniform(X0, X1)
    if SHOP0 - 1.5 < x < SHOP1 + 1.5: continue
    bm = bmesh.new(); hh = rnd.uniform(0.9, 1.7)
    for k in range(rnd.randint(4, 8)):
        lean = rnd.uniform(-0.35, 0.15); a = rnd.uniform(0, 6.28)
        p0 = Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0)); p1 = p0 + Vector((lean * hh * 0.5, 0, hh * rnd.uniform(0.75, 1.0)))
        beam(bm, p0, p1, 0.008, 0)
        if rnd.random() < 0.7:                                       # feathery plume
            e = ellipsoid(0.035, 0.025, 0.16, 8, 6)
            bmesh.ops.rotate(e, verts=e.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(lean * 0.9, 3, 'Y'))
            bmesh.ops.translate(e, vec=p1 + Vector((lean * 0.08, 0, 0.1)), verts=e.verts)
            me = bpy.data.meshes.new('pl'); e.to_mesh(me); e.free()
            for f in me.polygons: f.material_index = 1
            bm.from_mesh(me)
    ob = obj('susuki', bm, WEED, 8, flat=False, extra=(SUSUKI,)); ob.location = (x, rnd.uniform(3.35, 3.9), rnd.uniform(-0.2, 0.0))
    FAR.append(ob)
# utility poles on the far side (their long shadows cross the road and flick over Sam)
POLES = [(-9.0, 3.45), (5.2, 3.45), (19.0, 3.45), (33.5, 3.45), (48, 3.45)]
for x, y in POLES:
    p = upole(x, y, 0, 10.0, 8); p.data.materials[0] = POLE; FAR.append(p)
    bm = bmesh.new(); box(bm, (0, -0.2, 2.4), (0.36, 0.03, 0.9), 0)   # yellow-black guard sleeve + address plate
    box(bm, (0, -0.19, 0.45), (0.38, 0.03, 0.9), 1)
    pl = obj('pole_plate', bm, T('plate_blue', (0.30, 0.44, 0.70)), 8, extra=(YEL,)); pl.location = (x, y, 0); FAR.append(pl)
for (xa, ya), (xb, yb) in zip(POLES, POLES[1:]):
    for dz, dy in ((9.5, -0.8), (9.5, 0.8), (8.6, -0.8), (8.6, 0.8)):
        FAR.append(wire((xa, ya + dy, dz), (xb, yb + dy, dz), 0.45, 0.022))
FAR.append(wire((19.0, 3.45, 7.6), (SHOP1 - 0.6, WY + 0.6, 3.9), 0.6, 0.012))       # service drop to the shop
FAR.append(wire((5.2, 3.45, 7.8), (-1.0, -6.4, 5.2), 0.9, 0.012))                    # one crossing the road overhead

# ---------------- the Yamada shop (sake / tabako), front = window plane y = WY ----------------
SW = SHOP1 - SHOP0; SX = (SHOP0 + SHOP1) / 2
bm = bmesh.new()
box(bm, (SX, WY + 3.0, 1.75), (SW, 6.0, 3.5), 0)                      # body
box(bm, (SX, WY + 0.01, 3.05), (SW + 0.1, 0.10, 0.9), 0)              # fascia behind the sign
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
FAR.append(obj('shop', bm, PLASTER, 9))
# roof: low kawara gable, ridge parallel to the road
bm = bmesh.new(); o_ = 0.5; zt = 3.55; rh = 1.15; yc = WY + 3.0
x0_, x1_, y0_, y1_ = SHOP0 - o_, SHOP1 + o_, WY - o_, WY + 6.0 + o_
ra, rb = bm.verts.new((x0_, yc, zt + rh)), bm.verts.new((x1_, yc, zt + rh))
q_ = [bm.verts.new(v) for v in ((x0_, y0_, zt), (x1_, y0_, zt), (x1_, y1_, zt), (x0_, y1_, zt))]
bm.faces.new((q_[0], q_[1], rb, ra)); bm.faces.new((q_[2], q_[3], ra, rb))
for sx_ in (SHOP0, SHOP1):
    g_ = [bm.verts.new((sx_, WY, 3.5)), bm.verts.new((sx_, WY + 6.0, 3.5)), bm.verts.new((sx_, yc, zt + rh - 0.1))]
    bm.faces.new(g_).material_index = 2
beam(bm, (x0_, y0_, zt + 0.02), (x1_, y0_, zt + 0.02), 0.17, 1); beam(bm, (x0_, y1_, zt + 0.02), (x1_, y1_, zt + 0.02), 0.17, 1)
beam(bm, ra.co + Vector((0, 0, 0.12)), rb.co + Vector((0, 0, 0.12)), 0.22, 1)
for e_ in (ra.co, rb.co): box(bm, (e_.x, e_.y, e_.z + 0.25), (0.40, 0.40, 0.5), 1)
for e_ in (ra.co, rb.co):
    for yy in (y0_, y1_): beam(bm, (e_.x, yy, zt), e_, 0.12, 1)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
FAR.append(obj('shop_roof', bm, ROOF[0], 9, extra=(EAVE, PLASTER)))
# storefront: aluminium sash with 3 big panes + a sliding door, a low tiled stall-riser
GL0, GL1, GZ0, GZ1 = SHOP0 + 0.5, SHOP1 - 0.5, 0.55, 2.45
bm = bmesh.new()
box(bm, (SX, WY - 0.02, GZ0 / 2), (SW, 0.06, GZ0), 1)                  # riser
for x in [GL0 + k * (GL1 - GL0) / 4 for k in range(5)]:
    box(bm, (x, WY - 0.03, (GZ0 + GZ1) / 2), (0.07, 0.07, GZ1 - GZ0 + 0.1), 0)
for z in (GZ0, GZ1, 1.55):
    box(bm, (SX, WY - 0.03, z), (GL1 - GL0 + 0.07, 0.07, 0.06), 0)
for xx in (SHOP0 + 0.25, SHOP1 - 0.25): box(bm, (xx, WY - 0.03, 1.5), (0.5, 0.08, 3.0), 2)   # side piers
FAR.append(obj('sash', bm, ALU, 6, extra=(T('riser_tile', (0.42, 0.50, 0.50), tex=tex_rows(0.11, 0.7)), PLASTER)))
bm = bmesh.new(); vs = [bm.verts.new(v) for v in ((GL0, WY, GZ0), (GL1, WY, GZ0), (GL1, WY, GZ1), (GL0, WY, GZ1))]; bm.faces.new(vs)
GLASSOB = mesh_obj('shop_glass', bm, SHOPGLASS, ROAD, 0); FAR.append(GLASSOB)
GLASS_CORNERS = [Vector((GL0, WY, GZ0)), Vector((GL1, WY, GZ0)), Vector((GL1, WY, GZ1)), Vector((GL0, WY, GZ1))]
# awning (sticks out toward the road: it shows in the reflection too, so it is not in FAR)
bm = bmesh.new()
vs = [bm.verts.new(v) for v in ((SHOP0 + 0.2, WY, 2.75), (SHOP1 - 0.2, WY, 2.75), (SHOP1 - 0.2, WY - 1.0, 2.35), (SHOP0 + 0.2, WY - 1.0, 2.35))]
bm.faces.new(vs)
vs2 = [bm.verts.new(v) for v in ((SHOP0 + 0.2, WY - 1.0, 2.35), (SHOP1 - 0.2, WY - 1.0, 2.35), (SHOP1 - 0.2, WY - 1.0, 2.15), (SHOP0 + 0.2, WY - 1.0, 2.15))]
bm.faces.new(vs2)
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.02)
obj('awning', bm, AWN, 6)
# sign board + lettering (IPA Gothic): 山田商店 and 酒・たばこ
bm = bmesh.new(); box(bm, (SX, WY - 0.08, 3.1), (SW - 1.0, 0.06, 0.72), 0); FAR.append(obj('signboard', bm, SIGNB, 8))
text('山田商店', 0.50, INKK, (SX - 0.9, WY - 0.115, 3.1))
text('酒・たばこ', 0.30, INKR, (SX + 2.6, WY - 0.115, 3.1))
# the classic red tabako sign on a bracket
bm = bmesh.new(); box(bm, (0, 0, 0), (0.70, 0.05, 0.30), 0)
tb = obj('tabako_sign', bm, TABAKO, 6); tb.location = (SHOP1 - 0.25, WY - 0.12, 2.62); FAR.append(tb)
text('たばこ', 0.20, TABAKOW, (SHOP1 - 0.25, WY - 0.15, 2.62))
# vending machine (lone, by the shop), beer crates, potted plants
bm = bmesh.new(); box(bm, (0, 0, 0.92), (1.0, 0.72, 1.84), 0); box(bm, (0, -0.37, 1.1), (0.84, 0.03, 0.95), 1)
for r_ in range(3):
    for c_ in range(6):
        box(bm, (-0.35 + c_ * 0.14, -0.39, 0.75 + r_ * 0.3), (0.06, 0.02, 0.16), 2 + (r_ + c_) % 3)
box(bm, (0, -0.37, 0.22), (0.7, 0.05, 0.16), 5)
vo = obj('vending', bm, VBODY, 6, extra=(VFACE, T('can_red', (0.86, 0.22, 0.18)), T('can_blue', (0.22, 0.42, 0.78)), T('can_green', (0.36, 0.64, 0.34)), INKK))
vo.location = (SHOP1 + 0.75, WY - 0.6, 0.02)
for k, (x, z) in enumerate(((SHOP0 + 0.2, 0.0), (SHOP0 + 0.2, 0.3), (SHOP0 + 0.75, 0.0))):
    bm = bmesh.new(); box(bm, (0, 0, 0.15), (0.48, 0.34, 0.30), 0)
    for j in range(4): box(bm, (-0.18 + j * 0.12, 0, 0.32), (0.06, 0.28, 0.06), 1)
    co = obj('crate', bm, CRATE, 6, extra=(T('bottle', (0.32, 0.24, 0.16)),)); co.location = (x, WY - 0.45, z + 0.02)
for k in range(3):
    bm = lathe([(0, 0.13), (0.30, 0.17), (0.31, 0.0)], 14)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    for j in range(4):
        e = ellipsoid(0.17, 0.17, 0.14, 10, 6); bmesh.ops.translate(e, vec=(rnd.uniform(-.08, .08), rnd.uniform(-.08, .08), 0.38 + j * 0.07), verts=e.verts)
        me = bpy.data.meshes.new('lf'); e.to_mesh(me); e.free()
        for f in me.polygons: f.material_index = 1
        bm.from_mesh(me)
    po = obj('pot', bm, POT, 6, flat=False, extra=(SHRUB,)); po.location = (SHOP0 + 1.5 + k * 0.6, WY - 0.35, 0.02)

# ---------------- bike + Sam (real) and the 0.5 s-late twin the mirror camera sees ----------------
def make_rider(tag):
    before = set(sc.objects)
    B = make_bike(ROAD); rig = load_sam(B); ik = seat_rider(rig, B)
    B['root'].name = 'bike_root_' + tag
    objs = [o for o in sc.objects if o not in before]
    # spoke blur: hide spokes, add speed arcs that jump on twos
    arcs = []
    for wpiv in (B['wheel_r'], B['wheel_f']):
        for o in wpiv.children_recursive:
            if o.name.startswith('bike_wheel') and o.name.endswith('_spokes') or '_spokes' in o.name: o.hide_render = True
        bm = bmesh.new()
        for j, (rr, a0, span) in enumerate(((0.27, 0.2, 1.3), (0.22, 2.4, 1.0), (0.16, 4.1, 1.5), (0.25, 4.6, 0.9), (0.12, 1.4, 1.1))):
            pts = [Vector((math.cos(a0 + span * i / 14) * rr, (0.012 if j % 2 else -0.012), math.sin(a0 + span * i / 14) * rr)) for i in range(15)]
            for p, q in zip(pts, pts[1:]):
                n_ = Vector((p.x, 0, p.z)).normalized() * 0.0035
                bm.faces.new([bm.verts.new(p - n_), bm.verts.new(q - n_), bm.verts.new(q + n_), bm.verts.new(p + n_)])
        ao = mesh_obj('spoke_blur', bm, BLURM, wpiv, 0); arcs.append(ao); objs.append(ao)
    # konbini bag on the right half of the bar, near the stem
    st = HT_T - HT_B + (HT_T - HT_B).normalized() * 0.25
    piv = empty('bag_pivot_' + tag, B['steer'], st + Vector((-0.03, -0.13, 0.008)))
    bm = bmesh.new()
    r_ = random.Random(9)
    prof = []
    for i in range(15):                                    # bag body: flat-bottomed sack, gathered into the handles at the top
        t = i / 14; z = -0.12 - t * 0.29
        g = min(1.0, t / 0.28)                              # gather zone at the top
        wdt = 0.05 + 0.075 * (1 - (1 - g) ** 2)
        dep = 0.02 + 0.04 * (1 - (1 - g) ** 2) + 0.012 * math.sin(math.pi * t)
        if t > 0.9: rr_ = (t - 0.9) / 0.1; wdt *= 1 - 0.18 * rr_ ** 2; dep *= 1 - 0.5 * rr_ ** 2
        ring = []
        for k in range(24):
            a = 2 * math.pi * k / 24
            ca, sa = math.cos(a), math.sin(a)
            sq = (abs(ca) ** 0.45 * (1 if ca >= 0 else -1), abs(sa) ** 0.8 * (1 if sa >= 0 else -1))   # boxy plan
            crease = 1 + 0.035 * math.sin(k * 2.7 + i * 1.3) * (0.3 + t)
            ring.append(bm.verts.new((sq[0] * wdt * crease, sq[1] * dep * crease, z + 0.004 * r_.uniform(-1, 1) * t)))
        prof.append(ring)
    for A, Bq in zip(prof, prof[1:]):
        for k in range(24): bm.faces.new((A[k], A[(k + 1) % 24], Bq[(k + 1) % 24], Bq[k]))
    bm.faces.new(list(reversed(prof[-1])))
    for f in bm.faces:                                      # printed bands across the front (generic konbini print)
        zc = f.calc_center_median().z
        if -0.262 < zc < -0.250 and f.normal.y < -0.3: f.material_index = 1
        if -0.282 < zc < -0.268 and f.normal.y < -0.3: f.material_index = 2
    for side in (-1, 1):                                    # handles looped over the bar
        pts = [Vector((side * 0.055, 0, -0.13)), Vector((side * 0.045, 0, -0.06)), Vector((side * 0.02, -0.012, 0.0)),
               Vector((0, -0.006, 0.016)), Vector((-side * 0.015, 0.012, 0.004)), Vector((-side * 0.03, 0.01, -0.05))]
        _tube(bm, pts, 0.0055, 6, 0)
    bag = mesh_obj('konbini_bag_' + tag, bm, BAGM, piv, 0)
    for m in (BAGP1, BAGP2, BAGIN): bag.data.materials.append(m)
    outline(bag, 0.0022); objs += [piv, bag]
    rest = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}
    hair = []
    for b in rig.data.bones:
        if not b.name.startswith('HairJoint'): continue
        k = 0; p = b.parent
        while p and p.name.startswith('HairJoint'): k += 1; p = p.parent
        d = (b.tail_local - b.head_local).normalized()
        ax = d.cross(Vector((0, 1, 0)))                     # tilt the strand toward armature +Y = behind him (the wind)
        if ax.length < 1e-3: continue
        hair.append((b.name, k, (b.matrix_local.to_3x3().inverted() @ ax.normalized()).normalized(), ax.length, b.head_local.z))
    strings = []
    for n in ('Hoodie_String_L', 'Hoodie_String_R'):
        o = next((o for o in objs if o.name.startswith(n)), None)
        if o:
            sp_ = o.data.splines[0]
            P = list(sp_.bezier_points) if sp_.type == 'BEZIER' else list(sp_.points)
            strings.append((o, [Vector(p.co[:3]) for p in P]))
    face = next(o for o in objs if o.name.startswith('Face') and o.type == 'MESH' and o.data.shape_keys)
    return dict(B=B, rig=rig, ik=ik, objs=objs, arcs=arcs, bag=piv, rest=rest, hair=hair, strings=strings, face=face,
                base_loc=rig.location.copy())


def sam_rim(mat):
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    for em in [n for n in N if n.type == 'EMISSION' and n.inputs[0].links]:
        src_ = em.inputs[0].links[0].from_socket
        geo = N.new('ShaderNodeNewGeometry'); lw = N.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.5
        dt = N.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'; dt.inputs[1].default_value = SUNV
        L.new(geo.outputs['Normal'], dt.inputs[0])
        g1 = _m(N, L, 'GREATER_THAN', lw.outputs['Facing'], 0.60); g2 = _m(N, L, 'GREATER_THAN', dt.outputs['Value'], 0.10)
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; L.new(_m(N, L, 'MULTIPLY', _m(N, L, 'MULTIPLY', g1, g2), 0.85), mx.inputs[0])
        L.new(src_, mx.inputs[6]); mx.inputs[7].default_value = (*lin((1.0, 0.74, 0.50)), 1)
        L.new(mx.outputs[2], em.inputs[0])


RIMMED = set()


def sam_fix(objs):
    for o in objs:
        for md in o.modifiers:
            if md.type == 'SOLIDIFY' and md.name.startswith('Outline'): md.thickness = max(md.thickness * 1.9, 0.0018)
        if o.type in ('MESH', 'CURVE'):
            for ms in o.material_slots:
                m = ms.material
                if m and m.name.startswith('Sam_') and m.use_nodes and m.name not in RIMMED and not any(k in m.name for k in ('Eye', 'Iris', 'Lens', 'Brow', 'Mouth', 'Lash', 'line')):
                    sam_rim(m); RIMMED.add(m.name)


R1 = make_rider('real')
R2 = make_rider('late')
sam_fix(R1['objs']); sam_fix(R2['objs'])
for o in R1['objs']: o.hide_probe_plane = True
for o in R2['objs']:
    o.visible_camera = False; o.visible_shadow = False

# ---------------- motion: Sam coasts downhill, camera tracks then eases off so he overtakes it ----------------
V0, ACC = 3.9, 0.30
LANE = 1.05


def sam_x(f):
    t = (f - 1) / 24.0; return -1.6 + V0 * t + 0.5 * ACC * t * t


def ease(t):
    t = max(0, min(1, t)); return t * t * (3 - 2 * t)


CAMX = {}
xc = sam_x(-40) + 0.62
for f in range(-40, NF + 2):
    vs = (sam_x(f + 1) - sam_x(f))
    slow = 1 - 0.66 * ease((f - 58) / 34.0)
    CAMX[f] = xc; xc += vs * slow


def bump(f, f0, amp=1.0):
    """road-joint jolt: quick up, damped ring"""
    d = f - f0
    if d < 0: return 0.0
    return amp * math.exp(-d * 0.45) * math.sin(d * 1.3 + 0.3)


F_JOINT_F = None; F_JOINT_R = None
for f in range(-40, NF + 20):                               # frames when the front / rear wheel crosses the joint (x = 6.31)
    if F_JOINT_F is None and sam_x(f) + 1.12 >= 6.31: F_JOINT_F = f
    if F_JOINT_R is None and sam_x(f) >= 6.31: F_JOINT_R = f


def bag_sim():
    """pendulum: wind holds it back ~14 deg, the jolts kick it, plastic flutter on top"""
    th, w = math.radians(-14), 0.0; out = {}
    for f in range(-60, NF + 2):
        kick = 0.0
        if f in (F_JOINT_F, F_JOINT_R): kick = 2.6 if f == F_JOINT_F else 1.6
        w += kick
        for _ in range(4):
            dt = 1 / 96
            acc = -(9.8 / 0.26) * math.sin(th - math.radians(-14)) - 1.4 * w
            w += acc * dt; th += w * dt
        out[f] = th
    return out


BAG = bag_sim()
# lyrics: vowel, frame-on, frames  (a short phrase, a breath, a phrase; he mouths, doesn't sing out)
LYR = [('A', 3, 4), ('I', 7, 4), ('O', 11, 6), ('E', 19, 4), ('A', 23, 4), ('U', 27, 8),
       ('O', 43, 4), ('A', 47, 4), ('I', 51, 4), ('E', 55, 6), ('A', 63, 4), ('O', 67, 10), ('I', 81, 4), ('A', 85, 6)]
KEYS = {v: 'Face.M_F00_000_00_Fcl_MTH_' + v for v in 'AIUEO'}
BEAT = 14.4                                                  # ~100 bpm head bob


def pose_rider(R, f):
    """everything on twos except the bike travel (ones keeps the road smooth)"""
    fs = f - ((f - 1) % 2)
    rig, B = R['rig'], R['B']
    jolt = bump(fs, F_JOINT_F, 0.012) + bump(fs, F_JOINT_R, 0.009)
    B['root'].location = (sam_x(f), LANE, max(0.0, jolt) * 0.6)
    B['root'].rotation_euler = (0, -(bump(fs, F_JOINT_F, 0.010) - bump(fs, F_JOINT_R, 0.008)), 0)
    B['steer'].rotation_euler = (0, 0, math.radians(1.2 * math.sin(fs * 0.11) + 0.6 * math.sin(fs * 0.29)))
    spin = -(sam_x(f) / R_WHEEL)
    for wp in (B['wheel_r'], B['wheel_f']): wp.rotation_euler = (0, spin, 0)
    for k, a in enumerate(R['arcs']): a.rotation_euler = (0, random.Random(fs * 7 + k).uniform(0, 6.28), 0)
    # body: restore the seated pose, then layer bob / jolt lag / beat nod
    for pb in rig.pose.bones:
        q, l = R['rest'][pb.name]; pb.rotation_quaternion = q; pb.location = l
    lag = bump(fs - 2, F_JOINT_F, 0.016) + bump(fs - 2, F_JOINT_R, 0.012)
    rig.location = R['base_loc'] + Vector((0, 0, 0.004 * math.sin(fs * 2 * math.pi / BEAT) + lag))

    def rot(name, ax_arm, deg):
        pb = rig.pose.bones[name]; b = rig.data.bones[name]
        ax = (b.matrix_local.to_3x3().inverted() @ Vector(ax_arm)).normalized()
        pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(ax, math.radians(deg))
    nod = math.sin(fs * 2 * math.pi / BEAT + 0.6)
    rot('J_Bip_C_Neck', (1, 0, 0), 2.0 * nod - 120 * lag)
    rot('J_Bip_C_Head', (1, 0, 0), 1.5 * nod - 160 * bump(fs - 3, F_JOINT_F, 0.016))
    rot('J_Bip_C_Head', (0, 0, 1), 2.5 * math.sin(fs * 0.05))
    rot('J_Bip_C_Spine', (1, 0, 0), 60 * lag)
    # right index finger taps the beat on the grip
    tap = max(0.0, math.sin(fs * 2 * math.pi / BEAT)) ** 3
    rot('J_Bip_R_Index1', (0, 0, 1), -18 * tap)
    # hair: streams back in the 14 km/h wind, travelling flutter wave, kicked by the jolts
    for name, k, ax, amt, hz in R['hair']:
        base = (5.0 + 3.0 * k) * amt
        fl = (2.2 + 1.4 * k) * math.sin(fs * 0.9 + k * 1.1 + hz * 9 + hash(name) % 7)
        jo = 260 * lag * (k + 1) * 0.5
        rig.pose.bones[name].rotation_quaternion = R['rest'][name][0] @ Quaternion(ax, math.radians(base + fl + jo))
    # mouth
    sk = R['face'].data.shape_keys.key_blocks
    for v in KEYS.values(): sk[v].value = 0.0
    for v, f0, n in LYR:
        if f0 <= fs < f0 + n:
            t = (fs - f0) / n; sk[KEYS[v]].value = 0.55 * math.sin(math.pi * min(1, t * 1.4)) ** 0.5
    sk['Face.M_F00_000_00_Fcl_EYE_Close'].value = 1.0 if fs in (59, 61) else 0.0
    # bag
    th = BAG[fs]; R['bag'].rotation_euler = (math.radians(4) * math.sin(fs * 0.37), -th, 0)
    R['bag'].scale = (1, 1, 1 - 0.05 * max(0, -bump(fs, F_JOINT_F, 1.0)))


def pose_strings(R, f):
    """hoodie strings whip back in the wind (needs the evaluated pose for the wind direction)"""
    fs = f - ((f - 1) % 2)
    for i, (o, pts) in enumerate(R['strings']):
        wd = (o.matrix_world.inverted().to_3x3() @ Vector((-1, 0, 0.25))).normalized()   # air streams back (-x world)
        side = (o.matrix_world.inverted().to_3x3() @ Vector((0, 1, 0))).normalized()
        top = pts[0]
        sp_ = o.data.splines[0]
        P = list(sp_.bezier_points) if sp_.type == 'BEZIER' else list(sp_.points)
        for j, p in enumerate(P[:len(pts)]):
            if j == 0: continue
            d = (pts[j] - top).length
            sw = 0.55 + 0.25 * math.sin(fs * 1.1 + i * 2.0 + j * 0.8)
            q = pts[j] + wd * d * sw + side * 0.02 * d * math.sin(fs * 1.7 + i + j)
            if sp_.type == 'BEZIER':
                dl = q - Vector(p.co); p.co = q; p.handle_left = Vector(p.handle_left) + dl; p.handle_right = Vector(p.handle_right) + dl
            else:
                p.co = (q.x, q.y, q.z, 1)


# ---------------- lights + camera ----------------
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 5.0; sun.data.color = (1.0, 0.78, 0.55); sun.data.angle = math.radians(0.6)
sun.rotation_euler = (-SUN).to_track_quat('-Z', 'Y').to_euler()
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); sc.collection.objects.link(fill)
fill.data.energy = 0.45; fill.data.color = (0.55, 0.55, 0.85); fill.data.use_shadow = False
fill.rotation_euler = (Vector((0.3, -1.0, 0.35))).to_track_quat('-Z', 'Y').to_euler()
camd = bpy.data.cameras.new('cam'); camd.lens = 32; camd.sensor_fit = 'VERTICAL'; camd.sensor_height = 36
camd.clip_start = 0.05; camd.clip_end = 3000
cam = bpy.data.objects.new('cam', camd); sc.collection.objects.link(cam); sc.camera = cam
RM = ROAD.matrix_world.copy()


def road_pt(x, y, z):
    return ROAD.matrix_world @ Vector((x, y, z))


def cam_pose(f):
    """car-mount low tracking cam on ones: level to the world, a touch of road shake"""
    x = CAMX[f]
    p = road_pt(x, -3.05, 0.0) + Vector((0, 0, 0.50 + 0.004 * math.sin(f * 1.9) + 0.003 * math.sin(f * 3.3)))
    pitch = math.radians(8.5 + 0.15 * math.sin(f * 0.7)); roll = math.radians(0.25 * math.sin(f * 0.5))
    d = Vector((0, math.cos(pitch), math.sin(pitch)))
    q = d.to_track_quat('-Z', 'Y'); q = q @ Quaternion((0, 0, 1), roll)
    return p, q


def mirror_cam(p, q):
    """the same camera reflected in the window plane (road-local y = WY); its render is flipped left-right in comp"""
    Mi = ROAD.matrix_world.inverted(); M = ROAD.matrix_world
    pl = Mi @ p; pl.y = 2 * WY - pl.y
    R = q.to_matrix()
    fwd = Mi.to_3x3() @ (R @ Vector((0, 0, -1))); up = Mi.to_3x3() @ (R @ Vector((0, 1, 0)))
    fwd.y = -fwd.y; up.y = -up.y
    fwd = M.to_3x3() @ fwd; up = M.to_3x3() @ up
    z = -fwd.normalized(); x = up.cross(z).normalized(); y = z.cross(x)
    m = Matrix((x, y, z)).transposed()
    return M @ pl, m.to_quaternion()


def proj(pw):
    v = world_to_camera_view(sc, cam, pw); return (v.x, 1 - v.y, v.z)


# ---------------- aerial perspective: far geometry fades toward the warm bay haze ----------------
HAZE = lin((0.98, 0.70, 0.54))
for mat in list(bpy.data.materials):
    if not mat.use_nodes: continue
    nt = mat.node_tree
    em = next((n for n in nt.nodes if n.type == 'EMISSION'), None)
    if em is None or em.inputs[1].default_value > 2.0 or mat.name.startswith(('Sam', 'konbini', 'bag', 'bike', 'spoke', 'shop_glass')): continue
    src_ = em.inputs[0].links[0].from_socket if em.inputs[0].links else None
    cd = nt.nodes.new('ShaderNodeCameraData')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 14; mr.inputs['From Max'].default_value = 60
    mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = 0.35; mr.interpolation_type = 'SMOOTHSTEP'
    nt.links.new(cd.outputs['View Z Depth'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    nt.links.new(mr.outputs[0], mx.inputs[0])
    if src_: nt.links.new(src_, mx.inputs[6])
    else: mx.inputs[6].default_value = tuple(em.inputs[0].default_value)
    mx.inputs[7].default_value = (*HAZE, 1)
    nt.links.new(mx.outputs[2], em.inputs[0])

META = {}
frames = range(1, NF + 1) if FR == 'all' else [int(x) for x in FR.split(',')]
print('joint frames', F_JOINT_F, F_JOINT_R)
for f in frames:
    sc.frame_set(f)
    pose_rider(R1, f); pose_rider(R2, f - DELAY)
    bpy.context.view_layer.update()
    pose_strings(R1, f); pose_strings(R2, f - DELAY)
    p, q = cam_pose(f); cam.location = p; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = q
    bpy.context.view_layer.update()
    s_ = proj(cam.location + SUN * 1000)
    h_ = proj(cam.location + Vector((0, 1, 0)) * 5000)
    gc = [proj(ROAD.matrix_world @ c) for c in GLASS_CORNERS]
    vis = any(0 <= u <= 1 for u, v, z in gc) or (min(u for u, v, z in gc) < 0 < max(u for u, v, z in gc))
    sx_ = proj(R1['B']['root'].matrix_world.translation)
    META[f] = dict(sx=s_[0], sy=s_[1], hy=h_[1], glass=[(u, v) for u, v, z in gc], refl=bool(vis), samx=sx_[0])
    sc.render.filepath = os.path.join(OUT, 'cel_%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    if vis:
        # mirror pass: window-plane reflection of the street, with the late twin instead of Sam
        for o in R1['objs']: o.visible_camera = False; o.visible_shadow = False
        for o in R2['objs']: o.visible_camera = True; o.visible_shadow = True
        for o in FAR: o.visible_camera = False
        pm, qm = mirror_cam(p, q); cam.location = pm; cam.rotation_quaternion = qm
        bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(OUT, 'refl_%03d.png' % f)
        bpy.ops.render.render(write_still=True)
        for o in R1['objs']: o.visible_camera = True; o.visible_shadow = True
        for o in R2['objs']: o.visible_camera = False; o.visible_shadow = False
        for o in FAR: o.visible_camera = True
        cam.location = p; cam.rotation_quaternion = q
    print('frame', f, 'refl' if vis else '', flush=True)
json.dump(META, open(os.path.join(OUT, 'meta.json'), 'w'))
print('META', META[frames[0]])
