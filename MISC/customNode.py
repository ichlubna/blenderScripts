import bpy
from bl_ui import node_add_menu
import tempfile
import string
import random
import os

class RenderImage(bpy.types.Operator):
    """ Renders the scene, stores it in a file, loads the file back in Blender.
    """
    bl_idname = "mesh.render"
    bl_label = "Render Image"
    percentage : bpy.props.IntProperty(default=100)
    fileName : bpy.props.StringProperty(default="")

    def invoke(self, context, event):
        renderInfo = context.scene.render
        backupPath = renderInfo.filepath[:]
        backupFormat = renderInfo.image_settings.file_format
        backupPercent = renderInfo.resolution_percentage  
            
        with tempfile.TemporaryDirectory() as temp:
            file = os.path.join(temp, self.fileName)
            renderInfo.image_settings.file_format = "PNG"
            renderInfo.resolution_percentage = self.percentage
            renderInfo.filepath = file
            bpy.ops.render.render(write_still=True)
            
            image = bpy.data.images.get(self.fileName, None)
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
    
    percentage : bpy.props.IntProperty(name="Image size",
                                     description="Percentage of the render size",
                                     min=1, default=100,
                                     update=update_effect)
    fileName : bpy.props.StringProperty(name="Name of the image",
                                     description="This image is used to store the render",
                                     default="")
                                     
    def init(self, context):
        self.node_tree = bpy.data.node_groups.new(self.bl_name, 'ShaderNodeTree')
        inputColor = self.node_tree.interface.new_socket(name="Color", description="Color input", in_out='INPUT', socket_type='NodeSocketColor')
        outputColor = self.node_tree.interface.new_socket(name="Color", description="Color output", in_out='OUTPUT', socket_type='NodeSocketColor')
    
        inNode = self.node_tree.nodes.new(type='NodeGroupInput')
        outNode = self.node_tree.nodes.new(type='NodeGroupOutput')

        imageNode = self.node_tree.nodes.new("ShaderNodeTexImage")
        self.fileName = str((''.join(random.choices(string.ascii_letters, k=5))) + ".png")
        imageNode.name = 'resultImageNode'
        for image in bpy.data.images:
            if image.name == self.fileName:
                bpy.data.images.remove(image)
        textureImage = bpy.data.images.new(self.fileName, 0, 0)
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
        op.fileName = self.fileName

    def copy(self, node):
        self.init(bpy.context)
        return

    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)
        return

class NODE_MT_category_shader_test(bpy.types.Menu):
    bl_idname = "NODE_MT_category_shader_test"
    bl_label = "Test"

    def draw(self, context):
        layout = self.layout
        node_add_menu.add_node_type(layout, "TestNode")
        node_add_menu.draw_assets_for_catalog(layout, self.bl_label)

def testNodeDrawInNew(self, context):
    layout = self.layout
    layout.menu("NODE_MT_category_shader_test")

def extendDraw(fn):
     def newDraw(self, context):
         fn(self, context)
         node_add_menu.add_node_type(self.layout, "TestNode")
     return newDraw

def extendExistingCategory():
    category = bpy.types.NODE_MT_category_shader_output
    category.draw = extendDraw(category.draw)

def register():
    bpy.utils.register_class(NODE_MT_category_shader_test)
    bpy.types.NODE_MT_shader_node_add_all.append(testNodeDrawInNew)
    #extendExistingCategory()
    bpy.utils.register_class(RenderImage)
    bpy.utils.register_class(TestNode)


def unregister():
    bpy.types.NODE_MT_shader_node_add_all.remove(testNodeDrawInNew)
    bpy.utils.unregister_class(NODE_MT_category_shader_test)
    bpy.utils.unregister_class(TestNode)
    bpy.utils.unregister_class(RenderImage)

try:
    unregister()
except:
    pass
register()