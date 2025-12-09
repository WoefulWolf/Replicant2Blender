import bpy
import os
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from . import texture_export
from . import mesh_export

class EXPORT_OT_replicant_pack(Operator, ExportHelper):
    bl_idname = "export.replicant_pack"
    bl_label = "Export PACK"
    bl_description = "Export data in selected collections to a NieR Replicant PACK format"
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
            ('MATERIAL', "Material", "Export material PACK"),
        ],
        default='MESH',
        options={'HIDDEN'}
    )
    texture_pack: StringProperty(
        options={'HIDDEN'}
    )

    def invoke(self, context, event):
        # Validate before opening file dialog
        scene = context.scene
        original_pack_path = scene.replicant_original_mesh_pack

        if self.type == 'MESH' and not original_pack_path:
            self.report({'ERROR'}, "No original mesh PACK file specified")
            return {'CANCELLED'}

        collections_to_export = [col for col in bpy.data.collections if col.replicant_export]

        if not collections_to_export:
            self.report({'ERROR'}, "No collections selected for export")
            return {'CANCELLED'}

        # Set default filename to match original pack file
        if self.type == 'MESH':
            self.filepath = os.path.basename(original_pack_path)
        elif self.type == 'TEXTURE':
            self.filepath = os.path.basename(self.texture_pack)

        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        if self.type == 'MESH':
            return mesh_export.export(self)
        if self.type == 'TEXTURE':
            return texture_export.export(self)
        else:
            self.report({'ERROR'}, "Not yet implemented")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(EXPORT_OT_replicant_pack)


def unregister():
    bpy.utils.unregister_class(EXPORT_OT_replicant_pack)
