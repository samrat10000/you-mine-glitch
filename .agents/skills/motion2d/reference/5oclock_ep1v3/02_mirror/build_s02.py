"""5 O'CLOCK Ep1 v3 - shot 02 "The mirror" (3 s, 72 f @24). Built to SHOT_RULES (shot 01 v4).
Day cel layer: orange curve mirror on its pole at a crossroads, block wall, utility pole, wires, a leaf blowing across.
The mirror glass renders as pure key green; comp_s02.py replaces it with the painted NIGHT street (fisheye).
usage: python3 build_s02.py <outdir> <scale> [frames|all]"""
import os, sys
OUT = sys.argv[1]; SCALE = float(sys.argv[2]); FR = sys.argv[3] if len(sys.argv) > 3 else 'all'
os.makedirs(OUT, exist_ok=True)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'toonlib_v4.py')).read())
from bpy_extras.object_utils import world_to_camera_view

SUN = Vector(SUNV)                     # direction toward the low sun (same as shot 01)
FWD = Vector((SUN.x, SUN.y, 0)).normalized()          # we look roughly into the sun
SIDE = FWD.cross(Vector((0, 0, 1))).normalized()      # screen-right

ORANGE = toon('mirror_orange', (0.56, 0.21, 0.12), (0.93, 0.36, 0.16), (1.0, 0.78, 0.50))
KEY = bpy.data.materials.new('glassuv'); KEY.use_nodes = True
_n = KEY.node_tree.nodes; _l = KEY.node_tree.links
for _x in list(_n): _n.remove(_x)
_o = _n.new('ShaderNodeOutputMaterial'); _tc = _n.new('ShaderNodeTexCoord'); _sp = _n.new('ShaderNodeSeparateXYZ')
_l.new(_tc.outputs['Object'], _sp.inputs[0])
_ma = _n.new('ShaderNodeMath'); _ma.operation = 'MULTIPLY_ADD'; _ma.inputs[1].default_value = 1 / 0.8; _ma.inputs[2].default_value = 0.5
_mb = _n.new('ShaderNodeMath'); _mb.operation = 'MULTIPLY_ADD'; _mb.inputs[1].default_value = 1 / 0.8; _mb.inputs[2].default_value = 0.5
_l.new(_sp.outputs['X'], _ma.inputs[0]); _l.new(_sp.outputs['Z'], _mb.inputs[0])
_cb = _n.new('ShaderNodeCombineXYZ'); _l.new(_ma.outputs[0], _cb.inputs[0]); _l.new(_mb.outputs[0], _cb.inputs[1]); _cb.inputs[2].default_value = 1.0
_e = _n.new('ShaderNodeEmission'); _l.new(_cb.outputs[0], _e.inputs[0]); _l.new(_e.outputs[0], _o.inputs[0])
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.color_depth = '16'
WHITE = toon('plate', (0.45, 0.43, 0.52), (0.92, 0.90, 0.86), (1.0, 0.9, 0.7))
REDT = emis('redtext', (0.55, 0.05, 0.04))
GREENT = emis('greentext', (0.03, 0.22, 0.10))
WALL = toon('blockwall', (0.30, 0.28, 0.36), (0.55, 0.52, 0.54))
LEAFM = toon('leaf', (0.74, 0.24, 0.07), (0.97, 0.52, 0.16), (1.0, 0.80, 0.45))   # backlit leaves glow (translucent)
WIRE = emis('wire', (0.08, 0.05, 0.07))


def place(ob, fwd, side, up):
    ob.location = FWD * fwd + SIDE * side + Vector((0, 0, up))


