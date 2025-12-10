from bpy.types import Material, Node, NodeTree, Nodes

import bpy

from ...classes.material_instance import tpGxMaterialInstanceV2
from ...util import log, search_texture

# Renamed in 5.0
sepRGB_name = "ShaderNodeSeparateRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeSeparateColor"
sepRGB_input = 'Image' if bpy.app.version < (5, 0, 0) else "Color"
comRGB_name = "ShaderNodeCombineRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeCombineColor"
comRGB_output = 'Image' if bpy.app.version < (5, 0, 0) else "Color"

def texture_sampler(material: Material, nodes: Nodes, instance: tpGxMaterialInstanceV2, textures_dir: str, converted_textures: list[str], sampler_name: str) -> Node:
    tex_index = next((i for i, x in enumerate(instance.texture_samplers) if x.name == sampler_name), None)        
    tex_node = nodes.new(type='ShaderNodeTexImage')
    if tex_index is not None:
        texture = search_texture(textures_dir, converted_textures[tex_index])
        tex_node.image = bpy.data.images.load(texture)
        for sampler in material.replicant_texture_samplers:
            if sampler.name == sampler_name:
                # sampler.texture_path = texture # Temporarily disable to prioritise DDS
                break
    else:
        log.w(f"Failed to find sampler {sampler_name} for material: {material.name}")
    tex_node.hide = True
    tex_node.label = sampler_name
    return tex_node

def first_texture_sampler(material: Material, nodes: Nodes, instance: tpGxMaterialInstanceV2, textures_dir: str, converted_textures: list[str], sampler_names: list[str]) -> Node:
    tex_index, tex = next(((i, x) for i, x in enumerate(instance.texture_samplers) if x.name in sampler_names), (None, None))        
    tex_node = nodes.new(type='ShaderNodeTexImage')
    if tex_index is not None:
        sampler_name = tex.name
        texture = search_texture(textures_dir, converted_textures[tex_index])
        tex_node.image = bpy.data.images.load(texture)
        tex_node.label = sampler_name
        for sampler in material.replicant_texture_samplers:
            if sampler.name == sampler_name:
                # sampler.texture_path = texture # Temporarily disable to prioritise DDS
                break
    else:
        log.w(f"Failed to find any sampler in {sampler_names} for material: {material.name}")
    tex_node.hide = True
    return tex_node

def constant_buffer_value(material: Material, nodes: Nodes, instance: tpGxMaterialInstanceV2, buffer_name: str, constant_name: str) -> Node | None:
    for constant_buffer in instance.constant_buffers:
        if constant_buffer.name != buffer_name:
            continue
        for constant in constant_buffer.constants:
            if constant.name != constant_name:
                continue
            node_label = f"{buffer_name}_{constant_name}"
            if "color" in constant_name.lower():
                color = nodes.new(type=comRGB_name)
                color.hide = True
                color.label = node_label
                color.inputs[0].default_value = constant.value0
                color.inputs[1].default_value = constant.value1
                color.inputs[2].default_value = constant.value2
                return color
            elif "uv" in constant_name.lower():
                vector = nodes.new(type="ShaderNodeCombineXYZ")
                vector.hide = True
                vector.label = node_label
                vector.inputs[0].default_value = constant.value0
                vector.inputs[1].default_value = constant.value1
                return vector
            elif "density" in constant_name.lower() or "ior" in constant_name.lower():
                value = nodes.new(type="ShaderNodeValue")
                value.hide = True
                value.label = node_label
                value.outputs[0].default_value = constant.value0
                return value
    log.w(f"Failed to find constant {constant_name} in {buffer_name} for material: {material.name}")
    return None



def grid_location(x: int, y: int):
    return (x * 300, y * -80)

