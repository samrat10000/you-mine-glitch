"""5 O'CLOCK Ep1 v3 - shot 01 "The speaker" (3 s, 72 f @24).
Cel layer: Blender EEVEE toon (Shader-to-RGB ramp) + inverted-hull ink lines, transparent film.
BG layer: painted sunset sky (paint_bg.py). Composite + post in comp_s01.py.
Character/prop animation on twos (pose sampled at odd frames), camera on ones.
usage: python3 build_s01.py <outdir> <scale 0.25..1> [frames e.g. 1,24,40 or all]"""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix, Euler

OUT = sys.argv[1]; SCALE = float(sys.argv[2]); FR = sys.argv[3] if len(sys.argv) > 3 else 'all'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = int(SCALE * 100)
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
try:
    sc.eevee.taa_render_samples = 16
except Exception:
    pass
W = bpy.data.worlds.new('w'); sc.world = W
W.use_nodes = True
bg = W.node_tree.nodes.get('Background')
bg.inputs[0].default_value = (0.32, 0.25, 0.42, 1); bg.inputs[1].default_value = 0.12

# ---------------- materials ----------------
SUNV = tuple(Vector((-0.62, 1.0, 0.24)).normalized())
def toon(name, shadow, lit, rim=None, tex=None, rimfacing=0.40):
    """2-tone cel ramp (+ optional 3rd bright rim tone). tex: callable(nt, ramp_in) -> socket overriding colours"""
    lin = lambda c: tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
    shadow, lit = lin(shadow), lin(lit); rim = lin(rim) if rim else None
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N): N.remove(n)
    out = N.new('ShaderNodeOutputMaterial')
    dif = N.new('ShaderNodeBsdfDiffuse')
    s2r = N.new('ShaderNodeShaderToRGB')
    bw = N.new('ShaderNodeRGBToBW')
    L.new(dif.outputs[0], s2r.inputs[0]); L.new(s2r.outputs[0], bw.inputs[0])
    half = N.new('ShaderNodeMath'); half.operation = 'MULTIPLY'; half.inputs[1].default_value = 0.5
    L.new(bw.outputs[0], half.inputs[0])
    ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
    e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (*shadow, 1)
    e[1].position = 0.035; e[1].color = (*lit, 1)
    if rim:
        x = e.new(0.075); x.color = (*rim, 1)
    L.new(half.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if tex:
        col = tex(nt, ramp)
    if rim:
        # crisp warm rim on silhouette edges that face the low sun (classic backlit anime rim)
        geo = N.new('ShaderNodeNewGeometry')
        lw = N.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = 0.5
        dt = N.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'; dt.inputs[1].default_value = SUNV
        L.new(geo.outputs['Normal'], dt.inputs[0])
        g1 = N.new('ShaderNodeMath'); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = rimfacing
        L.new(lw.outputs['Facing'], g1.inputs[0])
        g2 = N.new('ShaderNodeMath'); g2.operation = 'GREATER_THAN'; g2.inputs[1].default_value = -0.15
        L.new(dt.outputs['Value'], g2.inputs[0])
        mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'
        L.new(g1.outputs[0], mm.inputs[0]); L.new(g2.outputs[0], mm.inputs[1])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        L.new(mm.outputs[0], mx.inputs[0]); L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (*rim, 1)
        col = mx.outputs[2]
    em = N.new('ShaderNodeEmission'); L.new(col, em.inputs[0]); em.inputs[1].default_value = 1.0
    L.new(em.outputs[0], out.inputs[0])
    return m


def rusty(nt, ramp):
    """paint -> rust streaks: multiply the cel colour by a rust mask (streaks run along local Z = down the horn)"""
    N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (9, 9, 1.6)
    L.new(tc.outputs['Object'], mp.inputs[0])
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6
    L.new(mp.outputs[0], nz.inputs[0])
    st = N.new('ShaderNodeValToRGB'); st.color_ramp.interpolation = 'CONSTANT'
    st.color_ramp.elements[0].position = 0; st.color_ramp.elements[0].color = (1, 1, 1, 1)
    st.color_ramp.elements[1].position = 0.62; st.color_ramp.elements[1].color = (0.62, 0.36, 0.24, 1)
    q = st.color_ramp.elements.new(0.7); q.color = (0.45, 0.24, 0.17, 1)
    L.new(nz.outputs[0], st.inputs[0])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    L.new(ramp.outputs[0], mx.inputs[6]); L.new(st.outputs[0], mx.inputs[7])
    return mx.outputs[2]


def emis(name, c, s=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes
    for n in list(N): N.remove(n)
    o = N.new('ShaderNodeOutputMaterial'); e = N.new('ShaderNodeEmission')
    e.inputs[0].default_value = (*c, 1); e.inputs[1].default_value = s
    m.node_tree.links.new(e.outputs[0], o.inputs[0]); return m


INKC = (0.10, 0.06, 0.08)
ink = emis('ink', INKC)
ink.use_backface_culling = True
PAINT = toon('paint', (0.27, 0.25, 0.37), (0.62, 0.66, 0.60), (1.0, 0.80, 0.55), rusty)
INSIDE = toon('inside', (0.07, 0.06, 0.08), (0.20, 0.17, 0.18), (0.55, 0.40, 0.32))
CONC = toon('concrete', (0.27, 0.25, 0.33), (0.55, 0.52, 0.55), (1.0, 0.78, 0.55))
STEEL = toon('steel', (0.20, 0.19, 0.25), (0.42, 0.42, 0.47), (1.0, 0.82, 0.6))
CROW = toon('crow', (0.07, 0.07, 0.11), (0.20, 0.21, 0.32), (1.0, 0.66, 0.45))
CROWW = toon('croww', (0.07, 0.07, 0.11), (0.20, 0.21, 0.32))
BEAK = toon('beak', (0.03, 0.03, 0.04), (0.10, 0.10, 0.13), (0.9, 0.7, 0.5))
EYEW = emis('eyehi', (1, 0.95, 0.85), 1.0)
EYE = emis('eye', (0.02, 0.02, 0.03))
WIRE = emis('wire', (0.08, 0.05, 0.07))


def outline(ob, t=0.006):
    ob.data.materials.append(ink)
    sm = ob.modifiers.new('ol', 'SOLIDIFY'); sm.thickness = -t if False else t
    sm.offset = 1; sm.use_flip_normals = True; sm.material_offset = len(ob.data.materials) - 1
    sm.use_rim = False


def mesh_obj(name, bm, mat, parent=None, line=0.006):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    me.materials.append(mat)
    if line: outline(ob, line)
    if parent: ob.parent = parent
    return ob


def lathe(prof, seg=56, cap_back=True):
    """prof: [(y, r)] along +Y; returns bmesh"""
    bm = bmesh.new(); rings = []
    for y, r in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / seg), y, r * math.sin(2 * math.pi * i / seg))) for i in range(seg)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_back:
        bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def ellipsoid(sx, sy, sz, seg=24, ring=14):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    return bm


