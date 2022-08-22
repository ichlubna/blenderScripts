import bpy
import tempfile
import shlex
import shutil
import subprocess


bl_info = {
    "name": "External FFmpeg interop",
    "description":
        "Allows to export the animation with external FFmpeg and all available formats.",
    "author": "ichlubna",
    "version": (1, 0),
    "blender": (3, 1, 0),
    "location": "3D View side panel",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/My_Script",
    "tracker_url":
        "https://github.com/ichlubna/blenderScripts",
    "support": "COMMUNITY",
    "category": "Import-Export"
}

class FFPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "FFExport"
    bl_label = "Exports the animation using full external FFmpeg"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene, "ffPath")
        col.prop(context.scene, "ffOutput")
        col.prop(context.scene, "ffParams")
        col.prop(context.scene, "ffImages")
        if context.scene.ffImages:  
            col.prop(context.scene, "ffImagesPath")
            col.prop(context.scene, "ffImagesRender")
        col.operator("ffexport.render", text="Render")
        col.prop(context.scene, "ffExamples")

class FFRender(bpy.types.Operator):
    """ Renders the animation using FFmpeg
    """
    bl_idname = "ffexport.render"
    bl_label = "Render animation"

    def getFPSStr(self):
        return str(round(bpy.context.scene.render.fps / bpy.context.scene.render.fps_base,2))

    def encodeRender(self, context, renderInfo, tempDir, pipe):
        renderInfo.filepath = tempDir+"/frame.png"
        renderInfo.image_settings.file_format = 'PNG'
        for i in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end+1):
            bpy.context.scene.frame_set(i)
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            if context.scene.ffImages: 
                renderInfo.filepath = context.scene.ffImagesPath+"/"+f'{i:05d}'+".png"
            bpy.ops.render.render( write_still=True ) 
            with open(renderInfo.filepath, 'rb') as f:
                data = f.read()
                pipe.stdin.write(data)
    
    def bulkEncodeFrames(self, context):
        print(self.getFPSStr())
        renderInfo = bpy.context.scene.render
        cmd = ['ffmpeg', '-y', '-r', str(renderInfo.fps), '-start_number',
            str(bpy.context.scene.frame_start),
            '-i', context.scene.ffImagesPath+'/%05d.png', '-r', self.getFPSStr()] + \
            shlex.split(context.scene.ffParams) + [context.scene.ffOutput]     
        pipe = subprocess.Popen(cmd)
        pipe.wait()

    def encodeScene(self, context):
        renderInfo = bpy.context.scene.render
        tempDir = tempfile.mkdtemp()
        
        cmd = ['ffmpeg', '-y', '-f', 'image2pipe', '-c:v', 'png', '-r', self.getFPSStr(), '-i', '-'] + \
        shlex.split(context.scene.ffParams) + [context.scene.ffOutput]     
        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        
        self.encodeRender(context, renderInfo, tempDir, pipe)
        
        pipe.stdin.close()
        pipe.wait()
        if pipe.returncode != 0:
            raise subprocess.CalledProcessError(pipe.returncode, cmd)
        shutil.rmtree(tempDir)

    def invoke(self, context, event):
        if context.scene.ffImagesRender:
            self.bulkEncodeFrames(context)
        else:
            self.encodeScene(context)      
        return {"FINISHED"}


def updateExample(self, context):
    print(context.scene.ffExamples)
    if context.scene.ffExamples == "none":
        context.scene.ffOutput = ""
        context.scene.ffParams = ""
    if context.scene.ffExamples == "h.265":
        context.scene.ffParams = "-c:v libx265 -crf 28 -pix_fmt yuv420p"
        context.scene.ffOutput = "example.mkv"
    if context.scene.ffExamples == "hevc_nvenc":
        context.scene.ffParams = "-c:v hevc_nvenc -crf 28"
        context.scene.ffOutput = "example.mkv"
    if context.scene.ffExamples == "AV1":
        context.scene.ffParams = "-c:v libaom-av1 -crf 28 -pix_fmt yuv420p -cpu-used 4"
        context.scene.ffOutput = "example.mkv"
    if context.scene.ffExamples == "gif":
        context.scene.ffParams = ""
        context.scene.ffOutput = "example.gif"

def register():
    bpy.utils.register_class(FFPanel)
    bpy.utils.register_class(FFRender)
    bpy.types.Scene.ffPath = bpy.props.StringProperty(name="FFmpeg path", subtype="FILE_PATH", description="The path to the ffmpeg binary", default="ffmpeg")
    bpy.types.Scene.ffOutput = bpy.props.StringProperty(name="Output file", subtype="FILE_PATH", description="The output file with extension", default="myFile.mkv")
    bpy.types.Scene.ffParams = bpy.props.StringProperty(name="FFmpeg params", description="The ffmpeg parameters", default="-c:v libx265 -crf 28")
    bpy.types.Scene.ffImages = bpy.props.BoolProperty(name="Store frames", description="Will store the frames as well", default=False)
    bpy.types.Scene.ffImagesRender = bpy.props.BoolProperty(name="Render frames", description="Will encode the stored frames without rendering", default=False)
    bpy.types.Scene.ffImagesPath = bpy.props.StringProperty(name="Images path", subtype="DIR_PATH", description="Path for the frames to store", default="./myFrames")
    bpy.types.Scene.ffExamples = bpy.props.EnumProperty(name="Examples", description="Sets the params to the selected example", items=[("none","none", ""), ("h.265","h.265", ""), ("hevc_nvenc","hevc_nvenc", ""), ("AV1","AV1", ""), ("gif", "gif", "")], update=updateExample)
    
def unregister():
    bpy.utils.unregister_class(FFPanel)
    bpy.utils.unregister_class(FFRender)
    
if __name__ == "__main__" :
    register()        
