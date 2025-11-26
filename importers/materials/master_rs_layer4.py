import bpy

from ...util import search_texture, log

from ...classes.tpGxAssetHeader import UnknownAsset

def master_rs_layer4(textures_dir, material, asset: UnknownAsset):
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

    converted_textures = []
    for texture in asset.textures:
        texture_filename_base = texture.filename.replace(".rtex", "")
        texture_filename = texture_filename_base + ".png"
        converted_textures.append(texture_filename)

    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = 2400, 0

    # Principled BSDF
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = 2100, 0
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # Mask
    mask_uv = nodes.new(type='ShaderNodeUVMap')
    mask_uv.uv_map = 'UVMap1'
    mask_uv.location = -900, 800
    mask_uv.hide = True

    mask_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texLayerMask"), None)
    if mask_texture_index is None:
        log.w(f"Failed to find texLayerMask in material: {material.name}")
        return

    mask_image = nodes.new(type='ShaderNodeTexImage')
    mask_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[mask_texture_index]))
    mask_image.image.colorspace_settings.name = 'Non-Color'
    mask_image.location = -600, 800
    mask_image.hide = True

    links.new(mask_uv.outputs['UV'], mask_image.inputs['Vector'])

    mask_sep = nodes.new(type=sepRGB_name)
    mask_sep.location = -300, 800
    mask_sep.hide = True
    links.new(mask_image.outputs['Color'], mask_sep.inputs[sepRGB_input])

    # Color 0
    color_0_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texBaseColor0"), None)
    if color_0_texture_index is None:
        log.w(f"Failed to find texBaseColor0 in material: {material.name}")
        return
    color_0_image = nodes.new(type='ShaderNodeTexImage')
    color_0_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_0_texture_index]))
    color_0_image.location = -600, 600
    color_0_image.hide = True

    # Color 1
    color_1_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texBaseColor1"), None)
    if color_1_texture_index is None:
        log.w(f"Failed to find texBaseColor1 in material: {material.name}")
        return
    color_1_image = nodes.new(type='ShaderNodeTexImage')
    color_1_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_1_texture_index]))
    color_1_image.location = -600, 450
    color_1_image.hide = True

    # Color 2
    color_2_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texBaseColor2"), None)
    if color_2_texture_index is None:
        log.w(f"Failed to find texBaseColor2 in material: {material.name}")
        return
    color_2_image = nodes.new(type='ShaderNodeTexImage')
    color_2_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_2_texture_index]))
    color_2_image.location = -600, 300
    color_2_image.hide = True

    # Color 3
    color_3_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texBaseColor3"), None)
    if color_3_texture_index is None:
        log.w(f"Failed to find texBaseColor3 in material: {material.name}")
        return
    color_3_image = nodes.new(type='ShaderNodeTexImage')
    color_3_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[color_3_texture_index]))
    color_3_image.location = -600, 150
    color_3_image.hide = True

    # Mix Color 0-1
    mix_col_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_01.location = 200, 525
    mix_col_01.hide = True
    links.new(mask_sep.outputs[0], mix_col_01.inputs['Fac'])
    links.new(color_0_image.outputs['Color'], mix_col_01.inputs['Color1'])
    links.new(color_1_image.outputs['Color'], mix_col_01.inputs['Color2'])

    # Mix Color 0-1-2
    mix_col_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_012.location = 600, 450
    mix_col_012.hide = True
    links.new(mask_sep.outputs[1], mix_col_012.inputs['Fac'])
    links.new(mix_col_01.outputs['Color'], mix_col_012.inputs['Color1'])
    links.new(color_2_image.outputs['Color'], mix_col_012.inputs['Color2'])

    # Mix Color 0-1-2-3
    mix_col_0123 = nodes.new(type='ShaderNodeMixRGB')
    mix_col_0123.location = 1000, 400
    mix_col_0123.hide = True
    links.new(mask_sep.outputs[2], mix_col_0123.inputs['Fac'])
    links.new(mix_col_012.outputs['Color'], mix_col_0123.inputs['Color1'])
    links.new(color_3_image.outputs['Color'], mix_col_0123.inputs['Color2'])

    links.new(mix_col_0123.outputs['Color'], principled.inputs['Base Color'])

    # ORM 0
    orm_0_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texORM0"), None)
    if orm_0_texture_index is None:
        log.w(f"Failed to find texORM0 in material: {material.name}")
        return
    orm_0_image = nodes.new(type='ShaderNodeTexImage')
    orm_0_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_0_texture_index]))
    orm_0_image.image.colorspace_settings.name = 'Non-Color'
    orm_0_image.location = -600, 0
    orm_0_image.hide = True

    orm_0_sep = nodes.new(type=sepRGB_name)
    orm_0_sep.location = -300, 0
    orm_0_sep.hide = True
    links.new(orm_0_image.outputs['Color'], orm_0_sep.inputs[sepRGB_input])

    # ORM 1
    orm_1_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texORM1"), None)
    if orm_1_texture_index is None:
        log.w(f"Failed to find texORM1 in material: {material.name}")
        return
    orm_1_image = nodes.new(type='ShaderNodeTexImage')
    orm_1_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_1_texture_index]))
    orm_1_image.image.colorspace_settings.name = 'Non-Color'
    orm_1_image.location = -600, -150
    orm_1_image.hide = True

    orm_1_sep = nodes.new(type=sepRGB_name)
    orm_1_sep.location = -300, -150
    orm_1_sep.hide = True
    links.new(orm_1_image.outputs['Color'], orm_1_sep.inputs[sepRGB_input])

    # ORM 2
    orm_2_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texORM2"), None)
    if orm_2_texture_index is None:
        log.w(f"Failed to find texORM2 in material: {material.name}")
        return
    orm_2_image = nodes.new(type='ShaderNodeTexImage')
    orm_2_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_2_texture_index]))
    orm_2_image.image.colorspace_settings.name = 'Non-Color'
    orm_2_image.location = -600, -300
    orm_2_image.hide = True

    orm_2_sep = nodes.new(type=sepRGB_name)
    orm_2_sep.location = -300, -300
    orm_2_sep.hide = True
    links.new(orm_2_image.outputs['Color'], orm_2_sep.inputs[sepRGB_input])

    # ORM 3
    orm_3_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texORM3"), None)
    if orm_3_texture_index is None:
        log.w(f"Failed to find texORM3 in material: {material.name}")
        return
    orm_3_image = nodes.new(type='ShaderNodeTexImage')
    orm_3_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[orm_3_texture_index]))
    orm_3_image.image.colorspace_settings.name = 'Non-Color'
    orm_3_image.location = -600, -450
    orm_3_image.hide = True

    orm_3_sep = nodes.new(type=sepRGB_name)
    orm_3_sep.location = -300, -450
    orm_3_sep.hide = True
    links.new(orm_3_image.outputs['Color'], orm_3_sep.inputs[sepRGB_input])

    # Mix O 0-1
    mix_o_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_o_01.location = 200, -75
    mix_o_01.hide = True
    links.new(mask_sep.outputs[0], mix_o_01.inputs['Fac'])
    links.new(orm_0_sep.outputs[0], mix_o_01.inputs['Color1'])
    links.new(orm_1_sep.outputs[0], mix_o_01.inputs['Color2'])

    # Mix O 0-1-2
    mix_o_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_o_012.location = 600, -150
    mix_o_012.hide = True
    links.new(mask_sep.outputs[1], mix_o_012.inputs['Fac'])
    links.new(mix_o_01.outputs['Color'], mix_o_012.inputs['Color1'])
    links.new(orm_2_sep.outputs[0], mix_o_012.inputs['Color2'])

    # Mix O 0-1-2-3
    mix_o_0123 = nodes.new(type='ShaderNodeMixRGB')
    mix_o_0123.location = 1000, -200
    mix_o_0123.hide = True
    links.new(mask_sep.outputs[2], mix_o_0123.inputs['Fac'])
    links.new(mix_o_012.outputs['Color'], mix_o_0123.inputs['Color1'])
    links.new(orm_3_sep.outputs[0], mix_o_0123.inputs['Color2'])

    # Mix R 0-1
    mix_r_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_r_01.location = 200, -225
    mix_r_01.hide = True
    links.new(mask_sep.outputs[0], mix_r_01.inputs['Fac'])
    links.new(orm_0_sep.outputs[1], mix_r_01.inputs['Color1'])
    links.new(orm_1_sep.outputs[1], mix_r_01.inputs['Color2'])

    # Mix R 0-1-2
    mix_r_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_r_012.location = 600, -300
    mix_r_012.hide = True
    links.new(mask_sep.outputs[1], mix_r_012.inputs['Fac'])
    links.new(mix_r_01.outputs['Color'], mix_r_012.inputs['Color1'])
    links.new(orm_2_sep.outputs[1], mix_r_012.inputs['Color2'])

    # Mix R 0-1-2-3
    mix_r_0123 = nodes.new(type='ShaderNodeMixRGB')
    mix_r_0123.location = 1000, -350
    mix_r_0123.hide = True
    links.new(mask_sep.outputs[2], mix_r_0123.inputs['Fac'])
    links.new(mix_r_012.outputs['Color'], mix_r_0123.inputs['Color1'])
    links.new(orm_3_sep.outputs[1], mix_r_0123.inputs['Color2'])

    # Roughness
    links.new(mix_r_0123.outputs['Color'], principled.inputs['Roughness'])

    # Mix M 0-1
    mix_m_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_m_01.location = 200, -375
    mix_m_01.hide = True
    links.new(mask_sep.outputs[0], mix_m_01.inputs['Fac'])
    links.new(orm_0_sep.outputs[2], mix_m_01.inputs['Color1'])
    links.new(orm_1_sep.outputs[2], mix_m_01.inputs['Color2'])

    # Mix M 0-1-2
    mix_m_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_m_012.location = 600, -450
    mix_m_012.hide = True
    links.new(mask_sep.outputs[1], mix_m_012.inputs['Fac'])
    links.new(mix_m_01.outputs['Color'], mix_m_012.inputs['Color1'])
    links.new(orm_2_sep.outputs[2], mix_m_012.inputs['Color2'])

    # Mix M 0-1-2-3
    mix_m_0123 = nodes.new(type='ShaderNodeMixRGB')
    mix_m_0123.location = 1000, -500
    mix_m_0123.hide = True
    links.new(mask_sep.outputs[2], mix_m_0123.inputs['Fac'])
    links.new(mix_m_012.outputs['Color'], mix_m_0123.inputs['Color1'])
    links.new(orm_3_sep.outputs[2], mix_m_0123.inputs['Color2'])

    # Metallic
    links.new(mix_m_0123.outputs['Color'], principled.inputs['Metallic'])

    # Normal 0
    normal_0_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texNormal0"), None)
    if normal_0_texture_index is None:
        log.w(f"Failed to find texNormal0 in material: {material.name}")
        return
    normal_0_image = nodes.new(type='ShaderNodeTexImage')
    normal_0_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_0_texture_index]))
    normal_0_image.image.colorspace_settings.name = 'Non-Color'
    normal_0_image.location = -600, -700
    normal_0_image.hide = True

    # Normal 1
    normal_1_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texNormal1"), None)
    if normal_1_texture_index is None:
        log.w(f"Failed to find texNormal1 in material: {material.name}")
        return
    normal_1_image = nodes.new(type='ShaderNodeTexImage')
    normal_1_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_1_texture_index]))
    normal_1_image.image.colorspace_settings.name = 'Non-Color'
    normal_1_image.location = -600, -850
    normal_1_image.hide = True

    # Normal 2
    normal_2_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texNormal2"), None)
    if normal_2_texture_index is None:
        log.w(f"Failed to find texNormal2 in material: {material.name}")
        return
    normal_2_image = nodes.new(type='ShaderNodeTexImage')
    normal_2_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_2_texture_index]))
    normal_2_image.image.colorspace_settings.name = 'Non-Color'
    normal_2_image.location = -600, -1000
    normal_2_image.hide = True

    # Normal 3
    normal_3_texture_index = next((i for i, x in enumerate(asset.textures) if x.mapType == "texNormal3"), None)
    if normal_3_texture_index is None:
        log.w(f"Failed to find texNormal3 in material: {material.name}")
        return
    normal_3_image = nodes.new(type='ShaderNodeTexImage')
    normal_3_image.image = bpy.data.images.load(search_texture(textures_dir, converted_textures[normal_3_texture_index]))
    normal_3_image.image.colorspace_settings.name = 'Non-Color'
    normal_3_image.location = -600, -1150
    normal_3_image.hide = True

    # Mix Normal 0-1
    mix_normal_01 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_01.location = 200, -775
    mix_normal_01.hide = True
    links.new(mask_sep.outputs[0], mix_normal_01.inputs['Fac'])
    links.new(normal_0_image.outputs['Color'], mix_normal_01.inputs['Color1'])
    links.new(normal_1_image.outputs['Color'], mix_normal_01.inputs['Color2'])

    # Mix Normal 0-1-2
    mix_normal_012 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_012.location = 600, -900
    mix_normal_012.hide = True
    links.new(mask_sep.outputs[1], mix_normal_012.inputs['Fac'])
    links.new(mix_normal_01.outputs['Color'], mix_normal_012.inputs['Color1'])
    links.new(normal_2_image.outputs['Color'], mix_normal_012.inputs['Color2'])

    # Mix Normal 0-1-2-3
    mix_normal_0123 = nodes.new(type='ShaderNodeMixRGB')
    mix_normal_0123.location = 1000, -1000
    mix_normal_0123.hide = True
    links.new(mask_sep.outputs[2], mix_normal_0123.inputs['Fac'])
    links.new(mix_normal_012.outputs['Color'], mix_normal_0123.inputs['Color1'])
    links.new(normal_3_image.outputs['Color'], mix_normal_0123.inputs['Color2'])

    # Separate Normal
    sepRGB_shader = nodes.new(type=sepRGB_name)
    sepRGB_shader.location = 1300, -1000
    sepRGB_shader.hide = True
    links.new(mix_normal_0123.outputs['Color'], sepRGB_shader.inputs[sepRGB_input])

    # Invert Normal Green
    invert_shader = nodes.new(type="ShaderNodeInvert")
    invert_shader.location = 1500, -1050
    invert_shader.hide = True
    links.new(sepRGB_shader.outputs[1], invert_shader.inputs['Color'])

    # Combine Normal
    comRGB_shader = nodes.new(type=comRGB_name)
    comRGB_shader.location = 1700, -1000
    comRGB_shader.hide = True
    comRGB_shader.inputs[2].default_value = 1.0
    links.new(sepRGB_shader.outputs[0], comRGB_shader.inputs[0])
    links.new(invert_shader.outputs['Color'], comRGB_shader.inputs[1])

    # Normal Map
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = 1900, -1000
    normal_map.hide = True
    links.new(comRGB_shader.outputs['Color'], normal_map.inputs['Color'])

    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])