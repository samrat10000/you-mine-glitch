"""Japanese city bike (mamachari) for shot 04, built in local space: x forward, y left, z up, ground z=0.
exec() after toonlib_v4 (needs toon, emis, ink, mesh_obj, lathe, ellipsoid, empty, bmesh, Vector, Matrix).
make_bike(parent) -> dict(root, wheel_f, wheel_r, crank, steer, grips (L, R), pedals (L, R), saddle)"""

R_WHEEL = 0.335
REAR = Vector((0.0, 0, R_WHEEL)); FRONT = Vector((1.12, 0, R_WHEEL))
BB = Vector((0.43, 0, 0.29)); SEATC = Vector((0.27, 0, 0.80)); SADDLE = Vector((0.225, 0, 0.955))
HT_B = Vector((0.985, 0, 0.60)); HT_T = Vector((0.945, 0, 0.79))
_lin = lambda c: tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def _sh(lit, k=0.45):
    return tuple(l * k + c * (1 - k) * 0.75 for l, c in zip(lit, (0.27, 0.25, 0.37)))


def _T(n, lit, rim=(1.0, 0.82, 0.58), rf=0.55):
    return toon(n, _sh(lit), lit, rim, None, rf)


B_FRAME = _T('bike_frame', (0.58, 0.76, 0.70))
B_CHROME = _T('bike_chrome', (0.80, 0.80, 0.84), rim=(1.0, 0.92, 0.75))
B_TYRE = _T('bike_tyre', (0.12, 0.11, 0.13), rim=(0.75, 0.6, 0.5))
B_SADDLE = _T('bike_saddle', (0.36, 0.24, 0.20))
B_GRIP = _T('bike_grip', (0.30, 0.22, 0.18))
B_LAMP = emis('bike_lamp_glass', (1.0, 0.95, 0.82), 1.4)
B_REFL = emis('bike_reflector', (0.85, 0.12, 0.08), 1.0)


def _tube(bm, pts, r, seg=10, mi=0):
    """swept circular tube through points"""
    pts = [Vector(p) for p in pts]; rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.orthogonal().normalized(); b = t.cross(a)
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)])
    for A, Bq in zip(rings, rings[1:]):
        for k in range(seg):
            f = bm.faces.new((A[k], A[(k + 1) % seg], Bq[(k + 1) % seg], Bq[k])); f.material_index = mi
    for ring in (rings[0], rings[-1][::-1]):
        f = bm.faces.new(ring); f.material_index = mi


def _bez(p0, p1, p2, n=10):
    return [p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t for t in (i / (n - 1) for i in range(n))]


def _torus(bm, R, r, seg=48, rs=8, mi=0, axis='Y'):
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; c = Vector((math.cos(a) * R, 0, math.sin(a) * R)); n = c.normalized()
        rings.append([bm.verts.new(c + n * (r * math.cos(2 * math.pi * k / rs)) + Vector((0, r * math.sin(2 * math.pi * k / rs), 0))) for k in range(rs)])
    for i in range(seg):
        A, Bq = rings[i], rings[(i + 1) % seg]
        for k in range(rs):
            f = bm.faces.new((A[k], A[(k + 1) % rs], Bq[(k + 1) % rs], Bq[k])); f.material_index = mi


def _box(bm, c, s, mi=0, rot=None):
    r = bmesh.ops.create_cube(bm, size=1); vs = r['verts']
    bmesh.ops.scale(bm, vec=s, verts=vs)
    if rot is not None: bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, vec=c, verts=vs)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi


def _obj(name, bm, mats, line=0.0028, smooth=True):
    ob = mesh_obj(name, bm, mats[0], None, 0)
    for m in mats[1:]: ob.data.materials.append(m)
    for p in ob.data.polygons: p.use_smooth = smooth
    nm = len(ob.data.materials)
    for _ in range(nm): ob.data.materials.append(ink)
    sm = ob.modifiers.new('ol', 'SOLIDIFY'); sm.thickness = line; sm.offset = 1; sm.use_flip_normals = True
    sm.material_offset = nm; sm.use_rim = False
    return ob


