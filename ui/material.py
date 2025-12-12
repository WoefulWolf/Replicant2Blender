from ntpath import isfile
from typing import Callable
import bpy
import os

from bpy.types import UILayout

dxgi_format_strings = ['UNKNOWN', 'R32G32B32A32_TYPELESS', 'R32G32B32A32_FLOAT', 'R32G32B32A32_UINT', 'R32G32B32A32_SINT', 'R32G32B32_TYPELESS', 'R32G32B32_FLOAT', 'R32G32B32_UINT', 'R32G32B32_SINT', 'R16G16B16A16_TYPELESS', 'R16G16B16A16_FLOAT', 'R16G16B16A16_UNORM', 'R16G16B16A16_UINT', 'R16G16B16A16_SNORM', 'R16G16B16A16_SINT', 'R32G32_TYPELESS', 'R32G32_FLOAT', 'R32G32_UINT', 'R32G32_SINT', 'R32G8X24_TYPELESS', 'D32_FLOAT_S8X24_UINT', 'R32_FLOAT_X8X24_TYPELESS', 'X32_TYPELESS_G8X24_UINT', 'R10G10B10A2_TYPELESS', 'R10G10B10A2_UNORM', 'R10G10B10A2_UINT', 'R11G11B10_FLOAT', 'R8G8B8A8_TYPELESS', 'R8G8B8A8_UNORM', 'R8G8B8A8_UNORM_SRGB', 'R8G8B8A8_UINT', 'R8G8B8A8_SNORM', 'R8G8B8A8_SINT', 'R16G16_TYPELESS', 'R16G16_FLOAT', 'R16G16_UNORM', 'R16G16_UINT', 'R16G16_SNORM', 'R16G16_SINT', 'R32_TYPELESS', 'D32_FLOAT', 'R32_FLOAT', 'R32_UINT', 'R32_SINT', 'R24G8_TYPELESS', 'D24_UNORM_S8_UINT', 'R24_UNORM_X8_TYPELESS', 'X24_TYPELESS_G8_UINT', 'R8G8_TYPELESS', 'R8G8_UNORM', 'R8G8_UINT', 'R8G8_SNORM', 'R8G8_SINT', 'R16_TYPELESS', 'R16_FLOAT', 'D16_UNORM', 'R16_UNORM', 'R16_UINT', 'R16_SNORM', 'R16_SINT', 'R8_TYPELESS', 'R8_UNORM', 'R8_UINT', 'R8_SNORM', 'R8_SINT', 'A8_UNORM', 'R1_UNORM', 'R9G9B9E5_SHAREDEXP', 'R8G8_B8G8_UNORM', 'G8R8_G8B8_UNORM', 'BC1_TYPELESS', 'BC1_UNORM', 'BC1_UNORM_SRGB', 'BC2_TYPELESS', 'BC2_UNORM', 'BC2_UNORM_SRGB', 'BC3_TYPELESS', 'BC3_UNORM', 'BC3_UNORM_SRGB', 'BC4_TYPELESS', 'BC4_UNORM', 'BC4_SNORM', 'BC5_TYPELESS', 'BC5_UNORM', 'BC5_SNORM', 'B5G6R5_UNORM', 'B5G5R5A1_UNORM', 'B8G8R8A8_UNORM', 'B8G8R8X8_UNORM', 'R10G10B10_XR_BIAS_A2_UNORM', 'B8G8R8A8_TYPELESS', 'B8G8R8A8_UNORM_SRGB', 'B8G8R8X8_TYPELESS', 'B8G8R8X8_UNORM_SRGB', 'BC6H_TYPELESS', 'BC6H_UF16', 'BC6H_SF16', 'BC7_TYPELESS', 'BC7_UNORM', 'BC7_UNORM_SRGB', 'AYUV', 'Y410', 'Y416', 'NV12', 'P010', 'P016', 'OPAQUE_420', 'YUY2', 'Y210', 'Y216', 'NV11', 'AI44', 'IA44', 'P8', 'A8P8', 'B4G4R4A4_UNORM']

def get_dxgi_format_items():
    """Generate enum items for DXGI formats with descriptions for common BC formats"""
    items = []
    for fmt in dxgi_format_strings:
        desc = ""
        if "BC1" in fmt:
            desc = "DXT1"
        elif "BC2" in fmt:
            desc = "DXT2/3"
        elif "BC3" in fmt:
            desc = "DXT4/5"
        items.append((fmt, fmt, desc))
    return items

