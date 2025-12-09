from decimal import Context
import os
import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty, PointerProperty
from bpy.types import Material, UILayout

from ..util import get_export_materials

class OUTPUT_OT_toggle_texture_pack_expand(bpy.types.Operator):
    """Toggle texture pack expand/collapse state"""
    bl_idname = "output.toggle_texture_pack_expand"
    bl_label = "Toggle Texture Pack"
    bl_options = {'INTERNAL'}

    pack_path: StringProperty(name="Pack Path")

    def execute(self, context):
        expanded_packs = set(context.scene.replicant_expanded_texture_packs.split(',')) if context.scene.replicant_expanded_texture_packs else set()

        if self.pack_path in expanded_packs:
            expanded_packs.remove(self.pack_path)
        else:
            expanded_packs.add(self.pack_path)

        # Remove empty strings from set
        expanded_packs.discard('')

        context.scene.replicant_expanded_texture_packs = ','.join(expanded_packs)
        return {'FINISHED'}

class OUTPUT_OT_rename_texture_pack(bpy.types.Operator):
    """Rename a texture pack path across all materials"""
    bl_idname = "output.rename_texture_pack"
    bl_label = "Rename Texture Pack"
    bl_options = {'REGISTER', 'UNDO'}

    old_pack: StringProperty(name="Old Pack Path", options={'HIDDEN'})
    new_pack: StringProperty(name="New Pack Path")

    def invoke(self, context, event):
        # Set new_pack to old_pack initially so user can edit it
        self.new_pack = self.old_pack
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Rename: {self.old_pack}")
        layout.prop(self, "new_pack", text="New Path")

    def execute(self, context):
        if not self.old_pack or not self.new_pack:
            return {'CANCELLED'}

        if self.old_pack == self.new_pack:
            return {'CANCELLED'}

        # Update all materials that use this pack path
        updated_count = 0
        for material in bpy.data.materials:
            if not hasattr(material, 'replicant_texture_samplers'):
                continue
            for sampler in material.replicant_texture_samplers:
                if sampler.pack_path == self.old_pack:
                    sampler.pack_path = self.new_pack
                    updated_count += 1

        # Rebuild expanded packs list with only valid packs that exist after rename
        # First, build the current set of all pack paths
        from ..util import get_export_materials
        export_materials = get_export_materials()
        replicant_materials = [m for m in export_materials if m.replicant_master_material]
        valid_packs = set()
        for material in replicant_materials:
            for sampler in material.replicant_texture_samplers:
                if sampler.pack_path:
                    valid_packs.add(sampler.pack_path)

        # Filter expanded packs to only include valid ones
        expanded_packs = set(context.scene.replicant_expanded_texture_packs.split(',')) if context.scene.replicant_expanded_texture_packs else set()
        # If old pack was expanded, add the new pack to expanded list
        if self.old_pack in expanded_packs:
            expanded_packs.add(self.new_pack)
        # Only keep packs that actually exist
        expanded_packs = {pack for pack in expanded_packs if pack and pack in valid_packs}
        context.scene.replicant_expanded_texture_packs = ','.join(expanded_packs)

        # Force UI redraw to show updated pack names immediately
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()

        self.report({'INFO'}, f"Updated {updated_count} sampler(s)")
        return {'FINISHED'}

class OUTPUT_PT_replicant(bpy.types.Panel):
    bl_label: str = "NieR Replicant ver.1.2247... Export"
    bl_idname: str = "OUTPUT_PT_replicant"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context: str = "output"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Export Sources:", icon='EXPORT')
        box = layout.box()
        valid_collections = [col for col in scene.collection.children if any(obj.type == 'MESH' for obj in col.objects)]
        if not valid_collections:
            box.label(text="None found", icon='INFO')
        else:
            for collection in valid_collections:
                row = box.row()
                row.label(text=collection.name, icon='OUTLINER_COLLECTION')
                row.prop(collection, "replicant_export", text="")

        layout.separator(type='LINE')

        mesh_export(layout, context)
        material_export(layout, context)
        texture_export(layout, context)

