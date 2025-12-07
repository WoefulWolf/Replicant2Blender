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
        mesh_export(layout, context, scene)
        material_export(layout, context, scene)
        texture_export(layout, context, scene)

def mesh_export(layout, context, scene):
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

    box.prop(scene, "replicant_original_mesh_pack")

    col_box = box.box()

    # Find direct child collections of root with mesh objects (in Outliner order)
    valid_collections = [col for col in context.scene.collection.children if any(obj.type == 'MESH' for obj in col.objects)]

    if not valid_collections:
        col_box.label(text="None found", icon='INFO')
    else:
        for collection in valid_collections:
            row = col_box.row()
            row.label(text=collection.name, icon='OUTLINER_COLLECTION')
            row.prop(collection, "replicant_export", text="")

    box.separator()

    # Export button
    row = box.row()
    row.scale_y = 2.0
    op = row.operator("export.replicant_pack", text="Export Mesh PACK", icon='EXPORT')
    op.type = 'MESH'

def material_export(layout, context, scene):
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

def texture_export(layout, context, scene):
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

def register():
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
    del bpy.types.Collection.replicant_export
