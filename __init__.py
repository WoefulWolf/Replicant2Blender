bl_info = {
    "name": "Replicant2Blender (NieR Replicant ver.1.2247 Mesh Pack Importer)",
    "author": "Woeful_Wolf",
    "version": (0, 2),
    "blender": (2, 92, 0),
    "api": 38019,
    "location": "File > Import",
    "description": "Import NieR Replicant Mesh Pack",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Operator, OperatorFileListElement


class ImportReplicantMeshPack(bpy.types.Operator, ImportHelper):
    '''Import NieR Replicant Mesh Pack File(s)'''
    bl_idname = "import.replicant_mesh_pack"
    bl_label = "Import File(s)"
    bl_options = {'PRESET', "REGISTER", "UNDO"}
    files : CollectionProperty(
            name="File Path",
            type=OperatorFileListElement,
            )
    directory : StringProperty(
            subtype='DIR_PATH',
            )
    #filename_ext = ".xap"
    #filter_glob: StringProperty(default="*.xap", options={'HIDDEN'})

    def execute(self, context):
        directory = self.directory
        from . import pack_import
        for file_elem in self.files:
            filepath = os.path.join(directory, file_elem.name)
            if os.path.isfile(filepath):
                pack_import.main(filepath)
        return {"FINISHED"}


# Registration
def replicant_import_mesh_pack(self, context):
    self.layout.operator(ImportReplicantMeshPack.bl_idname, text="NieR Replicant Mesh Pack(s)")

def register():
    bpy.utils.register_class(ImportReplicantMeshPack)
    bpy.types.TOPBAR_MT_file_import.append(replicant_import_mesh_pack)

def unregister():
    bpy.utils.unregister_class(ImportReplicantMeshPack)
    bpy.types.TOPBAR_MT_file_import.remove(replicant_import_mesh_pack)

if __name__ == '__main__':
    register()