# --- the curve mirror (カーブミラー): round convex glass, orange rim + hood, orange pole, sign plate ---
MPOS = FWD * 3.0 + SIDE * 0.0 + Vector((0, 0, 2.55))
R = 0.40
mroot = empty('mroot'); mroot.location = MPOS
mroot.rotation_mode = 'QUATERNION'
# glass faces the camera (-FWD), tilted down a little toward the road
facing = (-FWD + Vector((0, 0, -0.18))).normalized()
mroot.rotation_quaternion = Vector((0, -1, 0)).rotation_difference(facing)
# glass: shallow dome along local -Y
g = bmesh.new(); rings = []
for i in range(0, 13):
    rr = R * i / 12
    y = -0.045 * (1 - (rr / R) ** 2)
    rings.append([g.verts.new((rr * math.cos(2 * math.pi * k / 64), y, rr * math.sin(2 * math.pi * k / 64))) for k in range(64)])
for a, b in zip(rings, rings[1:]):
    for k in range(64):
        g.faces.new((a[k], a[(k + 1) % 64], b[(k + 1) % 64], b[k]))
bmesh.ops.remove_doubles(g, verts=g.verts, dist=1e-6)
glass = mesh_obj('glass', g, KEY, mroot, 0)
# rim: a thick orange ring with a rolled lip
rim = bmesh.new()
bmesh.ops.create_circle(rim, segments=72, radius=1)
rim.free()
tor = bpy.data.meshes.new('rim')
import bmesh as _bm
t = _bm.new()
for k in range(72):
    pass
t.free()
rb = lathe([(-0.05, R + 0.00), (-0.06, R + 0.03), (-0.035, R + 0.055), (0.03, R + 0.055), (0.05, R + 0.03), (0.05, R - 0.005)], seg=72, cap_back=False)
bmesh.ops.rotate(rb, verts=rb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(0, 3, 'X'))
rimo = mesh_obj('rim', rb, ORANGE, mroot, 0.006)
# back shell
bs = lathe([(0.05, 0.0), (0.05, R + 0.03), (0.09, R - 0.06), (0.11, 0.0)], seg=64)
mesh_obj('back', bs, ORANGE, mroot, 0.005)
# hood (visor) over the top half
hood = bmesh.new(); top = []; bot = []
for k in range(0, 37):
    a = math.pi * k / 36
    x, z = math.cos(a) * (R + 0.06), math.sin(a) * (R + 0.06)
    top.append(hood.verts.new((x, -0.05, z))); bot.append(hood.verts.new((x * 0.97, -0.17, z * 0.93 + 0.02)))
for k in range(36):
    hood.faces.new((top[k], top[k + 1], bot[k + 1], bot[k]))
