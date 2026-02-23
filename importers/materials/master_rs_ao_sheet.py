import bpy

from ...util import generate_converted_texture_paths
from ...classes.material_instance import tpGxMaterialInstanceV2

from .nodes import constant_buffer_value, grid_location

def master_rs_ao_sheet(textures_dir: str, material: bpy.types.Material, instance: tpGxMaterialInstanceV2):
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

    converted_textures = generate_converted_texture_paths(instance.texture_samplers)

    # gColorMultiply
    g_color_multiply = constant_buffer_value(material, nodes, instance, "CbAOSheet", "gColorMultiply")
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