class MATERIAL_OT_show_image_path(bpy.types.Operator):
    bl_idname = "material.show_image_path"
    bl_label = "Image Path"
    bl_options = {'INTERNAL'}

    filepath: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        path = properties.filepath if properties.filepath else "No image loaded"
        if os.path.exists(properties.filepath) and os.path.isfile(properties.filepath):
            return f"Texture Path\n{path}\n\nClick to copy to clipboard"
        else:
            return f"Texture Path\nFile not found!"

    def execute(self, context):
        if self.filepath:
            context.window_manager.clipboard = self.filepath
            self.report({'INFO'}, f"Copied to clipboard: {self.filepath}")
        return {'FINISHED'}

class MATERIAL_OT_open_sampler_texture(bpy.types.Operator):
    bl_idname = "material.open_sampler_texture"
    bl_label = "Open Texture"
    bl_description = "Open a texture file for this sampler"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    sampler_index: bpy.props.IntProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and 0 <= self.sampler_index < len(material.replicant_texture_samplers):
            sampler = material.replicant_texture_samplers[self.sampler_index]
            sampler.texture_path = self.filepath
            if self.filepath.endswith(".dds"):
                from puredds import DDS
                with open(self.filepath, 'rb') as f:
                    data = f.read()
                dds = DDS.from_bytes(data)
                sampler.dxgi_format = dds.get_format_str()
                sampler.mip_maps = dds.get_mip_count() > 1
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Operators for Constant Buffers
class MATERIAL_OT_add_constant_buffer(bpy.types.Operator):
    bl_idname = "material.add_constant_buffer"
    bl_label = "Add Constant Buffer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        material = context.active_object.active_material
        if material:
            cb = material.replicant_constant_buffers.add()
            cb.name = f"CbCustom{len(material.replicant_constant_buffers)}"
            cb.previous_name = cb.name  # Initialize previous_name
        return {'FINISHED'}

class MATERIAL_OT_remove_constant_buffer(bpy.types.Operator):
    bl_idname = "material.remove_constant_buffer"
    bl_label = "Remove Constant Buffer"
    bl_options = {'REGISTER', 'UNDO'}

    buffer_index: bpy.props.IntProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and 0 <= self.buffer_index < len(material.replicant_constant_buffers):
            material.replicant_constant_buffers.remove(self.buffer_index)
        return {'FINISHED'}

class MATERIAL_OT_add_constant(bpy.types.Operator):
    bl_idname = "material.add_constant"
    bl_label = "Add Constant"
    bl_options = {'REGISTER', 'UNDO'}

    buffer_index: bpy.props.IntProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and 0 <= self.buffer_index < len(material.replicant_constant_buffers):
            cb = material.replicant_constant_buffers[self.buffer_index]
            const = cb.constants.add()
            const.name = f"gCustom{len(cb.constants)}"
            const.previous_name = const.name  # Initialize previous_name
        return {'FINISHED'}

class MATERIAL_OT_remove_constant(bpy.types.Operator):
    bl_idname = "material.remove_constant"
    bl_label = "Remove Constant"
    bl_options = {'REGISTER', 'UNDO'}

    buffer_index: bpy.props.IntProperty()
    constant_index: bpy.props.IntProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and 0 <= self.buffer_index < len(material.replicant_constant_buffers):
            cb = material.replicant_constant_buffers[self.buffer_index]
            if 0 <= self.constant_index < len(cb.constants):
                cb.constants.remove(self.constant_index)
        return {'FINISHED'}

# Operators for Texture Parameters
class MATERIAL_OT_add_texture_parameter(bpy.types.Operator):
    """Adds a new texture parameter to the active material"""
    bl_idname = "material.add_texture_parameter"
    bl_label = "Add Texture Parameter"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        material = context.active_object.active_material
        if material:
            param = material.replicant_texture_parameters.add()
            param.name = f"TPSVAR_CUSTOM{len(material.replicant_texture_parameters)}"
        return {'FINISHED'}

class MATERIAL_OT_remove_texture_parameter(bpy.types.Operator):
    """Removes the specified texture parameter from the active material"""
    bl_idname = "material.remove_texture_parameter"
    bl_label = "Remove Texture Parameter"
    bl_options = {'REGISTER', 'UNDO'}

    parameter_index: bpy.props.IntProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and 0 <= self.parameter_index < len(material.replicant_texture_parameters):
            material.replicant_texture_parameters.remove(self.parameter_index)
        return {'FINISHED'}