def _wheel(name):
    bm = bmesh.new()
    _torus(bm, R_WHEEL - 0.019, 0.019, 64, 10, 0)                  # tyre
    _torus(bm, R_WHEEL - 0.045, 0.009, 64, 6, 1)                   # rim
    hub = lathe([(-0.045, 0.018), (-0.03, 0.03), (0.03, 0.03), (0.045, 0.018)], 16)
    me = bpy.data.meshes.new('h'); hub.to_mesh(me); hub.free(); bm.from_mesh(me)
    sp = bmesh.new()
    for k in range(32):                                            # tangent-laced spokes, two flanges (own object: shots swap in a blur)
        a = 2 * math.pi * k / 32; side = 1 if k % 2 else -1
        h = Vector((math.cos(a) * 0.028, side * 0.03, math.sin(a) * 0.028))
        a2 = a + side * 0.55
        rm = Vector((math.cos(a2) * (R_WHEEL - 0.05), 0, math.sin(a2) * (R_WHEEL - 0.05)))
        _tube(sp, [h, rm], 0.0016, 4, 0)
    for f in bm.faces:
        if f.material_index > 1: f.material_index = 1
    w = _obj(name, bm, [B_TYRE, B_CHROME], 0.0022)
    s = _obj(name + '_spokes', sp, [B_CHROME], 0.0012); s.parent = w
    return w


