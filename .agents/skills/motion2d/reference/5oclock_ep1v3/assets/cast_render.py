"""Front full-body PNG (512x1024) of every .vrm under <dl>. blender -b --python cast_render.py -- <dl> <outdir>"""
import bpy, sys, os, glob, json, addon_utils
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]; DL, OUT = argv[0], argv[1]; os.makedirs(OUT, exist_ok=True)
if not any('vrm' in m for m in bpy.context.preferences.addons.keys()):
    addon_utils.enable('bl_ext.user_default.vrm', default_set=True)
info = {}
for path in sorted(glob.glob(os.path.join(DL, '*', '*.vrm'))):
    bpy.ops.wm.read_homefile(use_empty=True)
    sc = bpy.context.scene
    assert bpy.ops.import_scene.vrm(filepath=path) == {'FINISHED'}
    meshes = [o for o in sc.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    h = hi.z - lo.z; cx = (lo.x + hi.x) / 2
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = h * 1.08
    cam.location = (cx, lo.y - 5, lo.z + h / 2); cam.rotation_euler = (1.5708, 0, 0)
    for rot, en in (((0.9, 0, 0.4), 3.0), ((1.2, 0, -2.5), 1.2)):
        L = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); L.data.energy = en; L.rotation_euler = rot; sc.collection.objects.link(L)
    sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.55, 0.55, 0.6)
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 512, 1024; sc.render.film_transparent = False
    name = os.path.splitext(os.path.basename(path))[0]
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
    meta = {}
    for o in sc.objects:
        if o.type == 'ARMATURE':
            ext = getattr(o.data, 'vrm_addon_extension', None)
            m0 = getattr(getattr(ext, 'vrm0', None), 'meta', None) if ext else None
            if m0:
                for k in ('title', 'author', 'version', 'license_name', 'allowed_user_name', 'commercial_ussage_name', 'other_license_url'):
                    v = getattr(m0, k, None); meta[k] = str(v) if v is not None else None
    info[name] = dict(height_m=round(h, 3), file=os.path.relpath(path, DL), meta=meta)
    print('CAST', name, round(h, 3), meta, flush=True)
json.dump(info, open(os.path.join(OUT, 'cast_info.json'), 'w'), indent=1, ensure_ascii=False)
