import bpy
import bmesh


def triangulate_mesh(obj, context):
    """
    Triangulate all faces in a mesh.

    Args:
        obj: The mesh object to triangulate
        context: Blender context

    Returns:
        tuple: (success: bool, message: str, face_count: int)
    """
    if not obj or obj.type != 'MESH':
        return False, "Object is not a mesh", 0

    # Store the current mode and selection
    original_active = context.view_layer.objects.active
    original_mode = obj.mode if obj == original_active else 'OBJECT'

    # Set the object as active and enter edit mode
    context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Create BMesh from the object
    bm = bmesh.from_edit_mesh(obj.data)

    # Select all faces
    bpy.ops.mesh.select_all(action='SELECT')

    # Count faces before triangulation
    faces_before = len(bm.faces)

    # Triangulate
    original_face_count = len(bm.faces)
    try:
        result = bmesh.ops.triangulate(bm, faces=bm.faces[:])
        new_face_count = len(result['faces']) - original_face_count
    except Exception as e:
        bm.free()
        bpy.ops.object.mode_set(mode=original_mode)
        if original_active:
            context.view_layer.objects.active = original_active
        return False, f"Failed to triangulate: {str(e)}", 0

    # Update the mesh
    bmesh.update_edit_mesh(obj.data)

    # Free BMesh and restore mode
    bm.free()
    bpy.ops.object.mode_set(mode=original_mode)

    # Restore original active object
    if original_active:
        context.view_layer.objects.active = original_active

    return True, f"Triangulated mesh ({new_face_count} new faces created)", new_face_count


class REPLICANT_OT_triangulate(bpy.types.Operator):
    """Triangulate mesh"""
    bl_idname = "replicant.triangulate"
    bl_label = "Triangulate Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    mesh_name: bpy.props.StringProperty(
        name="Mesh",
        description="Name of the mesh object to process",
        default=""
    )

    def execute(self, context):
        # Get the mesh object
        if not self.mesh_name:
            self.report({'ERROR'}, "No mesh name specified")
            return {'CANCELLED'}

        obj = bpy.data.objects.get(self.mesh_name)
        if not obj:
            self.report({'ERROR'}, f"Object '{self.mesh_name}' not found")
            return {'CANCELLED'}

        # Call the standalone function
        success, message, face_count = triangulate_mesh(obj, context)

        # Report the result
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(REPLICANT_OT_triangulate)


def unregister():
    bpy.utils.unregister_class(REPLICANT_OT_triangulate)
