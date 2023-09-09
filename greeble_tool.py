import bpy
import bmesh

import numpy as np

import math
from mathutils import Vector

def update_greeble(instance, context):
    bpy.ops.object.mode_set(mode='OBJECT')

    o = context.active_object
    settings = o.greeble_properties
    o_d = o.data
    o_n = o.data.name
    o.data = settings.root_mesh.copy()
    o.data.name = o_n
    bpy.data.meshes.remove(bpy.data.meshes[o_d.name], do_unlink=True)

    me = o.data

    bmMain = bmesh.new()
    bmNext = bmesh.new()
    bmDest = bmesh.new()

    bmMain.from_mesh(me)

    for f in bmMain.faces:
        if f.select:
            f.select = False

    for layer in range(settings.layer):

        layerNum = str(layer+1)

        subdivs = eval('settings.subdivs_' + layerNum)
        if int(layerNum) < 6:
            style = eval('settings.greeble_style_' + layerNum)

        bmesh.ops.subdivide_edges(bmMain,
                                edges=bmMain.edges,
                                cuts=subdivs,
                                use_grid_fill=True,
                                use_only_quads=True)

        bmesh.ops.split_edges(bmMain, edges=bmMain.edges)

        bmNext = bmMain.copy()
        
        bmMain.faces.ensure_lookup_table()
        bmNext.faces.ensure_lookup_table()

        seed = eval('settings.seed_' + layerNum)
        rng = np.random.Generator(np.random.SFC64(seed))

        ratio = eval('settings.ratio_' + layerNum) * 0.01
        faceCount = len(bmMain.faces)
        faceTargCount = math.floor(ratio * faceCount)
        randFaceIndices = rng.choice(range(0, faceCount), faceTargCount, False)

        randFaces = []
        nextFaces = []

        xScatter = eval('settings.x_scatter_' + layerNum)
        yScatter = eval('settings.y_scatter_' + layerNum)
        scale = eval('settings.scale_' + layerNum) * .01
        scaleDisorder = eval('settings.scale_disorder_' + layerNum) * .01
        scaleDisorderType = eval('settings.scale_disorder_method_' + layerNum)
        for i in randFaceIndices:
            f = bmMain.faces[i]
            randFaces.append(bmNext.faces[i])
            f.select = True
            if xScatter > 0 or yScatter > 0 :
                normal = f.normal
                tangent = f.calc_tangent_edge()
                bitangent = Vector.cross(normal, tangent)

                tangent.xyz   *= rng.random(dtype=np.float32) * xScatter * 2 - xScatter     
                bitangent.xyz *= rng.random(dtype=np.float32) * yScatter * 2 - yScatter

                translateVec = tangent + bitangent
            else:
                translateVec = Vector((0,0,0))

            center = f.calc_center_median()

            if scaleDisorderType == '1':
                randScale = scale + rng.uniform(-scaleDisorder, scaleDisorder)
            elif scaleDisorderType == '2':
                randScale = scale + rng.uniform(0, scaleDisorder)
            else:
                randScale = scale + rng.uniform(-scaleDisorder, 0)

            for v in f.verts:
                v.co = (center + randScale * (v.co - center)) + translateVec

        for f in bmMain.faces:
            if f.select is False:
                nextFaces.append(bmMain.faces[f.index])
            else:
                f.select = False
                
        bmesh.ops.delete(bmNext, geom=randFaces, context='FACES')
        bmesh.ops.delete(bmMain, geom=nextFaces, context='FACES')
        
        if settings.extrude_backface_toggle is True:
            extrudedFaces = bmesh.ops.extrude_face_region(bmMain, geom=bmMain.faces, use_keep_orig=False)['geom']
        else:
            extrudedFaces = bmesh.ops.extrude_discrete_faces(bmMain, faces=bmMain.faces)['faces'] 

        extrudeScale = eval('settings.extrude_' + layerNum)
        extrudeDisorder = eval('settings.extrude_disorder_' + layerNum) * .01
        for f in extrudedFaces:
            if isinstance(f, bmesh.types.BMFace):
                ed = rng.random(dtype=np.float32) * extrudeDisorder * 2 - extrudeDisorder
                for v in f.verts:    
                    v.co += f.normal * (extrudeScale + (ed * extrudeScale))

        if int(layerNum) < 6:
            if style == '2':
                bmRec = bmMain.copy()
                bmRecToDel = []

                bmRec.faces.ensure_lookup_table()

                for f in extrudedFaces:
                    if isinstance(f, bmesh.types.BMFace):
                        bmRec.faces[f.index].select = True

                for f in bmRec.faces:
                    if f.select:
                        f.select = False
                    else:
                        bmRecToDel.append(f)
                
                bmesh.ops.delete(bmRec, geom=bmRecToDel, context='FACES')

        bmMain.to_mesh(me)

        if int(layerNum) < 6:
            if style == '1':
                bmMain = bmNext
            elif style == '2':
                bmMain = bmRec
            else:
                bmMain = bmMain

        bmDest.from_mesh(me)

    segments = settings.bevel_segments
    if segments > 0:
        bmDest.from_mesh(me)
        bmesh.ops.bevel(bmDest, 
                        geom=bmDest.edges, 
                        offset=settings.bevel_width, 
                        offset_type=settings.bevel_width_type, 
                        segments=segments,
                        profile=0.5,
                        affect='EDGES',
                        clamp_overlap=settings.bevel_clamp_overlap,
                        harden_normals=settings.bevel_harden_normals)

    bmDest.to_mesh(me)

    bmDest.free()
    bmNext.free()
    bmMain.free()