ho = mesh_obj('hood', hood, ORANGE, mroot, 0.005)
sm = ho.modifiers.new('th', 'SOLIDIFY'); sm.thickness = 0.008; ho.modifiers.move(len(ho.modifiers) - 1, 0)
# pole: orange steel pipe from the ground, bent cantilever to the mirror back
pole_x = MPOS + FWD * 0.13 + Vector((0, 0, -2.55))
pb = lathe([(0, 0.038), (2.62, 0.038), (2.64, 0)])
bmesh.ops.rotate(pb, verts=pb.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
pole = mesh_obj('pole', pb, ORANGE, None, 0.004); pole.location = pole_x
# black/yellow reflector band on the pole
band = lathe([(1.05, 0.040), (1.25, 0.040)], cap_back=False)
bmesh.ops.rotate(band, verts=band.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
bo = mesh_obj('band', band, toon('band', (0.45, 0.38, 0.12), (0.95, 0.82, 0.25), (1, 0.9, 0.6)), None, 0.003); bo.location = pole_x
# sign plate under the mirror: 交通安全 (traffic safety), white with red text
plate = bmesh.new(); bmesh.ops.create_cube(plate, size=1)
bmesh.ops.scale(plate, vec=(0.22, 0.012, 0.075), verts=plate.verts)
po = mesh_obj('plate', plate, WHITE, None, 0.004)
po.location = pole_x + Vector((0, 0, 2.02)) - FWD * 0.05
po.rotation_euler = (0, 0, math.atan2(FWD.y, FWD.x) - math.pi / 2)
cu = bpy.data.curves.new('txt', 'FONT')
try:
    cu.font = bpy.data.fonts.load('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf')
except Exception:
    pass
cu.body = '交通安全'; cu.size = 0.07; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = 0.001
to = bpy.data.objects.new('txt', cu); sc.collection.objects.link(to); cu.materials.append(REDT)
to.location = po.location - FWD * 0.008
to.rotation_euler = (math.radians(90), 0, math.atan2(FWD.y, FWD.x) - math.pi / 2)

# --- block wall (ブロック塀) running along the right of the street ---
wl = bmesh.new(); bmesh.ops.create_cube(wl, size=1)
bmesh.ops.scale(wl, vec=(0.15, 9.0, 1.4), verts=wl.verts)
wo = mesh_obj('wall', wl, WALL, None, 0.006)
wo.location = FWD * 3.6 - SIDE * 1.15 + Vector((0, 0, 0.7))
wo.rotation_euler = (0, 0, math.atan2(FWD.y, FWD.x) - math.pi / 2)
# block joints as thin ink strips on the street-facing side
for r in range(1, 7):
    j = bmesh.new(); bmesh.ops.create_cube(j, size=1); bmesh.ops.scale(j, vec=(0.002, 9.0, 0.006), verts=j.verts)
    jo = mesh_obj('joint', j, emis('jnt', (0.12, 0.08, 0.12)), None, 0)
    jo.location = wo.location + SIDE * 0.077 + Vector((0, 0, -0.7 + r * 0.2))
    jo.rotation_euler = wo.rotation_euler
gr = bmesh.new(); bmesh.ops.create_grid(gr, x_segments=1, y_segments=1, size=30)
mesh_obj('road', gr, toon('road', (0.20, 0.17, 0.24), (0.36, 0.32, 0.38)), None, 0)
# --- concrete utility pole on the left + wires ---
up = lathe([(0, 0.17), (9.0, 0.13), (9.02, 0)])
bmesh.ops.rotate(up, verts=up.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
uo = mesh_obj('upole', up, CONC, None, 0.007); uo.location = FWD * 7.5 - SIDE * 3.2
for i in range(3):
    c = bpy.data.curves.new('w%d' % i, 'CURVE'); c.dimensions = '3D'; c.bevel_depth = 0.008
    sp = c.splines.new('POLY'); n = 30; sp.points.add(n - 1)
    a0 = uo.location + Vector((0, 0, 7.6 + 0.35 * i)); a1 = a0 + SIDE * 9 + FWD * 4 + Vector((0, 0, -0.4))
    for k in range(n):
        tt = k / (n - 1); q = a0.lerp(a1, tt); q.z -= 0.9 * 4 * tt * (1 - tt)
        sp.points[k].co = (*q, 1)
    co = bpy.data.objects.new('w%d' % i, c); sc.collection.objects.link(co); c.materials.append(WIRE)
# --- a maple leaf that blows across the frame (the mirror shows it going the other way) ---
lf = bmesh.new(); pts = []
# real maple (momiji) outline: 7 palmate lobes, serrated edge, notch at the stem, slight cup
NV = 140
for k in range(NV):
    th = 2 * math.pi * k / NV                           # 0 = stem (down), lobes fan out above
    ph = (th - math.pi) / math.pi                        # -1..1, 0 = top lobe
    tri = ((ph + 1) * 3.5) % 1.0
    lobe = (1 - abs(tri * 2 - 1)) ** 0.75                # 7 pointed lobes
    env = 0.35 + 0.65 * math.cos(ph * math.pi / 2.25) ** 0.7
    serr = 0.04 * abs(math.sin(th * 44))
    rr = 0.06 * env * (0.58 + 0.42 * lobe) * (1 - serr)
    if abs(ph) > 0.93: rr *= 0.35                        # stem notch
    x, y = rr * math.sin(th), -rr * math.cos(th)
    pts.append(lf.verts.new((x, y, 3.0 * (x * x + y * y))))
ctr = lf.verts.new((0, 0.004, 0))
for i in range(NV):
    lf.faces.new((ctr, pts[i], pts[(i + 1) % NV]))
st = [lf.verts.new(v) for v in ((-0.0025, -0.012, 0), (0.0025, -0.012, 0), (0.0018, -0.05, 0.002), (-0.0018, -0.05, 0.002))]
lf.faces.new(st)
leaf = mesh_obj('leaf', lf, LEAFM, None, 0.002)
sm = leaf.modifiers.new('th', 'SOLIDIFY'); sm.thickness = 0.002; leaf.modifiers.move(len(leaf.modifiers) - 1, 0)
leaf.rotation_mode = 'XYZ'

# --- camera: low, slightly below the mirror, looking up at it against the sky ---
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 38; cam_d.sensor_fit = 'VERTICAL'; cam_d.sensor_height = 36
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = empty('tgt'); tgt.location = MPOS + SIDE * 0.13 + Vector((0, 0, -0.75))
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
CAM0 = MPOS - FWD * 2.3 + SIDE * 0.6 + Vector((0, 0, -1.45))
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 5.0; sun.data.color = (1.0, 0.78, 0.55)
sun.rotation_euler = (-SUN).to_track_quat('-Z', 'Y').to_euler()
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); sc.collection.objects.link(fill)
fill.data.energy = 0.35; fill.data.color = (0.55, 0.55, 0.85)
fill.rotation_euler = (Vector((0.4, 1.0, 0.35))).to_track_quat('-Z', 'Y').to_euler()


def ease(t):
    t = max(0, min(1, t)); return t * t * (3 - 2 * t)


import json
META = {}


def pose(f):
    fs = f - ((f - 1) % 2)                          # props on twos, camera on ones
    k = (f - 1) / 71
    cam.location = CAM0.lerp(MPOS, 0.06 * ease(k)) + Vector((0.006 * math.sin(f * 0.07), 0, 0.004 * math.sin(f * 0.05)))
    # leaf: enters left at f14, tumbles across in front of the mirror pole, exits right ~f58
    u = (fs - 14) / 44
    leaf.hide_render = not (0 <= u <= 1)
    base = MPOS - FWD * 0.95 + Vector((0, 0, -0.95))
    leaf.location = base + SIDE * (-0.75 + 1.5 * u) + Vector((0, 0, 0.18 * math.sin(u * 6.0) - 0.25 * u))
    leaf.rotation_euler = (1.2 + 0.5 * math.sin(fs * 0.21), fs * 0.16 + 0.6, 0.4 * math.sin(fs * 0.13) + fs * 0.09)


frames = range(1, 73) if FR == 'all' else [int(x) for x in FR.split(',')]
for f in frames:
    sc.frame_set(f); pose(f)
    bpy.context.view_layer.update()
    # where the mirror sits on screen (for the fisheye insert) and the sun
    c = world_to_camera_view(sc, cam, MPOS)
    e = world_to_camera_view(sc, cam, MPOS + SIDE * R)
    s_ = world_to_camera_view(sc, cam, cam.location + SUN * 100)
    lv = world_to_camera_view(sc, cam, leaf.location)
    META[f] = dict(mx=c.x, my=1 - c.y, mr=abs(e.x - c.x), sx=s_.x, sy=1 - s_.y, leaf=[lv.x, 1 - lv.y, not leaf.hide_render])
    sc.render.filepath = os.path.join(OUT, 'cel_%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)
json.dump(META, open(os.path.join(OUT, 'meta.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 's02.blend'))
print('SUN', META[frames[0]]['sx'], META[frames[0]]['sy'], 'MIRROR', META[frames[0]])
