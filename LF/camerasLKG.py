import bpy
import bmesh
import mathutils
import math
import os

class LFPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "LKG"
    bl_label = "Generate LKG array"

    def draw(self, context):
        col = self.layout.column(align=True)
        if context.scene.lfType == "plane":  
            col.prop(context.scene, "lfAspect")
        col.prop(context.scene, "lfNumber")
        col.prop(context.scene, "lfBaseline")
        col.prop(context.scene, "lfLens")
        col.prop(context.scene, "lfPosition")
        col.operator("mesh.generate", text="Generate")
        col.operator("mesh.select", text="Select")
        col.operator("mesh.render", text="Render")

class LFArray(bpy.types.Operator):
    """ Generates the camera grid with given parameters.
    """
    bl_idname = "mesh.generate"
    bl_label = "Generate LF array"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        lookAtCenter = False
        y=context.scene.lfPosition[1]
        
        position = context.scene.lfPosition
        for i in range(context.scene.lfNumber):
            position[1] += (context.scene.lfNumber/2.0 - i)*context.scene.lfBaseline
            bpy.ops.object.camera_add(location=position, rotation=(1.57,0,1.57))  
            camera = context.object
            camera.name = "LKG"+str(i)
            camera.data.lens = context.scene.lfLens
            position[1] = y
        
        context.scene.lfPosition[1]=y
            
        return {"FINISHED"}

class LFSelect(bpy.types.Operator):
    """ Generates the camera grid with given parameters.
    """
    bl_idname = "mesh.select"
    bl_label = "Select LF array"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        objects = bpy.context.scene.objects
        for obj in objects:
            obj.select_set(obj.name[:3] == "LKG")       
        return {"FINISHED"}

class LFRender(bpy.types.Operator):
    """ Renders whole animation (start-end frame), all frames for one cam in one folder.
        Takes format settings from Render options.
    """
    bl_idname = "mesh.render"
    bl_label = "Render LF"
    bl_descripiton = "Render all views to the output folder"
    #TODO render depthmaps button

    def invoke(self, context, event):
        renderInfo = bpy.data.scenes["Scene"].render
        path = renderInfo.filepath[:]
        camCount = 0
        for obj in bpy.context.scene.objects:
            if obj.name[:3] == "LKG":
                camCount += 1
                bpy.context.scene.camera = obj
                renderInfo.filepath = path+"/"+obj.name[3:]
                bpy.ops.render.render( write_still=True ) 
        renderInfo.filepath = path    
        bpy.data.scenes["Scene"].render.filepath = path

        infoFile = open(path+"/info", "w")
        infoFile.write("Camera count: " + str(camCount))
        infoFile.write("\nFPS: " + str(renderInfo.fps))
        infoFile.write("\nFrame count: " + str(bpy.context.scene.frame_end - bpy.context.scene.frame_start))
        infoFile.write("\nWidth: " + str(int((renderInfo.resolution_x * renderInfo.resolution_percentage)/100)))
        infoFile.write("\nHeight: " + str(int((renderInfo.resolution_y * renderInfo.resolution_percentage)/100)))
        #TODO camparams
        infoFile.close()
        
        
        return {"FINISHED"}

def register():
    bpy.utils.register_class(LFArray)
    bpy.utils.register_class(LFRender)
    bpy.utils.register_class(LFSelect)
    bpy.utils.register_class(LFPanel)
    bpy.types.Scene.lfBaseline = bpy.props.FloatProperty(name="Baseline", description="Distance between two cameras", default=1.0)
    bpy.types.Scene.lfLens = bpy.props.FloatProperty(name="Lens", description="Camera lens value", default=50.0)
    bpy.types.Scene.lfNumber = bpy.props.IntProperty(name="Number", description="Number of cameras", default=8)
    bpy.types.Scene.lfPosition = bpy.props.FloatVectorProperty(name="Position", description="Coordinates of the first camera", default=(0,0,0))
    
def unregister():
    bpy.utils.unregister_class(LFArray)
    bpy.utils.unregister_class(LFRender)
    bpy.utils.unregister_class(LFSelect)
    bpy.utils.unregister_class(LFPanel)
    del bpy.types.Scene.lfType 
    
if __name__ == "__main__" :
    register()