class GREEBLETOOL_PG_scene_properties(bpy.types.PropertyGroup):
    file_path : bpy.props.StringProperty(name="File path", default="/tmp\\", maxlen=1024, subtype="FILE_PATH")


class GREEBLETOOL_PG_object_properties(bpy.types.PropertyGroup):
    root_mesh : bpy.props.PointerProperty(name='Original Mesh', type=bpy.types.Mesh)
    root_obj : bpy.props.PointerProperty(name='Original Object', type=bpy.types.Object)
    
    material : bpy.props.PointerProperty(name='Material', type=bpy.types.Material)
    texture_resolution : bpy.props.EnumProperty(name='Texture Resolution', 
                                                default='1024',
                                                items=[('4096', '4096x4096', '', 1),
                                                       ('2048', '2048x2048', '', 2),
                                                       ('1024', '1024x1024', '', 3),
                                                       ('512',  '512x512',   '', 4),
                                                       ('256',  '256x256',   '', 5),],)
    normal_map : bpy.props.PointerProperty(name='Baked Normal Map', type=bpy.types.Image)
    normal_map_bake : bpy.props.BoolProperty(name="Bake Normal Map Toggle", default=True)
    normal_map_export : bpy.props.BoolProperty(name="Export Normal Map Toggle", default=True)
    normal_map_margin : bpy.props.IntProperty(name='Normal Map Margin', default=16, min=0, max=64)
    normal_map_format : bpy.props.EnumProperty(name='Format', items = [('POS_Y', 'OpenGL', ''), ('NEG_Y', 'DirectX', ''),])
    normal_map_root_bake : bpy.props.BoolProperty(name='Clear Normal Map Before Baking', default=True)

    ao_map :bpy.props.PointerProperty(name='Baked AO Map', type=bpy.types.Image)
    ao_map_bake : bpy.props.BoolProperty(name="Bake AO Map Toggle", default=True)
    ao_map_export : bpy.props.BoolProperty(name="Export AO Map Toggle", default=True)
    ao_map_margin : bpy.props.IntProperty(name='AO Map Margin', default=16, min=0, max=64)
    ao_map_margin_type : bpy.props.EnumProperty(name='AO Map Margin Type', default='ADJACENT_FACES',items=[('ADJACENT_FACES', 'Adjacent Faces', ''), ('EXTEND', 'Extend', ''),])
    ao_map_root_bake : bpy.props.BoolProperty(name='Clear AO Map Before Baking', default=True)

    maps_toggle_image_preview : bpy.props.BoolProperty(name='Toggle Map Image Preview', default=True)

    is_gt_activated : bpy.props.BoolProperty(name='is Greeble Tool Activated', default=False)
    layer : bpy.props.IntProperty(name='Recursive Subdivision', default=1, min=1, max=6, update=update_greeble)

    subdivs_1 : bpy.props.IntProperty(name='Subdivisions', default=1, min=0, max=4, update=update_greeble)
    subdivs_2 : bpy.props.IntProperty(name='Subdivisions', default=1, min=0, max=4, update=update_greeble)
    subdivs_3 : bpy.props.IntProperty(name='Subdivisions', default=1, min=0, max=4, update=update_greeble)
    subdivs_4 : bpy.props.IntProperty(name='Subdivisions', default=1, min=0, max=4, update=update_greeble)
    subdivs_5 : bpy.props.IntProperty(name='Subdivisions', default=1, min=0, max=4, update=update_greeble)
    subdivs_6 : bpy.props.IntProperty(name='Subdivisions', default=1, min=0, max=4, update=update_greeble)

    ratio_1 : bpy.props.IntProperty(name='Ratio', subtype='PERCENTAGE', default=50, min=0, max=100, update=update_greeble)
    ratio_2 : bpy.props.IntProperty(name='Ratio', subtype='PERCENTAGE', default=50, min=0, max=100, update=update_greeble)
    ratio_3 : bpy.props.IntProperty(name='Ratio', subtype='PERCENTAGE', default=50, min=0, max=100, update=update_greeble)
    ratio_4 : bpy.props.IntProperty(name='Ratio', subtype='PERCENTAGE', default=50, min=0, max=100, update=update_greeble)
    ratio_5 : bpy.props.IntProperty(name='Ratio', subtype='PERCENTAGE', default=50, min=0, max=100, update=update_greeble)
    ratio_6 : bpy.props.IntProperty(name='Ratio', subtype='PERCENTAGE', default=50, min=0, max=100, update=update_greeble)

    seed_1 : bpy.props.IntProperty(name='Seed', default=1, min=0, max=1000, update=update_greeble)
    seed_2 : bpy.props.IntProperty(name='Seed', default=1, min=0, max=1000, update=update_greeble)
    seed_3 : bpy.props.IntProperty(name='Seed', default=1, min=0, max=1000, update=update_greeble)
    seed_4 : bpy.props.IntProperty(name='Seed', default=1, min=0, max=1000, update=update_greeble)
    seed_5 : bpy.props.IntProperty(name='Seed', default=1, min=0, max=1000, update=update_greeble)
    seed_6 : bpy.props.IntProperty(name='Seed', default=1, min=0, max=1000, update=update_greeble)

    greeble_style_1 : bpy.props.EnumProperty(name='Greeble Style', items=[('1', 'Grid', '', 1),('2', 'Panel', '', 2),('3', 'Recursive', '', 3),], update=update_greeble)
    greeble_style_2 : bpy.props.EnumProperty(name='Greeble Style', items=[('1', 'Grid', '', 1),('2', 'Panel', '', 2),('3', 'Recursive', '', 3),], update=update_greeble)
    greeble_style_3 : bpy.props.EnumProperty(name='Greeble Style', items=[('1', 'Grid', '', 1),('2', 'Panel', '', 2),('3', 'Recursive', '', 3),], update=update_greeble)
    greeble_style_4 : bpy.props.EnumProperty(name='Greeble Style', items=[('1', 'Grid', '', 1),('2', 'Panel', '', 2),('3', 'Recursive', '', 3),], update=update_greeble)
    greeble_style_5 : bpy.props.EnumProperty(name='Greeble Style', items=[('1', 'Grid', '', 1),('2', 'Panel', '', 2),('3', 'Recursive', '', 3),], update=update_greeble)

    x_scatter_1 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    x_scatter_2 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    x_scatter_3 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    x_scatter_4 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    x_scatter_5 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    x_scatter_6 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)

    y_scatter_1 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    y_scatter_2 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    y_scatter_3 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    y_scatter_4 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    y_scatter_5 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)
    y_scatter_6 : bpy.props.FloatProperty(name='Scatter', default=0, min=0, max=1, update=update_greeble)

    scale_1 : bpy.props.IntProperty(name='Face Scale', subtype='PERCENTAGE', default=95, min=1, max=100, update=update_greeble)
    scale_2 : bpy.props.IntProperty(name='Face Scale', subtype='PERCENTAGE', default=95, min=1, max=100, update=update_greeble)
    scale_3 : bpy.props.IntProperty(name='Face Scale', subtype='PERCENTAGE', default=95, min=1, max=100, update=update_greeble)
    scale_4 : bpy.props.IntProperty(name='Face Scale', subtype='PERCENTAGE', default=95, min=1, max=100, update=update_greeble)
    scale_5 : bpy.props.IntProperty(name='Face Scale', subtype='PERCENTAGE', default=95, min=1, max=100, update=update_greeble)
    scale_6 : bpy.props.IntProperty(name='Face Scale', subtype='PERCENTAGE', default=95, min=1, max=100, update=update_greeble)

    scale_disorder_1 : bpy.props.IntProperty(name='Face Scale Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    scale_disorder_2 : bpy.props.IntProperty(name='Face Scale Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    scale_disorder_3 : bpy.props.IntProperty(name='Face Scale Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    scale_disorder_4 : bpy.props.IntProperty(name='Face Scale Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    scale_disorder_5 : bpy.props.IntProperty(name='Face Scale Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    scale_disorder_6 : bpy.props.IntProperty(name='Face Scale Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)

    scale_disorder_method_1 : bpy.props.EnumProperty(name='Face Scale Disorder Method', items=[('1', 'Default', '', 1),('2', 'Expand', '', 2),('3', 'Shrink', '', 3),], update=update_greeble)
    scale_disorder_method_2 : bpy.props.EnumProperty(name='Face Scale Disorder Method', items=[('1', 'Default', '', 1),('2', 'Expand', '', 2),('3', 'Shrink', '', 3),], update=update_greeble)
    scale_disorder_method_3 : bpy.props.EnumProperty(name='Face Scale Disorder Method', items=[('1', 'Default', '', 1),('2', 'Expand', '', 2),('3', 'Shrink', '', 3),], update=update_greeble)
    scale_disorder_method_4 : bpy.props.EnumProperty(name='Face Scale Disorder Method', items=[('1', 'Default', '', 1),('2', 'Expand', '', 2),('3', 'Shrink', '', 3),], update=update_greeble)
    scale_disorder_method_5 : bpy.props.EnumProperty(name='Face Scale Disorder Method', items=[('1', 'Default', '', 1),('2', 'Expand', '', 2),('3', 'Shrink', '', 3),], update=update_greeble)
    scale_disorder_method_6 : bpy.props.EnumProperty(name='Face Scale Disorder Method', items=[('1', 'Default', '', 1),('2', 'Expand', '', 2),('3', 'Shrink', '', 3),], update=update_greeble)

    extrude_1 : bpy.props.FloatProperty(name='Extrude Scale', default=0.1, min=0.001, max=2, update=update_greeble)
    extrude_2 : bpy.props.FloatProperty(name='Extrude Scale', default=0.1, min=0.001, max=2, update=update_greeble)
    extrude_3 : bpy.props.FloatProperty(name='Extrude Scale', default=0.1, min=0.001, max=2, update=update_greeble)
    extrude_4 : bpy.props.FloatProperty(name='Extrude Scale', default=0.1, min=0.001, max=2, update=update_greeble)
    extrude_5 : bpy.props.FloatProperty(name='Extrude Scale', default=0.1, min=0.001, max=2, update=update_greeble)
    extrude_6 : bpy.props.FloatProperty(name='Extrude Scale', default=0.1, min=0.001, max=2, update=update_greeble)

    extrude_disorder_1 : bpy.props.IntProperty(name='Extrude Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    extrude_disorder_2 : bpy.props.IntProperty(name='Extrude Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    extrude_disorder_3 : bpy.props.IntProperty(name='Extrude Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    extrude_disorder_4 : bpy.props.IntProperty(name='Extrude Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    extrude_disorder_5 : bpy.props.IntProperty(name='Extrude Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)
    extrude_disorder_6 : bpy.props.IntProperty(name='Extrude Disorder', subtype='PERCENTAGE', default=0, min=0, max=100, update=update_greeble)

    extrude_backface_toggle : bpy.props.BoolProperty(name='Fill Extrude Back-face', default=False, update=update_greeble)

    bevel_width_type : bpy.props.EnumProperty(name='Bevel Width Type',
                                              items=[('OFFSET',   'Offset',   '', 1),
                                                     ('WIDTH',    'Width',    '', 2),
                                                     ('DEPTH',    'Depth',    '', 3),
                                                     ('PERCENT',  'Percent',  '', 4),
                                                     ('ABSOLUTE', 'Absolute', '', 5),],
                                                update=update_greeble)
    bevel_width : bpy.props.FloatProperty(name='Bevel Width', default=0.04, min=0, update=update_greeble)
    bevel_segments : bpy.props.IntProperty(name='Bevel Segments', default=1, min=0, max=6, update=update_greeble)
    bevel_clamp_overlap : bpy.props.BoolProperty(name='Bevel Clamp Overlap', default=True, update=update_greeble)
    bevel_harden_normals : bpy.props.BoolProperty(name='Bevel Harden Normals', default=True, update=update_greeble)



class GREEBLETOOL_OT_greeble_ops(bpy.types.Operator):
    bl_label = 'Greeble Tool'
    bl_idname = 'greebletool.greebleops_operator'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = bpy.context.active_object
        if o.mode == 'EDIT':
            o.update_from_editmode()
            for f in o.data.polygons:
                if f.select:
                    return True
            return False
        else:
            return o != None    
    
    def process(self, context):
        oao = bpy.context.active_object

        if len(oao.data.materials) == 0:
            mat = bpy.data.materials.get('Material')
            if mat is None:
                mat = bpy.data.materials.new(name="Material")
            oao.data.materials.append(mat)

        if oao.mode == 'EDIT':
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            bpy.ops.mesh.duplicate()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.context.view_layer.objects.active = bpy.context.selected_objects[-1]

            ao = bpy.context.active_object
            o = ao.copy()
            o.data = ao.data.copy() 

            settings = o.greeble_properties
            settings.root_mesh = ao.data
            settings.root_obj = oao
            bpy.context.collection.objects.link(o)

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = o

            settings.is_gt_activated = True
            bpy.data.objects[ao.name].select_set(True)

            bpy.ops.object.delete()

        else:
            o = oao.copy()
            o.data = oao.data.copy() 

            settings = o.greeble_properties
            settings.root_mesh = oao.data
            settings.root_obj = oao
            bpy.context.collection.objects.link(o)

            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = o

            settings.is_gt_activated = True

        bpy.data.objects[o.name].select_set(True)

        settings.material = oao.data.materials[0]

        update_greeble(self,context) 

    def execute(self, context):
        self.process(context)

        return {'FINISHED'}


class GREEBLETOOL_OT_terminate(bpy.types.Operator):
    bl_label = 'Greeble Tool Termination'
    bl_idname = 'greebletool.greebleops_terminate'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None and bpy.context.active_object.mode == 'OBJECT'
    
    def process(self, context):
        o = context.active_object
        settings = o.greeble_properties

        keys = []

        for p in settings.keys():
            keys.append(p)

        for k in keys:
            settings.property_unset(k)

    def execute(self, context):
        self.process(context)

        return {'FINISHED'}


class GREEBLETOOL_OT_bake(bpy.types.Operator):
    bl_label = 'Greeble Tool Bake'
    bl_idname = 'greebletool.greebleops_bake'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None and bpy.context.active_object.mode == 'OBJECT'

    def process(self, context):

        if context.scene.render.engine == 'BLENDER_EEVEE':
            context.scene.render.engine = 'CYCLES'

        if context.scene.cycles.device == 'CPU':
            context.scene.cycles.device = 'GPU'

        o = context.active_object
        settings = o.greeble_properties
        oo = settings.root_obj

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[o.name].select_set(True)
        bpy.data.objects[oo.name].select_set(True)
        context.view_layer.objects.active = oo

        mat = settings.material
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.name = 'Greeble Baker'
        tex_node.select = True
        nodes.active = tex_node

        res = int(settings.texture_resolution)

        es_max = 0
        ed_max = 0
        for layer in range(settings.layer):
            layerNum = str(layer+1)
            es_cur = eval('settings.extrude_' + layerNum)
            ed_cur = eval('settings.extrude_disorder_' + layerNum) * .01

            if es_cur > es_max:
                es_max = es_cur

            if ed_cur > ed_max:
                ed_max = ed_cur

        e = (es_max + (es_max * es_cur)) * 10

        if settings.normal_map_bake:
            img_name = oo.name + '_Normal'
            root_img = bpy.data.images.get(img_name)
            if settings.normal_map_root_bake is False or root_img is None:
                if root_img is not None:
                    bpy.data.images.remove(root_img)
                img = bpy.data.images.new(img_name, res, res)
            else:
                if root_img is not None:
                    img = root_img
                else:
                    img = settings.normal_map

            tex_node.image = img

            bpy.ops.object.bake(type='NORMAL', 
                                use_selected_to_active=True, 
                                cage_extrusion=e, 
                                max_ray_distance=0, 
                                margin=settings.normal_map_margin, 
                                normal_g=settings.normal_map_format,
                                use_clear=not settings.normal_map_root_bake)

            img.preview_ensure()
            settings.normal_map = img

        if settings.ao_map_bake:
            img_name = oo.name + '_AO'
            root_img = bpy.data.images.get(img_name)
            if settings.ao_map_root_bake is False or root_img is None:
                if root_img is not None:
                    bpy.data.images.remove(root_img)
                img = bpy.data.images.new(img_name, res, res)
            else:
                if root_img is not None:
                    img = root_img
                else:
                    img = settings.ao_map

            tex_node.image = img                

            bpy.ops.object.bake(type='AO', 
                                use_selected_to_active=True, 
                                cage_extrusion=e, 
                                max_ray_distance=0, 
                                margin=settings.ao_map_margin, 
                                margin_type=settings.ao_map_margin_type,
                                use_clear=not settings.ao_map_root_bake)

            img.preview_ensure()
            settings.ao_map = img
            
        for n in nodes:
            if n.name == 'Greeble Baker':
                nodes.remove(n)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[o.name].select_set(True)
        context.view_layer.objects.active = o


    def execute(self, context):
        self.process(context)

        return {'FINISHED'}


class GREEBLETOOL_OT_export(bpy.types.Operator):
    bl_label = 'Greeble Tool Export'
    bl_idname = 'greebletool.greebleops_export'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object.greeble_properties.normal_map != None or context.active_object.greeble_properties.ao_map != None

    def execute(self, context):
        settings = context.active_object.greeble_properties
        scene_settings = context.scene.greeble_scene_properties
        if settings.normal_map_export and settings.normal_map is not None:
            settings.normal_map.save(filepath=scene_settings.file_path + settings.normal_map.name + ".png")
        if settings.ao_map_export and settings.ao_map is not None:
            settings.ao_map.save(filepath=scene_settings.file_path + settings.ao_map.name + ".png")

        return {'FINISHED'}


class GREEBLETOOL_PT_main_panel(bpy.types.Panel):
    bl_label = 'Greeble Tool Panel'
    bl_idname = 'GREEBLETOOL_PT_main_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Greeble Tool'

    @classmethod
    def poll(cls, context):
        return context.active_object != None and context.active_object.type == 'MESH'
    
    def draw(self, context):
        layout = self.layout
        settings = context.active_object.greeble_properties
        scene_settings = context.scene.greeble_scene_properties

        row = layout.row()
        if bpy.context.active_object.mode == 'EDIT' and not settings.is_gt_activated:
            row.operator('GREEBLETOOL.greebleops_operator', text='Create greeble object from selected face(s)',icon='IMGDISPLAY')
        elif bpy.context.active_object.mode == 'OBJECT' and not settings.is_gt_activated:
            row.operator('GREEBLETOOL.greebleops_operator', text='Create greeble object from selected object',icon='IMGDISPLAY')

        if settings.is_gt_activated == True:
            row.enabled = False

            box = layout.box()
            split = box.split(factor=0.135)
            col_l = split.column(align=True)
            col_r = split.column(align=True)
            col_l.label(text='Layers:')
            col_r.prop(settings, 'layer', text='')   

            box = layout.box()
            cf = box.column_flow(columns=7, align=False)

            cf.scale_y = 1

            tc = cf.grid_flow(columns=1, even_columns=False, align=True)
            tc.alignment = 'RIGHT'
            tc.label(text='')
            tc.label(text='Subdivisions')
            tc.label(text='Ratio')
            tc.label(text='Seed')
            tc.label(text='Style')
            tc.separator()
            tc.label(text='X Scatter')
            tc.label(text='Y Scatter')
            tc.separator()
            tc.label(text='Scale')
            tc.label(text='Disorder')
            tc.label(text='Method')
            tc.separator()
            tc.label(text='Extrusion')
            tc.label(text='Disorder')

            c1 = cf.grid_flow(columns=1, even_columns=True, align=True)
            c1.alignment = 'CENTER'
            c1.label(text='1',)
            c1.prop(settings, 'subdivs_1', text='')
            c1.prop(settings, 'ratio_1', text='', slider=True)
            c1.prop(settings, 'seed_1', text='')
            c1.label(text='')
            c1.separator()
            c1.prop(settings, 'x_scatter_1', text='')
            c1.prop(settings, 'y_scatter_1', text='')
            c1.separator()
            c1.prop(settings, 'scale_1', text='', slider=True)
            c1.prop(settings, 'scale_disorder_1', text='', slider=True)
            c1.prop(settings, 'scale_disorder_method_1', text='')
            c1.separator()
            c1.prop(settings, 'extrude_1', slider=True, text='')
            c1.prop(settings, 'extrude_disorder_1', slider=True, text='')

            c2 = cf.grid_flow(columns=1, even_columns=True, align=True)
            c2.alignment = 'CENTER'
            c2.label(text='2')
            c2.prop(settings, 'subdivs_2', text='')
            c2.prop(settings, 'ratio_2', text='', slider=True)
            c2.prop(settings, 'seed_2', text='')
            c2.prop(settings, 'greeble_style_1', text='')
            c2.separator()
            c2.prop(settings, 'x_scatter_2', text='')
            c2.prop(settings, 'y_scatter_2', text='')
            c2.separator()
            c2.prop(settings, 'scale_2', text='', slider=True)
            c2.prop(settings, 'scale_disorder_2', text='', slider=True)
            c2.prop(settings, 'scale_disorder_method_2', text='')
            c2.separator()
            c2.prop(settings, 'extrude_2', slider=True, text='')
            c2.prop(settings, 'extrude_disorder_2', slider=True, text='')

            c3 = cf.grid_flow(columns=1, even_columns=True, align=True)
            c3.alignment = 'CENTER'
            c3.label(text='3')
            c3.prop(settings, 'subdivs_3', text='')
            c3.prop(settings, 'ratio_3', text='', slider=True)
            c3.prop(settings, 'seed_3', text='')
            c3.prop(settings, 'greeble_style_2', text='')
            c3.separator()
            c3.prop(settings, 'x_scatter_3', text='')
            c3.prop(settings, 'y_scatter_3', text='')
            c3.separator()
            c3.prop(settings, 'scale_3', text='', slider=True)
            c3.prop(settings, 'scale_disorder_3', text='', slider=True)
            c3.prop(settings, 'scale_disorder_method_3', text='')
            c3.separator()
            c3.prop(settings, 'extrude_3', slider=True, text='')
            c3.prop(settings, 'extrude_disorder_3', slider=True, text='')

            c4 = cf.grid_flow(columns=1, even_columns=True, align=True)
            c4.alignment = 'CENTER'
            c4.label(text='4')
            c4.prop(settings, 'subdivs_4', text='')
            c4.prop(settings, 'ratio_4', text='', slider=True)
            c4.prop(settings, 'seed_4', text='')
            c4.prop(settings, 'greeble_style_3', text='')
            c4.separator()
            c4.prop(settings, 'x_scatter_4', text='')
            c4.prop(settings, 'y_scatter_4', text='')
            c4.separator()
            c4.prop(settings, 'scale_4', text='', slider=True)
            c4.prop(settings, 'scale_disorder_4', text='', slider=True)
            c4.prop(settings, 'scale_disorder_method_4', text='')
            c4.separator()
            c4.prop(settings, 'extrude_4', slider=True, text='')
            c4.prop(settings, 'extrude_disorder_4', slider=True, text='')

            c5 = cf.grid_flow(columns=1, even_columns=True, align=True)
            c5.alignment = 'CENTER'
            c5.label(text='5')
            c5.prop(settings, 'subdivs_5', text='')
            c5.prop(settings, 'ratio_5', text='', slider=True)
            c5.prop(settings, 'seed_5', text='')
            c5.prop(settings, 'greeble_style_4', text='')
            c5.separator()
            c5.prop(settings, 'x_scatter_5', text='')
            c5.prop(settings, 'y_scatter_5', text='')
            c5.separator()
            c5.prop(settings, 'scale_5', text='', slider=True)
            c5.prop(settings, 'scale_disorder_5', text='', slider=True)
            c5.prop(settings, 'scale_disorder_method_5', text='')
            c5.separator()
            c5.prop(settings, 'extrude_5', slider=True, text='')
            c5.prop(settings, 'extrude_disorder_5', slider=True, text='')

            c6 = cf.grid_flow(columns=1, even_columns=True, align=True)
            c6.alignment = 'CENTER'
            c6.label(text='6')
            c6.prop(settings, 'subdivs_6', text='')
            c6.prop(settings, 'ratio_6', text='', slider=True)
            c6.prop(settings, 'seed_6', text='')
            c6.prop(settings, 'greeble_style_5', text='')
            c6.separator()
            c6.prop(settings, 'x_scatter_6', text='')
            c6.prop(settings, 'y_scatter_6', text='')
            c6.separator()
            c6.prop(settings, 'scale_6', text='', slider=True)
            c6.prop(settings, 'scale_disorder_6', text='', slider=True)
            c6.prop(settings, 'scale_disorder_method_6', text='')
            c6.separator()
            c6.prop(settings, 'extrude_6', slider=True, text='')
            c6.prop(settings, 'extrude_disorder_6', slider=True, text='')

            box.use_property_split = True
            box.use_property_decorate = False
            box.prop(settings, 'extrude_backface_toggle', text='Fill back-faces after extrusion:')   

            box = layout.box()
            box.scale_y = 1
            box.use_property_split = True
            box.use_property_decorate = False
            box.prop(settings, 'bevel_width_type')
            box.prop(settings, 'bevel_width')
            box.prop(settings, 'bevel_segments')
            box.prop(settings, 'bevel_clamp_overlap')
            box.prop(settings, 'bevel_harden_normals')

            box = layout.box()
            box.scale_y = 1
            box.use_property_split = True
            box.use_property_decorate = False
            box.prop(settings, 'root_obj', text='Root Object')
            box.prop(settings, 'material', text='Material to bake to')
            box.prop(settings, 'texture_resolution', text='Resolution')

            split = layout.split()
            col_l = split.column(align=True)
            col_r = split.column(align=True)

            box_l = col_l.box()
            box_r = col_r.box()

            box_l.label(text='Normal Map')
            box_r.label(text='Ambient Occlusion Map')   

            box_l.scale_y = 1
            box_l.use_property_split = True
            box_l.use_property_decorate = False
            box_l.prop(settings, 'normal_map_bake', text='Bake', toggle=-1)
            box_l.prop(settings, 'normal_map_export', text='Export', toggle=-1)
            box_l.prop(settings, 'normal_map_root_bake', text='Bake to Root', toggle=-1)
            box_l.prop(settings, 'normal_map_format', text='Format')
            box_l.prop(settings, 'normal_map_margin', text='Margin')
            
            box_r.scale_y = 1
            box_r.use_property_split = True
            box_r.use_property_decorate = False
            box_r.prop(settings, 'ao_map_bake', text='Bake', toggle=-1)
            box_r.prop(settings, 'ao_map_export', text='Export', toggle=-1)
            box_r.prop(settings, 'ao_map_root_bake', text='Bake to Root', toggle=-1)
            box_r.prop(settings, 'ao_map_margin_type', text='Margin Type')
            box_r.prop(settings, 'ao_map_margin', text='Margin')

            box = layout.box()
            box.scale_y = 1
            row = box.row()
            row.operator('GREEBLETOOL.greebleops_bake',text='Bake Map(s)', icon='RENDER_RESULT')
            row = box.row()
            row.prop(scene_settings, 'file_path')
            row.operator('greebletool.greebleops_export', text='Export Map(s)', icon='EXPORT')

            if settings.normal_map or settings.ao_map:
                row = layout.row()
                icon = 'HIDE_OFF' if settings.maps_toggle_image_preview else 'HIDE_ON'
                row.prop(settings, 'maps_toggle_image_preview', text='Preview Generated Map(s)', icon=icon)

            split = layout.split()
            col_l = split.column(align=True)
            col_r = split.column(align=True)

            if settings.normal_map:
                if settings.maps_toggle_image_preview:
                    col_l.template_icon(settings.normal_map.preview.icon_id, scale=14)

            if settings.ao_map:
                if settings.maps_toggle_image_preview:
                    col_r.template_icon(settings.ao_map.preview.icon_id, scale=14)

            row = box.row()
            row.use_property_split = True
            row.operator('GREEBLETOOL.greebleops_terminate',text='Apply', icon='CHECKMARK')

            if settings.layer > 1:
                c2.enabled = True
            else:
                c2.enabled = False

            if settings.layer > 2:
                c3.enabled = True
            else:
                c3.enabled = False

            if settings.layer > 3:
                c4.enabled = True
            else:
                c4.enabled = False

            if settings.layer > 4:
                c5.enabled = True
            else:
                c5.enabled = False

            if settings.layer > 5:
                c6.enabled = True
            else:
                c6.enabled = False