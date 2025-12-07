import bpy

from ...classes.material_instance import tpGxMaterialInstanceV2

from .nodes import constant_buffer_value, dx_to_gl_normal, grid_location, texture_sampler

def master_rs_xlu_water(textures_dir: str, material: bpy.types.Material, instance: tpGxMaterialInstanceV2):
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
    material.volume_intersection_method = 'ACCURATE'

    converted_textures: list[str] = []
    for texture in instance.textures:
        texture_filename_base = texture.texture_name.replace(".rtex", "")
        texture_filename = texture_filename_base + ".png"
        converted_textures.append(texture_filename)

    # Time
    time = nodes.new(type='ShaderNodeValue')
    time.location = grid_location(0, 0)
    time.label = "Time"
    time.hide = True
    driver_target_property = 'outputs["Value"].default_value'
    driver = material.node_tree.driver_add(f'nodes["{time.name}"].{driver_target_property}')
    driver.driver.type = 'SCRIPTED'
    driver.driver.expression = 'frame / 60.0'
    bpy.context.view_layer.update()

    # UVMap0
    uv0 = nodes.new(type='ShaderNodeUVMap')
    uv0.uv_map = 'UVMap0'
    uv0.location = grid_location(0, 1)
    uv0.label = 'UVMap0'
    uv0.hide = True

    # gUVOffset0
    g_uv_offset_0 = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gUVOffset0")
    if g_uv_offset_0 is not None:
        g_uv_offset_0.location = grid_location(0, 2)

    # gUVOffset0 multiply Time
    g_uv_offset_0_mul_time = nodes.new(type='ShaderNodeVectorMath')
    g_uv_offset_0_mul_time.operation = 'MULTIPLY'
    g_uv_offset_0_mul_time.location = grid_location(1, 2)
    g_uv_offset_0_mul_time.hide = True
    if g_uv_offset_0 is not None:
        links.new(time.outputs['Value'], g_uv_offset_0_mul_time.inputs[0])
        links.new(g_uv_offset_0.outputs['Vector'], g_uv_offset_0_mul_time.inputs[1])

    # gUVScale0
    g_uv_scale_0 = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gUVScale0")
    if g_uv_scale_0 is not None:
        g_uv_scale_0.location = grid_location(0, 3)

    # Mapping0
    mapping_0 = nodes.new(type='ShaderNodeMapping')
    mapping_0.location = grid_location(2, 2)
    mapping_0.hide = True
    links.new(uv0.outputs['UV'], mapping_0.inputs['Vector'])
    links.new(g_uv_offset_0_mul_time.outputs['Vector'], mapping_0.inputs['Location'])
    if g_uv_scale_0 is not None:
        links.new(g_uv_scale_0.outputs['Vector'], mapping_0.inputs['Scale'])

    # gUVOffset1
    g_uv_offset_1 = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gUVOffset1")
    if g_uv_offset_1 is not None:
        g_uv_offset_1.location = grid_location(0, 4)

    # gUVOffset1 multiply Time
    g_uv_offset_1_mul_time = nodes.new(type='ShaderNodeVectorMath')
    g_uv_offset_1_mul_time.operation = 'MULTIPLY'
    g_uv_offset_1_mul_time.location = grid_location(1, 4)
    g_uv_offset_1_mul_time.hide = True
    if g_uv_offset_1 is not None:
        links.new(time.outputs['Value'], g_uv_offset_1_mul_time.inputs[0])
        links.new(g_uv_offset_1.outputs['Vector'], g_uv_offset_1_mul_time.inputs[1])

    # gUVScale1
    g_uv_scale_1 = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gUVScale1")
    if g_uv_scale_1 is not None:
        g_uv_scale_1.location = grid_location(0, 5)

    # Mapping1
    mapping_1 = nodes.new(type='ShaderNodeMapping')
    mapping_1.location = grid_location(2, 4)
    mapping_1.hide = True
    links.new(uv0.outputs['UV'], mapping_1.inputs['Vector'])
    links.new(g_uv_offset_1_mul_time.outputs['Vector'], mapping_1.inputs['Location'])
    if g_uv_scale_1 is not None:
        links.new(g_uv_scale_1.outputs['Vector'], mapping_1.inputs['Scale'])

    # gBaseColor
    g_base_color = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gBaseColor")
    if g_base_color is not None:
        g_base_color.location = grid_location(3, 1)

    # texORM
    tex_orm = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texORM")
    if tex_orm.image is not None:
        tex_orm.image.colorspace_settings.name = 'Non-Color'
    tex_orm.location = grid_location(3, 2)
    links.new(mapping_0.outputs['Vector'], tex_orm.inputs['Vector'])

    # texNormal0
    tex_normal_0 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texNormal0")
    if tex_normal_0.image is not None:
        tex_normal_0.image.colorspace_settings.name = 'Non-Color'
    tex_normal_0.location = grid_location(3, 3)
    links.new(mapping_0.outputs['Vector'], tex_normal_0.inputs['Vector'])

    # texNormal1
    tex_normal_1 = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texNormal1")
    if tex_normal_1.image is not None:
        tex_normal_1.image.colorspace_settings.name = 'Non-Color'
    tex_normal_1.location = grid_location(3, 4)
    links.new(mapping_1.outputs['Vector'], tex_normal_1.inputs['Vector'])

    # texFoamColor
    tex_foam_color = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texFoamColor")
    tex_foam_color.location = grid_location(3, 5)
    links.new(mapping_0.outputs['Vector'], tex_foam_color.inputs['Vector'])

    # texFoamIntensity
    tex_foam_intensity = texture_sampler(material, nodes, instance, textures_dir, converted_textures, "texFoamIntensity")
    tex_foam_intensity.location = grid_location(3, 6)
    links.new(mapping_0.outputs['Vector'], tex_foam_intensity.inputs['Vector'])

    # Color0
    color_0 = nodes.new(type='ShaderNodeAttribute')
    color_0.attribute_name = 'Color0'
    color_0.location = grid_location(3, 7)
    color_0.hide = True

    # texORM Separate Color
    tex_orm_sep = nodes.new(type=sepRGB_name)
    tex_orm_sep.location = grid_location(4, 2)
    tex_orm_sep.hide = True
    links.new(tex_orm.outputs['Color'], tex_orm_sep.inputs[sepRGB_input])

    # texNormal0 add texNormal1
    tex_normal_0_add_tex_normal_1 = nodes.new(type='ShaderNodeVectorMath')
    tex_normal_0_add_tex_normal_1.operation = 'ADD'
    tex_normal_0_add_tex_normal_1.location = grid_location(4, 3)
    tex_normal_0_add_tex_normal_1.hide = True
    links.new(tex_normal_0.outputs['Color'], tex_normal_0_add_tex_normal_1.inputs[0])
    links.new(tex_normal_1.outputs['Color'], tex_normal_0_add_tex_normal_1.inputs[1])

    # Color0 Separate Color
    color_0_sep = nodes.new(type=sepRGB_name)
    color_0_sep.location = grid_location(4, 7)
    color_0_sep.hide = True
    links.new(color_0.outputs['Color'], color_0_sep.inputs[sepRGB_input])

    # texNormal normalize
    tex_normal_normalize = nodes.new(type='ShaderNodeVectorMath')
    tex_normal_normalize.operation = 'NORMALIZE'
    tex_normal_normalize.location = grid_location(5, 3)
    tex_normal_normalize.hide = True
    links.new(tex_normal_0_add_tex_normal_1.outputs['Vector'], tex_normal_normalize.inputs[0])

    # texNormal DirectX to OpenGl
    tex_normal_dx_gl = nodes.new('ShaderNodeGroup')
    tex_normal_dx_gl.node_tree = dx_to_gl_normal()
    tex_normal_dx_gl.location = grid_location(6, 3)
    tex_normal_dx_gl.hide = True
    links.new(tex_normal_normalize.outputs[0], tex_normal_dx_gl.inputs['Color'])

    # texFoamIntensity multiply Color0 Red
    tex_foam_intensity_mul_color_0_sep = nodes.new(type='ShaderNodeMath')
    tex_foam_intensity_mul_color_0_sep.operation = 'MULTIPLY'
    tex_foam_intensity_mul_color_0_sep.location = grid_location(6, 6)
    tex_foam_intensity_mul_color_0_sep.hide = True
    links.new(tex_foam_intensity.outputs['Color'], tex_foam_intensity_mul_color_0_sep.inputs[0])
    links.new(color_0_sep.outputs[0], tex_foam_intensity_mul_color_0_sep.inputs[1])

    # gBaseColor mix texFoamColor
    g_base_color_mix_tex_foam_color = nodes.new(type='ShaderNodeMixRGB')
    g_base_color_mix_tex_foam_color.location = grid_location(7, 1)
    g_base_color_mix_tex_foam_color.hide = True
    links.new(tex_foam_intensity_mul_color_0_sep.outputs[0], g_base_color_mix_tex_foam_color.inputs[0])
    links.new(g_base_color.outputs['Color'], g_base_color_mix_tex_foam_color.inputs['Color1'])
    links.new(tex_foam_color.outputs['Color'], g_base_color_mix_tex_foam_color.inputs['Color2'])

    # texORM Rughness mix 1.0
    roughness_mix_1 = nodes.new(type='ShaderNodeMix')
    roughness_mix_1.location = grid_location(7, 2)
    roughness_mix_1.hide = True
    links.new(tex_foam_intensity_mul_color_0_sep.outputs[0], roughness_mix_1.inputs[0])
    links.new(tex_orm_sep.outputs[1], roughness_mix_1.inputs['A'])
    roughness_mix_1.inputs['B'].default_value = 1

    # Normal Map
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = grid_location(7, 3)
    normal_map.hide = True
    links.new(tex_normal_dx_gl.outputs[0], normal_map.inputs['Color'])

    # gIor
    g_ior = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gIor")
    if g_ior is not None:
        g_ior.location = grid_location(7, 4)

    # Alpha 0.7 mix 1.0
    alpha_07_mix_1 = nodes.new(type='ShaderNodeMix')
    alpha_07_mix_1.location = grid_location(7, 5)
    alpha_07_mix_1.hide = True
    links.new(tex_foam_intensity_mul_color_0_sep.outputs[0], alpha_07_mix_1.inputs[0])
    alpha_07_mix_1.inputs['A'].default_value = 0.7
    alpha_07_mix_1.inputs['B'].default_value = 1

    # Transmission 1.0 mix 0.0
    transmission_1_mix_0 = nodes.new(type='ShaderNodeMix')
    transmission_1_mix_0.location = grid_location(7, 6)
    transmission_1_mix_0.hide = True
    links.new(tex_foam_intensity_mul_color_0_sep.outputs[0], transmission_1_mix_0.inputs[0])
    transmission_1_mix_0.inputs['A'].default_value = 1
    transmission_1_mix_0.inputs['B'].default_value = 0

    # texORM multiply AO
    tex_orm_ao_multiply = nodes.new('ShaderNodeMixRGB')
    tex_orm_ao_multiply.location = grid_location(8, 1)
    tex_orm_ao_multiply.hide = True
    tex_orm_ao_multiply.blend_type = 'MULTIPLY'
    tex_orm_ao_multiply.inputs[0].default_value = 1.0
    links.new(g_base_color_mix_tex_foam_color.outputs['Color'], tex_orm_ao_multiply.inputs[1])
    links.new(tex_orm_sep.outputs[0], tex_orm_ao_multiply.inputs[2])

    # gIor add 1
    g_ior_add_1 = nodes.new(type='ShaderNodeMath')
    g_ior_add_1.operation = 'ADD'
    g_ior_add_1.location = grid_location(8, 4)
    g_ior_add_1.hide = True
    if g_ior is not None:
        links.new(g_ior.outputs['Value'], g_ior_add_1.inputs[0])
    else:
        g_ior_add_1.inputs[0].default_value = 0.333
    g_ior_add_1.inputs[1].default_value = 1

    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = grid_location(9, 1)
    links.new(tex_orm_ao_multiply.outputs['Color'], principled.inputs['Base Color'])
    links.new(tex_orm_sep.outputs[2], principled.inputs['Metallic'])
    links.new(roughness_mix_1.outputs[0], principled.inputs['Roughness'])
    links.new(g_ior_add_1.outputs[0], principled.inputs['IOR'])
    links.new(alpha_07_mix_1.outputs[0], principled.inputs['Alpha'])
    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
    links.new(transmission_1_mix_0.outputs[0], principled.inputs['Transmission Weight'])

    # gFogColor
    g_fog_color = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gFogColor")
    if g_fog_color is not None:
        g_fog_color.location = grid_location(10, 2)

    # gFogDensity
    g_fog_density = constant_buffer_value(material, nodes, instance, "CbTransparentWater", "gFogDensity")
    if g_fog_density is not None:
        g_fog_density.location = grid_location(10, 3)

    # Volume Absorption
    volume_absorption = nodes.new(type='ShaderNodeVolumeAbsorption')
    volume_absorption.location = grid_location(11, 2)
    links.new(g_fog_color.outputs['Color'], volume_absorption.inputs['Color'])
    links.new(g_fog_density.outputs['Value'], volume_absorption.inputs['Density'])

    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = grid_location(12, 1)
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    links.new(volume_absorption.outputs['Volume'], output.inputs['Volume'])