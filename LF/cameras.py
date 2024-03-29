import bpy
import bmesh
import mathutils
import math
import os

class LFPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "Lightfield"
    bl_label = "Generate lightfield array"

    def draw(self, context):
        col = self.layout.column(align=True)
        if context.scene.lfType == "plane":  
            col.prop(context.scene, "lfAspect")
        col.prop(context.scene, "lfType")
        col.prop(context.scene, "lfSize")
        col.prop(context.scene, "lfDensity")
        col.prop(context.scene, "lfDepth")
        col.operator("mesh.generate", text="Generate")
        col.operator("mesh.render", text="Render")

class LFArray(bpy.types.Operator):
    """ Generates the camera grid with given parameters.
    """
    bl_idname = "mesh.generate"
    bl_label = "Generate LF array"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        bm = bmesh.new()
        mesh = bpy.data.meshes.new('Basic_Cube')
        lookAtCenter = False
  
        if context.scene.lfType == "row":
            position = [0,0,0]
            baseline = context.scene.lfSize/context.scene.lfDensity
            for i in range(context.scene.lfDensity):
                position = [0,0,0]
                position[1] = (context.scene.lfDensity/2.0 - i)*baseline
                bpy.ops.object.camera_add(location=position, rotation=(1.57,0,1.57))  
                camera = context.object
                camera.name = "LF_Cam_"+str(i)
        
        else:
            if context.scene.lfType == "plane":   
                ratio = 1.0
                if context.scene.lfAspect == "16:9":
                    ratio = 16.0/9
                elif context.scene.lfAspect == "4:3":
                    ratio = 4.0/3.0
                mat = mathutils.Matrix.Scale(ratio, 4, (1.0, 0.0, 0.0)) @ mathutils.Matrix.Rotation(math.radians(180), 4, 'X') #rotation to place the first cam to top left corner
                bmesh.ops.create_grid(bm, x_segments= context.scene.lfDensity, y_segments=context.scene.lfDensity, size=context.scene.lfSize, matrix=mat),
            elif context.scene.lfType == "sphere":
                bmesh.ops.create_icosphere(bm, subdivisions=context.scene.lfDensity, radius=context.scene.lfSize)
                lookAtCenter = True
            
            bm.to_mesh(mesh)
            for v in mesh.vertices:
                direction = -v.co
                rotation = (0,0,0)
                if lookAtCenter:
                    rotation = direction.to_track_quat('-Z', 'Y').to_euler()
                bpy.ops.object.camera_add(location=v.co, rotation=rotation)  
                camera = context.object
                camera.name = "LF_Cam_"+str(v.index)       
            
        objects = bpy.context.scene.objects
        for obj in objects:
            obj.select_set(obj.name[:6] == "LF_Cam")
            
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
            if obj.name[:6] == "LF_Cam":
                camCount += 1
                bpy.context.scene.camera = obj
                camPath = path+"/"+obj.name[7:]
                if not os.path.exists(camPath):
                    os.makedirs(camPath)
                #context.window_manager.progress_begin(0,context.scene.lfS)
                for i in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end+1):
                    renderInfo.filepath = camPath+"/"+str(bpy.context.scene.frame_start-i)
                    bpy.context.scene.frame_set(i)
                    bpy.ops.render.render( write_still=True ) 
            
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
    bpy.utils.register_class(LFPanel)
    bpy.types.Scene.lfType = bpy.props.EnumProperty(name="Type", description="Shape of the LF camera array", items=[("row","Row","Horizontal line"), ("plane","Plane","Planar grid"), ("sphere","Sphere","Spherical grid (icosphere)")])
    bpy.types.Scene.lfAspect = bpy.props.EnumProperty(name="Aspect", description="Aspect ratio for the camera grid", items=[("16:9", "16:9", ""), ("4:3", "4:3", ""), ("1:1", "1:1", "")])
    bpy.types.Scene.lfSize = bpy.props.FloatProperty(name="Size", description="Scale of the array", default=1.0)
    bpy.types.Scene.lfDensity = bpy.props.IntProperty(name="Density", description="Density of the array", default=8)
    bpy.types.Scene.lfDepth = bpy.props.BoolProperty(name="Depth maps", description="Will render depth maps too", default=True)
    
def unregister():
    bpy.utils.unregister_class(LFArray)
    bpy.utils.unregister_class(LFRender)
    bpy.utils.unregister_class(LFPanel)
    del bpy.types.Scene.lfType 
    
if __name__ == "__main__" :
    register()