def if_nz(type: str="Float") -> NodeTree:
    types = ["Float", "Vector", "Color"]

    if type not in types:
        return None

    name = 'If Non-Zero (%s)' % type

    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    node_group.color_tag = 'CONVERTER'

    interface = node_group.interface
    interface.new_socket(
        name='Value',
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    interface.new_socket(
        name='True',
        in_out='INPUT',
        socket_type='NodeSocket%s' % type
    )
    interface.new_socket(
        name='False',
        in_out='INPUT',
        socket_type='NodeSocket%s' % type
    )
    interface.new_socket(
        name='Value',
        in_out='OUTPUT',
        socket_type='NodeSocket%s' % type
    )

    nodes = node_group.nodes
    links = node_group.links

    nodes.clear()

    group_input = nodes.new('NodeGroupInput')
    group_input.location = grid_location(0, 1)
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = grid_location(3, 0)

    greater_than_node = nodes.new(type='ShaderNodeMath')
    greater_than_node.operation = 'GREATER_THAN'
    greater_than_node.inputs[1].default_value = 0.0
    greater_than_node.location = grid_location(1, 0)
    links.new(group_input.outputs['Value'], greater_than_node.inputs['Value'])

    mix_node = nodes.new(type='ShaderNodeMix')
    mix_node.blend_type = 'MIX'
    mix_node.data_type = type.upper() if type != "Color" else "RGBA"
    mix_node.location = grid_location(2, 0)
    links.new(greater_than_node.outputs['Value'], mix_node.inputs['Factor'])
    links.new(group_input.outputs['True'], mix_node.inputs['B'])
    links.new(group_input.outputs['False'], mix_node.inputs['A'])

    links.new(mix_node.outputs['Result'], group_output.inputs['Value'])

    return node_group

def dx_to_gl_normal() -> NodeTree:
    name = 'DirectX to OpenGL Normal'
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    node_group.color_tag = 'CONVERTER'

    interface = node_group.interface
    interface.new_socket(
        name='Color',
        in_out='INPUT',
        socket_type='NodeSocketColor'
    )
    interface.new_socket(
        name='Color',
        in_out='OUTPUT',
        socket_type='NodeSocketColor'
    )

    nodes = node_group.nodes
    links = node_group.links
    nodes.clear()

    group_input = nodes.new('NodeGroupInput')
    group_input.location = grid_location(0, 0)
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = grid_location(5, 0)

    # Invert Normal Green Channel for OpenGL
    normal_invert_g = nodes.new('ShaderNodeGroup')
    normal_invert_g.node_tree = invert_channel("Green")
    normal_invert_g.location = grid_location(1, 0)
    normal_invert_g.hide = True
    links.new(group_input.outputs['Color'], normal_invert_g.inputs['Color'])

    # Separate
    sep_col_node = nodes.new(type=sepRGB_name)
    sep_col_node.location = grid_location(2, 0)
    sep_col_node.hide = True
    links.new(normal_invert_g.outputs['Color'], sep_col_node.inputs[sepRGB_input])

    # Don't touch blue channel if non-zero, else set to 1.0
    if_nz_blue = nodes.new('ShaderNodeGroup')
    if_nz_blue.node_tree = if_nz()
    if_nz_blue.location = grid_location(3, 1)
    if_nz_blue.hide = True
    if_nz_blue.inputs['False'].default_value = 1.0
    links.new(sep_col_node.outputs[2], if_nz_blue.inputs['Value'])
    links.new(sep_col_node.outputs[2], if_nz_blue.inputs['True'])

    # Combine again
    cmb_col_shader = nodes.new(type=comRGB_name)
    cmb_col_shader.location = grid_location(4, 0)
    cmb_col_shader.hide = True
    links.new(sep_col_node.outputs[0], cmb_col_shader.inputs[0])
    links.new(sep_col_node.outputs[1], cmb_col_shader.inputs[1])
    links.new(if_nz_blue.outputs['Value'], cmb_col_shader.inputs[2])

    links.new(cmb_col_shader.outputs[comRGB_output], group_output.inputs['Color'])

    return node_group

def invert_channel(channel: str="Green") -> NodeTree:
    channels = ["Red", "Green", "Blue"]
    if channel not in channels:
        return None

    channel_index = channels.index(channel)
    
    unaffected_channels = channels
    unaffected_channels.remove(channel)

    unaffected_channel_indices = [channels.index(chan) for chan in unaffected_channels]

    name = 'Invert ' + channel
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    node_group.color_tag = 'COLOR'

    interface = node_group.interface
    interface.new_socket(
        name='Color',
        in_out='INPUT',
        socket_type='NodeSocketColor'
    )
    interface.new_socket(
        name='Color',
        in_out='OUTPUT',
        socket_type='NodeSocketColor'
    )

    nodes = node_group.nodes
    links = node_group.links

    nodes.clear()

    group_input = nodes.new('NodeGroupInput')
    group_input.location = grid_location(0, 0)
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = grid_location(4, 0)

    sep_col_node = nodes.new(type=sepRGB_name)
    sep_col_node.location = grid_location(1, 0)
    sep_col_node.hide = True
    links.new(group_input.outputs['Color'], sep_col_node.inputs[sepRGB_input])

    # 1 - Selected Channel
    subtract_node = nodes.new(type='ShaderNodeMath')
    subtract_node.location = grid_location(2, 1)
    subtract_node.hide = True
    subtract_node.operation = 'SUBTRACT'
    subtract_node.inputs[0].default_value = 1.0
    links.new(sep_col_node.outputs[channel_index], subtract_node.inputs[1])

    # Combine again
    cmb_col_shader = nodes.new(type=comRGB_name)
    cmb_col_shader.location = grid_location(3, 0)
    cmb_col_shader.hide = True
    for index in unaffected_channel_indices:
        links.new(sep_col_node.outputs[index], cmb_col_shader.inputs[index])
    links.new(subtract_node.outputs[0], cmb_col_shader.inputs[channel_index])
	
    links.new(cmb_col_shader.outputs[comRGB_output], group_output.inputs['Color'])

    return node_group