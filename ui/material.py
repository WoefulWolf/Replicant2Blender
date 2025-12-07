import bpy
import os

class MATERIAL_OT_show_image_path(bpy.types.Operator):
    bl_idname = "material.show_image_path"
    bl_label = "Image Path"
    bl_options = {'INTERNAL'}

    filepath: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        path = properties.filepath if properties.filepath else "No image loaded"
        return f"{path}\n\nClick to copy to clipboard"

    def execute(self, context):
        if self.filepath:
            context.window_manager.clipboard = self.filepath
            self.report({'INFO'}, f"Copied to clipboard: {self.filepath}")
        return {'FINISHED'}

class MATERIAL_OT_open_node_image(bpy.types.Operator):
    bl_idname = "material.open_node_image"
    bl_label = "Open Image"
    bl_description = "Open an image file for this texture node"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and material.use_nodes:
            node = material.node_tree.nodes.get(self.node_name)
            if node and node.type == 'TEX_IMAGE':
                # Load or get existing image
                img = bpy.data.images.load(self.filepath, check_existing=True)
                node.image = img
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
    bl_idname = "material.remove_texture_parameter"
    bl_label = "Remove Texture Parameter"
    bl_options = {'REGISTER', 'UNDO'}

    parameter_index: bpy.props.IntProperty()

    def execute(self, context):
        material = context.active_object.active_material
        if material and 0 <= self.parameter_index < len(material.replicant_texture_parameters):
            material.replicant_texture_parameters.remove(self.parameter_index)
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

class MATERIAL_PT_replicant(bpy.types.Panel):
    bl_label: str = "NieR Replicant ver.1.2247... Material Instance"
    bl_idname: str = "MATERIAL_PT_replicant"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context: str = "material"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or not obj.active_material:
            layout.label(text="No active material")
            return

        material = obj.active_material

        layout.prop(material, "replicant_master_material", text="", icon='SHADING_TEXTURE')

        texture_samplers(layout, context, material)
        constant_buffers(layout, context, material)
        texture_parameters(layout, context, material)

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

    if not material.use_nodes:
        box.label(text="Please enable nodes")
        return

    # Find all Image Texture nodes
    image_texture_nodes = [node for node in material.node_tree.nodes
                            if node.type == 'TEX_IMAGE' and node.label.startswith('tex')]

    if not image_texture_nodes:
        box.label(text="No texture samplers found")
        return

    for node in image_texture_nodes:
        row = box.row(align=True)

        split = row.split(factor=0.5, align=True)
        split.prop(node, "label", text="", icon='IMAGE_DATA')

        # Right column - filename takes up most space, icon button at the end
        right_col = split.row(align=True)

        # Show image filename (basename only, full path on hover) - expands to fill
        if node.image:
            filepath = node.image.filepath
            basename = os.path.basename(filepath) if filepath else "Unknown"

            # Show basename as a button with full path tooltip
            path_op = right_col.operator("material.show_image_path", text=basename)
            path_op.filepath = filepath
        else:
            right_col.label(text="No image", icon='ERROR')

        # Open image button (small icon only) - always on the right
        icon_col = right_col.column(align=True)
        op = icon_col.operator("material.open_node_image", text="", icon='FILEBROWSER')
        op.node_name = node.name

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
    bpy.utils.register_class(TextureParameter)
    bpy.utils.register_class(ConstantValue)
    bpy.utils.register_class(ConstantBuffer)

    # Register operators and panels
    bpy.utils.register_class(MATERIAL_OT_show_image_path)
    bpy.utils.register_class(MATERIAL_OT_open_node_image)
    bpy.utils.register_class(MATERIAL_OT_add_constant_buffer)
    bpy.utils.register_class(MATERIAL_OT_remove_constant_buffer)
    bpy.utils.register_class(MATERIAL_OT_add_constant)
    bpy.utils.register_class(MATERIAL_OT_remove_constant)
    bpy.utils.register_class(MATERIAL_OT_add_texture_parameter)
    bpy.utils.register_class(MATERIAL_OT_remove_texture_parameter)
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

    # Add master material to Material
    bpy.types.Material.replicant_master_material = bpy.props.StringProperty(
        name="Master Material",
        default="material/master/master_rs_standard"
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

def unregister():
    # Remove material properties
    del bpy.types.Material.replicant_texture_parameters
    del bpy.types.Material.replicant_constant_buffers
    del bpy.types.Material.replicant_master_material

    # Remove scene properties
    del bpy.types.Scene.replicant_show_texture_samplers
    del bpy.types.Scene.replicant_show_constant_buffers
    del bpy.types.Scene.replicant_show_texture_parameters

    # Unregister classes
    bpy.utils.unregister_class(MATERIAL_PT_replicant)
    bpy.utils.unregister_class(MATERIAL_OT_remove_texture_parameter)
    bpy.utils.unregister_class(MATERIAL_OT_add_texture_parameter)
    bpy.utils.unregister_class(MATERIAL_OT_remove_constant)
    bpy.utils.unregister_class(MATERIAL_OT_add_constant)
    bpy.utils.unregister_class(MATERIAL_OT_remove_constant_buffer)
    bpy.utils.unregister_class(MATERIAL_OT_add_constant_buffer)
    bpy.utils.unregister_class(MATERIAL_OT_open_node_image)
    bpy.utils.unregister_class(MATERIAL_OT_show_image_path)
    bpy.utils.unregister_class(ConstantBuffer)
    bpy.utils.unregister_class(ConstantValue)
    bpy.utils.unregister_class(TextureParameter)