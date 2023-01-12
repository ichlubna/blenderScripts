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
import mathutils
import math
from pathlib import Path

class LFReader:
    cols = 0
    rows = 0
    files = []
    path = ""

    def loadDir(self, path):
        self.path = path
        files = sorted(os.listdir(path))
        length = Path(files[-1]).stem.split("_")
        if len(length) == 1:
            self.cols = len(files)
            self.rows = 1
        else:
            self.cols = int(length[1])+1
            self.rows = int(length[0])+1
        self.files = [files[i:i+self.cols] for i in range(0, len(files), self.cols)]

    def getColsRows(self):
        return [self.cols, self.rows]

    def getImagePath(self, row, column):
        filePath = os.path.join(self.path, self.files[row][column]
        return filePath

class LFPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "LFGenerator"
    bl_label = "Takes input LF grid and creates plane with LF material"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene, "LFInput")
        col.prop(context.scene, "LFOverrideCoords")
        if(context.scene.LFOverrideCoords):
            col.prop(context.scene, "LFViewCoords")
        col.operator("lf.generate", text="Generate")

class LFGenerator(bpy.types.Operator):
    """Generates the LF asset"""
    bl_idname = "lf.generate"
    bl_label = "Generate"
    
    def cameraView(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
    
    def createMaterial(self, context):
        LFReader lf
        #lf.loadDir(context.scene.LFInput)
    
    def createPlane(self, context):
        camera = context.scene.camera
        direction = camera.matrix_world.to_quaternion() @ mathutils.Vector((0.0, 0.0, -1.0))
        direction = direction.normalized()
        position = camera.location+direction
        xSize = 2*math.tan(camera.data.angle_x*0.5)
        renderInfo = bpy.context.scene.render
        aspectRatio = renderInfo.resolution_y / renderInfo.resolution_x
        bpy.ops.mesh.primitive_plane_add(size=(xSize), location=position, rotation=camera.rotation_euler)
        context.object.dimensions[1] = xSize*aspectRatio
        self.createMaterial(context)

    def invoke(self, context, event):
        self.cameraView(context)
        self.createPlane(context)
        return {"FINISHED"}

def register():
    bpy.utils.register_class(LFGenerator)
    bpy.utils.register_class(LFPanel)
    bpy.types.Scene.LFInput = bpy.props.StringProperty(name="Input", subtype="FILE_PATH", description="The path to the input views in format cols_rows.ext", default="")
    bpy.types.Scene.LFOverrideCoords = bpy.props.BoolProperty(name="Override view", description="Disables view-dependent changes and sets static coordinates for LF", default=False)
    bpy.types.Scene.LFViewCoords = bpy.props.FloatVectorProperty(name="View coordinates", size=2, description="Normalized view coordinates", default=(0.5,0.5), min=0, max=1)
       
def unregister():
    bpy.utils.unregister_class(LFGenerator)
    bpy.utils.unregister_class(LFPanel)
    
if __name__ == "__main__" :
    register()        