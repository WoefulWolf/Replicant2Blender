import bpy
import os
from bpy.types import Operator, UILayout
from bpy.props import EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from ..util import get_collection_objects, get_export_collections, get_export_collections_materials, label_multiline
from . import material_export
from . import texture_export
from . import mesh_export

class EXPORT_OT_replicant_pack(Operator, ExportHelper):
    bl_idname = "export.replicant_pack"
    bl_label = "Export PACK(s)"
    bl_description = "Export data in selected collections to NieR Replicant PACK format"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ""

    filter_glob: StringProperty(
        default="*",
        options={'HIDDEN'},
        maxlen=255,
    )

    type: EnumProperty(
        name="Type",
        description="Export type",
        items=[
            ('MESH', "Mesh", "Export mesh PACK"),
            ('TEXTURE', "Texture", "Export texture PACK"),
            ('MATERIAL', "Material", "Export material PACK(s)"),
        ],
        default='MESH',
        options={'HIDDEN'}
    )

    texture_pack: StringProperty(
        options={'HIDDEN'}
    )

    directory: StringProperty(
        subtype='DIR_PATH',
        options={'HIDDEN'}
    )

    def draw(self, context) -> None:
        layout: UILayout = self.layout
        if self.type == 'MATERIAL':
            label_multiline(context, layout, "Please select a directory where the following material PACK(s) will be written to:")
            box = layout.box()
            listed_filenames = set()
            materials = [m for m in get_export_collections_materials() if m.replicant_master_material and m.replicant_export]
            for mat in materials:
                filename = os.path.basename(mat.replicant_pack_path)
                row = box.row()
                duplicate = False
                icon = 'NODE_SOCKET_SHADER'
                if filename in listed_filenames:
                    duplicate = True
                    row.alert = True
                    icon = 'ERROR'
                listed_filenames.add(filename)
                row.label(text=f"{filename}", icon=icon)
                if duplicate:
                    error_row = box.row()
                    error_row.alert = True
                    error_row.label(text="", icon='FILE_PARENT')
                    error_box = error_row.box()
                    error_box.label(text="Duplicate material PACK name, will overwrite another during export! Did you remember to change a custom material's PACK path?")
        elif self.type == 'TEXTURE':
            label_multiline(context, layout, "Please specify a file which the following texture PACK will be written to:")
            box = layout.box()
            box.label(text=self.texture_pack, icon='FILE_FOLDER')
            tex_box = box.box()
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
            materials = texture_packs[self.texture_pack]
            texture_paths = set()
            for mat in materials:
                for sampler in mat.replicant_texture_samplers:
                    if sampler.texture_path in texture_paths:
                        continue
                    else:
                        texture_paths.add(sampler.texture_path)
                    texture_basename = os.path.basename(sampler.texture_path)
                    texture_filename = os.path.splitext(texture_basename)[0] + ".rtex"
                    tex_box.label(text=texture_filename, icon='NODE_SOCKET_TEXTURE')
        elif self.type == 'MESH':
            label_multiline(context, layout, "Please select a directory where the following mesh PACK(s) will be written to:")
            export_collections = get_export_collections()
            for root, collections in export_collections.items():
                root_box = layout.box()
                root_box.label(text=root.name, icon='FILE_FOLDER')
                for col in collections:
                    box= root_box.box()
                    box.label(text=col.name, icon='FILE')

            return

        return

    def invoke(self, context, event):
        # Validate before opening file dialog
        scene = context.scene

        root_collections_to_export = [col for col in bpy.context.scene.collection.children if any(obj.type == 'MESH' for obj in col.all_objects) and col.replicant_export]
        collections_to_export = [col for root_col in root_collections_to_export for col in root_col.children if any(obj.type == 'MESH' for obj in col.objects) and col.replicant_export]

        if not collections_to_export:
            self.report({'ERROR'}, "No collections selected for export")
            return {'CANCELLED'}

        # For material export, use directory selection
        if self.type == 'MATERIAL':
            materials = [m for m in get_export_collections_materials() if m.replicant_master_material and m.replicant_export]
            if len(materials) == 0:
                self.report({'ERROR'}, "No materials selected for export")
                return {'CANCELLED'}
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        if self.type == 'MESH':
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        if self.type == 'TEXTURE':
            self.filepath = os.path.basename(self.texture_pack)

        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        if self.type == 'MESH':
            return mesh_export.export(self)
        elif self.type == 'TEXTURE':
            return texture_export.export(self)
        elif self.type == 'MATERIAL':
            return material_export.export(self)
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(EXPORT_OT_replicant_pack)


def unregister():
    bpy.utils.unregister_class(EXPORT_OT_replicant_pack)
