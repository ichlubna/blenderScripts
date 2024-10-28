import bpy
import tempfile
import os

class RenderImage(bpy.types.Operator):
    """ Renders the scene, stores it in a file, loads the file back in Blender.
    """
    bl_idname = "mesh.render"
    bl_label = "Render Image"
    percentage = bpy.props.IntProperty(default=100)

    def invoke(self, context, event):
        renderInfo = context.scene.render
        backupPath = renderInfo.filepath[:]
        backupFormat = renderInfo.image_settings.file_format
        backupPercent = renderInfo.resolution_percentage  
            
        with tempfile.TemporaryDirectory() as temp:
            file = os.path.join(temp, "TestImage.png")
            renderInfo.image_settings.file_format = "PNG"
            renderInfo.resolution_percentage = context.scene.resolutionPercent
            renderInfo.filepath = file
            bpy.ops.render.render(write_still=True)
            
            image = bpy.data.images.get("TestImage", None)
            image.source = 'FILE'
            image.filepath = file
            image.reload()
            image.update()
             
        renderInfo.filepath = backupPath[:]   
        renderInfo.image_settings.file_format = backupFormat  
        renderInfo.resolution_percentage = backupPercent
        return {"FINISHED"}

class TestNode (bpy.types.ShaderNodeCustomGroup):
    """ This is a new material node that uses the RenderImage operator, renders the scene and uses the rendered image as a texture which can be colorized by the input color.
    """
    bl_name = 'TestNode'
    bl_label = 'TestNode'

    def update_effect(self, context):
        if (bpy.context.scene.use_nodes == False):
            return
        mixNode = self.node_tree.nodes.get("mixNode")
        mixNode.inputs[0].default_value = self.colorStrength
        mixNode.update()
        return
    
    percentage: bpy.props.IntProperty(name="Image size",
                                     description="Percentage of the render size",
                                     min=1, default=100,
                                     update=update_effect)
                                     
    def init(self, context):
        self.node_tree = bpy.data.node_groups.new(self.bl_name, 'ShaderNodeTree')
        inputColor = self.node_tree.interface.new_socket(name="Color", description="Color input", in_out='INPUT', socket_type='NodeSocketColor')
        outputColor = self.node_tree.interface.new_socket(name="Color", description="Color output", in_out='OUTPUT', socket_type='NodeSocketColor')
    
        inNode = self.node_tree.nodes.new(type='NodeGroupInput')
        outNode = self.node_tree.nodes.new(type='NodeGroupOutput')

        imageNode = self.node_tree.nodes.new("ShaderNodeTexImage")
        imageNode.name = 'resultImageNode'
        for image in bpy.data.images:
            if image.name == "TestImage":
                bpy.data.images.remove(image)
        textureImage = bpy.data.images.new("TestImage", 0, 0)
        imageNode.image = textureImage

        mixNode = self.node_tree.nodes.new("ShaderNodeMixRGB")
        mixNode.name = 'mixNode'
        mixNode.blend_type = 'COLOR'

        self.node_tree.links.new(imageNode.outputs[0], mixNode.inputs[1])
        self.node_tree.links.new(inNode.outputs[0], mixNode.inputs[2])
        self.node_tree.links.new(mixNode.outputs[0], outNode.inputs[0])
        return

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)   
        textureImage = bpy.data.images.get("TestImage", None)    
        col.prop(self, "percentage")
        op = col.operator("mesh.render", text="Render")
        op.percentage = self.percentage

    def copy(self, node):
        self.init(bpy.context)
        return

    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)
        return

def register():
    bpy.utils.register_class(RenderImage)
    bpy.utils.register_class(TestNode)


def unregister():
    bpy.utils.unregister_class(TestNode)
    bpy.utils.unregister_class(RenderImage)

try:
    unregister()
except:
    pass
register()

bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.selected_objects[0]
mat = bpy.data.materials.new(name="Material")
cube.data.materials.append(mat)
mat.use_nodes = True
nodes = mat.node_tree.nodes
node = nodes.new('TestNode')