import bpy

from ...util import generate_converted_texture_paths
from ...classes.material_instance import tpGxMaterialInstanceV2

from .nodes import constant_buffer_value, dx_to_gl_normal, grid_location, texture_sampler

def master_rs_layer3(textures_dir: str, material: bpy.types.Material, instance: tpGxMaterialInstanceV2):
    # Renamed in 5.0
    sepRGB_name = "ShaderNodeSeparateRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeSeparateColor"
    sepRGB_input = 'Image' if bpy.app.version < (5, 0, 0) else "Color"
    comRGB_name = "ShaderNodeCombineRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeCombineColor"
    comRGB_output = 'Image' if bpy.app.version < (5, 0, 0) else "Color"

    material.use_nodes = True
    material.node_tree.links.clear()
    material.node_tree.nodes.clear()
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    material.blend_method = 'CLIP'

    converted_textures = generate_converted_texture_paths(instance.texture_samplers)

    # UV Map 1
    uv1 = nodes.new(type='ShaderNodeUVMap')
    uv1.uv_map = 'UVMap1'
    uv1.location = grid_location(-2, -1)
    uv1.hide = True
    uv1.label = 'UVMap1'

    # Mapping 3
    mapping_3 = nodes.new(type='ShaderNodeMapping')
    mapping_3.location = grid_location(-1, 0)
    mapping_3.hide = True
    links.new(uv1.outputs['UV'], mapping_3.inputs['Vector'])

    # gUVOffset3
    g_uv_offset_3 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVOffset3")
    if g_uv_offset_3 is not None:
        g_uv_offset_3.location = grid_location(-2, 0)
        links.new(g_uv_offset_3.outputs[0], mapping_3.inputs['Location'])

    # gUVScale3
    g_uv_scale_3 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVScale3")
    if g_uv_scale_3 is not None:
        g_uv_scale_3.location = grid_location(-2, 1)
        links.new(g_uv_scale_3.outputs[0], mapping_3.inputs['Scale'])

    # texLayerMask
    tex_layer_mask = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texLayerMask")
    if tex_layer_mask.image is not None:
        tex_layer_mask.image.colorspace_settings.name = 'Non-Color'
    tex_layer_mask.location = grid_location(0, 0)
    links.new(mapping_3.outputs['Vector'], tex_layer_mask.inputs['Vector'])

    # texLayerMask Separate Color
    tex_layer_mask_sep = nodes.new(type=sepRGB_name)
    tex_layer_mask_sep.location = grid_location(1, 0)
    tex_layer_mask_sep.hide = True
    links.new(tex_layer_mask.outputs['Color'], tex_layer_mask_sep.inputs[sepRGB_input])

    # UV Map 0
    uv0 = nodes.new(type='ShaderNodeUVMap')
    uv0.uv_map = 'UVMap0'
    uv0.location = grid_location(-2, 2)
    uv0.hide = True
    uv0.label = 'UVMap0'

    # Mapping 0
    mapping_0 = nodes.new(type='ShaderNodeMapping')
    mapping_0.location = grid_location(-1, 3)
    mapping_0.hide = True
    links.new(uv0.outputs['UV'], mapping_0.inputs['Vector'])

    # gUVOffset0
    g_uv_offset_0 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVOffset0")
    if g_uv_offset_0 is not None:
        g_uv_offset_0.location = grid_location(-2, 3)
        links.new(g_uv_offset_0.outputs[0], mapping_0.inputs['Location'])

    # gUVScale0
    g_uv_scale_0 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVScale0")
    if g_uv_scale_0 is not None:
        g_uv_scale_0.location = grid_location(-2, 4)
        links.new(g_uv_scale_0.outputs[0], mapping_0.inputs['Scale'])

    # Mapping 1
    mapping_1 = nodes.new(type='ShaderNodeMapping')
    mapping_1.location = grid_location(-1, 5)
    mapping_1.hide = True
    links.new(uv0.outputs['UV'], mapping_1.inputs['Vector'])

    # gUVOffset1
    g_uv_offset_1 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVOffset1")
    if g_uv_offset_1 is not None:
        g_uv_offset_1.location = grid_location(-2, 5)
        links.new(g_uv_offset_1.outputs[0], mapping_1.inputs['Location'])

    # gUVScale1
    g_uv_scale_1 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVScale1")
    if g_uv_scale_1 is not None:
        g_uv_scale_1.location = grid_location(-2, 6)
        links.new(g_uv_scale_1.outputs[0], mapping_1.inputs['Scale'])

    # Mapping 2
    mapping_2 = nodes.new(type='ShaderNodeMapping')
    mapping_2.location = grid_location(-1, 7)
    mapping_2.hide = True
    links.new(uv0.outputs['UV'], mapping_2.inputs['Vector'])

    # gUVOffset2
    g_uv_offset_2 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVOffset2")
    if g_uv_offset_2 is not None:
        g_uv_offset_2.location = grid_location(-2, 7)
        links.new(g_uv_offset_2.outputs[0], mapping_2.inputs['Location'])

    # gUVScale2
    g_uv_scale_2 = constant_buffer_value(material, nodes, instance, "CbLayer3", "gUVScale2")
    if g_uv_scale_2 is not None:
        g_uv_scale_2.location = grid_location(-2, 8)
        links.new(g_uv_scale_2.outputs[0], mapping_2.inputs['Scale'])

    # texBaseColor0
    tex_base_color_0 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texBaseColor0")
    tex_base_color_0.location = grid_location(0, 1)
    links.new(mapping_0.outputs['Vector'], tex_base_color_0.inputs['Vector'])

    # texBaseColor1
    tex_base_color_1 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texBaseColor1")
    tex_base_color_1.location = grid_location(0, 2)
    links.new(mapping_1.outputs['Vector'], tex_base_color_1.inputs['Vector'])

    # texBaseColor2
    tex_base_color_2 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texBaseColor2")
    tex_base_color_2.location = grid_location(0, 3)
    links.new(mapping_2.outputs['Vector'], tex_base_color_2.inputs['Vector'])

    # Mix Color 0-1
    mix_col_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_01.location = grid_location(2, 1)
    mix_col_01.hide = True
    links.new(tex_layer_mask_sep.outputs[0], mix_col_01.inputs['Fac'])
    links.new(tex_base_color_0.outputs['Color'], mix_col_01.inputs['Color1'])
    links.new(tex_base_color_1.outputs['Color'], mix_col_01.inputs['Color2'])

    # Mix Color 0-1-2
    mix_col_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_012.location = grid_location(3, 2)
    mix_col_012.hide = True
    links.new(tex_layer_mask_sep.outputs[1], mix_col_012.inputs['Fac'])
    links.new(mix_col_01.outputs['Color'], mix_col_012.inputs['Color1'])
    links.new(tex_base_color_2.outputs['Color'], mix_col_012.inputs['Color2'])

    # texORM0
    tex_orm_0 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texORM0")
    tex_orm_0.image.colorspace_settings.name = 'Non-Color'
    tex_orm_0.location = grid_location(0, 4)
    links.new(mapping_0.outputs['Vector'], tex_orm_0.inputs['Vector'])

    # texORM1
    tex_orm_1 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texORM1")
    tex_orm_1.image.colorspace_settings.name = 'Non-Color'
    tex_orm_1.location = grid_location(0, 5)
    links.new(mapping_1.outputs['Vector'], tex_orm_1.inputs['Vector'])

    # texORM2
    tex_orm_2 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texORM2")
    tex_orm_2.image.colorspace_settings.name = 'Non-Color'
    tex_orm_2.location = grid_location(0, 6)
    links.new(mapping_2.outputs['Vector'], tex_orm_2.inputs['Vector'])

    # Mix ORM 0-1
    mix_orm_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_orm_01.location = grid_location(2, 4)
    mix_orm_01.hide = True
    links.new(tex_layer_mask_sep.outputs[0], mix_orm_01.inputs['Fac'])
    links.new(tex_orm_0.outputs['Color'], mix_orm_01.inputs['Color1'])
    links.new(tex_orm_1.outputs['Color'], mix_orm_01.inputs['Color2'])

    # Mix ORM 0-1-2
    mix_orm_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_orm_012.location = grid_location(3, 5)
    mix_orm_012.hide = True
    links.new(tex_layer_mask_sep.outputs[1], mix_orm_012.inputs['Fac'])
    links.new(mix_orm_01.outputs['Color'], mix_orm_012.inputs['Color1'])
    links.new(tex_orm_2.outputs['Color'], mix_orm_012.inputs['Color2'])

    # ORM 0-1-2 Separate Color
    orm_012_sep = nodes.new(type=sepRGB_name)
    orm_012_sep.location = grid_location(4, 5)
    orm_012_sep.hide = True
    links.new(mix_orm_012.outputs['Color'], orm_012_sep.inputs[sepRGB_input])

    # ORM 0-1-2 multiply AO
    ao_multiply = nodes.new('ShaderNodeMixRGB')
    ao_multiply.location = grid_location(5, 2)
    ao_multiply.hide = True
    ao_multiply.blend_type = 'MULTIPLY'
    ao_multiply.inputs[0].default_value = 1.0
    links.new(mix_col_012.outputs['Color'], ao_multiply.inputs[1])
    links.new(orm_012_sep.outputs[0], ao_multiply.inputs[2])

    # texNormal0
    tex_normal_0 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texNormal0")
    tex_normal_0.image.colorspace_settings.name = 'Non-Color'
    tex_normal_0.location = grid_location(0, 7)
    links.new(mapping_0.outputs['Vector'], tex_normal_0.inputs['Vector'])

    # texNormal1
    tex_normal_1 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texNormal1")
    tex_normal_1.image.colorspace_settings.name = 'Non-Color'
    tex_normal_1.location = grid_location(0, 8)
    links.new(mapping_1.outputs['Vector'], tex_normal_1.inputs['Vector'])

    # texNormal2
    tex_normal_2 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texNormal2")
    tex_normal_2.image.colorspace_settings.name = 'Non-Color'
    tex_normal_2.location = grid_location(0, 9)
    links.new(mapping_2.outputs['Vector'], tex_normal_2.inputs['Vector'])

    # Mix Normal 0-1
    mix_normal_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_01.location = grid_location(2, 7)
    mix_normal_01.hide = True
    links.new(tex_layer_mask_sep.outputs[0], mix_normal_01.inputs['Fac'])
    links.new(tex_normal_0.outputs['Color'], mix_normal_01.inputs['Color1'])
    links.new(tex_normal_1.outputs['Color'], mix_normal_01.inputs['Color2'])

    # Mix Normal 0-1-2
    mix_normal_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_012.location = grid_location(3, 8)
    mix_normal_012.hide = True
    links.new(tex_layer_mask_sep.outputs[1], mix_normal_012.inputs['Fac'])
    links.new(mix_normal_01.outputs['Color'], mix_normal_012.inputs['Color1'])
    links.new(tex_normal_2.outputs['Color'], mix_normal_012.inputs['Color2'])

    # Convert DirectX normal to OpenGL
    normal_dx_gl = nodes.new('ShaderNodeGroup')
    normal_dx_gl.node_tree = dx_to_gl_normal()
    normal_dx_gl.location = grid_location(4, 8)
    normal_dx_gl.hide = True
    links.new(mix_normal_012.outputs['Color'], normal_dx_gl.inputs['Color'])

    # Normal Map
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = grid_location(5, 8)
    normal_map.hide = True
    links.new(normal_dx_gl.outputs[0], normal_map.inputs['Color'])

    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = grid_location(6, 2)
    links.new(ao_multiply.outputs['Color'], principled.inputs['Base Color'])
    links.new(orm_012_sep.outputs[1], principled.inputs['Roughness'])
    links.new(orm_012_sep.outputs[2], principled.inputs['Metallic'])
    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])

    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = grid_location(7, 2)
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])