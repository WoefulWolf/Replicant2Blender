bl_info = {
    "name": "Replicant2Blender (NieR Replicant ver.1.2247 Mesh Pack Importer)",
    "author": "Woeful_Wolf",
    "version": (0, 1),
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
from bpy.props import StringProperty, BoolProperty, EnumProperty

class ImportReplicantMeshPack(bpy.types.Operator, ImportHelper):
    '''Import a NieR Replicant Mesh Pack File.'''
    bl_idname = "import.replicant_mesh_pack"
    bl_label = "Import Mesh Pack File"
    bl_options = {'PRESET', "REGISTER", "UNDO"}
    #filename_ext = ".xap"
    #filter_glob: StringProperty(default="*.xap", options={'HIDDEN'})

    def execute(self, context):
        from . import pack_import
        return pack_import.main(self.filepath)


# Registration
def replicant_import_mesh_pack(self, context):
    self.layout.operator(ImportReplicantMeshPack.bl_idname, text="NieR Replicant Mesh Pack")

def register():
    bpy.utils.register_class(ImportReplicantMeshPack)
    bpy.types.TOPBAR_MT_file_import.append(replicant_import_mesh_pack)

def unregister():
    bpy.utils.unregister_class(ImportReplicantMeshPack)
    bpy.types.TOPBAR_MT_file_import.remove(replicant_import_mesh_pack)

if __name__ == '__main__':
    register()