# Praaniva pooja kit box: an ivory board box and a separate lid wrapped in the printed maroon artwork, with gold foil.
# Run with Blender's Python (bpy). Builds the model, exports GLB, and renders preview stills.
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'tex')
OUT = ARGS[0] if ARGS else os.path.join(HERE, 'out')
RENDER = '--no-render' not in ARGS
os.makedirs(OUT, exist_ok=True)

# sizes in metres: a real 30 x 22 x 9.5 cm box of 2.5 mm board
W, D, H, T = 0.260, 0.260, 0.085, 0.0025
GAP = 0.0008                                  # the lid slides over the base with a little air
LW, LD, LH = W + 2 * (T + GAP), D + 2 * (T + GAP), 0.034
TOP = LH                                      # lid's outer top, in the lid's own space

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- materials ----------
def img(name, non_color=False):
    im = bpy.data.images.load(os.path.join(TEX, name), check_existing=True)
    if non_color: im.colorspace_settings.name = 'Non-Color'
    return im

def material(name, col=None, nrm=None, rough=0.8, nrm_strength=1.0, color=None, sheen=0.0, sheen_tint=(1, 1, 1, 1), coat=0.0, mr=None):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; bsdf = nt.nodes.get('Principled BSDF')
    if bsdf is None:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = nt.nodes.get('Material Output') or nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    if col:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(col)
        nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    elif color:
        bsdf.inputs['Base Color'].default_value = color
    if nrm:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(nrm, True)
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nrm_strength
        nt.links.new(t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    if mr:   # glTF layout: G = roughness, B = metallic
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(mr, True)
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(t.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    if sheen:
        bsdf.inputs['Sheen Weight'].default_value = sheen
        bsdf.inputs['Sheen Roughness'].default_value = 0.35
        bsdf.inputs['Sheen Tint'].default_value = sheen_tint
    if coat: bsdf.inputs['Coat Weight'].default_value = coat
    return m

M_WALL = material('Ivory board', 'paper_col.png', 'paper_nrm.png', rough=0.8, nrm_strength=0.3)
M_PAPER = material('Ivory paper', 'paper_col.png', 'paper_nrm.png', rough=0.82, nrm_strength=0.3)
M_LINING = material('Maroon lining', 'lining_col.png', 'lining_nrm.png', rough=0.86, nrm_strength=0.3)
M_LIDTOP = material('Lid artwork (print + gold foil)', 'lidtop_col.png', 'lidtop_nrm.png', nrm_strength=0.6, mr='lidtop_mr.png')

# ---------- helpers ----------
def open_box(w, d, h, open_side):
    """A box of board thickness T with one face open, bevelled like folded card. Returns bmesh."""
    me = bpy.data.meshes.new('tmp')
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    kill = [f for f in bm.faces if (f.normal.z > 0.9 if open_side == 'top' else f.normal.z < -0.9)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('tmp', me); scene.collection.objects.link(ob)
    s = ob.modifiers.new('solid', 'SOLIDIFY'); s.thickness = T; s.offset = -1; s.use_even_offset = True
    b = ob.modifiers.new('bevel', 'BEVEL'); b.width = 0.0011; b.segments = 3; b.limit_method = 'ANGLE'; b.angle_limit = math.radians(40)
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)
    bm = bmesh.new(); bm.from_mesh(me2); bpy.data.meshes.remove(me2)
    return bm

def planar_uv(n, co, scale):
    a = max(range(3), key=lambda i: abs(n[i]))
    if a == 0: return (co.y * scale, co.z * scale)
    if a == 1: return (co.x * scale, co.z * scale)
    return (co.x * scale, co.y * scale)

def finish(bm, name, mats):
    """Smooth the rounded edges, keep flat faces crisp, and make an object."""
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(35): e.smooth = False
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    return ob

# ---------- the base ----------
bm = open_box(W, D, H, 'top')
uv = bm.loops.layers.uv.new('UVMap')
for f in bm.faces:
    c, n = f.calc_center_median(), f.normal
    inner = abs(c.x) < W / 2 - T * .75 and abs(c.y) < D / 2 - T * .75 and c.z > T * .5
    if inner: f.material_index = 2                              # lined inside
    elif n.z < -0.5: f.material_index = 1                       # the underside
    elif c.z > H - T * 1.5 and n.z > 0.3: f.material_index = 1  # the rim
    else: f.material_index = 0                                  # outer walls
    for l in f.loops:
        if f.material_index == 0:
            u = (l.vert.co.y if abs(n.x) >= abs(n.y) else l.vert.co.x) / 0.15
            l[uv].uv = (u, l.vert.co.z / H)
        else:
            l[uv].uv = planar_uv(n, l.vert.co, 1 / 0.2)
base = finish(bm, 'Box_Base', [M_WALL, M_PAPER, M_LINING])

# ---------- the lid ----------
bm = open_box(LW, LD, LH, 'bottom')
uv = bm.loops.layers.uv.new('UVMap')
for f in bm.faces:
    c, n = f.calc_center_median(), f.normal
    inner = abs(c.x) < LW / 2 - T * .75 and abs(c.y) < LD / 2 - T * .75 and c.z < LH - T * .5
    if inner: f.material_index = 2
    elif n.z > 0.9 and c.z > LH - T * .5: f.material_index = 0
    else: f.material_index = 1
    for l in f.loops:
        if f.material_index == 0:
            l[uv].uv = ((l.vert.co.x + LW / 2) / LW, (l.vert.co.y + LD / 2) / LD)
        else:
            l[uv].uv = planar_uv(n, l.vert.co, 1 / 0.2)
lid = finish(bm, 'Box_Lid', [M_LIDTOP, M_PAPER, M_LINING])

# the lid sits closed on the base. Its origin is the middle of its open edge, so lifting it is a plain move up
lid.location = (0, 0, H - (LH - T) + 0.0004)

# ---------- export ----------
def export(path, objs):
    bpy.context.view_layer.update()
    for ob in scene.objects: ob.select_set(False)
    for ob in objs: ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_image_format='JPEG', export_jpeg_quality=90, export_yup=True)
export(os.path.join(OUT, 'praaniva-kit-box.glb'), [base, lid])
export(os.path.join(OUT, 'praaniva-kit-box-base.glb'), [base])
export(os.path.join(OUT, 'praaniva-kit-box-lid.glb'), [lid])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'praaniva-kit-box.blend'))
print('exported')
if not RENDER: sys.exit(0)