# Operators for Textures
class MATERIAL_OT_add_texture_sampler(bpy.types.Operator):
    """Adds a new texture sampler to the active material"""
    bl_idname = "material.add_texture_sampler"
    bl_label = "Add Texture Sampler"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        material = context.active_object.active_material
        if material:
            sampler = material.replicant_texture_samplers.add()
            sampler.name = f"tex{len(material.replicant_texture_samplers)}"
            sampler.previous_name = sampler.name  # Initialize previous_name
        return {'FINISHED'}

class MATERIAL_OT_remove_texture_sampler(bpy.types.Operator):
    """Removes the specified texture sampler from the active material"""
    bl_idname = "material.remove_texture_sampler"
    bl_label = "Remove Texture Sampler"
    bl_options = {'REGISTER', 'UNDO'}

    sampler_index: bpy.props.IntProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and 0 <= self.sampler_index < len(material.replicant_texture_samplers):
            material.replicant_texture_samplers.remove(self.sampler_index)
        return {'FINISHED'}

# Helper functions for syncing with nodes
def get_node_label(buffer_name, constant_name):
    """Generate node label from buffer and constant names"""
    return f"{buffer_name}_{constant_name}"

def find_constant_node(material, buffer_name, constant_name):
    """Find a node by the constant buffer naming pattern"""
    if not material or not material.use_nodes:
        return None
    label = get_node_label(buffer_name, constant_name)
    for node in material.node_tree.nodes:
        if node.label == label:
            return node
    return None

def update_constant_node_label(material, old_buffer_name, old_constant_name, new_buffer_name, new_constant_name):
    """Update node label when constant or buffer name changes"""
    node = find_constant_node(material, old_buffer_name, old_constant_name)
    if node:
        node.label = get_node_label(new_buffer_name, new_constant_name)

def update_constant_node_values(material, buffer_name, constant_name, values):
    """Update node custom properties with constant values"""
    node = find_constant_node(material, buffer_name, constant_name)
    if node:
        for i, val in enumerate(values):
            node[f"value_{i}"] = val

def get_material_from_constant(constant_prop):
    """Get material from a ConstantValue property"""
    for mat in bpy.data.materials:
        if not hasattr(mat, 'replicant_constant_buffers'):
            continue
        for cb in mat.replicant_constant_buffers:
            for const in cb.constants:
                if const == constant_prop:
                    return mat, cb
    return None, None

# Property Groups for Constant Buffers
def constant_name_update(self, context):
    """Update callback when constant name changes"""
    mat, cb = get_material_from_constant(self)
    if mat and cb and mat.use_nodes:
        # Use previous name to find the node with old label
        old_label = get_node_label(cb.name, self.previous_name)
        new_label = get_node_label(cb.name, self.name)

        node = find_constant_node(mat, cb.name, self.previous_name)
        if node:
            node.label = new_label

        # Update previous name to current name
        self.previous_name = self.name

def constant_values_update(self, context):
    """Update callback when constant values change"""
    mat, cb = get_material_from_constant(self)
    if mat and cb and mat.use_nodes:
        node = find_constant_node(mat, cb.name, self.name)
        if node:
            for i, val in enumerate(self.values):
                if i >= len(node.inputs):
                    continue
                node.inputs[i].default_value = val

def buffer_name_update(self, context):
    """Update callback when buffer name changes"""
    # Find the material that contains this buffer
    for mat in bpy.data.materials:
        if not hasattr(mat, 'replicant_constant_buffers') or not mat.use_nodes:
            continue
        for cb in mat.replicant_constant_buffers:
            if cb == self:
                # Update all constant node labels using previous buffer name
                for const in cb.constants:
                    old_label = get_node_label(self.previous_name, const.name)
                    new_label = get_node_label(self.name, const.name)

                    node = find_constant_node(mat, self.previous_name, const.name)
                    if node:
                        node.label = new_label

                # Update previous name to current name
                self.previous_name = self.name
                return

