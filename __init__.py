bl_info = {
    "name": "Replicant2Blender (NieR Replicant ver.1.2247... Mesh Pack Importer)",
    "author": "Woeful_Wolf",
    "version": (0, 7, 1),
    "blender": (4, 1, 0),
    "api": 38019,
    "location": "File > Import",
    "description": "Import NieR Replicant Mesh Pack",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}

import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Operator, OperatorFileListElement
from . import pack_import
from .util import log, show_blender_system_console

class ImportReplicantMeshPack(bpy.types.Operator, ImportHelper):
    '''Import NieR Replicant Mesh Pack File(s)'''
    bl_idname = "import_scene.replicant_mesh_pack"
    bl_label = "Import File(s)"
    bl_options = {'PRESET', "REGISTER", "UNDO"}
    files : CollectionProperty(
            name="File Path",
            type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')
    extract_textures: bpy.props.BoolProperty(name="Extract Textures", description="This automatically extracts and tries to convert textures to PNG", default=True)
    construct_materials: bpy.props.BoolProperty(name="Construct Materials", description="This automatically sets up materials with the appropriate textures (Requires the user to have extracted the textures at least once before)", default=True)
    only_extract_textures: bpy.props.BoolProperty(name="Only Extract Textures", description="This can be used to simply extract the textures from a PACK containing some, nothing else will be done", default=False)

    def execute(self, context):
        directory = self.directory
        for file_elem in self.files:
            filepath = os.path.join(directory, file_elem.name)
            if os.path.isfile(filepath):
                show_blender_system_console()
                if self.only_extract_textures:
                    pack_import.only_extract_textures(filepath, __name__)
                else:
                    pack_import.main(filepath, self.extract_textures, self.construct_materials, __name__)
        pack_import.clear_importLists()
        return {"FINISHED"}

class Replicant2BlenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    assets_path : StringProperty(options={'HIDDEN'})

    def draw(self, context):
        layout = self.layout
        layout.label(text="Path To Assets Folder:")
        row = layout.row()
        row.prop(self, "assets_path", text="")
            

# Registration
def replicant_import_mesh_pack(self, context):
    self.layout.operator(ImportReplicantMeshPack.bl_idname, text="NieR Replicant Mesh Pack(s)")

def register():
    log.d("Registering...")
    bpy.utils.register_class(ImportReplicantMeshPack)
    bpy.types.TOPBAR_MT_file_import.append(replicant_import_mesh_pack)
    bpy.utils.register_class(Replicant2BlenderPreferences)
    log.d("Registered")

def unregister():
    log.d("Unregistering...")
    bpy.utils.unregister_class(ImportReplicantMeshPack)
    bpy.types.TOPBAR_MT_file_import.remove(replicant_import_mesh_pack)
    bpy.utils.unregister_class(Replicant2BlenderPreferences)
    log.d("Unregistered")

if __name__ == '__main__':
    register()
