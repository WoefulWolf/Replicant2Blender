from decimal import Context
import os
import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, CollectionProperty, PointerProperty
from bpy.types import Material, UILayout

from ..util import get_export_collections, get_export_collections_materials, label_multiline

class PreprocessingSteps(bpy.types.PropertyGroup):
    triangulate: bpy.props.BoolProperty(
        name="Triangulate Meshes",
        description="Enable automated triangulation of meshes",
        default=True,
    )

    rip_mesh_uv_islands: bpy.props.BoolProperty(
        name="Rip Meshes By UV Islands",
        description="Enable automated ripping of meshes by UV islands",
        default=True,
    )

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
        from ..util import get_export_collections_materials
        export_materials = get_export_collections_materials()
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

class OUTPUT_OT_toggle_archive_directory_expand(bpy.types.Operator):
    """Toggle directory directory expand/collapse state"""
    bl_idname = "output.toggle_archive_directory_expand"
    bl_label = "Toggle Archive Directory"
    bl_options = {'INTERNAL'}

    archive_directory: StringProperty(name="Archive Directory")

    def execute(self, context):
        expanded_directories = set(context.scene.replicant_expanded_archive_directories.split(',')) if context.scene.replicant_expanded_archive_directories else set()

        if self.archive_directory in expanded_directories:
            expanded_directories.remove(self.archive_directory)
        else:
            expanded_directories.add(self.archive_directory)

        # Remove empty strings from set
        expanded_directories.discard('')

        context.scene.replicant_expanded_archive_directories = ','.join(expanded_directories)
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

        header = layout.row(align=True)
        header.alignment = 'LEFT'
        header.prop(context.scene, "replicant_show_export_sources",
                    text="",
                    icon='TRIA_DOWN' if context.scene.replicant_show_export_sources else 'TRIA_RIGHT',
                    icon_only=True, emboss=False)
        header.prop(context.scene, "replicant_show_export_sources",
                    text="Export Sources:",
                    icon='EXPORT',
                    emboss=False, toggle=True)
        if scene.replicant_show_export_sources:
            box = layout.box()
            valid_root_collections = [col for col in scene.collection.children if any(obj.type == 'MESH' for obj in col.all_objects)]
            if not valid_root_collections:
                box.label(text="None found", icon='INFO')
            else:
                for root_collection in valid_root_collections:
                    root_box = box.box()
                    row = root_box.row()
                    split = row.split(factor=0.85)
                    left = split.row()
                    left.alignment = 'LEFT'
                    left.prop(root_collection, "replicant_expanded",
                            text="",
                            icon='TRIA_DOWN' if root_collection.replicant_expanded else 'TRIA_RIGHT',
                            icon_only=True, emboss=False)
                    left.prop(root_collection, "replicant_expanded",
                            text=root_collection.name,
                            icon='FILE_FOLDER',
                            emboss=False, toggle=True)
                    right = split.row()
                    right.alignment = 'RIGHT'
                    right.prop(root_collection, "replicant_export", text="")
                    if not root_collection.replicant_expanded:
                        continue
                    sub_box = root_box.box()
                    sub_box.enabled = root_collection.replicant_export
                    split = sub_box.split(factor=0.35, align=True)
                    col1 = split.column()
                    col1.label(text="Original Mesh PACK:", icon='FILE_ALIAS')
                    col2 = split.column()
                    col2.prop(root_collection, "replicant_original_mesh_pack", text="")
                    valid_collections = [col for col in root_collection.children if any(obj.type == 'MESH' for obj in col.objects)]
                    if not valid_collections:
                        sub_box.label(text="None found", icon='INFO')
                        continue
                    for collection in  valid_collections:
                        split = sub_box.split(factor=0.35, align=True)
                        col1 = split.column()
                        col1.label(text=collection.name, icon='FILE')
                        col2 = split.column()
                        row = col2.row()
                        row.prop(collection, "replicant_lod_distance")
                        row.prop(collection, "replicant_export", text="")

        layout.separator(type='LINE')

        mesh_export(layout, context)
        material_export(layout, context)
        texture_export(layout, context)
        archive_export(layout, context)

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

    export_collections = get_export_collections()
    if not export_collections:
        box = box.box()
        box.label(text="None found", icon='INFO')
        return

    pp_box = box.box()
    pp_box.label(text="Non-Destructive Preprocessing", icon='PRESET')
    row = pp_box.row(align=True)
    row.prop(context.scene.replicant_preprocessing_steps, "triangulate", icon='MOD_TRIANGULATE')
    row.prop(context.scene.replicant_preprocessing_steps, "rip_mesh_uv_islands", icon='UV_ISLANDSEL')

    # Export button
    row = box.row()
    row.scale_y = 2.0
    op = row.operator("export.replicant_pack", text="Export Mesh PACK(s)", icon='EXPORT')
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

    mats_box = box.box()
    materials = [m for m in get_export_collections_materials() if m.replicant_master_material]
    
    if len(materials) == 0:
        mats_box.label(text="None found", icon='INFO')
        return
    
    listed_paths = set()
    for material in materials:
        duplicate = False
        if (material.replicant_pack_path, material.replicant_export) in listed_paths:
            duplicate = True
        listed_paths.add((material.replicant_pack_path, material.replicant_export))
        row = mats_box.row()
        icon = 'NODE_SOCKET_SHADER'
        if duplicate:
            row.alert = True
            icon = 'ERROR'
        row.label(text=material.replicant_pack_path, icon=icon)
        row.label(text=material.name, icon='MATERIAL')
        sub_row = row.row()
        sub_row.enabled = False
        sub_row.label(text=material.replicant_master_material)
        row.prop(material, "replicant_export", text="")
        if duplicate:
            error_row = mats_box.row()
            error_row.alert = True
            error_row.label(text="", icon='FILE_PARENT')
            error_box = error_row.box()
            error_box.label(text="Duplicate material PACK path, will overwrite another during export! Did you remember to change a custom material's PACK path?")

    # Export button
    row = box.row()
    row.scale_y = 2.0
    op = row.operator("export.replicant_pack", text="Export Material PACK(s)", icon='EXPORT')
    op.type = 'MATERIAL'

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

    export_materials = get_export_collections_materials()
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

    if len(texture_packs) == 0:
        box = box.box()
        box.label(text="None found", icon='INFO')
        return

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
                    exists= os.path.exists(sampler.texture_path)
                    icon = 'NODE_SOCKET_TEXTURE' if exists else 'ERROR'
                    row.alert = not exists

                    split = row.split(factor=0.5)
                    path_op = split.operator("material.show_image_path", text=os.path.basename(sampler.texture_path), icon=icon)
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