def sampler_name_update(self, context):
    """Update callback when sampler name changes"""
    # Find the material that contains this sampler
    for mat in bpy.data.materials:
        if not hasattr(mat, 'replicant_texture_samplers') or not mat.use_nodes:
            continue
        for sampler in mat.replicant_texture_samplers:
            if sampler == self:
                # Find TEX_IMAGE node with old label
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.label == self.previous_name:
                        node.label = self.name
                        break

                # Update previous name to current name
                self.previous_name = self.name
                return

def texture_path_update(self, context):
    """Update callback when texture path changes"""
    # Find the material that contains this sampler
    for mat in bpy.data.materials:
        if not hasattr(mat, 'replicant_texture_samplers') or not mat.use_nodes:
            continue
        for sampler in mat.replicant_texture_samplers:
            if sampler == self:
                # Find ShaderNodeTexImage with matching label
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.label == self.name:
                        # Load the image if path is valid
                        if self.texture_path and os.path.exists(self.texture_path):
                            node.image = bpy.data.images.load(self.texture_path, check_existing=True)
                        else:
                            node.image = None
                return

def dxgi_format_update(self, context):
    """Update callback when DXGI format changes - syncs format across all samplers with same pack/texture paths"""
    # Get the pack_path and texture_path from the current sampler
    pack_path = self.pack_path
    texture_path = self.texture_path
    new_format = self.dxgi_format

    # Find all texture samplers in all materials with matching paths
    for mat in bpy.data.materials:
        if not hasattr(mat, 'replicant_texture_samplers'):
            continue
        for sampler in mat.replicant_texture_samplers:
            # Skip the current sampler itself
            if sampler == self:
                continue
            # Update format if both pack_path and texture_path match, and format is different
            if (sampler.pack_path == pack_path and
                sampler.texture_path == texture_path and
                sampler.dxgi_format != new_format):
                sampler.dxgi_format = new_format

def mip_maps_update(self, context):
    """Update callback when generate Mipmaps changes - syncs format across all samplers with same pack/texture paths"""
    # Get the pack_path and texture_path from the current sampler
    pack_path = self.pack_path
    texture_path = self.texture_path
    new_value = self.mip_maps

    # Find all texture samplers in all materials with matching paths
    for mat in bpy.data.materials:
        if not hasattr(mat, 'replicant_texture_samplers'):
            continue
        for sampler in mat.replicant_texture_samplers:
            # Skip the current sampler itself
            if sampler == self:
                continue
            # Update format if both pack_path and texture_path match, and format is different
            if (sampler.pack_path == pack_path and
                sampler.texture_path == texture_path and
                sampler.mip_maps != new_value):
                sampler.mip_maps = new_value

class MaterialFlags(bpy.types.PropertyGroup):
    cast_shadows: bpy.props.BoolProperty(
        name="Cast Shadows",
        description="Enable shadow casting on this material",
        default=True,
    )
    draw_backfaces: bpy.props.BoolProperty(
        name="Draw Backfaces",
        description="Enables the drawing of backfaces",
        default=False,
    )
    enable_alpha: bpy.props.BoolProperty(
        name="Enable Alpha",
        description="Enables texture alpha tests",
        default=False,
    )

class TextureSampler(bpy.types.PropertyGroup):
    """Represents a texture sampler with a PACK and image path"""
    name: bpy.props.StringProperty(
        name="Sampler Name",
        default="texCustom",
        update=sampler_name_update
    )
    previous_name: bpy.props.StringProperty(
        name="Previous Sampler Name",
        default="texCustom"
    )
    pack_path: bpy.props.StringProperty(
        name="PACK Path",
        default=""
    )
    texture_path: bpy.props.StringProperty(
        name="Texture Path",
        default="",
        update=texture_path_update
    )
    dxgi_format: bpy.props.EnumProperty(
        name="DXGI Format",
        description="Output DirectX texture compression format",
        items=get_dxgi_format_items(),
        default='BC1_UNORM_SRGB',
        update=dxgi_format_update
    )
    mip_maps: bpy.props.BoolProperty(
        name="Generate Mipmaps",
        description="Generate Mipmaps when output",
        default=True,
        update=mip_maps_update
    )

class ConstantValue(bpy.types.PropertyGroup):
    """Represents a single constant with a name and 6 float values"""
    name: bpy.props.StringProperty(
        name="Constant Name",
        default="gCustom",
        update=constant_name_update
    )
    previous_name: bpy.props.StringProperty(
        name="Previous Constant Name",
        default="gCustom"
    )
    values: bpy.props.FloatVectorProperty(
        name="Values",
        size=6,
        default=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        update=constant_values_update
    )
    expanded: bpy.props.BoolProperty(
        name="Expanded",
        default=False
    )

