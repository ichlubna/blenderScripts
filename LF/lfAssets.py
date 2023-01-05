bl_info = {
    "name": "Light Field Asset Generator",
    "author": "ichlubna",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "3D View side panel",
    "description": "Generates a plane with material based on the input light field grid",
    "warning": "",
    "doc_url": "",
    "category": "Material"
}

import bpy
import os

class LFPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "LFGenerator"
    bl_label = "Takes input LF grid and creates plane with LF material"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene, "LFInput")
        col.operator("lf.generate", text="Generate")

class LFGenerator(bpy.types.Operator):
    """Generates the LF asset"""
    bl_idname = "lf.generate"
    bl_label = "Generate"

    def invoke(self, context, event):
        return {"FINISHED"}

def register():
    bpy.utils.register_class(LFGenerator)
    bpy.utils.register_class(LFPanel)
    bpy.types.Scene.LFInput = bpy.props.StringProperty(name="Input path", subtype="FILE_PATH", description="The path to the input views in format cols_rows.ext", default="")
    
    
def unregister():
    bpy.utils.unregister_class(LFGenerator)
    bpy.utils.unregister_class(LFPanel)
    
if __name__ == "__main__" :
    register()        