def lunar_tear_footer(context, parent: UILayout):
    parent.separator(type='LINE')
    label_multiline(context, parent, "The Replicant2Blender archive exporting functionality is ported from the original UnsealedVerses, which is part of Lunar Tear.")
    row = parent.row()
    op = row.operator("replicant.open_url", text="Check out Lunar Tear here")
    op.url = "https://github.com/ifa-ifa/Lunar-Tear/"

def archive_export(layout: UILayout, context: Context):
    box = layout.box()
    header = box.row(align=True)
    header.alignment = 'LEFT'
    header.prop(context.scene, "replicant_show_archive_export",
                text="",
                icon='TRIA_DOWN' if context.scene.replicant_show_archive_export else 'TRIA_RIGHT',
                icon_only=True, emboss=False)
    header.prop(context.scene, "replicant_show_archive_export",
                text="UnsealedVerses - Archive Export",
                icon='OUTLINER_COLLECTION',
                emboss=False, toggle=True)

    if not context.scene.replicant_show_archive_export:
        return

    box = box.box()
    box.prop(context.scene, "replicant_archive_root")

    if context.scene.replicant_archive_root == "":
        lunar_tear_footer(context, box)
        return

    if not os.path.exists(context.scene.replicant_archive_root) or not os.path.isdir(context.scene.replicant_archive_root):
        box.label(text="None found", icon='INFO')
        lunar_tear_footer(context, box)
        return

    archive_directories: dict[str, list[str]] = {}
    for root, dirs, files in os.walk(context.scene.replicant_archive_root):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, context.scene.replicant_archive_root)
            head, tail = os.path.split(relative_path)
            if not head:
                head = "."
            archive_directories.setdefault(head, []).append(tail)

    if not archive_directories:
        box = box.box()
        box.label(text="None found", icon='INFO')
        lunar_tear_footer(context, box)
        return

    # Get set of expanded dirs
    expanded_dirs = set(context.scene.replicant_expanded_archive_directories.split(',')) if context.scene.replicant_expanded_archive_directories else set()

    for dir in archive_directories.keys():
        dir_box = box.box()

        # Dir header with collapse/expand toggle and dir name
        dir_header = dir_box.row(align=True)
        dir_header.alignment = 'LEFT'
        is_expanded = dir in expanded_dirs

        # Toggle expand/collapse
        icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
        toggle_op = dir_header.operator("output.toggle_archive_directory_expand", text="", icon=icon, emboss=False)
        toggle_op.archive_directory = dir

        dir_header.label(text=dir, icon='FILE_FOLDER')

        if not is_expanded:
            continue

        files_box = dir_box.box()
        for file in archive_directories[dir]:
            files_box.label(text=file, icon='DOT')

    # Export button
    row = box.row()
    row.scale_y = 2.0
    op = row.operator("export.replicant_archive", text="Export Archive", icon='EXPORT')
    label_multiline(context, box, "The Replicant2Blender archive exporting functionality is ported from the original UnsealedVerses, which is part of Lunar Tear.")
    row = box.row()
    op = row.operator("replicant.open_url", text="Check out Lunar Tear here")
    op.url = "https://github.com/ifa-ifa/Lunar-Tear/"


