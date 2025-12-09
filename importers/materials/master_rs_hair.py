import bpy

from ...classes.material_instance import tpGxMaterialInstanceV2

from .nodes import dx_to_gl_normal, grid_location, texture_sampler

def master_rs_hair(textures_dir: str, material: bpy.types.Material, instance: tpGxMaterialInstanceV2):
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
    for texture in instance.texture_samplers:
        texture_filename_base = texture.texture_name.replace(".rtex", "")
        texture_filename = texture_filename_base + ".png"
        converted_textures.append(texture_filename)

    # texBaseColor     
    tex_base_color = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texBaseColor")
    tex_base_color.location = grid_location(0, 0)

    # texSecondAO
    tex_second_ao = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texSecondAO")
    tex_second_ao.location = grid_location(0, 1)

    #texSecondAO UV Map
    uv1 = nodes.new(type='ShaderNodeUVMap')
    uv1.uv_map = 'UVMap1'
    uv1.location = grid_location(-1, 1)
    uv1.hide = True
    links.new(uv1.outputs['UV'], tex_second_ao.inputs['Vector'])

    # texORM
    tex_orm = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texORM")
    tex_orm.image.colorspace_settings.name = 'Non-Color'
    tex_orm.location = grid_location(0, 2)

    # texNormal
    tex_normal = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texNormal")
    tex_orm.image.colorspace_settings.name = 'Non-Color'
    tex_normal.location = grid_location(0, 3)

    # texORM Separate Color
    tex_orm_sep = nodes.new(type=sepRGB_name)
    tex_orm_sep.location = grid_location(1, 2)
    tex_orm_sep.hide = True
    links.new(tex_orm.outputs['Color'], tex_orm_sep.inputs[sepRGB_input])

    # texNormal DirectX to OpenGl
    tex_normal_dx_gl = nodes.new('ShaderNodeGroup')
    tex_normal_dx_gl.node_tree = dx_to_gl_normal()
    tex_normal_dx_gl.location = grid_location(1, 3)
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
    normal_map.location = grid_location(2, 3)
    normal_map.hide = True
    links.new(tex_normal_dx_gl.outputs[0], normal_map.inputs['Color'])

    # texSecondAO multiply AO
    tex_second_ao_multiply = nodes.new('ShaderNodeMixRGB')
    tex_second_ao_multiply.location = grid_location(3, 1)
    tex_second_ao_multiply.hide = True
    tex_second_ao_multiply.blend_type = 'MULTIPLY'
    tex_second_ao_multiply.inputs[0].default_value = 0.0 if tex_second_ao.image is None else 1.0
    links.new(tex_orm_ao_multiply.outputs['Color'], tex_second_ao_multiply.inputs[1])
    links.new(tex_second_ao.outputs[0], tex_second_ao_multiply.inputs[2])

    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = grid_location(4, 1)
    links.new(tex_second_ao_multiply.outputs['Color'], principled.inputs['Base Color'])
    links.new(tex_base_color.outputs['Alpha'], principled.inputs['Alpha'])
    links.new(tex_orm_sep.outputs[1], principled.inputs['Roughness'])
    links.new(tex_orm_sep.outputs[2], principled.inputs['Metallic'])
    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])

    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = grid_location(5, 1)
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])