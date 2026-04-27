import bpy
import bmesh


def limit_bones(obj, context):
    if not obj or obj.type != 'MESH':
        return False, "Object is not a mesh", 0

    if not obj.vertex_groups:
        return True, "No vertex groups to process", 0

    vg_count = len(obj.vertex_groups)
    weights_removed = 0

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        deform_layer = bm.verts.layers.deform.verify()
        for v in bm.verts:
            deform = v[deform_layer]
            if len(deform) <= 4:
                continue
            # Drop everything past the top 4 entries by weight
            extras = sorted(deform.items(), key=lambda item: item[1], reverse=True)[4:]
            for group_idx, _weight in extras:
                del deform[group_idx]
                weights_removed += 1
        bm.to_mesh(obj.data)
    finally:
        bm.free()

    return True, f"Limited {weights_removed} extra weight(s) across {vg_count} vertex group(s)", vg_count


class REPLICANT_OT_limit_bones(bpy.types.Operator):
    """Limit each vertex to its 4 strongest bone-weight assignments"""
    bl_idname = "replicant.limit_bones"
    bl_label = "Limit Bones to 4"
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

        success, message, _ = limit_bones(obj, context)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, message)
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(REPLICANT_OT_limit_bones)


def unregister():
    bpy.utils.unregister_class(REPLICANT_OT_limit_bones)
