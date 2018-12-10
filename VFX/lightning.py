import bpy
import random
import math

class LightningGen (bpy.types.NodeCustomGroup):

    bl_name='LightningGen'
    bl_label='Lightning'
    imageName = 'Lightning' 

    def drawBolt (self, bitmap, x0, y0, x1, y1, w, h):
        def drawLine(start, end):
            def setPixel(x,y):
                offset = (x + int(y*w))*4
                for i in range(4):
                    bitmap[offset+i] = 1.0
            def drawPoint(x,y):
                setPixel(x, y)
                setPixel(x+1, y)
                setPixel(x-1, y)
                setPixel(x, y+1)
                setPixel(x, y-1)

            #Bressenham
            dx = abs(end[0] - start[0])
            dy = abs(end[1] - start[1])
            x, y = start[0], start[1]
            sx = -1 if start[0] > end[0] else 1
            sy = -1 if start[1] > end[1] else 1
            if dx > dy:
                err = dx / 2.0
                while x != end[0]:
                    drawPoint(x, y)
                    err -= dy
                    if err < 0:
                        y += sy
                        err += dx
                    x += sx
            else:
                err = dy / 2.0
                while y != end[1]:
                    drawPoint(x, y)

                    err -= dx
                    if err < 0:
                        x += sx
                        err += dy
                    y += sy        
            drawPoint(x, y)

        lines = [((x0,y0), (x1,y1))]
        #random.seed(self.seed)
        randRange = int(self.stability*200)
        for i in range(0,self.complexity):
            tempLines = lines
            lines = []
            for line in tempLines:
                start = line[0]
                end = line[1]
                
                #for better results maybe move new points by normal
                randOffset = ( random.randint(-randRange, randRange), random.randint(-randRange, randRange) )
                midpoint = ( int((start[0]+end[0])/2) + randOffset[0], int((start[1]+end[1])/2) + randOffset[1] )
                if random.uniform(0.0, 1.0) < self.forking:
                    forkEnd  = (end[0]+randOffset[1],end[1]+randOffset[0])
                    lines.append((midpoint, forkEnd))
                
                lines.append((start, midpoint))
                lines.append((midpoint, end))
            randRange = int(randRange/2)
        for line in lines:
            drawLine(line[0], line[1])
        
    def update_effect(self, context):
        #TODO update compositor tree
        #TODO different names
        scene = bpy.context.scene
        img = bpy.data.images[self.imageName]
        pixels =  [0.0,0.0,0.0,1.0]*(img.size[0]*img.size[1])
        #img.user_clear()
        #bpy.data.images.remove(img)
        #img = bpy.data.images.new(name=self.imageName, width=scene.render.resolution_x, height=scene.render.resolution_y)
        self.drawBolt(pixels, 500,500,1400,500, img.size[0], img.size[1])
        img.pixels[:] = pixels    
        img.update()  
        #to force backdrop update, dunno how to do it correctly :D              
        self.inputs['Start X'].default_value = self.inputs['Start X'].default_value
        #bpy.context.scene.nodes.node_tree.update()

        #resultNode = self.node_tree.nodes.new("CompositorNodeImage")
        #resultNode.label = 'resultImageNode'
        #outNode = bpy.context.scene.node_tree.nodes.new("CompositorNodeImage")
        #resultNode.image = bpy.data.images[self.imageName]
        #print(self.node_tree.nodes.keys())
        #self.outputs['Image'].default_value = resultNode.outputs[0].default_value
        return
    
    forking=bpy.props.FloatProperty(name="Forking", description="The probability of forking", min=0.0, max=1.0, default=0.0, update=update_effect)
    complexity=bpy.props.IntProperty(name="Complexity", description="Number of recursive segments (curves of the bolt)", min=0, max=15, default=0, update=update_effect)
    stability=bpy.props.FloatProperty(name="Stability", description="How much does the bolt wiggle", min=0.0, max=1.0, default=0.0, update=update_effect)
    falloff=bpy.props.FloatProperty(name="Falloff", description="Making the bolt thin at the end", min=0.0, max=1.0, default=0.0, update=update_effect, unit='LENGTH')
    glow=bpy.props.FloatProperty(name="Glow", description="The amount of glow/light emitted by the core", min=0.0, max=1.0, default=0.0, update=update_effect,)
    seed=bpy.props.IntProperty(name="Seed", description="Random seed affecting the shape of the bolt", min=0, default=0, update=update_effect)
    
    def init(self, context):
        scene = bpy.context.scene
        bpy.data.images.new(name=self.imageName, width=scene.render.resolution_x, height=scene.render.resolution_y)

        self.node_tree=bpy.data.node_groups.new(self.bl_name, 'CompositorNodeTree')
        inputs = self.node_tree.nodes.new('NodeGroupInput')
        outputs = self.node_tree.nodes.new('NodeGroupOutput') 
        self.node_tree.inputs.new("NodeSocketColor", "Glow color")
        self.node_tree.inputs.new("NodeSocketFloat", "Start X")
        self.node_tree.inputs.new("NodeSocketFloat", "Start Y")
        self.node_tree.inputs.new("NodeSocketFloat", "End X")
        self.node_tree.inputs.new("NodeSocketFloat", "End y")
        self.node_tree.outputs.new("NodeSocketColor", "Image")
        
    def draw_buttons(self, context, layout):
        row=layout.row()
        row.label("Image: "+self.imageName)
        row=layout.row()
        row.prop(self, 'forking',  text='Forking', slider=1)
        row=layout.row()
        row.prop(self, 'complexity',  text='Complexity', slider=1)
        row=layout.row()
        row.prop(self, 'stability', text='Stability', slider=1)
        row=layout.row()
        row.prop(self, 'falloff', text='Falloff', slider=1)
        row=layout.row()
        row.prop(self, 'glow', text='Glow', slider=1)
        row=layout.row()
        row.prop(self, 'seed', text='Seed')


    def copy(self, node):
        '''
        self.node_tree=node.node_tree.copy()
        '''
        return

    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)
        #bpy.context.scene.node_tree.nodes.remove(self.group, do_unlink=True)
        img = bpy.data.images[self.imageName]
        img.user_clear()
        bpy.data.images.remove(img)


from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories
from nodeitems_builtins import CompositorNodeCategory

def register():
    bpy.utils.register_class(LightningGen)
    newcatlist = [CompositorNodeCategory("CP_GENERATE", "Generate", items=[NodeItem("LightningGen"),]),]
    register_node_categories("GENERATE_NODES", newcatlist)

def unregister():
    unregister_node_categories("GENERATE_NODES")
    bpy.utils.unregister_class(LightningGen)

try :
    unregister()
except:
    pass
register() 