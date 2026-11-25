"""Render Sam look-test + composite + turnaround from sam_toon.blend.
blender -b -P render_sam.py -- [quick]"""
import bpy, sys, math, time, os
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = 'C:/Users/cross/Downloads/xc/anime-5oclock/toon3d/'
QUICK = 'quick' in sys.argv
bpy.ops.wm.open_mainfile(filepath=ROOT + 'sam_toon.blend')
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
OUT = ROOT if not QUICK else ROOT + '_quick/'
os.makedirs(OUT, exist_ok=True)
times = {}

def hexrgb(h): h = h.lstrip('#'); return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]

def obj_pts(names):
    pts = []
    for n in names:
        o = bpy.data.objects[n]; ev = o.evaluated_get(dg); me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in list(me.vertices)[::3]]; ev.to_mesh_clear()
    return pts

cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam

def look(cam, target):
    d = (Vector(target) - cam.location)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def render(path, w, h, samples):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 50 if QUICK else 100
    sc.eevee.taa_render_samples = 16 if QUICK else samples
    sc.render.filepath = path
    t = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t
    times[os.path.basename(path)] = dt; print('RENDER', path, f'{dt:.1f}s'); return dt

def load_px(path):
    im = bpy.data.images.load(path); w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4); bpy.data.images.remove(im); return a

def save_px(path, a):
    h, w = a.shape[:2]; im = bpy.data.images.new('tmp', w, h, alpha=True)
    im.pixels = a.ravel().tolist() if a.size < 4e6 else a.ravel()
    im.filepath_raw = path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)

def over(fg, bg_rgb):
    out = fg.copy(); a = fg[..., 3:4]
    out[..., :3] = fg[..., :3] * a + np.array(bg_rgb, np.float32) * (1 - a); out[..., 3] = 1; return out

# ---------------------------------------------------------------- look-test camera (3/4, head faces screen-left)
head = bpy.data.objects['Sam_Rig'].pose.bones['J_Bip_C_Head']
hc = bpy.data.objects['Sam_Rig'].matrix_world @ head.head + Vector((0, 0, 0.07))
cam_d.lens = 85; cam_d.sensor_fit = 'HORIZONTAL'; cam_d.sensor_width = 36
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
az = math.radians(38); el = math.radians(-2)
dirv = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
hair_pts = obj_pts(['Hair'])
dist = 1.2; tgt_drop = 0.0
for it in range(6):
    target = hc + Vector((0, 0, -tgt_drop))
    cam.location = target + dirv * dist; look(cam, target); bpy.context.view_layer.update()
    uv = [world_to_camera_view(sc, cam, p) for p in hair_pts]
    xs = [u.x for u in uv]; ys = [u.y for u in uv]
    frac = max(xs) - min(xs); cy = (max(ys) + min(ys)) / 2
    print('fit', it, f'frac={frac:.3f} cy={cy:.3f} dist={dist:.3f}')
    dist *= frac / 0.45
    tgt_drop += (0.66 - cy) * dist * 36 / 85 * 1920 / 1080  # put head centre ~1/3 from the top
cam_d.dof.use_dof = False
render(OUT + 'sam_toon_looktest.png', 1080, 1920, 64)
fg = load_px(OUT + 'sam_toon_looktest.png')
bgp = 'C:/Users/cross/Downloads/xc/anime-5oclock/ep1v1/bg_003.png'
if os.path.exists(bgp):
    bg = load_px(bgp)
    comp = fg.copy(); a = fg[..., 3:4]
    comp[..., :3] = fg[..., :3] * a + bg[..., :3] * (1 - a); comp[..., 3] = 1
    save_px(OUT + 'sam_toon_looktest_comp.png', comp)
else:
    # flat warm #e7b99a with a very soft lighter glow behind the head (stands in for a blurred bg)
    h, w = fg.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.exp(-(((xx - w * 0.42) / (w * 0.7)) ** 2 + ((yy - h * 0.68) / (h * 0.45)) ** 2))[..., None]
    base = np.array(hexrgb('#e7b99a'), np.float32); glow = np.array(hexrgb('#f3d2b4'), np.float32)
    bg = base * (1 - g * 0.6) + glow * g * 0.6
    comp = fg.copy(); a = fg[..., 3:4]; comp[..., :3] = fg[..., :3] * a + bg * (1 - a); comp[..., 3] = 1
    save_px(OUT + 'sam_toon_looktest_comp.png', comp)

# ---------------------------------------------------------------- turnaround (neutral head), ortho full body
rig = bpy.data.objects['Sam_Rig']
for n in ('J_Bip_C_Neck', 'J_Bip_C_Head', 'J_Adj_L_FaceEye', 'J_Adj_R_FaceEye'):
    pb = rig.pose.bones[n]; pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
bpy.context.view_layer.update()
cam_d.type = 'ORTHO'; cam_d.ortho_scale = 2.05; cam_d.sensor_fit = 'VERTICAL'
panels = []
sun = bpy.data.objects['Sun_GoldenHour']; sun_rot = sun.rotation_euler.copy()
for k, ang in enumerate((0, 45, 90, 180)):
    a = math.radians(ang)
    cam.location = (4 * math.sin(a), -4 * math.cos(a), 0.97); cam.rotation_euler = (math.radians(90), 0, a)
    sun.rotation_euler = sun_rot.copy(); sun.rotation_euler.z += a - math.radians(38)  # same light relative to camera
    p = OUT + f'_turn_{k}.png'; render(p, 700, 1500, 32); panels.append(load_px(p))
sun.rotation_euler = sun_rot
strip = np.concatenate(panels, axis=1)
strip = over(strip, hexrgb('#efe3d8'))
save_px(OUT + 'sam_toon_turnaround.png', strip)
for k in range(4): os.remove(OUT + f'_turn_{k}.png')
print('TIMES', times)
