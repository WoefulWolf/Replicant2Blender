import bpy

from ...classes.asset_package import Asset

from ...util import search_texture, log
from .nodes import dx_to_gl_normal, grid_location

def master_rs_layer4(textures_dir: str, material: bpy.types.Material, asset: Asset):
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
    for texture in asset.textures:
        texture_filename_base = texture.texture_name.replace(".rtex", "")
        texture_filename = texture_filename_base + ".png"
        converted_textures.append(texture_filename)

    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = grid_location(8, 0)

    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = grid_location(7, 0)
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Mask
    mask_uv = nodes.new(type='ShaderNodeUVMap')
    mask_uv.uv_map = 'UVMap1'
    mask_uv.location = grid_location(-3, -10)
    mask_uv.hide = True

    mask_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texLayerMask"), None)
    if mask_texture_index is None:
        log.w(f"Failed to find texLayerMask in material: {material.name}")
        return

    mask_image = nodes.new(type='ShaderNodeTexImage')
    mask_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[mask_texture_index]))
    mask_image.image.colorspace_settings.name = 'Non-Color'
    mask_image.location = grid_location(-2, -10)
    mask_image.hide = True
    mask_image.label = "texLayerMask"

    links.new(mask_uv.outputs['UV'], mask_image.inputs['Vector'])

    mask_sep = nodes.new(type=sepRGB_name)
    mask_sep.location = grid_location(-1, -10)
    mask_sep.hide = True
    links.new(mask_image.outputs['Color'], mask_sep.inputs[sepRGB_input])

    # Color 0
    color_0_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texBaseColor0"), None)
    if color_0_texture_index is None:
        log.w(f"Failed to find texBaseColor0 in material: {material.name}")
        return
    color_0_image = nodes.new(type='ShaderNodeTexImage')
    color_0_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_0_texture_index]))
    color_0_image.location = grid_location(-2, -8)
    color_0_image.hide = True
    color_0_image.label = "texBaseColor0"

    # Color 1
    color_1_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texBaseColor1"), None)
    if color_1_texture_index is None:
        log.w(f"Failed to find texBaseColor1 in material: {material.name}")
        return
    color_1_image = nodes.new(type='ShaderNodeTexImage')
    color_1_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_1_texture_index]))
    color_1_image.location = grid_location(-2, -6)
    color_1_image.hide = True
    color_1_image.label = "texBaseColor1"

    # Color 2
    color_2_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texBaseColor2"), None)
    if color_2_texture_index is None:
        log.w(f"Failed to find texBaseColor2 in material: {material.name}")
        return
    color_2_image = nodes.new(type='ShaderNodeTexImage')
    color_2_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_2_texture_index]))
    color_2_image.location = grid_location(-2, -4)
    color_2_image.hide = True
    color_2_image.label = "texBaseColor2"

    # Color 3
    color_3_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texBaseColor3"), None)
    if color_3_texture_index is None:
        log.w(f"Failed to find texBaseColor3 in material: {material.name}")
        return
    color_3_image = nodes.new(type='ShaderNodeTexImage')
    color_3_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_3_texture_index]))
    color_3_image.location = grid_location(-2, -2)
    color_3_image.hide = True
    color_3_image.label = "texBaseColor3"

    # Mix Color 0-1
    mix_col_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_01.location = grid_location(1, -7)
    mix_col_01.hide = True
    links.new(mask_sep.outputs[0], mix_col_01.inputs['Fac'])
    links.new(color_0_image.outputs['Color'], mix_col_01.inputs['Color1'])
    links.new(color_1_image.outputs['Color'], mix_col_01.inputs['Color2'])

    # Mix Color 0-1-2
    mix_col_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_012.location = grid_location(2, -6)
    mix_col_012.hide = True
    links.new(mask_sep.outputs[1], mix_col_012.inputs['Fac'])
    links.new(mix_col_01.outputs['Color'], mix_col_012.inputs['Color1'])
    links.new(color_2_image.outputs['Color'], mix_col_012.inputs['Color2'])

    # Mix Color 0-1-2-3
    mix_col_0123 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_0123.location = grid_location(3, -5)
    mix_col_0123.hide = True
    links.new(mask_sep.outputs[2], mix_col_0123.inputs['Fac'])
    links.new(mix_col_012.outputs['Color'], mix_col_0123.inputs['Color1'])
    links.new(color_3_image.outputs['Color'], mix_col_0123.inputs['Color2'])

    links.new(mix_col_0123.outputs['Color'], principled.inputs['Base Color'])

    # ORM 0
    orm_0_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texORM0"), None)
    if orm_0_texture_index is None:
        log.w(f"Failed to find texORM0 in material: {material.name}")
        return
    orm_0_image = nodes.new(type='ShaderNodeTexImage')
    orm_0_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_0_texture_index]))
    orm_0_image.image.colorspace_settings.name = 'Non-Color'
    orm_0_image.location = grid_location(-2, 0)
    orm_0_image.hide = True
    orm_0_image.label = "texORM0"

    orm_0_sep = nodes.new(type=sepRGB_name)
    orm_0_sep.location = grid_location(-1, 0)
    orm_0_sep.hide = True
    links.new(orm_0_image.outputs['Color'], orm_0_sep.inputs[sepRGB_input])

    # ORM 1
    orm_1_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texORM1"), None)
    if orm_1_texture_index is None:
        log.w(f"Failed to find texORM1 in material: {material.name}")
        return
    orm_1_image = nodes.new(type='ShaderNodeTexImage')
    orm_1_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_1_texture_index]))
    orm_1_image.image.colorspace_settings.name = 'Non-Color'
    orm_1_image.location = grid_location(-2, 2)
    orm_1_image.hide = True
    orm_1_image.label = "texORM1"

    orm_1_sep = nodes.new(type=sepRGB_name)
    orm_1_sep.location = grid_location(-1, 2)
    orm_1_sep.hide = True
    links.new(orm_1_image.outputs['Color'], orm_1_sep.inputs[sepRGB_input])

    # ORM 2
    orm_2_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texORM2"), None)
    if orm_2_texture_index is None:
        log.w(f"Failed to find texORM2 in material: {material.name}")
        return
    orm_2_image = nodes.new(type='ShaderNodeTexImage')
    orm_2_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_2_texture_index]))
    orm_2_image.image.colorspace_settings.name = 'Non-Color'
    orm_2_image.location = grid_location(-2, 4)
    orm_2_image.hide = True
    orm_2_image.label = "texORM2"

    orm_2_sep = nodes.new(type=sepRGB_name)
    orm_2_sep.location = grid_location(-1, 4)
    orm_2_sep.hide = True
    links.new(orm_2_image.outputs['Color'], orm_2_sep.inputs[sepRGB_input])

    # ORM 3
    orm_3_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texORM3"), None)
    if orm_3_texture_index is None:
        log.w(f"Failed to find texORM3 in material: {material.name}")
        return
    orm_3_image = nodes.new(type='ShaderNodeTexImage')
    orm_3_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_3_texture_index]))
    orm_3_image.image.colorspace_settings.name = 'Non-Color'
    orm_3_image.location = grid_location(-2, 6)
    orm_3_image.hide = True
    orm_3_image.label = "texORM3"

    orm_3_sep = nodes.new(type=sepRGB_name)
    orm_3_sep.location = grid_location(-1, 6)
    orm_3_sep.hide = True
    links.new(orm_3_image.outputs['Color'], orm_3_sep.inputs[sepRGB_input])

    # Mix O 0-1
    mix_o_01 = nodes.new(type='ShaderNodeMix')
    mix_o_01.location = grid_location(1, 1)
    mix_o_01.hide = True
    links.new(mask_sep.outputs[0], mix_o_01.inputs['Factor'])
    links.new(orm_0_sep.outputs[0], mix_o_01.inputs['A'])
    links.new(orm_1_sep.outputs[0], mix_o_01.inputs['B'])

    # Mix O 0-1-2
    mix_o_012 = nodes.new(type='ShaderNodeMix')
    mix_o_012.location = grid_location(2, 2)
    mix_o_012.hide = True
    links.new(mask_sep.outputs[1], mix_o_012.inputs['Factor'])
    links.new(mix_o_01.outputs[0], mix_o_012.inputs['A'])
    links.new(orm_2_sep.outputs[0], mix_o_012.inputs['B'])

    # Mix O 0-1-2-3
    mix_o_0123 = nodes.new(type='ShaderNodeMix')
    mix_o_0123.location = grid_location(3, 3)
    mix_o_0123.hide = True
    links.new(mask_sep.outputs[2], mix_o_0123.inputs['Factor'])
    links.new(mix_o_012.outputs[0], mix_o_0123.inputs['A'])
    links.new(orm_3_sep.outputs[0], mix_o_0123.inputs['B'])

    # Ambient Occlusion
    ao_multiply = nodes.new('ShaderNodeMixRGB')
    ao_multiply.location = grid_location(4, 3)
    ao_multiply.hide = True
    ao_multiply.blend_type = 'MULTIPLY'
    ao_multiply.inputs[0].default_value = 1.0
    links.new(mix_col_0123.outputs['Color'], ao_multiply.inputs[1])
    links.new(mix_o_0123.outputs[0], ao_multiply.inputs[2])

    links.new(ao_multiply.outputs['Color'], principled.inputs['Base Color'])

    # Mix R 0-1
    mix_r_01 = nodes.new(type='ShaderNodeMix')
    mix_r_01.location = grid_location(1, 3)
    mix_r_01.hide = True
    links.new(mask_sep.outputs[0], mix_r_01.inputs['Factor'])
    links.new(orm_0_sep.outputs[1], mix_r_01.inputs['A'])
    links.new(orm_1_sep.outputs[1], mix_r_01.inputs['B'])

    # Mix R 0-1-2
    mix_r_012 = nodes.new(type='ShaderNodeMix')
    mix_r_012.location = grid_location(2, 4)
    mix_r_012.hide = True
    links.new(mask_sep.outputs[1], mix_r_012.inputs['Factor'])
    links.new(mix_r_01.outputs[0], mix_r_012.inputs['A'])
    links.new(orm_2_sep.outputs[1], mix_r_012.inputs['B'])

    # Mix R 0-1-2-3
    mix_r_0123 = nodes.new(type='ShaderNodeMix')
    mix_r_0123.location = grid_location(3, 4)
    mix_r_0123.hide = True
    links.new(mask_sep.outputs[2], mix_r_0123.inputs['Factor'])
    links.new(mix_r_012.outputs[0], mix_r_0123.inputs['A'])
    links.new(orm_3_sep.outputs[1], mix_r_0123.inputs['B'])

    # Roughness
    links.new(mix_r_0123.outputs[0], principled.inputs['Roughness'])

    # Mix M 0-1
    mix_m_01 = nodes.new(type='ShaderNodeMix')
    mix_m_01.location = grid_location(1, 5)
    mix_m_01.hide = True
    links.new(mask_sep.outputs[0], mix_m_01.inputs['Factor'])
    links.new(orm_0_sep.outputs[2], mix_m_01.inputs['A'])
    links.new(orm_1_sep.outputs[2], mix_m_01.inputs['B'])

    # Mix M 0-1-2
    mix_m_012 = nodes.new(type='ShaderNodeMix')
    mix_m_012.location = grid_location(2, 6)
    mix_m_012.hide = True
    links.new(mask_sep.outputs[1], mix_m_012.inputs['Factor'])
    links.new(mix_m_01.outputs[0], mix_m_012.inputs['A'])
    links.new(orm_2_sep.outputs[2], mix_m_012.inputs['B'])

    # Mix M 0-1-2-3
    mix_m_0123 = nodes.new(type='ShaderNodeMix')
    mix_m_0123.location = grid_location(3, 6)
    mix_m_0123.hide = True
    links.new(mask_sep.outputs[2], mix_m_0123.inputs['Factor'])
    links.new(mix_m_012.outputs[0], mix_m_0123.inputs['A'])
    links.new(orm_3_sep.outputs[2], mix_m_0123.inputs['B'])

    # Metallic
    links.new(mix_m_0123.outputs[0], principled.inputs['Metallic'])

    # Normal 0
    normal_0_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texNormal0"), None)
    if normal_0_texture_index is None:
        log.w(f"Failed to find texNormal0 in material: {material.name}")
        return
    normal_0_image = nodes.new(type='ShaderNodeTexImage')
    normal_0_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_0_texture_index]))
    normal_0_image.image.colorspace_settings.name = 'Non-Color'
    normal_0_image.location = grid_location(-2, 9)
    normal_0_image.hide = True
    normal_0_image.label = "texNormal0"

    # Normal 1
    normal_1_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texNormal1"), None)
    if normal_1_texture_index is None:
        log.w(f"Failed to find texNormal1 in material: {material.name}")
        return
    normal_1_image = nodes.new(type='ShaderNodeTexImage')
    normal_1_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_1_texture_index]))
    normal_1_image.image.colorspace_settings.name = 'Non-Color'
    normal_1_image.location = grid_location(-2, 11)
    normal_1_image.hide = True
    normal_1_image.label = "texNormal1"

    # Normal 2
    normal_2_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texNormal2"), None)
    if normal_2_texture_index is None:
        log.w(f"Failed to find texNormal2 in material: {material.name}")
        return
    normal_2_image = nodes.new(type='ShaderNodeTexImage')
    normal_2_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_2_texture_index]))
    normal_2_image.image.colorspace_settings.name = 'Non-Color'
    normal_2_image.location = grid_location(-2, 13)
    normal_2_image.hide = True
    normal_2_image.label = "texNormal2"

    # Normal 3
    normal_3_texture_index = next((i for i, x in enumerate(asset.textures) if x.sampler_name == "texNormal3"), None)
    if normal_3_texture_index is None:
        log.w(f"Failed to find texNormal3 in material: {material.name}")
        return
    normal_3_image = nodes.new(type='ShaderNodeTexImage')
    normal_3_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_3_texture_index]))
    normal_3_image.image.colorspace_settings.name = 'Non-Color'
    normal_3_image.location = grid_location(-2, 14)
    normal_3_image.hide = True
    normal_3_image.label = "texNormal3"

    # Mix Normal 0-1
    mix_normal_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_01.location = grid_location(1, 10)
    mix_normal_01.hide = True
    links.new(mask_sep.outputs[0], mix_normal_01.inputs['Fac'])
    links.new(normal_0_image.outputs['Color'], mix_normal_01.inputs['Color1'])
    links.new(normal_1_image.outputs['Color'], mix_normal_01.inputs['Color2'])

    # Mix Normal 0-1-2
    mix_normal_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_012.location = grid_location(2, 11)
    mix_normal_012.hide = True
    links.new(mask_sep.outputs[1], mix_normal_012.inputs['Fac'])
    links.new(mix_normal_01.outputs['Color'], mix_normal_012.inputs['Color1'])
    links.new(normal_2_image.outputs['Color'], mix_normal_012.inputs['Color2'])

    # Mix Normal 0-1-2-3
    mix_normal_0123 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_0123.location = grid_location(3, 13)
    mix_normal_0123.hide = True
    links.new(mask_sep.outputs[2], mix_normal_0123.inputs['Fac'])
    links.new(mix_normal_012.outputs['Color'], mix_normal_0123.inputs['Color1'])
    links.new(normal_3_image.outputs['Color'], mix_normal_0123.inputs['Color2'])

    # Convert DirectX normal to OpenGL
    normal_convert = nodes.new('ShaderNodeGroup')
    normal_convert.node_tree = dx_to_gl_normal()
    normal_convert.location = grid_location(4, 13)
    normal_convert.hide = True
    links.new(mix_normal_0123.outputs['Color'], normal_convert.inputs['Color'])

    # Normal Map
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = grid_location(6, 13)
    normal_map.hide = True
    links.new(normal_convert.outputs[0], normal_map.inputs['Color'])

    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])