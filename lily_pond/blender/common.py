"""Shared helpers for the Lily Pond asset scripts (run inside Blender).

Every asset is rendered straight from above with an orthographic camera,
twice: a "beauty" pass lit only by a soft white dome (so it carries colour,
ambient occlusion and translucency but no light direction), and a normal
pass.  The game adds the sun itself, per pixel, so sprites can be rotated
freely and still be lit from the right side.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector


def reset_scene(samples=64, res=384):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for kind in ('OPTIX', 'CUDA'):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                if any(d.type == kind for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = True
                    sc.cycles.device = 'GPU'
                    break
            except Exception:
                pass
    except Exception:
        pass
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.film_transparent = True
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    sc.view_settings.view_transform = 'Standard'
    try:
        sc.view_settings.look = 'None'
    except Exception:
        pass
    # soft white dome
    world = bpy.data.worlds.new('Dome')
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (1, 1, 1, 1)
    bg.inputs[1].default_value = 1.0
    sc.world = world
    cam_data = bpy.data.cameras.new('Cam')
    cam_data.type = 'ORTHO'
    cam = bpy.data.objects.new('Cam', cam_data)
    sc.collection.objects.link(cam)
    cam.location = (0, 0, 20)
    cam.rotation_euler = (0, 0, 0)
    cam_data.clip_end = 100
    sc.camera = cam
    return sc


def set_camera(size, cx=0.0, cy=0.0):
    cam = bpy.context.scene.camera
    cam.data.ortho_scale = size
    cam.location = (cx, cy, 20)


def set_input(node, names, value):
    """Set the first socket that exists (socket names differ between versions)."""
    if isinstance(names, str):
        names = [names]
    for n in names:
        if n in node.inputs:
            try:
                node.inputs[n].default_value = value
            except Exception:
                pass
            return node.inputs[n]
    return None


def principled(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    return mat, nt, bsdf


_normal_mat = None


def normal_material():
    """Emission material that writes the world-space normal as a colour."""
    global _normal_mat
    if _normal_mat and _normal_mat.name in bpy.data.materials:
        return _normal_mat
    mat = bpy.data.materials.new('NormalOut')
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    mad = nt.nodes.new('ShaderNodeVectorMath')
    mad.operation = 'MULTIPLY_ADD'
    mad.inputs[1].default_value = (0.5, 0.5, 0.5)
    mad.inputs[2].default_value = (0.5, 0.5, 0.5)
    em = nt.nodes.new('ShaderNodeEmission')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(geo.outputs['Normal'], mad.inputs[0])
    nt.links.new(mad.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    _normal_mat = mat
    return mat


def render_pair(path_base, normal=True, samples=None):
    """Render <path_base>.png (beauty) and <path_base>_n.png (normals)."""
    sc = bpy.context.scene
    vl = bpy.context.view_layer
    if samples:
        sc.cycles.samples = samples
    vl.material_override = None
    sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = path_base + '.png'
    bpy.ops.render.render(write_still=True)
    if normal:
        keep = sc.cycles.samples, sc.cycles.use_denoising
        vl.material_override = normal_material()
        sc.view_settings.view_transform = 'Raw'
        sc.cycles.samples = 16
        sc.cycles.use_denoising = False
        sc.render.filepath = path_base + '_n.png'
        bpy.ops.render.render(write_still=True)
        vl.material_override = None
        sc.view_settings.view_transform = 'Standard'
        sc.cycles.samples, sc.cycles.use_denoising = keep


def render_normal_only(path_base):
    sc = bpy.context.scene
    vl = bpy.context.view_layer
    keep = sc.cycles.samples, sc.cycles.use_denoising
    vl.material_override = normal_material()
    sc.view_settings.view_transform = 'Raw'
    sc.cycles.samples = 16
    sc.cycles.use_denoising = False
    sc.render.filepath = path_base + '_n.png'
    bpy.ops.render.render(write_still=True)
    vl.material_override = None
    sc.view_settings.view_transform = 'Standard'
    sc.cycles.samples, sc.cycles.use_denoising = keep


def mesh_object(name, verts, faces, smooth=True, material=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if material:
        me.materials.append(material)
    return ob


def add_subsurf(ob, levels=2):
    m = ob.modifiers.new('sub', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    return m


def clear_objects(keep_types=('CAMERA',)):
    for ob in list(bpy.data.objects):
        if ob.type not in keep_types:
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def script_args():
    argv = sys.argv
    return argv[argv.index('--') + 1:] if '--' in argv else []