# ---------- preview stills: the box on a red cotton cloth, soft window light, a diya's warmth ----------
M_CLOTH = material('Stone ledge (preview only)', color=(0.45, 0.34, 0.25, 1), rough=0.9)
_nt = M_CLOTH.node_tree; _b = _nt.nodes.get('Principled BSDF')
_n = _nt.nodes.new('ShaderNodeTexNoise'); _n.inputs['Scale'].default_value = 18; _n.inputs['Detail'].default_value = 12
_r = _nt.nodes.new('ShaderNodeValToRGB'); _r.color_ramp.elements[0].color = (0.36, 0.26, 0.18, 1); _r.color_ramp.elements[1].color = (0.52, 0.40, 0.29, 1)
_nt.links.new(_n.outputs['Fac'], _r.inputs['Fac']); _nt.links.new(_r.outputs['Color'], _b.inputs['Base Color'])
_bm = _nt.nodes.new('ShaderNodeBump'); _bm.inputs['Strength'].default_value = 0.15
_nt.links.new(_n.outputs['Fac'], _bm.inputs['Height']); _nt.links.new(_bm.outputs['Normal'], _b.inputs['Normal'])
M_WALLBG = material('Warm wall (preview only)', color=(0.50, 0.32, 0.20, 1), rough=0.95)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.5)
uv = bm.loops.layers.uv.new('UVMap')
for f in bm.faces:
    for l in f.loops: l[uv].uv = (l.vert.co.x / 0.05, l.vert.co.y / 0.05)
floor = finish(bm, 'floor', [M_CLOTH])
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.5)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0.55, 0.5))
finish(bm, 'backwall', [M_WALLBG])

world = bpy.data.worlds.new('w'); scene.world = world
try: world.use_nodes = True
except Exception: pass
bg = world.node_tree.nodes.get('Background') or world.node_tree.nodes.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (0.42, 0.30, 0.22, 1); bg.inputs['Strength'].default_value = 0.35
if not bg.outputs['Background'].links:
    o = world.node_tree.nodes.get('World Output') or world.node_tree.nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs['Background'], o.inputs['Surface'])

def light(name, kind, loc, energy, color, size=0.5, target=(0, 0, 0.05)):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.shape = 'DISK'; ld.size = size
    if kind == 'POINT': ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld); scene.collection.objects.link(ob); ob.location = loc
    v = Vector(target) - Vector(loc); ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    return ob
light('key', 'AREA', (-0.75, -0.45, 1.0), 70, (1.0, 0.88, 0.72), size=1.2)
light('fill', 'AREA', (0.9, -0.7, 0.45), 9, (0.95, 0.93, 1.0), size=1.0)
light('rim', 'AREA', (0.35, 0.9, 0.6), 22, (1.0, 0.86, 0.68), size=0.6)
light('diya', 'POINT', (0.27, -0.20, 0.035), 0.6, (1.0, 0.55, 0.2), size=0.01)

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 62; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new('cam', cam_d); scene.collection.objects.link(cam); scene.camera = cam
def aim(loc, target):
    cam.location = loc; v = Vector(target) - Vector(loc)
    cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler(); cam_d.dof.focus_distance = v.length

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'; scene.cycles.samples = int(os.environ.get('SAMPLES', 160))
scene.cycles.use_denoising = True
try: scene.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
scene.render.resolution_x, scene.render.resolution_y = 1600, 1100
scene.render.image_settings.file_format = 'PNG'
try:
    scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'; scene.view_settings.exposure = -0.75
except Exception: pass

shots = [
    ('closed', (-0.40, -0.66, 0.50), (0.0, 0.0, 0.055), None),
    ('open', (-0.52, -0.88, 0.70), (0.03, 0.05, 0.12), 'open'),
    ('top', (0.0, -0.10, 0.80), (0.0, 0.0, 0.05), None),
]
closed_loc = lid.location.copy()
for name, loc, target, state in shots:
    if state == 'open':
        lid.location = (0.05, 0.10, closed_loc.z + 0.16)
        lid.rotation_euler = (math.radians(30), math.radians(-6), math.radians(8))
    else:
        lid.location = closed_loc; lid.rotation_euler = (0, 0, 0)
    aim(loc, target)
    scene.render.filepath = os.path.join(OUT, f'render-{name}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
