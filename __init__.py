import bpy
import os
from bpy_extras.io_utils import ExportHelper,ImportHelper
from bpy.types import Operator, OperatorFileListElement

from .importers import pack_import
from .exporters import pack_export, archive_export
from .ui import output, material
from .operators import rip_mesh_uv_islands, triangulate, open_url
from .util import log, show_blender_system_console

class ImportReplicantMeshPack(bpy.types.Operator, ImportHelper):
    '''Import NieR Replicant Mesh Pack File(s)'''
    bl_idname = "import_scene.replicant_mesh_pack"
    bl_label = "Import File(s)"
    bl_options = {'PRESET', "REGISTER", "UNDO"}
    files : bpy.props.CollectionProperty(name="File Path", type=OperatorFileListElement)
    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    extract_textures: bpy.props.BoolProperty(name="Extract Textures", description="This automatically extracts and tries to convert textures to PNG/TIF", default=True)
    construct_materials: bpy.props.BoolProperty(name="Construct Materials", description="This automatically sets up materials with the appropriate textures (Requires the user to have extracted the textures at least once before)", default=True)
    only_extract_textures: bpy.props.BoolProperty(name="Only Extract Textures", description="This can be used to simply extract the textures from a PACK containing some, nothing else will be done", default=False)

    def execute(self, context):
        directory = self.directory
        show_blender_system_console()
        bpy.context.scene.render.fps = 60
        bpy.context.scene.frame_end = 600
        for file_elem in self.files:
            filepath = os.path.join(directory, file_elem.name)
            if os.path.isfile(filepath):
                if self.only_extract_textures:
                    pack_import.only_extract_textures(filepath, __name__)
                else:
                    pack_import.main(filepath, self.extract_textures, self.construct_materials, __name__)
        pack_import.clear_import_lists()
        return {"FINISHED"}

class Replicant2BlenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    assets_path : bpy.props.StringProperty(options={'HIDDEN'})

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
    pack_export.register()
    archive_export.register()
    triangulate.register()
    rip_mesh_uv_islands.register()
    open_url.register()
    output.register()
    material.register()
    log.d("Registered")

def unregister():
    log.d("Unregistering...")
    material.unregister()
    output.unregister()
    open_url.unregister()
    rip_mesh_uv_islands.unregister()
    triangulate.unregister()
    archive_export.unregister()
    pack_export.unregister()
    bpy.utils.unregister_class(Replicant2BlenderPreferences)
    bpy.types.TOPBAR_MT_file_import.remove(replicant_import_mesh_pack)
    bpy.utils.unregister_class(ImportReplicantMeshPack)
    log.d("Unregistered")

if __name__ == '__main__':
    register()
