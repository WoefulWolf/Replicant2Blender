import bpy

from ...classes.asset_package import Asset

from .nodes import constant_buffer_value, dx_to_gl_normal, grid_location, texture_sampler

def master_rs_ao_sheet(textures_dir: str, material: bpy.types.Material, asset: Asset):
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
    material.blend_method = 'BLEND'

    converted_textures: list[str] = []
    for texture in asset.textures:
        texture_filename_base = texture.texture_name.replace(".rtex", "")
        texture_filename = texture_filename_base + ".png"
        converted_textures.append(texture_filename)

    # gColorMultiply
    g_color_multiply = constant_buffer_value(material, nodes, asset, "CbAOSheet", "gColorMultiply")
    if g_color_multiply is not None:
        g_color_multiply.location = grid_location(0, 0)

    # Principled BSDF
    transparent = nodes.new(type='ShaderNodeBsdfTransparent')
    transparent.location = grid_location(1, 0)
    if g_color_multiply is not None:
        links.new(g_color_multiply.outputs[0], transparent.inputs['Color'])

    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = grid_location(2, 0)
    links.new(transparent.outputs['BSDF'], output.inputs['Surface'])