def mesh_export(layout: UILayout, context: Context):
    box = layout.box()
    header = box.row(align=True)
    header.alignment = 'LEFT'
    header.prop(context.scene, "replicant_show_mesh_export",
                text="",
                icon='TRIA_DOWN' if context.scene.replicant_show_mesh_export else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.prop(context.scene, "replicant_show_mesh_export",
                text="Mesh PACK Export",
                icon='MESH_MONKEY',
                emboss=False, toggle=True)

    if not context.scene.replicant_show_mesh_export:
        return

    split = box.split(factor=0.35, align=True)
    col1 = split.column()
    col1.label(text="Original Mesh PACK:", icon='FILE_ALIAS')
    col2 = split.column()
    col2.prop(context.scene, "replicant_original_mesh_pack", text="")

    # Export button
    row = box.row()
    row.scale_y = 2.0
    op = row.operator("export.replicant_pack", text="Export Mesh PACK", icon='EXPORT')
    op.type = 'MESH'

def material_export(layout: UILayout, context: Context):
    box = layout.box()
    header = box.row(align=True)
    header.alignment = 'LEFT'
    header.prop(context.scene, "replicant_show_material_export",
                text="",
                icon='TRIA_DOWN' if context.scene.replicant_show_material_export else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.prop(context.scene, "replicant_show_material_export",
                text="Material PACK Export",
                icon='MATERIAL',
                emboss=False, toggle=True)

    if not context.scene.replicant_show_material_export:
        return

def texture_export(layout: UILayout, context: Context):
    box = layout.box()
    header = box.row(align=True)
    header.alignment = 'LEFT'
    header.prop(context.scene, "replicant_show_texture_export",
                text="",
                icon='TRIA_DOWN' if context.scene.replicant_show_texture_export else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.prop(context.scene, "replicant_show_texture_export",
                text="Texture PACK Export",
                icon='TEXTURE',
                emboss=False, toggle=True)

    if not context.scene.replicant_show_texture_export:
        return

    export_materials = get_export_materials()
    replicant_materials = [m for m in export_materials if m.replicant_master_material]
    texture_packs: dict[str, list[Material]] = {}
    for material in replicant_materials:
        for sampler in material.replicant_texture_samplers:
            if sampler.pack_path in texture_packs:
                if material in texture_packs[sampler.pack_path]:
                    continue
                texture_packs[sampler.pack_path].append(material)
                continue
            else:
                texture_packs[sampler.pack_path] = [material]

    # Get set of expanded packs
    expanded_packs = set(context.scene.replicant_expanded_texture_packs.split(',')) if context.scene.replicant_expanded_texture_packs else set()

    for pack, materials in texture_packs.items():
        pack_box = box.box()

        # Pack header with collapse/expand toggle and pack name
        pack_header = pack_box.row(align=True)
        pack_header.alignment = 'LEFT'
        is_expanded = pack in expanded_packs

        # Toggle expand/collapse
        icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
        toggle_op = pack_header.operator("output.toggle_texture_pack_expand", text="", icon=icon, emboss=False)
        toggle_op.pack_path = pack

        # Show pack path as label
        pack_header.label(text=pack, icon='FILE_FOLDER')

        # Rename button
        rename_op = pack_header.operator("output.rename_texture_pack", text="", icon='GREASEPENCIL', emboss=False)
        rename_op.old_pack = pack

        # Only show contents if expanded
        if not is_expanded:
            continue

        texture_paths = set()

        tex_box = pack_box.box()
        for mat in materials:
            for sampler in mat.replicant_texture_samplers:
                if sampler.pack_path == pack:  # Only show textures from this pack
                    if sampler.texture_path in texture_paths:
                        continue
                    else:
                        texture_paths.add(sampler.texture_path)

                    row = tex_box.row()
                    split = row.split(factor=0.5)
                    path_op = split.operator("material.show_image_path", text=os.path.basename(sampler.texture_path), icon='NODE_SOCKET_TEXTURE')
                    path_op.filepath = sampler.texture_path

                    if os.path.splitext(sampler.texture_path)[-1] == ".dds":
                        right_split = split.split(factor=0.6)
                        right_split.label(text=sampler.dxgi_format, icon='CHECKMARK')
                        if sampler.mip_maps:
                            right_split.label(text=f"Mipmaps", icon='CHECKBOX_HLT')
                        else:
                            right_split.label(text=f"Mipmaps", icon='CHECKBOX_DEHLT')
                    else:
                        right_split = split.split(factor=0.5)
                        right_split.enabled = False
                        right_split.alert = True
                        right_split.label(text="Embedded DXGI compression not implemented yet!", icon='X')
                        right_split.prop(sampler, "dxgi_format", text="")
                        right_split.prop(sampler, "mip_maps", text="Mipmaps")

        # Export button
        row = tex_box.row()
        row.scale_y = 2.0
        op = row.operator("export.replicant_pack", text="Export Texture PACK", icon='EXPORT')
        op.type = 'TEXTURE'
        op.texture_pack = pack


def register():
    # Register operators
    bpy.utils.register_class(OUTPUT_OT_toggle_texture_pack_expand)
    bpy.utils.register_class(OUTPUT_OT_rename_texture_pack)

    bpy.types.Scene.replicant_show_mesh_export = bpy.props.BoolProperty(
        name="Show Mesh PACK Export",
        default=True
    )
    bpy.types.Scene.replicant_show_material_export = bpy.props.BoolProperty(
        name="Show Material PACK Export",
        default=False
    )
    bpy.types.Scene.replicant_show_texture_export = bpy.props.BoolProperty(
        name="Show Texture PACK Export",
        default=False
    )

    bpy.types.Scene.replicant_original_mesh_pack = StringProperty(
        name="Original Mesh PACK",
        description="Path to the original mesh PACK file",
        default="",
        subtype='FILE_PATH'
    )

    # Property to store which texture packs are expanded
    bpy.types.Scene.replicant_expanded_texture_packs = StringProperty(
        name="Expanded Texture Packs",
        description="Comma-separated list of expanded texture pack paths",
        default=""
    )

    bpy.types.Collection.replicant_export = BoolProperty(
        name="Export",
        description="Include this collection in the export",
        default=False
    )

    bpy.utils.register_class(OUTPUT_PT_replicant)

def unregister():
    bpy.utils.unregister_class(OUTPUT_PT_replicant)

    del bpy.types.Scene.replicant_show_mesh_export
    del bpy.types.Scene.replicant_show_material_export
    del bpy.types.Scene.replicant_show_texture_export
    del bpy.types.Scene.replicant_original_mesh_pack
    del bpy.types.Scene.replicant_expanded_texture_packs
    del bpy.types.Collection.replicant_export

    # Unregister operators
    bpy.utils.unregister_class(OUTPUT_OT_rename_texture_pack)
    bpy.utils.unregister_class(OUTPUT_OT_toggle_texture_pack_expand)
