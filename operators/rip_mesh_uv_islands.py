import bpy
import bmesh
from mathutils import Vector


def rip_mesh_uv_islands(obj, context):
    """
    Rip mesh based on UV islands, separating geometry at UV seams while preserving normals.

    Args:
        obj: The mesh object to process
        context: Blender context

    Returns:
        tuple: (success: bool, message: str, seam_count: int)
    """
    if not obj or obj.type != 'MESH':
        return False, "Object is not a mesh", 0

    # Store the current mode and selection
    original_active = context.view_layer.objects.active
    original_mode = obj.mode if obj == original_active else 'OBJECT'

    # Make sure we're in object mode to read normals correctly
    context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')

    # Store loop normals (split normals) before any modifications
    mesh = obj.data

    # Get the current loop normals
    original_loop_normals = {}
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]
            pos = vert.co.copy()
            key = (round(pos.x, 6), round(pos.y, 6), round(pos.z, 6))

            # Store normal with vertex position as key
            # Use a list to store multiple normals per position (for different loops)
            if key not in original_loop_normals:
                original_loop_normals[key] = []
            original_loop_normals[key].append(loop.normal.copy())

    # Now enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    # Create BMesh from the object
    bm = bmesh.from_edit_mesh(obj.data)

    # Get the active UV layer
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        bm.free()
        bpy.ops.object.mode_set(mode=original_mode)
        context.view_layer.objects.active = original_active
        return False, "No UV layer found on the mesh", 0

    # Clear all seams first
    for edge in bm.edges:
        edge.seam = False

    # Update mesh
    bmesh.update_edit_mesh(obj.data)

    # Select all to apply seams from islands
    bpy.ops.mesh.select_all(action='SELECT')

    # Mark seams from UV islands
    bpy.ops.uv.seams_from_islands()

    # Update BMesh to get the new seams
    bm.free()
    bm = bmesh.from_edit_mesh(obj.data)

    # Select only edges marked as seams
    bpy.ops.mesh.select_all(action='DESELECT')
    seam_count = 0
    for edge in bm.edges:
        if edge.seam:
            edge.select = True
            seam_count += 1

    # Update mesh to reflect selection
    bmesh.update_edit_mesh(obj.data)

    # If no seams found, exit early
    if seam_count == 0:
        bm.free()
        bpy.ops.object.mode_set(mode=original_mode)
        if original_active:
            context.view_layer.objects.active = original_active
        return True, "No UV island boundaries found", 0

    # Split the selected edges (this separates the geometry at UV seams)
    try:
        bpy.ops.mesh.edge_split()
    except Exception as e:
        bm.free()
        bpy.ops.object.mode_set(mode=original_mode)
        if original_active:
            context.view_layer.objects.active = original_active
        return False, f"Failed to split edges: {str(e)}", 0

    # Free BMesh and switch to object mode
    bm.free()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Apply the stored normals to preserve shading
    mesh = obj.data

    # Apply normals to all loops based on their vertex positions
    normals_to_set = []
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]
            pos = vert.co
            key = (round(pos.x, 6), round(pos.y, 6), round(pos.z, 6))

            # Get the original normal for this position
            if key in original_loop_normals and len(original_loop_normals[key]) > 0:
                # If there are multiple normals at this position, pick the one that best matches
                # the current loop normal direction (to avoid flipped normals)
                if len(original_loop_normals[key]) == 1:
                    normals_to_set.append(original_loop_normals[key][0])
                else:
                    # Find the normal with the highest dot product (most similar direction)
                    current_normal = loop.normal
                    best_normal = original_loop_normals[key][0]
                    best_dot = current_normal.dot(best_normal)

                    for stored_normal in original_loop_normals[key][1:]:
                        dot = current_normal.dot(stored_normal)
                        if dot > best_dot:
                            best_dot = dot
                            best_normal = stored_normal

                    normals_to_set.append(best_normal)
            else:
                # Fallback to current loop normal if not found
                normals_to_set.append(loop.normal)

    # Set custom normals
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set(normals_to_set)

    # Restore original mode and active object
    if original_active:
        context.view_layer.objects.active = original_active
        if original_active == obj:
            bpy.ops.object.mode_set(mode=original_mode)

    return True, f"Ripped {seam_count} edges on UV island boundaries", seam_count


class REPLICANT_OT_rip_mesh_uv_islands(bpy.types.Operator):
    """Rip mesh based on UV islands"""
    bl_idname = "replicant.rip_mesh_uv_islands"
    bl_label = "Rip Mesh by UV Islands"
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
        success, message, seam_count = rip_mesh_uv_islands(obj, context)

        # Report the result
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(REPLICANT_OT_rip_mesh_uv_islands)


def unregister():
    bpy.utils.unregister_class(REPLICANT_OT_rip_mesh_uv_islands)