def register():
    # Register operators
    bpy.utils.register_class(OUTPUT_OT_toggle_archive_directory_expand)
    bpy.utils.register_class(OUTPUT_OT_toggle_texture_pack_expand)
    bpy.utils.register_class(OUTPUT_OT_rename_texture_pack)
    bpy.utils.register_class(PreprocessingSteps)

    bpy.types.Scene.replicant_archive_root = StringProperty(
        name="Archive Root",
        description="Path to the archive root",
        default="",
        subtype='FILE_PATH'
    )

    bpy.types.Scene.replicant_preprocessing_steps = bpy.props.PointerProperty(type=PreprocessingSteps)

    bpy.types.Scene.replicant_show_export_sources = bpy.props.BoolProperty(
        name="Show Export Sources",
        default=True
    )
    bpy.types.Scene.replicant_show_mesh_export = bpy.props.BoolProperty(
        name="Show Mesh PACK Export",
        default=False
    )
    bpy.types.Scene.replicant_show_material_export = bpy.props.BoolProperty(
        name="Show Material PACK Export",
        default=False
    )
    bpy.types.Scene.replicant_show_texture_export = bpy.props.BoolProperty(
        name="Show Texture PACK Export",
        default=False
    )
    bpy.types.Scene.replicant_show_archive_export = bpy.props.BoolProperty(
        name="Show Archive Export",
        default=False
    )

    bpy.types.Collection.replicant_original_mesh_pack = StringProperty(
        name="Original Mesh PACK",
        description="Path to the original mesh PACK file",
        default="",
        subtype='FILE_PATH'
    )
    bpy.types.Collection.replicant_lod_distance = FloatProperty(
        name="LOD Distance",
        description="The LOD distance of this mesh file",
        default=0,
    )
    bpy.types.Collection.replicant_expanded = BoolProperty(
        name="Expanded",
        default=False,
    )

    bpy.types.Scene.replicant_expanded_texture_packs = StringProperty(
        name="Expanded Texture Packs",
        description="Comma-separated list of expanded texture pack paths",
        default=""
    )

    bpy.types.Scene.replicant_expanded_archive_directories = StringProperty(
        name="Expanded Archive Directories",
        description="Comma-separated list of expanded archive directory paths",
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

    del bpy.types.Scene.replicant_preprocessing_steps
    del bpy.types.Scene.replicant_show_archive_export
    del bpy.types.Scene.replicant_show_mesh_export
    del bpy.types.Scene.replicant_show_material_export
    del bpy.types.Scene.replicant_show_texture_export
    del bpy.types.Collection.replicant_original_mesh_pack
    del bpy.types.Scene.replicant_expanded_texture_packs
    del bpy.types.Scene.replicant_archive_root
    del bpy.types.Collection.replicant_export

    # Unregister operators
    bpy.utils.unregister_class(PreprocessingSteps)
    bpy.utils.unregister_class(OUTPUT_OT_rename_texture_pack)
    bpy.utils.unregister_class(OUTPUT_OT_toggle_texture_pack_expand)
    bpy.utils.unregister_class(OUTPUT_OT_toggle_archive_directory_expand)