def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.parent = parent; e.location = loc; e.empty_display_size = .02
    return e


# ---------------- the loudspeaker cluster on a concrete pole ----------------
L_H, R0, R1 = 0.72, 0.045, 0.30
K = math.log(R1 / R0) / 0.62


def horn_r(y):
    return R0 * math.exp(K * y) if y < 0.62 else R1 + (y - 0.62) * 0.9


def horn(name, parent):
    prof = [(-0.20, 0.0), (-0.20, 0.085), (-0.06, 0.092), (-0.03, 0.06), (0.0, R0)]
    prof += [(0.62 * i / 22, horn_r(0.62 * i / 22)) for i in range(1, 23)]
    prof += [(0.64, R1 + 0.012), (0.66, R1 + 0.02), (0.675, R1 + 0.016)]
    bm = lathe(prof)
    ob = mesh_obj(name, bm, PAINT, parent, 0.007)
    # dark throat seen through the mouth
    ins = lathe([(0.05, 0.0), (0.05, horn_r(0.05) * .95)] + [(0.62 * i / 16, horn_r(0.62 * i / 16) * .97) for i in range(2, 17)], cap_back=True)
    bmesh.ops.reverse_faces(ins, faces=ins.faces)
    io = mesh_obj(name + '_in', ins, INSIDE, ob, 0)
    # clamp band + bolts
    band = lathe([(0.10, horn_r(0.10) + 0.006), (0.13, horn_r(0.13) + 0.008)], cap_back=False)
    mesh_obj(name + '_band', band, STEEL, ob, 0.004)
    return ob


