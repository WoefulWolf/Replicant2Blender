import webbrowser
import bpy

class REPLICANT_OT_open_url(bpy.types.Operator):
    bl_idname = "replicant.open_url"
    bl_label = "Open URL"
    
    url: bpy.props.StringProperty()

    def execute(self, context):
        webbrowser.open(self.url)
        self.report({'INFO'}, f"Opening: {self.url}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(REPLICANT_OT_open_url)


def unregister():
    bpy.utils.unregister_class(REPLICANT_OT_open_url)