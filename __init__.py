bl_info = {
    "name": "Replicant2Blender (NieR Replicant ver.1.2247... Mesh Pack Importer)",
    "author": "Woeful_Wolf",
    "version": (0, 6, 1),
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
from .util import log

class ImportReplicantMeshPack(bpy.types.Operator, ImportHelper):
    '''Import NieR Replicant Mesh Pack File(s)'''
    bl_idname = "import_scene.replicant_mesh_pack"
    bl_label = "Import File(s)"
    bl_options = {'PRESET', "REGISTER", "UNDO"}
    files : CollectionProperty(
            name="File Path",
            type=OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')
    batch_size: bpy.props.IntProperty(name="Texture Conversion Batch Size", default=15, description="Batch sizes when converting textures. Higher values will be faster but require more CPU resources", min=1)
    extract_textures: bpy.props.BoolProperty(name="Extract Textures (Slow)", description="This automatically extracts and tries to convert textures to PNG (Conversion to PNG requires the user to have setup Noesis in this add-on's preferences)", default=True)
    construct_materials: bpy.props.BoolProperty(name="Construct Materials", description="This automatically sets up materials with the appropriate textures (Requires the user to have extracted the textures at least once before)", default=True)
    only_extract_textures: bpy.props.BoolProperty(name="Only Extract Textures", description="This can be used to simply extract the textures from a PACK containing some, nothing else will be done (Requires the user to have setup Noesis in this add-on's preferences)", default=False)

    def execute(self, context):
        directory = self.directory
        for file_elem in self.files:
            filepath = os.path.join(directory, file_elem.name)
            if os.path.isfile(filepath):
                if self.only_extract_textures:
                    pack_import.only_extract_textures(filepath, self.batch_size, __name__)
                else:
                    pack_import.main(filepath, self.extract_textures, self.construct_materials, self.batch_size, __name__)
        pack_import.clear_importLists()
        return {"FINISHED"}

class SelectNoesisExecutable(bpy.types.Operator, ImportHelper):
    '''Select Noesis Executable'''
    bl_idname = "replicant.noesis_select"
    bl_label = "Select Noesis Executable"
    filename_ext = ".exe"
    filter_glob: StringProperty(default="*.exe", options={'HIDDEN'})

    def execute(self, context):
        context.preferences.addons[__name__].preferences.noesis_path = self.filepath
        return {'FINISHED'}

class Replicant2BlenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    # noesis_path : StringProperty(default="D:\\Programs\\Noesis\\Noesis.exe", options={'HIDDEN'})
    noesis_path : StringProperty(options={'HIDDEN'})
    assets_path : StringProperty(options={'HIDDEN'})

    def draw(self, context):
        layout = self.layout
        layout.label(text="Automatic texture & material setup requires that you have Noesis:")
        row = layout.row()
        row.operator("wm.url_open", text="Noesis Download").url = "https://richwhitehouse.com/index.php?content=inc_projects.php"
        layout.label(text="Path To Noesis Executable:")
        if os.name != 'nt':
            layout.label(text="If you aren't on Windows this probably won't work out of the box, but I'll leave it accessible anyways.")
        row = layout.row()
        row.prop(self, "noesis_path", text="")
        row.operator("replicant.noesis_select", icon="FILE_TICK", text="")
        layout.label(text="Path To Assets Folder:")
        row = layout.row()
        row.prop(self, "assets_path", text="")
            

# Registration
def replicant_import_mesh_pack(self, context):
    self.layout.operator(ImportReplicantMeshPack.bl_idname, text="NieR Replicant Mesh Pack(s)")

def register():
    log.d("Registering...")
    bpy.utils.register_class(ImportReplicantMeshPack)
    bpy.utils.register_class(SelectNoesisExecutable)
    bpy.types.TOPBAR_MT_file_import.append(replicant_import_mesh_pack)
    bpy.utils.register_class(Replicant2BlenderPreferences)
    log.d("Registered")

def unregister():
    log.d("Unregistering...")
    bpy.utils.unregister_class(ImportReplicantMeshPack)
    bpy.utils.unregister_class(SelectNoesisExecutable)
    bpy.types.TOPBAR_MT_file_import.remove(replicant_import_mesh_pack)
    bpy.utils.unregister_class(Replicant2BlenderPreferences)
    log.d("Unregistered")

if __name__ == '__main__':
    register()
