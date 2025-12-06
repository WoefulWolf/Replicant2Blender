import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty, PointerProperty

class OUTPUT_PT_replicant(bpy.types.Panel):
    bl_label: str = "NieR Replicant ver.1.2247... Export"
    bl_idname: str = "OUTPUT_PT_replicant"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context: str = "output"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "replicant_original_mesh_pack")

        layout.separator()
        layout.label(text="Collections to Export:")

        box = layout.box()

        # Find direct child collections of root with mesh objects (in Outliner order)
        valid_collections = [col for col in context.scene.collection.children if any(obj.type == 'MESH' for obj in col.objects)]

        if not valid_collections:
            box.label(text="None found", icon='INFO')
        else:
            for collection in valid_collections:
                row = box.row()
                row.label(text=collection.name, icon='OUTLINER_COLLECTION')
                row.prop(collection, "replicant_export", text="")

        layout.separator()

        # Export button
        row = layout.row()
        row.scale_y = 2.0
        op = row.operator("export.replicant_pack", text="Export Mesh PACK", icon='EXPORT')
        op.type = 'MESH'

def register():
    bpy.types.Scene.replicant_original_mesh_pack = StringProperty(
        name="Original Mesh PACK",
        description="Path to the original mesh PACK file",
        default="",
        subtype='FILE_PATH'
    )

    bpy.types.Collection.replicant_export = BoolProperty(
        name="Export",
        description="Include this collection in the export",
        default=False
    )

    bpy.utils.register_class(OUTPUT_PT_replicant)

def unregister():
    bpy.utils.unregister_class(OUTPUT_PT_replicant)

    del bpy.types.Scene.replicant_original_mesh_pack
    del bpy.types.Collection.replicant_export