pole_root = empty('pole_root', loc=(0.30, 0.42, -2.0))
pb = lathe([(0, 0.065), (2.42, 0.062), (2.44, 0.075), (2.47, 0.075), (2.48, 0.0)])
bmesh.ops.rotate(pb, verts=pb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
pole = mesh_obj('pole', pb, STEEL, pole_root, 0.005)
# step bolts on the pole (Japanese utility-pole footholds)
for i in range(0):
    z = 1.3 + i * 0.42; a = math.radians(200 + 180 * (i % 2))
    b = lathe([(0, 0.012), (0.2, 0.012), (0.21, 0)])
    bmesh.ops.rotate(b, verts=b.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(a + math.pi / 2, 3, 'Z'))
    bmesh.ops.translate(b, verts=b.verts, vec=(0.15 * math.cos(a), 0.15 * math.sin(a), z))
    mesh_obj('bolt%d' % i, b, STEEL, pole_root, 0.003)

# bracket head: the horns hang off a steel cross-arm; this empty is the wobble pivot
arm = empty('arm', pole_root, (0, 0, 2.30))
bar = ellipsoid(0.45, 0.025, 0.025, 12, 6)
mesh_obj('crossbar', bar, STEEL, arm, 0.004)
DIR_A = Vector((-0.50, -1.0, 0.10)).normalized()
DIR_B = Vector((0.95, -0.15, 0.04)).normalized()


def aim(ob, d):
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(d)


hA = horn('hornA', arm); hA.location = (-0.16, -0.10, 0.02); aim(hA, DIR_A)
hB = horn('hornB', arm); hB.location = (0.26, -0.12, -0.02); aim(hB, DIR_B)
# cables from the driver units down the pole
for i, (x0, y0) in enumerate([(-0.33, -0.06), (0.22, -0.06)]):
    cu = bpy.data.curves.new('cab%d' % i, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.007
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
    p0, p1 = sp.bezier_points
    p0.co = (x0, y0, 0.0); p0.handle_left = p0.co; p0.handle_right = (x0 * .5, y0 - 0.15, -0.20)
    p1.co = (0.0, -0.17, -0.55); p1.handle_left = (0.0, -0.17, -0.25); p1.handle_right = p1.co
    co = bpy.data.objects.new('cab%d' % i, cu); sc.collection.objects.link(co); co.parent = arm
    cu.materials.append(WIRE)
# overhead power lines crossing the frame (catenary), far behind
for i in range(3):
    cu = bpy.data.curves.new('pl%d' % i, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.010
    sp = cu.splines.new('POLY'); n = 30; sp.points.add(n - 1)
    for k in range(n):
        t = k / (n - 1); x = -4 + 8 * t
        sp.points[k].co = (x, 3.5 + i * 0.25, 1.9 + i * 0.26 - 0.45 * 4 * t * (1 - t) + 0.9 * t, 1)
    co = bpy.data.objects.new('pl%d' % i, cu); sc.collection.objects.link(co); cu.materials.append(WIRE)

# ---------------- the crow: artist-made jungle-crow model (Teh_Bucket "Raven", CC0) ----------------
CROW_GLB = os.environ.get('CROW_GLB', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crow.glb'))
crow = empty('crow')
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=CROW_GLB)
for o in set(bpy.data.objects) - _before:
    if o.name not in sc.collection.objects and not o.users_collection:
        sc.collection.objects.link(o)
croot = bpy.data.objects['root']; croot.parent = crow
croot.rotation_mode = 'XYZ'; croot.rotation_euler = (0, 0, math.radians(-90))   # model faces -Y -> our +X
bpy.data.objects['Icosphere'].hide_render = True
CARM = bpy.data.objects['raven_armature']; CMESH = bpy.data.objects['raven_mesh']
CMESH.data.materials.clear(); CMESH.data.materials.append(toon('crowm', (0.07, 0.07, 0.11), (0.20, 0.21, 0.32), (1.0, 0.66, 0.45), rimfacing=0.72))
for p_ in CMESH.data.polygons: p_.use_smooth = True
CMESH.modifiers.new('subd', 'SUBSURF').levels = 2
CMESH.modifiers['subd'].render_levels = 2
outline(CMESH, 0.0035)
CARM.animation_data.action = None
POSES = {}


def capture(act, fr):
    key = (act, fr)
    if key not in POSES:
        ad = CARM.animation_data
        ad.action = bpy.data.actions[act]
        try:
            if ad.action.slots and ad.action_slot is None:
                ad.action_slot = ad.action.slots[0]
        except AttributeError:
            pass
        sc.frame_set(int(fr))
        POSES[key] = {b.name: (b.location.copy(), b.rotation_quaternion.copy(), b.scale.copy()) for b in CARM.pose.bones}
        CARM.animation_data.action = None
    return POSES[key]


def blend(pa, pb_, w, bones=None):
    out = {}
    for n in pa:
        ww = w if (bones is None or n in bones) else 0.0
        la, qa, sa = pa[n]; lb, qb, sb = pb_[n]
        out[n] = (la.lerp(lb, ww), qa.slerp(qb, ww), sa.lerp(sb, ww))
    return out


def apply_pose(P):
    for b in CARM.pose.bones:
        l, q, s_ = P[b.name]
        b.location = l; b.rotation_quaternion = q; b.scale = s_


# pick the flare drawing: the fly frame with the wings highest
_best = (-9, 0)
for fr in range(0, 34):
    apply_pose(capture('fly', fr)); bpy.context.view_layer.update()
    z = (CARM.pose.bones['Bone.001_L.005'].tail.z + CARM.pose.bones['Bone.001_R.005'].tail.z)
    _best = max(_best, (z, fr))
FLARE = _best[1]
apply_pose(capture('stand', 0)); bpy.context.view_layer.update()
LEGS_B = {n for n in POSES[('stand', 0)] if n.startswith(('leg', 'toe'))}
TOES = [b for b in CARM.pose.bones if b.name.startswith('toe')]
# anime eye glint: a tiny bright bead parented to the head bone
for sx in (1, -1):
    hb = CARM.pose.bones['Bone']
    e = ellipsoid(0.0045, 0.0045, 0.0045, 10, 8)
    eo = mesh_obj('glint%d' % sx, e, EYEW, None, 0)
    eo.parent = CARM; eo.parent_type = 'BONE'; eo.parent_bone = 'Bone'
    bpy.context.view_layer.update()
    eo.matrix_parent_inverse = (CARM.matrix_world @ hb.matrix @ Matrix.Translation((0, hb.length, 0))).inverted()
    eo.matrix_basis = Matrix.Translation(CARM.matrix_world @ Vector((0.021 * sx, -0.150, 0.279)))

# ---------------- camera ----------------
bpy.context.view_layer.update()
mid = hA.matrix_world @ Vector((0, 0.38, 0))
top = hA.matrix_world @ Vector((0, 0.30, horn_r(0.30) + 0.005))
LAND = top.copy()
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 38; cam_d.sensor_fit = 'VERTICAL'; cam_d.sensor_height = 36
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = empty('tgt'); tgt.location = LAND + Vector((0.02, 0.0, 0.03))
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
CAM0 = LAND + Vector((0.95, -1.35, -0.62))
# lights: low sun behind-right (backlight -> rim), weak cool fill from front-left
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 5.0; sun.data.color = (1.0, 0.78, 0.55); sun.data.angle = math.radians(1)
sun.rotation_euler = (Vector((0.62, -1.0, -0.24))).to_track_quat('-Z', 'Y').to_euler()  # light travels toward the camera
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); sc.collection.objects.link(fill)
fill.data.energy = 0.35; fill.data.color = (0.55, 0.55, 0.85)
fill.rotation_euler = (Vector((0.4, 1.0, 0.35))).to_track_quat('-Z', 'Y').to_euler()


# ---------------- animation (sampled; crow + horn on twos) ----------------
def ease(t):
    t = max(0, min(1, t)); return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def keys(f, ks):
    """piecewise smooth interpolation over [(frame, value)]"""
    if f <= ks[0][0]: return ks[0][1]
    for (f0, v0), (f1, v1) in zip(ks, ks[1:]):
        if f <= f1:
            return lerp(v0, v1, ease((f - f0) / (f1 - f0)))
    return ks[-1][1]


def pose_wing(s, spread, flap, sweep):
    """spread 0 folded..1 open; flap deg (+ up); sweep deg (back)"""
    sh, el, wr, sec, pri = WING[s]
    fold = 1 - spread
    sh.rotation_euler = (math.radians(s * flap), math.radians(-8 * fold), math.radians(s * (-sweep - 78 * fold)))
    el.rotation_euler = (math.radians(s * flap * 0.35), 0, math.radians(s * 150 * fold))
    wr.rotation_euler = (math.radians(s * flap * 0.5), 0, math.radians(s * (-150 * fold + 6 * spread)))
    for k, f in enumerate(sec):
        f.rotation_euler = (0, 0, math.radians(s * (-6 + 2 * k) * spread))
    for k, f in enumerate(pri):
        f.rotation_euler = (math.radians(s * 4 * k * spread), 0, math.radians(s * (-4 + 9 * k * spread - 4 * k * fold)))


def pose(f):
    fs = f - ((f - 1) % 2)          # on twos
    t = fs
    # flight path: from upper-right (off frame) gliding down onto LAND by f22
    start = LAND + Vector((0.95, 0.55, 0.85))
    pa = ease(min(t / 22, 1)) if t < 22 else 1
    p = start.lerp(LAND, 1 - (1 - min(t / 22, 1)) ** 2.2)
    p.z += 0.10 * math.sin(math.pi * min(t / 22, 1))
    dip = 0
    if t >= 22:
        u = t - 22; dip = -0.022 * math.exp(-u / 4) * math.cos(u * 0.9)
    heading = math.atan2(LAND.y - start.y, LAND.x - start.x)
    face = math.atan2(CAM0.y - LAND.y, CAM0.x - LAND.x) - math.radians(70)
    yaw = heading if t < 22 else lerp(heading, face, ease((t - 22) / 10))
    pitch = keys(t, [(1, -2), (12, 4), (17, 42), (21, 34), (25, 10), (30, 12), (34, 10)])
    crow.rotation_euler = (0, math.radians(-pitch), yaw)
    # body pose from the artist's clips: flap -> flare (wings high, spread) -> perched, blended on twos
    fly = capture('fly', int((t * 1.25) % 34))
    flare = capture('fly', FLARE)
    stand = capture('stand', 0)
    if t < 12:
        P = fly
    elif t < 22:
        P = blend(fly, flare, ease((t - 12) / 5))
        P = blend(P, stand, ease((t - 15) / 6), LEGS_B)          # legs swing forward to land
    else:
        P = blend(flare, stand, ease((t - 22) / 9))              # wings fold in ~0.4 s
        if 38 <= t <= 46:                                        # feather ruffle / wing shrug
            P = blend(P, flare, 0.10 * math.sin(math.pi * (t - 38) / 8))
    apply_pose(P)
    # head snaps (birds hold, then snap)
    hy, hp, roll = 0, 0, 0
    if t >= 30: hy, hp = 20, 4
    if t >= 48: hy, hp, roll = 55, 0, -10      # looks at camera
    if t >= 56: hy, hp, roll = 35, 8, 14       # cocks head
    if t >= 64: hy, hp, roll = -40, 28, 0      # speaker clicks: snaps down toward the horn mouth
    bpy.context.view_layer.update()
    hb = CARM.pose.bones['Bone']
    R = (Matrix.Rotation(math.radians(hy), 4, 'Z') @ Matrix.Rotation(math.radians(-hp), 4, 'X') @ Matrix.Rotation(math.radians(roll), 4, 'Y'))
    hb.matrix = Matrix.Translation(hb.head) @ R @ Matrix.Translation(-hb.head) @ hb.matrix
    # feet: perched toes sit exactly on the horn surface (no hovering)
    crow.location = p
    if t >= 21:
        crow.location.z += dip
        bpy.context.view_layer.update()
        mz = min((CARM.matrix_world @ b.tail).z for b in TOES)
        crow.location.z += (LAND.z + 0.004) - mz + (dip if t >= 22 else 0) * 0
    # horn cluster wobble from the landing weight + the click jolt
    w = 0
    if t >= 22:
        u = t - 22; w = 2.2 * math.exp(-u / 9) * math.sin(2 * math.pi * u / 10)
    if t >= 64:
        u = t - 64; w += 0.6 * math.exp(-u / 3) * math.sin(2 * math.pi * u / 4)
    arm.rotation_euler = (math.radians(w), 0, math.radians(w * 0.3))
    # camera on ones: slow push (2.5%) + tiny drift
    k = (f - 1) / 71
    cam.location = CAM0.lerp(mid, 0.035 * ease(k)) + Vector((0.01 * math.sin(f * 0.07), 0, 0.006 * math.sin(f * 0.05)))


frames = range(1, 73) if FR == 'all' else [int(x) for x in FR.split(',')]
for f in frames:
    sc.frame_set(f); pose(f)
    sc.render.filepath = os.path.join(OUT, 'cel_%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 's01.blend'))
# export camera projection for the BG painter (sun screen position)
from bpy_extras.object_utils import world_to_camera_view
sunpos = cam.location + Vector((-0.62, 1.0, 0.24)) * 100
v = world_to_camera_view(sc, cam, sunpos)
print('SUN_SCREEN', v.x, 1 - v.y)
for z in (0.0, 1.0, 2.0, 2.3):
    q = world_to_camera_view(sc, cam, pole_root.matrix_world @ Vector((0, 0, z)))
    print('POLE', z, round(q.x, 2), round(1 - q.y, 2), round(q.z, 2))
