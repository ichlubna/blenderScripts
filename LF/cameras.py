import bpy
import bmesh
import mathutils
import math
import os

class LFPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Create"
    bl_label = "Generate lightfield array"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene, "lfType")
        col.prop(context.scene, "lfSize")
        col.prop(context.scene, "lfDensity")
        col.operator("mesh.generate", text="Generate")
        col.operator("mesh.render", text="Render")

class LFArray(bpy.types.Operator):
    bl_idname = "mesh.generate"
    bl_label = "Generate LF array"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        bm = bmesh.new()
        mesh = bpy.data.meshes.new('Basic_Cube')
        lookAtCenter = False
  
        if context.scene.lfType == "plane":   
            bmesh.ops.create_grid(bm, x_segments= context.scene.lfDensity, y_segments=context.scene.lfDensity, size=context.scene.lfSize)
        elif context.scene.lfType == "sphere":
            bmesh.ops.create_icosphere(bm, subdivisions=context.scene.lfDensity, diameter=context.scene.lfSize)
            lookAtCenter = True
        
        bm.to_mesh(mesh)
        for v in mesh.vertices:
            direction = -v.co
            rotation = (0,0,0)
            if lookAtCenter:
                rotation = direction.to_track_quat('-Z', 'Y').to_euler()
            bpy.ops.object.camera_add(view_align=False,
                          location=v.co,
                          rotation=rotation)  
            camera = context.object
            camera.name = "LF_Cam_"+str(v.index)
            
        objects = bpy.context.scene.objects
        for obj in objects:
            obj.select = obj.name[:6] == "LF_Cam"
            
        return {"FINISHED"}

class LFRender(bpy.types.Operator):
    bl_idname = "mesh.render"
    bl_label = "Render LF"
    #bl_descripiton = "Render all views to the output folder"

    def invoke(self, context, event):
        path = bpy.data.scenes["Scene"].render.filepath[:]
        for obj in bpy.context.scene.objects:
            if obj.name[:6] == "LF_Cam":
                bpy.context.scene.camera = obj
                bpy.data.scenes["Scene"].render.filepath = path+ obj.name[7:]
                bpy.ops.render.render( write_still=True ) 
            
        bpy.data.scenes["Scene"].render.filepath = path
        return {"FINISHED"}

def register():
    bpy.utils.register_class(LFArray)
    bpy.utils.register_class(LFRender)
    bpy.utils.register_class(LFPanel)
    bpy.types.Scene.lfType = bpy.props.EnumProperty(name="Type", description="Shape of the LF camera array", items=[("plane","Plane","Planar grid"), ("sphere","Sphere","Spherical grid (icosphere)")])
    bpy.types.Scene.lfSize = bpy.props.FloatProperty(name="Size", description="Scale of the array", default=1.0)
    bpy.types.Scene.lfDensity = bpy.props.IntProperty(name="Density", description="Density of the array", default=8)
    
def unregister():
    bpy.utils.unregister_class(LFArray)
    bpy.utils.unregister_class(LFRender)
    bpy.utils.unregister_class(LFPanel)
    del bpy.types.Scene.lfType 
    
if __name__ == "__main__" :
    register()
