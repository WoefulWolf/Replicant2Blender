import bpy

from ..util import log


def apply_modifiers(obj, context):
    """
    Apply all non-armature modifiers in stack order.

    Args:
        obj: The mesh object whose modifiers should be applied
        context: Blender context

    Returns:
        tuple: (success: bool, message: str, applied_count: int)
    """
    if not obj or obj.type != 'MESH':
        return False, "Object is not a mesh", 0

    if not any(m.type != 'ARMATURE' for m in obj.modifiers):
        return True, "No modifiers to apply", 0

    original_active = context.view_layer.objects.active
    original_mode = obj.mode if obj == original_active else 'OBJECT'

    context.view_layer.objects.active = obj
    if obj.mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass

    # Move every armature modifier to the bottom of the stack so it isn't in the
    # evaluation path of the modifiers we're about to apply.
    armature_names = [m.name for m in obj.modifiers if m.type == 'ARMATURE']
    for arm_name in armature_names:
        if obj.modifiers.find(arm_name) == len(obj.modifiers) - 1:
            continue
        try:
            bpy.ops.object.modifier_move_to_index(modifier=arm_name, index=len(obj.modifiers) - 1)
            log.d(f"  Moved armature modifier '{arm_name}' to bottom of stack")
        except RuntimeError as e:
            log.w(f"  Failed to move armature modifier '{arm_name}' to bottom: {e}")

    # Snapshot post-reorder. Applying mutates obj.modifiers, so we can't iterate it directly.
    modifier_names = [m.name for m in obj.modifiers if m.type != 'ARMATURE']

    applied_count = 0
    failed: list[str] = []
    for mod_name in modifier_names:
        mod = obj.modifiers.get(mod_name)
        if mod is None:
            continue
        mod_type = mod.type
        try:
            bpy.ops.object.modifier_apply(modifier=mod_name)
            log.d(f"  Applied modifier '{mod_name}' ({mod_type})")
            applied_count += 1
        except RuntimeError as e:
            log.w(f"  Failed to apply modifier '{mod_name}' ({mod_type}): {e}")
            failed.append(mod_name)

    if obj.mode != original_mode:
        try:
            bpy.ops.object.mode_set(mode=original_mode)
        except RuntimeError:
            pass

    if original_active:
        try:
            context.view_layer.objects.active = original_active
        except (ReferenceError, AttributeError):
            pass

    if failed:
        return False, f"Applied {applied_count} modifier(s), {len(failed)} failed: {', '.join(failed)}", applied_count
    return True, f"Applied {applied_count} modifier(s)", applied_count


class REPLICANT_OT_apply_modifiers(bpy.types.Operator):
    """Apply all non-armature modifiers on a mesh in stack order"""
    bl_idname = "replicant.apply_modifiers"
    bl_label = "Apply Modifiers"
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

        success, message, _ = apply_modifiers(obj, context)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, message)
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(REPLICANT_OT_apply_modifiers)


def unregister():
    bpy.utils.unregister_class(REPLICANT_OT_apply_modifiers)
