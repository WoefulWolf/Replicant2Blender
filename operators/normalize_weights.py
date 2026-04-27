import bpy
import bmesh


def normalize_weights(obj, context):
    if not obj or obj.type != 'MESH':
        return False, "Object is not a mesh", 0

    if not obj.vertex_groups:
        return True, "No vertex groups to process", 0

    vg_count = len(obj.vertex_groups)
    vertices_normalized = 0

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        deform_layer = bm.verts.layers.deform.verify()
        for v in bm.verts:
            deform = v[deform_layer]
            if not deform:
                continue
            total = sum(deform.values())
            if total <= 0 or abs(total - 1.0) < 1e-6:
                continue
            for group_idx in list(deform.keys()):
                deform[group_idx] = deform[group_idx] / total
            vertices_normalized += 1
        bm.to_mesh(obj.data)
    finally:
        bm.free()

    return True, f"Normalized weights for {vertices_normalized} vertex/vertices", vg_count


class REPLICANT_OT_normalize_weights(bpy.types.Operator):
    """Normalize all vertex weights so they sum to 1 per vertex"""
    bl_idname = "replicant.normalize_weights"
    bl_label = "Normalize Weights"
    bl_options = {'REGISTER', 'UNDO'}

    mesh_name: bpy.props.StringProperty(
        name="Mesh",
        description="Name of the mesh object to process",
        default=""
    )

    def execute(self, context):
        if not self.mesh_name:
            self.report({'ERROR'}, "No mesh name specified")
            return {'CANCELLED'}

        obj = bpy.data.objects.get(self.mesh_name)
        if not obj:
            self.report({'ERROR'}, f"Object '{self.mesh_name}' not found")
            return {'CANCELLED'}

        success, message, _ = normalize_weights(obj, context)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, message)
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(REPLICANT_OT_normalize_weights)


def unregister():
    bpy.utils.unregister_class(REPLICANT_OT_normalize_weights)