class ConstantBuffer(bpy.types.PropertyGroup):
    """Represents a constant buffer containing multiple constants"""
    name: bpy.props.StringProperty(
        name="Buffer Name",
        default="CbCustom",
        update=buffer_name_update
    )
    previous_name: bpy.props.StringProperty(
        name="Previous Buffer Name",
        default="CbCustom"
    )
    constants: bpy.props.CollectionProperty(
        type=ConstantValue,
        name="Constants"
    )
    expanded: bpy.props.BoolProperty(
        name="Expanded",
        default=False
    )

class TextureParameter(bpy.types.PropertyGroup):
    """Represents a texture parameter with a name and 3 integer values"""
    name: bpy.props.StringProperty(
        name="Parameter Name",
        default="TPSVAR_CUSTOM"
    )
    values: bpy.props.IntVectorProperty(
        name="Values",
        size=3,
        default=(0, 0, 0)
    )

class MATERIAL_PT_replicant(bpy.types.Panel):
    bl_label: str = "NieR Replicant ver.1.2247... Material Instance"
    bl_idname: str = "MATERIAL_PT_replicant"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context: str = "material"

    def draw(self, context):
        layout: UILayout = self.layout
        obj = context.active_object

        if not obj or not obj.active_material:
            layout.label(text="No active material")
            return

        material = obj.active_material

        layout.prop(material, "replicant_pack_path", text="PACK Path", icon='FILE_PARENT')
        layout.prop(material, "replicant_master_material", text="Master Material", icon='SHADING_TEXTURE')

        material_flags(layout, context, material)
        texture_samplers(layout, context, material)
        constant_buffers(layout, context, material)
        texture_parameters(layout, context, material)

def material_flags(layout, context, material):
    box = layout.box()
    box.label(text="Material Flags", icon='BOOKMARKS')
    row = box.row(align=True)
    row.prop(material.replicant_flags, "cast_shadows", icon='MATSHADERBALL')
    row.prop(material.replicant_flags, "draw_backfaces", icon='FACESEL')
    row.prop(material.replicant_flags, "enable_alpha", icon='IMAGE_ALPHA')
    return