def make_bike(parent=None):
    root = empty('bike_root', parent)
    # ---- frame: low curved step-through main tube, seat tube, stays, head tube, fork ----
    bm = bmesh.new()
    _tube(bm, _bez(HT_B + Vector((0, 0, 0.03)), Vector((0.62, 0, 0.26)), BB + Vector((0.02, 0, 0.0)), 14), 0.021)
    _tube(bm, _bez(HT_B + Vector((0, 0, 0.12)), Vector((0.66, 0, 0.42)), SEATC + Vector((0.02, 0, -0.18)), 12), 0.015)   # twin top tube
    _tube(bm, [BB, SEATC + Vector((0.0, 0, 0.03))], 0.017)
    for sy in (-0.045, 0.045):
        _tube(bm, [BB + Vector((0, sy * 0.6, 0)), REAR + Vector((0, sy, 0))], 0.009)
        _tube(bm, [SEATC + Vector((0, sy * 0.3, -0.02)), REAR + Vector((0.01, sy, 0.01))], 0.008)
    _tube(bm, [HT_B, HT_T], 0.024)
    bb = lathe([(-0.04, 0.022), (0.04, 0.022)], 14); me = bpy.data.meshes.new('bb'); bb.to_mesh(me); bb.free(); me.transform(Matrix.Translation(BB)); bm.from_mesh(me)
    frame = _obj('bike_frame', bm, [B_FRAME], 0.003); frame.parent = root
    # ---- steering assembly (fork, stem, swept-back bar, grips, basket, lamp, bell) pivots on the head tube ----
    steer = empty('bike_steer', root, HT_B)
    axis = (HT_T - HT_B).normalized()
    sb = bmesh.new()
    for sy in (-0.05, 0.05):
        _tube(sb, [v - HT_B for v in _bez(HT_B + Vector((0, sy * 0.5, 0)), HT_B + Vector((0.07, sy, -0.18)), FRONT + Vector((0.02, sy, 0)), 8)], 0.011, 8, 1)
    _tube(sb, [Vector((0, 0, 0)) - axis * 0.02, HT_T - HT_B + axis * 0.25], 0.013, 10, 1)
    _box(sb, HT_T - HT_B + axis * 0.25, (0.05, 0.045, 0.04), 1)                     # bar clamp
    st = HT_T - HT_B + axis * 0.25
    for side in (-1, 1):
        # comfort bar: rises out of the clamp, swings wide, then curves back and DOWN to the grips (real mamachari shape)
        p0 = st; p1 = st + Vector((0.05, side * 0.24, 0.085)); p2 = st + Vector((-0.24, side * 0.30, 0.05)); p3 = st + Vector((-0.34, side * 0.295, 0.0))
        pts = [p0 * (1 - u) ** 3 + p1 * 3 * u * (1 - u) ** 2 + p2 * 3 * u * u * (1 - u) + p3 * u ** 3 for u in (i / 13 for i in range(14))]
        _tube(sb, pts, 0.0115, 8, 1)
        g0 = pts[-1]; gd = (pts[-1] - pts[-2]).normalized()
        _tube(sb, [g0 - gd * 0.01, g0 + gd * 0.115], 0.0175, 10, 2)                  # ribbed rubber grip in line with the bar end
        _tube(sb, [g0 + gd * 0.115, g0 + gd * 0.122], 0.019, 10, 2)                  # end flange
    # front basket (wire): rim frame + vertical and horizontal wires, mounted to the bar and fork
    bc = Vector((FRONT.x - HT_B.x + 0.02, 0, 0.885 - HT_B.z)); bw, bd, bh = 0.34, 0.30, 0.23
    corners = lambda z, s: [bc + Vector((sx * bw / 2 * s, sy * bd / 2 * s, z)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    for z, s in ((bh / 2, 1.0), (0.0, 0.99), (-bh / 2, 0.92)):
        c4 = corners(z, s); _tube(sb, c4 + [c4[0]], 0.0042 if z > 0.1 else 0.0028, 5, 1)
    for k in range(9):
        for sy in (-1, 1):
            x = -bw / 2 + k * bw / 8
            _tube(sb, [bc + Vector((x, sy * bd / 2, bh / 2)), bc + Vector((x * 0.92, sy * bd / 2 * 0.92, -bh / 2))], 0.0022, 4, 1)
    for k in range(7):
        for sx in (-1, 1):
            y = -bd / 2 + k * bd / 6
            _tube(sb, [bc + Vector((sx * bw / 2, y, bh / 2)), bc + Vector((sx * bw / 2 * 0.92, y * 0.92, -bh / 2))], 0.0022, 4, 1)
    for k in range(5):
        y = -bd / 2 * 0.92 + k * bd * 0.92 / 4
        _tube(sb, [bc + Vector((-bw / 2 * 0.92, y, -bh / 2)), bc + Vector((bw / 2 * 0.92, y, -bh / 2))], 0.0022, 4, 1)
    _tube(sb, [bc + Vector((-bw / 2, 0, -bh / 2)), FRONT - HT_B + Vector((0.0, 0, 0.0))], 0.005, 5, 1)    # basket stay
    lamp = lathe([(0.0, 0.0), (0.005, 0.03), (0.055, 0.034), (0.06, 0.0)], 16)       # dynamo headlamp on the fork
    me = bpy.data.meshes.new('l'); lamp.to_mesh(me); lamp.free()
    me.transform(Matrix.Translation(FRONT - HT_B + Vector((0.05, 0.06, 0.12))) @ Matrix.Rotation(math.radians(-90), 4, 'Z')); sb.from_mesh(me)
    bell = ellipsoid(0.024, 0.024, 0.014, 12, 6); bmesh.ops.translate(bell, vec=st + Vector((-0.06, 0.14, 0.03)), verts=bell.verts)
    me = bpy.data.meshes.new('b'); bell.to_mesh(me); bell.free(); sb.from_mesh(me)
    for f in sb.faces:
        if f.material_index > 2: f.material_index = 1
    so = _obj('bike_steer_parts', sb, [B_FRAME, B_CHROME, B_GRIP], 0.0026); so.parent = steer
    GRIPS = [HT_B + st + Vector((-0.395, s * 0.293, -0.015)) for s in (1, -1)]        # L (+y), R (-y): middle of the rubber
    # ---- fenders, chain guard, rear carrier, saddle, kickstand, reflector ----
    fb = bmesh.new()
    for c, a0, a1 in ((REAR, 0.15, 2.6), (FRONT, 0.55, 2.75)):
        pts = [c + Vector((math.cos(a) * (R_WHEEL + 0.018), 0, math.sin(a) * (R_WHEEL + 0.018))) for a in [a0 + (a1 - a0) * i / 20 for i in range(21)]]
        for i in range(20):
            p, q = pts[i], pts[i + 1]
            vs = [fb.verts.new(p + Vector((0, -0.032, 0))), fb.verts.new(q + Vector((0, -0.032, 0))), fb.verts.new(q + Vector((0, 0.032, 0))), fb.verts.new(p + Vector((0, 0.032, 0)))]
            fb.faces.new(vs)
    fo = _obj('bike_fenders', fb, [B_CHROME], 0.0024, smooth=False); fo.parent = root
    cg = bmesh.new()                                              # chain guard: rounded plate on the right side
    ring = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        cx = BB.x * 0.55 + REAR.x * 0.45; rx = (BB.x - REAR.x) / 2 + 0.04
        ring.append(cg.verts.new((cx + math.cos(a) * rx, -0.07, (BB.z + REAR.z) / 2 + math.sin(a) * (0.062 + 0.012 * math.cos(a)))))
    cg.faces.new(ring); go = _obj('bike_chainguard', cg, [B_FRAME], 0.0025, smooth=False); go.parent = root
    rk = bmesh.new()
    for sy in (-0.06, 0.06):
        _tube(rk, [REAR + Vector((-0.17, sy, 0.38)), REAR + Vector((0.16, sy, 0.38))], 0.006, 6)
        _tube(rk, [REAR + Vector((-0.12, sy, 0.38)), REAR + Vector((0.0, sy + 0.01 * (1 if sy > 0 else -1), 0.0))], 0.005, 6)
    for k in range(4): _tube(rk, [REAR + Vector((-0.17 + k * 0.11, -0.06, 0.38)), REAR + Vector((-0.17 + k * 0.11, 0.06, 0.38))], 0.005, 6)
    _tube(rk, [REAR + Vector((0.16, 0, 0.38)), SEATC + Vector((-0.01, 0, -0.01))], 0.006, 6)
    _tube(rk, [SADDLE + Vector((0.03, 0, -0.04)), SEATC], 0.012, 8)                                  # seat post
    _box(rk, REAR + Vector((-0.20, 0, 0.30)), (0.012, 0.05, 0.03), 1)                                 # rear reflector
    _tube(rk, [REAR + Vector((0.02, -0.06, 0.0)), REAR + Vector((-0.30, -0.07, 0.03))], 0.007, 6)   # kickstand folded up along the stay
    ko = _obj('bike_rack', rk, [B_CHROME, B_REFL], 0.0024); ko.parent = root
    sd = bmesh.new()
    s_ = ellipsoid(0.13, 0.085, 0.035, 18, 8)
    for v in s_.verts:
        if v.co.x > 0: v.co.y *= 1 - 0.55 * (v.co.x / 0.13) ** 1.5                # nose narrows
        v.co.z += 0.012 * (v.co.x / 0.13) ** 2
    bmesh.ops.translate(s_, vec=SADDLE, verts=s_.verts)
    me = bpy.data.meshes.new('s'); s_.to_mesh(me); s_.free(); sd.from_mesh(me)
    for sy in (-0.04, 0.04): _tube(sd, [SADDLE + Vector((-0.09, sy, -0.03)), SADDLE + Vector((-0.06, sy, -0.075)), SADDLE + Vector((0.02, sy * 0.5, -0.05))], 0.004, 5, 1)
    sdo = _obj('bike_saddle', sd, [B_SADDLE, B_CHROME], 0.0028); sdo.parent = root
    # ---- wheels (spin), cranks + pedals (spin slowly / coast) ----
    wr = empty('wheel_r', root, REAR); wf = empty('wheel_f_pivot', steer, FRONT - HT_B)
    w1 = _wheel('bike_wheel_r'); w1.parent = wr
    w2 = _wheel('bike_wheel_f'); w2.parent = wf
    crank = empty('crank', root, BB)
    cb = bmesh.new()
    ring_ = lathe([(-0.004, 0.095), (0.004, 0.095)], 40)                                            # chainring
    me = bpy.data.meshes.new('c'); ring_.to_mesh(me); ring_.free(); me.transform(Matrix.Translation((0, -0.055, 0))); cb.from_mesh(me)
    PED = []
    for side, a in ((1, 0.0), (-1, math.pi)):
        tip = Vector((math.cos(a) * 0.165, side * 0.085, math.sin(a) * 0.165))
        _tube(cb, [Vector((0, side * 0.05, 0)), tip], 0.010, 8, 0)
        _box(cb, tip + Vector((0, side * 0.055, 0)), (0.085, 0.10, 0.022), 1)
        PED.append(tip + Vector((0, side * 0.055, 0)))
    co = _obj('bike_crank', cb, [B_CHROME, B_TYRE], 0.0024); co.parent = crank
    return dict(root=root, wheel_f=wf, wheel_r=wr, crank=crank, steer=steer, grips=GRIPS, pedals=[BB + p for p in PED], saddle=SADDLE)
