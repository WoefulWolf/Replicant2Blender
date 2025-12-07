import bpy

from ...classes.material_instance import tpGxMaterialInstanceV2

from .nodes import constant_buffer_value, dx_to_gl_normal, grid_location, texture_sampler

def master_rs_leaf(textures_dir: str, material: bpy.types.Material, instance: tpGxMaterialInstanceV2):
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

    converted_textures: list[str] = []
    for texture in instance.textures:
        texture_filename_base = texture.texture_name.replace(".rtex", "")
        texture_filename = texture_filename_base + ".png"
        converted_textures.append(texture_filename)

    # UV Map
    uv0 = nodes.new(type='ShaderNodeUVMap')
    uv0.uv_map = 'UVMap0'
    uv0.location = grid_location(-2, -1)
    uv0.hide = True

    # Mapping
    mapping = nodes.new(type='ShaderNodeMapping')
    mapping.location = grid_location(-1, 0)
    mapping.hide = True
    links.new(uv0.outputs['UV'], mapping.inputs['Vector'])

    # gUVOffset
    g_uv_offset = constant_buffer_value(material, nodes, instance, "CbLeaf", "gUVOffset")
    if g_uv_offset is not None:
        g_uv_offset.location = grid_location(-2, 0)
        links.new(g_uv_offset.outputs[0], mapping.inputs['Location'])

    # gUVScale
    g_uv_scale = constant_buffer_value(material, nodes, instance, "CbLeaf", "gUVScale")
    if g_uv_scale is not None:
        g_uv_scale.location = grid_location(-2, 1)
        links.new(g_uv_scale.outputs[0], mapping.inputs['Scale'])

    # texBaseColor     
    tex_base_color = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texBaseColor")
    tex_base_color.location = grid_location(0, 0)
    links.new(mapping.outputs['Vector'], tex_base_color.inputs['Vector'])

    # texORM
    tex_orm = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texORM")
    if tex_orm.image is not None:
        tex_orm.image.colorspace_settings.name = 'Non-Color'
    tex_orm.location = grid_location(0, 1)
    links.new(mapping.outputs['Vector'], tex_orm.inputs['Vector'])

    # texNormal
    tex_normal = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texNormal")
    if tex_normal.image is not None:
        tex_normal.image.colorspace_settings.name = 'Non-Color'
    tex_normal.location = grid_location(0, 2)
    links.new(mapping.outputs['Vector'], tex_normal.inputs['Vector'])

    # texThickness
    tex_thickness = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texThickness")
    if tex_thickness.image is not None:
        tex_thickness.image.colorspace_settings.name = 'Non-Color'
    tex_thickness.location = grid_location(0, 3)
    links.new(mapping.outputs['Vector'], tex_thickness.inputs['Vector'])

    # texORM Separate Color
    tex_orm_sep = nodes.new(type=sepRGB_name)
    tex_orm_sep.location = grid_location(1, 1)
    tex_orm_sep.hide = True
    links.new(tex_orm.outputs['Color'], tex_orm_sep.inputs[sepRGB_input])

    # texNormal DirectX to OpenGl
    tex_normal_dx_gl = nodes.new('ShaderNodeGroup')
    tex_normal_dx_gl.node_tree = dx_to_gl_normal()
    tex_normal_dx_gl.location = grid_location(1, 2)
    tex_normal_dx_gl.hide = True
    links.new(tex_normal.outputs['Color'], tex_normal_dx_gl.inputs['Color'])

    # texORM multiply AO
    tex_orm_ao_multiply = nodes.new('ShaderNodeMixRGB')
    tex_orm_ao_multiply.location = grid_location(2, 0)
    tex_orm_ao_multiply.hide = True
    tex_orm_ao_multiply.blend_type = 'MULTIPLY'
    tex_orm_ao_multiply.inputs[0].default_value = 1.0
    links.new(tex_base_color.outputs['Color'], tex_orm_ao_multiply.inputs[1])
    links.new(tex_orm_sep.outputs[0], tex_orm_ao_multiply.inputs[2])

    # Normal Map
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = grid_location(2, 2)
    normal_map.hide = True
    links.new(tex_normal_dx_gl.outputs[0], normal_map.inputs['Color'])

    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = grid_location(3, 0)
    links.new(tex_orm_ao_multiply.outputs['Color'], principled.inputs['Base Color'])
    links.new(tex_base_color.outputs['Alpha'], principled.inputs['Alpha'])
    links.new(tex_orm_sep.outputs[1], principled.inputs['Roughness'])
    links.new(tex_orm_sep.outputs[2], principled.inputs['Metallic'])
    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
    links.new(tex_thickness.outputs['Color'], principled.inputs['Subsurface Weight'])
    principled.inputs['Subsurface Radius'].default_value = (1, 1, 1)
    principled.inputs['Subsurface Scale'].default_value = 10

    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = grid_location(4, 0)
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])