def texture_samplers(layout, context, material):
    # Display the list of image texture node labels
    box = layout.box()
    header = box.row(align=True)
    header.alignment = 'LEFT'
    header.prop(context.scene, "replicant_show_texture_samplers",
                text="",
                icon='TRIA_DOWN' if context.scene.replicant_show_texture_samplers else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.prop(context.scene, "replicant_show_texture_samplers",
                text="Texture Samplers",
                icon='TEXTURE',
                emboss=False, toggle=True)

    if not context.scene.replicant_show_texture_samplers:
        return

    for sampler_idx, sampler in enumerate(material.replicant_texture_samplers):
        sampler_box = box.box()
        row = sampler_box.row(align=True)
        row.prop(sampler, "name", text="", icon='IMAGE_DATA')
        remove_op = row.operator("material.remove_texture_sampler", text="", icon='X')
        remove_op.sampler_index = sampler_idx

        row = sampler_box.row(align=True)
        split = row.split(factor=0.5, align=True)
        split.prop(sampler, "pack_path", text="", icon='FILE_PARENT')

        # Right column - filename takes up most space, icon button at the end
        right_col = split.row(align=True)

        # Show image filename (basename only, full path on hover) - expands to fill
        if sampler.texture_path != "":
            filepath = sampler.texture_path
            basename = os.path.basename(filepath) if filepath else "Unknown"
            exists= os.path.exists(filepath)
            right_col.alert = not exists
            icon = 'NONE' if exists else 'ERROR'

            # Show basename as a button with full path tooltip
            path_op = right_col.operator("material.show_image_path", text=basename, icon=icon)
            path_op.filepath = filepath
        else:
            right_col.label(text="No image", icon='ERROR')

        # Open image button (small icon only) - always on the right
        icon_col = right_col.column(align=True)
        op = icon_col.operator("material.open_sampler_texture", text="", icon='FILEBROWSER')
        op.sampler_index = sampler_idx
    
    # Add new texture parameter button
    add_row = box.row()
    add_row.operator("material.add_texture_sampler", text="Add Texture Sampler", icon='ADD')

def constant_buffers(layout, context, material):
    box = layout.box()
    header = box.row(align=True)
    header.alignment = 'LEFT'
    header.prop(context.scene, "replicant_show_constant_buffers",
                text="",
                icon='TRIA_DOWN' if context.scene.replicant_show_constant_buffers else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.prop(context.scene, "replicant_show_constant_buffers",
                text="Constant Buffers",
                icon='DOCUMENTS',
                emboss=False, toggle=True)

    if not context.scene.replicant_show_constant_buffers:
        return

    # Display each constant buffer
    for cb_idx, cb in enumerate(material.replicant_constant_buffers):
        # Constant buffer box
        cb_box = box.box()

        # Header: expand toggle, buffer name, and remove button
        cb_header = cb_box.row(align=True)
        cb_header.prop(cb, "expanded",
                      text="",
                      icon='TRIA_DOWN' if cb.expanded else 'TRIA_RIGHT',
                      icon_only=True, emboss=False)
        cb_header.prop(cb, "name", text="", icon='PROPERTIES')
        remove_op = cb_header.operator("material.remove_constant_buffer", text="", icon='X')
        remove_op.buffer_index = cb_idx

        # Only show contents if expanded
        if not cb.expanded:
            continue

        # Display each constant in the buffer
        for const_idx, const in enumerate(cb.constants):
            const_box = cb_box.box()

            # Constant name and remove button
            const_header = const_box.row(align=True)
            const_header.prop(const, "expanded",
                      text="",
                      icon='TRIA_DOWN' if const.expanded else 'TRIA_RIGHT',
                      icon_only=True, emboss=False)
            const_header.prop(const, "name", text="", icon='NODE_SOCKET_FLOAT')
            remove_const_op = const_header.operator("material.remove_constant", text="", icon='X')
            remove_const_op.buffer_index = cb_idx
            remove_const_op.constant_index = const_idx

            # Only show contents if expanded
            if not const.expanded:
                continue

            # Display the 6 float values in a grid
            values_col = const_box.column(align=True)

            # Row 1: values 0-2
            row1 = values_col.row(align=True)
            row1.prop(const, "values", index=0, text="")
            row1.prop(const, "values", index=1, text="")
            row1.prop(const, "values", index=2, text="")

            # Row 2: values 3-5
            row2 = values_col.row(align=True)
            row2.prop(const, "values", index=3, text="")
            row2.prop(const, "values", index=4, text="")
            row2.prop(const, "values", index=5, text="")

        # Add constant button
        add_const_row = cb_box.row()
        add_const_op = add_const_row.operator("material.add_constant", text="Add Constant", icon='ADD')
        add_const_op.buffer_index = cb_idx

    # Add new constant buffer button
    add_row = box.row()
    add_row.operator("material.add_constant_buffer", text="Add Constant Buffer", icon='ADD')

def texture_parameters(layout, context, material):
    # Display the list of texture parameters
    box = layout.box()
    header = box.row(align=True)
    header.alignment = 'LEFT'
    header.prop(context.scene, "replicant_show_texture_parameters",
                text="",
                icon='TRIA_DOWN' if context.scene.replicant_show_texture_parameters else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.prop(context.scene, "replicant_show_texture_parameters",
                text="Texture Parameters",
                icon='MOD_UVPROJECT',
                emboss=False, toggle=True)

    if not context.scene.replicant_show_texture_parameters:
        return

    # Display each texture parameter
    for param_idx, param in enumerate(material.replicant_texture_parameters):
        param_box = box.box()

        # Parameter name and remove button
        param_header = param_box.row(align=True)
        param_header.prop(param, "name", text="", icon='NODE_SOCKET_INT')
        remove_op = param_header.operator("material.remove_texture_parameter", text="", icon='X')
        remove_op.parameter_index = param_idx

        # Display the 3 integer values in a row
        values_row = param_box.row(align=True)
        values_row.prop(param, "values", index=0, text="")
        values_row.prop(param, "values", index=1, text="")
        values_row.prop(param, "values", index=2, text="")

    # Add new texture parameter button
    add_row = box.row()
    add_row.operator("material.add_texture_parameter", text="Add Texture Parameter", icon='ADD')

def register():
    # Register PropertyGroups first
    bpy.utils.register_class(MaterialFlags)
    bpy.utils.register_class(TextureParameter)
    bpy.utils.register_class(ConstantValue)
    bpy.utils.register_class(ConstantBuffer)
    bpy.utils.register_class(TextureSampler)

    # Register operators and panels
    bpy.utils.register_class(MATERIAL_OT_show_image_path)
    bpy.utils.register_class(MATERIAL_OT_open_sampler_texture)
    bpy.utils.register_class(MATERIAL_OT_add_constant_buffer)
    bpy.utils.register_class(MATERIAL_OT_remove_constant_buffer)
    bpy.utils.register_class(MATERIAL_OT_add_constant)
    bpy.utils.register_class(MATERIAL_OT_remove_constant)
    bpy.utils.register_class(MATERIAL_OT_add_texture_parameter)
    bpy.utils.register_class(MATERIAL_OT_remove_texture_parameter)
    bpy.utils.register_class(MATERIAL_OT_add_texture_sampler)
    bpy.utils.register_class(MATERIAL_OT_remove_texture_sampler)
    bpy.utils.register_class(MATERIAL_PT_replicant)

    # Add property to track expansion states
    bpy.types.Scene.replicant_show_texture_samplers = bpy.props.BoolProperty(
        name="Show Texture Samplers",
        default=True
    )
    bpy.types.Scene.replicant_show_constant_buffers = bpy.props.BoolProperty(
        name="Show Constant Buffers",
        default=False
    )
    bpy.types.Scene.replicant_show_texture_parameters = bpy.props.BoolProperty(
        name="Show Texture Parameters",
        default=False
    )

    # Material pack pack
    bpy.types.Material.replicant_pack_path = bpy.props.StringProperty(
        name="Material Pack Path",
        default=""
    )

    # Add master material to Material
    bpy.types.Material.replicant_master_material = bpy.props.StringProperty(
        name="Master Material",
        default="material/master/master_rs_standard"
    )

    # Add flags to material
    bpy.types.Material.replicant_flags = bpy.props.PointerProperty(type=MaterialFlags)

    # Add textures to Material
    bpy.types.Material.replicant_texture_samplers = bpy.props.CollectionProperty(
        type=TextureSampler,
        name="Texture Samplers",
    )

    # Add constant buffers to Material
    bpy.types.Material.replicant_constant_buffers = bpy.props.CollectionProperty(
        type=ConstantBuffer,
        name="Constant Buffers"
    )

    # Add texture parameters to Material
    bpy.types.Material.replicant_texture_parameters = bpy.props.CollectionProperty(
        type=TextureParameter,
        name="Texture Parameters"
    )

    bpy.types.Material.replicant_export = bpy.props.BoolProperty(
        name="Export",
        description="Include this material in the export",
        default=True
    )

def unregister():
    # Remove material properties
    del bpy.types.Material.replicant_texture_parameters
    del bpy.types.Material.replicant_constant_buffers
    del bpy.types.Material.replicant_texture_samplers
    del bpy.types.Material.replicant_flags
    del bpy.types.Material.replicant_master_material

    # Remove scene properties
    del bpy.types.Scene.replicant_show_texture_samplers
    del bpy.types.Scene.replicant_show_constant_buffers
    del bpy.types.Scene.replicant_show_texture_parameters

    # Unregister classes
    bpy.utils.unregister_class(MATERIAL_PT_replicant)
    bpy.utils.unregister_class(MATERIAL_OT_remove_texture_sampler)
    bpy.utils.unregister_class(MATERIAL_OT_add_texture_sampler)
    bpy.utils.unregister_class(MATERIAL_OT_remove_texture_parameter)
    bpy.utils.unregister_class(MATERIAL_OT_add_texture_parameter)
    bpy.utils.unregister_class(MATERIAL_OT_remove_constant)
    bpy.utils.unregister_class(MATERIAL_OT_add_constant)
    bpy.utils.unregister_class(MATERIAL_OT_remove_constant_buffer)
    bpy.utils.unregister_class(MATERIAL_OT_add_constant_buffer)
    bpy.utils.unregister_class(MATERIAL_OT_open_sampler_texture)
    bpy.utils.unregister_class(MATERIAL_OT_show_image_path)

    bpy.utils.unregister_class(MaterialFlags)
    bpy.utils.unregister_class(TextureSampler)
    bpy.utils.unregister_class(ConstantBuffer)
    bpy.utils.unregister_class(ConstantValue)
    bpy.utils.unregister_class(TextureParameter)
    