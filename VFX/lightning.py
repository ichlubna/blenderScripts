import bpy
import random
import math

class LightningGen (bpy.types.CompositorNodeCustomGroup):

    bl_name='LightningGen'
    bl_label='Lightning'
    
    def drawBolt (self, bitmap, coord, w, h):
        
        def drawLine(start, end, thickness):
        
            def setPixel(x,y):
                if (0 <= x < w) and (0 <= y < h):
                    offset = (x + int(y*w))*4
                    for i in range(4):
                        try:
                            bitmap[offset+i] = 1.0
                        except:
                            {}
                        
            def drawPoint(x,y,radius):
                for X in range(-radius, radius+1):
                    for Y in range(-radius, radius+1):
                        if(X*X+Y*Y <= radius*radius):
                            setPixel(X+x, Y+y)

            #Bressenham
            dx = abs(end[0] - start[0])
            dy = abs(end[1] - start[1])
            x, y = start[0], start[1]
            sx = -1 if start[0] > end[0] else 1
            sy = -1 if start[1] > end[1] else 1
            if dx > dy:
                err = dx / 2.0
                while x != end[0]:
                    drawPoint(x, y, thickness)
                    err -= dy
                    if err < 0:
                        y += sy
                        err += dx
                    x += sx
            else:
                err = dy / 2.0
                while y != end[1]:
                    drawPoint(x, y, thickness)

                    err -= dx
                    if err < 0:
                        x += sx
                        err += dy
                    y += sy        
            drawPoint(x, y, thickness)


        #TODO add spatially consistent random generator like perlin noise so that moving the bolt doesn't change shape rapidly
        lines = [((coord[0],coord[1]), (coord[2],coord[3]), self.thickness)]
        length = int(math.sqrt(pow(coord[2]-coord[0],2)+pow(coord[3]-coord[1],2)))
        random.seed(self.seed)
        randRange = int((1.0-self.stability)*int(length/4))
        for i in range(0,self.complexity):
            tempLines = lines.copy()
            lines = []
            for line in tempLines:
                start = line[0]
                end = line[1]
                randOffset = ( random.randint(-randRange, randRange), random.randint(-randRange, randRange) )
                midpoint = ( int((start[0]+end[0])/2) + randOffset[0], int((start[1]+end[1])/2) + randOffset[1] )
                if random.uniform(0.0, 1.0) < self.forking and i < int(self.complexity/3):
                    direction = (midpoint[0]-start[0], midpoint[1]-start[1])
                    angle = random.uniform(0.0,0.9)
                    if random.uniform(0.0, 1.0) > 0.5:
                        angle = -angle
                    cosVal = math.cos(angle)
                    sinVal = math.sin(angle)
                    forkEnd = (int(cosVal*direction[0] - sinVal*direction[1])+midpoint[0], int(sinVal*direction[0] + cosVal*direction[1])+midpoint[1])
                    lines.append((midpoint, forkEnd, int(line[2]/2)))
                
                lines.append((start, midpoint, line[2]))
                lines.append((midpoint, end, line[2]))
            randRange = int(randRange/2)
        for line in lines:
            drawLine(line[0], line[1], line[2])
        
    def update_effect(self, context):
        scene = bpy.context.scene
        img = bpy.data.images[self.name]
        pixels = [0.0,0.0,0.0,1.0]*(img.size[0]*img.size[1])
        
        boltCoordinates=[0,0,0,0]
        inputs=['Start X', 'Start Y', 'End X', 'End Y']
        for i in range(len(inputs)):
            boltCoordinates[i]=self.inputs[inputs[i]].default_value
            if len(self.inputs[inputs[i]].links) != 0:
                inputNode = self.inputs[inputs[i]].links[0].from_node
                if isinstance(inputNode, bpy.types.CompositorNodeTrackPos):
                    markerPosition = inputNode.clip.tracking.tracks[inputNode.track_name].markers[0].co
                    xy = 1
                    if i%2 == 0:
                        xy = 0
                    boltCoordinates[i] = int(markerPosition[xy]*inputNode.clip.size[xy])
                else:
                    bpy.context.scene.node_tree.links.remove(self.inputs[inputs[i]].links[0])

        self.drawBolt(pixels, boltCoordinates, img.size[0], img.size[1])
        img.pixels[:] = pixels    
        img.update()  
        coreBlurNode = self.node_tree.nodes.get('coreBlurNode')
        coreBlurNode.size_x = self.coreBlur
        coreBlurNode.size_y = self.coreBlur
        glowBlurNode = self.node_tree.nodes.get('glowBlurNode')
        glowBlurNode.size_x = self.glow
        glowBlurNode.size_y = self.glow
        #to force backdrop update, dunno how to do it correctly :D              
        self.inputs['Start X'].default_value = self.inputs['Start X'].default_value
        #bpy.context.scene.nodes.node_tree.update()
        return
    
    forking: bpy.props.FloatProperty(name="Forking", description="The probability of forking", min=0.0, max=1.0, default=0.3, update=update_effect)
    complexity: bpy.props.IntProperty(name="Complexity", description="Number of recursive segments (curves of the bolt)", min=5, max=15, default=5, update=update_effect)
    stability: bpy.props.FloatProperty(name="Stability", description="How much does the bolt wiggle", min=0.0, max=1.0, default=0.5, update=update_effect)
    falloff: bpy.props.FloatProperty(name="Falloff", description="Making the bolt thin at the end", min=0.0, max=1.0, default=0.0, update=update_effect, unit='LENGTH')
    thickness: bpy.props.IntProperty(name="Thickness", description="Overall thickness of the bolt", min=0, max=100, default=3, update=update_effect)
    glow: bpy.props.IntProperty(name="Glow", description="The amount of glow/light emitted by the core", min=0, max=200, default=60, update=update_effect)
    coreBlur: bpy.props.IntProperty(name="Core blur", description="How sharp the core is", min=0, max=30, default=5, update=update_effect)
    seed: bpy.props.IntProperty(name="Seed", description="Random seed affecting the shape of the bolt", min=0, default=0, update=update_effect)
    
    def init(self, context):
        #WORKAROUND since socket update is not working
        def update(dummy):
            self.update_effect(bpy.context)
        bpy.app.handlers.depsgraph_update_pre.append(update)
        
        scene = bpy.context.scene
        bpy.data.images.new(name=self.name, width=scene.render.resolution_x, height=scene.render.resolution_y)

        self.node_tree=bpy.data.node_groups.new(self.bl_name, 'CompositorNodeTree')
        inputs = self.node_tree.nodes.new('NodeGroupInput')
        outputs = self.node_tree.nodes.new('NodeGroupOutput') 
        self.node_tree.inputs.new("NodeSocketColor", "Glow color")
        self.node_tree.inputs.new("NodeSocketInt", "Start X")
        self.node_tree.inputs.new("NodeSocketInt", "Start Y")
        self.node_tree.inputs.new("NodeSocketInt", "End X")
        self.node_tree.inputs.new("NodeSocketInt", "End Y")
        self.node_tree.outputs.new("NodeSocketColor", "Image")
        
        imageNode = self.node_tree.nodes.new("CompositorNodeImage")
        imageNode.name = 'resultImageNode'
        imageNode.image = bpy.data.images[self.name]
        
        coreBlurNode = self.node_tree.nodes.new("CompositorNodeBlur")
        coreBlurNode.name = 'coreBlurNode'
        coreBlurNode.filter_type = 'FAST_GAUSS'
       
        glowBlurNode = self.node_tree.nodes.new("CompositorNodeBlur")
        glowBlurNode.name = 'glowBlurNode'
        glowBlurNode.filter_type = 'FAST_GAUSS'
        
        mixNode = self.node_tree.nodes.new("CompositorNodeMixRGB")
        mixNode.name = 'mixNode'
        mixNode.blend_type = 'ADD'
        
        colorizeNode = self.node_tree.nodes.new("CompositorNodeMixRGB")
        colorizeNode.name = 'colorizeNode'
        colorizeNode.blend_type = 'MIX'
        colorizeNode.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
        colorizeNode.inputs[2].default_value = (0.0, 0.0, 1.0, 1.0)
           
        self.outputs['Image'].default_value = imageNode.outputs[0].default_value      
        self.node_tree.links.new(imageNode.outputs[0], coreBlurNode.inputs[0])
        self.node_tree.links.new(imageNode.outputs[0], glowBlurNode.inputs[0])
        self.node_tree.links.new(coreBlurNode.outputs[0], mixNode.inputs[1])
        self.node_tree.links.new(glowBlurNode.outputs[0], colorizeNode.inputs[0])
        self.node_tree.links.new(self.node_tree.nodes['Group Input'].outputs[0], colorizeNode.inputs[2])      
        self.node_tree.links.new(colorizeNode.outputs[0], mixNode.inputs[2])
        self.node_tree.links.new(mixNode.outputs[0],self.node_tree.nodes['Group Output'].inputs[0])
        
    def draw_buttons(self, context, layout):
        row=layout.row()
        row.prop(self, 'forking',  text='Forking', slider=1)
        row=layout.row()
        row.prop(self, 'complexity',  text='Complexity', slider=1)
        row=layout.row()
        row.prop(self, 'stability', text='Stability', slider=1)
        row=layout.row()
        row.prop(self, 'falloff', text='Falloff', slider=1)
        row=layout.row()
        row.prop(self, 'thickness', text='Thickness', slider=1)
        row=layout.row()
        row.prop(self, 'glow', text='Glow', slider=1)
        row=layout.row()
        row.prop(self, 'coreBlur', text='Core blur', slider=1)
        row=layout.row()
        row.prop(self, 'seed', text='Seed')


    def copy(self, node):
        '''
        TODO copy necessary structures especially allocate new Image for result
        self.node_tree=node.node_tree.copy()
        '''
        return

    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)
        #bpy.context.scene.node_tree.nodes.remove(self.group, do_unlink=True)
        img = bpy.data.images[self.name]
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
