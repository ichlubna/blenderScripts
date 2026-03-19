import bpy
import random
import math
import gpu
import numpy as np
import mathutils
import bl_math
from gpu_extras.batch import batch_for_shader
import nodeitems_utils
from nodeitems_builtins import CompositorNodeCategory
from multiprocessing import Pool

import time


bl_info = {
    "name": "Compositor lightning generator node",
    "description":
        "Adds a new node in compositor that generates an electric lightning effect.",
    "author": "ichlubna",
    "version": (1, 0),
    "blender": (5, 0, 0),
    "location": "Compositing > Add > Input > Lightning",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/My_Script",
    "tracker_url":
        "https://github.com/ichlubna/blenderScripts/tree/master/VFX",
    "support": "COMMUNITY",
    "category": "Compositing"
}


class LightningGen (bpy.types.CompositorNodeCustomGroup):

    bl_name = 'LightningGen'
    bl_label = 'Lightning'        

    def generateBolt(self, p0, p1):
        # TODO add spatially consistent random generator so that moving the bolt doesn't change shape rapidly
        # https://docs.blender.org/api/current/mathutils.noise.html
        class Lines:
            class Segment:
                p0 = 0
                p1 = 0
                level = 0
                def __init__(self, a, b, l):
                    self.p0 = a
                    self.p1 = b
                    self.level = l
            maxLevel = 0
            segments = []
            vertices = []
            initP0 = []
            initP1 = []
            initDirection = []
            initLength = 0
            def __init__(self, p0, p1):
                self.initP0 = p0
                self.initP1 = p1
                self.initDirection = p1-p0
                self.initLength = np.linalg.norm(self.initDirection)
                self.addVertex(p0)
                self.addVertex(p1)
                self.addLine(0,1,0)  
            def removeSegment(self, i):
                del self.segments[i]
            def getCoords(self,s):
                return [(self.vertices[s.p0], self.vertices[s.p1])]
            def addLine(self, a, b, level):
                    if level > self.maxLevel:
                        self.maxLevel = level
                    self.segments.append(self.Segment(a, b, level))
            def addVertex(self, v):
                self.vertices.append(v)
                return len(self.vertices)-1
            def getMaxLevel(self):
                return self.maxLevel;
            def getInitPts(self):
                return (self.initP1, self.initP0)
            def getInitLength(self):
                return self.initLength
            def getInitDirection(self):
                return self.initDirection
        
        lines = Lines(p0,p1)     
        length = lines.getInitLength()
        random.seed(self.seed)
        randRange = int((1.0-self.stability)*int(length))
        for i in range(0, self.complexity):
            for si in range (0, len(lines.segments)):
                segment = lines.segments[si]
                pts = lines.getCoords(segment)[0]
                vector = pts[1]-pts[0]
                normal = np.array([vector[1], -vector[0]])
                normal = normal/np.linalg.norm(normal, ord=1)   
                randOffset = normal*random.randint(-randRange, randRange)
                midpoint = ((pts[0]+pts[1])/2)+randOffset
                midpointID = lines.addVertex(midpoint)
                
                if random.uniform(0.0, 1.0) < self.forking and i < int(self.complexity/2):
                    forkDirection = midpoint-pts[0]
                    angle = random.uniform(0.1, 1.55*self.maxForkAngle)
                    if random.uniform(0.0, 1.0) > 0.5:
                        angle = -angle
                    cosVal = math.cos(angle)
                    sinVal = math.sin(angle)
                    csd = np.array([cosVal, -sinVal])*forkDirection
                    scd = np.array([sinVal, cosVal])*forkDirection
                    forkEnd = midpoint+np.array([np.sum(csd), np.sum(scd)]) 
                    forkEndID = lines.addVertex(forkEnd)
                    lines.addLine(midpointID, forkEndID, segment.level+1)
                
                lines.addLine(segment.p0, midpointID, segment.level)
                lines.addLine(midpointID, segment.p1, segment.level)
                lines.removeSegment(si)
            randRange = int(randRange/2)
        return lines

    def drawBolt(self, lines, pixels, coord, w, h):
        bitmap = [0.0, 0.0, 0.0, 1.0]*(w*h)
        def drawLine(start, end, thickness):
            def scaleRadius(radius, point, start, end, scale):
                if (scale == 1.0):
                    return radius
                maxDistMultiplier = 1.0
                maxDist = math.dist((coord[0], coord[1]), (coord[2], coord[3]))*maxDistMultiplier
                currentDist = math.dist(point, (coord[0], coord[1]))
                if(currentDist == 0.0):
                    return radius
                return int(round((currentDist/maxDist)*scale*radius+radius))

            def setPixel(x, y):
                if (0 <= x < w) and (0 <= y < h):
                    offset = (x + int(y*w))*4
                    for i in range(4):
                        try:
                            bitmap[offset+i] = 1.0
                        except:
                            {}

            def drawPoint(x, y, thickness):
                radius = scaleRadius(thickness, [x,y], start, end, self.perspectiveScale)
                for X in range(-radius, radius+1):
                    for Y in range(-radius, radius+1):
                        if(X*X+Y*Y <= radius*radius):
                            setPixel(X+x, Y+y)                        

            # Bressenham
            dx = abs(end[0] - start[0])
            dy = abs(end[1] - start[1])
            x, y = start[0], start[1]
            sx = -1 if start[0] > end[0] else 1
            sy = -1 if start[1] > end[1] else 1
            if dx > dy:
                err = dx / 2.0
                while x != end[0] and (0 <= x < w):
                    drawPoint(x, y, thickness)
                    err -= dy
                    if err < 0:
                        y += sy
                        err += dx
                    x += sx
            else:
                err = dy / 2.0
                while y != end[1] and (0 <= y < h):
                    drawPoint(x, y, thickness)

                    err -= dx
                    if err < 0:
                        x += sx
                        err += dy
                    y += sy
            drawPoint(x, y, thickness)
            
        for segment in lines.segments:
            pts = lines.getCoords(segment)[0]
            width = int(bl_math.clamp(self.thickness*(1.0-(segment.level/(self.falloff*lines.getMaxLevel()))), 0, self.thickness))
            drawLine((int(pts[0][0]), int(pts[0][1])), (int(pts[1][0]), int(pts[1][1])), width)
        pixels.foreach_set(bitmap)
                    
    def drawBoltGPU(self, lines, pixels, coord, w, h):
        print("Not implemented.")

    def update_effect(self, context):
        scene = bpy.context.scene
        img = bpy.data.images[self.name]
        coords = [0, 0, 0, 0]
        inputs = ['Start X', 'Start Y', 'End X', 'End Y']
        for i in range(len(inputs)):
            coords[i] = self.inputs[inputs[i]].default_value
            if len(self.inputs[inputs[i]].links) != 0:
                inputNode = self.inputs[inputs[i]].links[0].from_node
                if isinstance(inputNode, bpy.types.CompositorNodeTrackPos):
                    markerPosition = inputNode.clip.tracking.tracks[inputNode.track_name].markers.find_frame(bpy.context.scene.frame_current).co
                    xy = 1
                    if i % 2 == 0:
                        xy = 0
                    coords[i] = int(markerPosition[xy]*inputNode.clip.size[xy])
                else:
                    bpy.context.scene.node_tree.links.remove(self.inputs[inputs[i]].links[0])
        if(abs(coords[0]-coords[2]) + abs(coords[1]-coords[3]) < 0.0001):
            return
        start = time.time()
        lines = self.generateBolt(np.array([coords[0],coords[1]]), np.array([coords[2],coords[3]]))
        if(self.gpuComp):
            self.drawBoltGPU(lines, img.pixels, coords, img.size[0], img.size[1])
        else:
            self.drawBolt(lines, img.pixels, coords, img.size[0], img.size[1])

        end = time.time()
        img.update()
        coreBlurNode = self.node_tree.nodes.get('coreBlurNode')
        coreBlurNode.inputs[1].default_value = (self.coreBlur, self.coreBlur)
        glowBlurNode = self.node_tree.nodes.get('glowBlurNode')
        glowBlurNode.inputs[1].default_value = (self.glow, self.glow)
        return

    forking: bpy.props.FloatProperty(name="Forking",
                                     description="The probability of forking",
                                     min=0.0, max=1.0, default=0.5,
                                     update=update_effect)
    maxForkAngle: bpy.props.FloatProperty(name="Max fork angle",
                                     description="Maximal angle of the forks",
                                     min=0.0, max=1.0, default=0.5,
                                     update=update_effect)
    complexity: bpy.props.IntProperty(name="Complexity",
                                      description="Number of recursive segments (curves of the bolt)",
                                      min=5, max=17, default=8,
                                      update=update_effect)
    stability: bpy.props.FloatProperty(name="Stability",
                                       description="How much does the bolt wiggle",
                                       min=0.0, max=1.0, default=0.5,
                                       update=update_effect)
    falloff: bpy.props.FloatProperty(name="Falloff",
                                     description="Making the bolt thin at the end",
                                     min=0.5, max=2.0, default=0.5,
                                     update=update_effect)
    thickness: bpy.props.IntProperty(name="Thickness",
                                     description="Overall thickness of the bolt",
                                     min=0, max=100, default=3,
                                     update=update_effect)
    perspectiveScale: bpy.props.FloatProperty(name="Perspective scale",
                                              description="Scales the bolt in the direction of end point",
                                              min=1.0, max=10.0, default=1.0,
                                              update=update_effect)
    glow: bpy.props.IntProperty(name="Glow",
                                description="The amount of glow/light emitted by the core",
                                min=0, max=200, default=60,
                                update=update_effect)
    coreBlur: bpy.props.IntProperty(name="Core blur",
                                    description="How sharp the core is",
                                    min=0, max=30, default=5,
                                    update=update_effect)
    seed: bpy.props.IntProperty(name="Seed",
                                description="Random seed affecting the shape of the bolt",
                                min=0, default=0,
                                update=update_effect)
    gpuComp: bpy.props.BoolProperty(name="GPU compute",
                                description="Use GPU acceleration (good for very thick and complex bolts)",
                                default=0,
                                update=update_effect)

    def init(self, context):
        scene = bpy.context.scene
        bpy.data.images.new(name=self.name, width=scene.render.resolution_x, height=scene.render.resolution_y)

        self.node_tree = bpy.data.node_groups.new(self.bl_name, 'CompositorNodeTree')
        group_input = self.node_tree.nodes.new('NodeGroupInput')
        group_output = self.node_tree.nodes.new('NodeGroupOutput')

        interface = self.node_tree.interface
        interface.new_socket(name="Glow color", in_out='INPUT', socket_type='NodeSocketColor')
        interface.new_socket(name="Start X", in_out='INPUT', socket_type='NodeSocketInt')
        interface.new_socket(name="Start Y", in_out='INPUT', socket_type='NodeSocketInt')
        interface.new_socket(name="End X", in_out='INPUT', socket_type='NodeSocketInt')
        interface.new_socket(name="End Y", in_out='INPUT', socket_type='NodeSocketInt')
        interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        
        self.inputs["Start X"].default_value = int(scene.render.resolution_x / 3)
        self.inputs["Start Y"].default_value = int(scene.render.resolution_y / 2)
        self.inputs["End X"].default_value = int(scene.render.resolution_x - scene.render.resolution_x / 3)
        self.inputs["End Y"].default_value = int(scene.render.resolution_y / 2)
        self.inputs["Glow color"].default_value = (0.0, 0.27, 1.0, 1.0)

        imageNode = self.node_tree.nodes.new("CompositorNodeImage")
        imageNode.name = 'resultImageNode'
        imageNode.image = bpy.data.images[self.name]

        coreBlurNode = self.node_tree.nodes.new("CompositorNodeBlur")
        coreBlurNode.name = 'coreBlurNode'
        coreBlurNode.inputs[2].default_value = 'Fast Gaussian'

        glowBlurNode = self.node_tree.nodes.new("CompositorNodeBlur")
        glowBlurNode.name = 'glowBlurNode'
        glowBlurNode.inputs[2].default_value = 'Fast Gaussian'

        mixNode = self.node_tree.nodes.new("ShaderNodeMix")
        mixNode.name = 'mixNode'
        mixNode.data_type = 'RGBA'
        mixNode.inputs[0].default_value = 1.0
        mixNode.blend_type = 'ADD'

        colorizeNode = self.node_tree.nodes.new("ShaderNodeMix")
        colorizeNode.name = 'colorizeNode'
        colorizeNode.data_type = 'RGBA'
        colorizeNode.blend_type = 'COLOR'
        colorizeNode.inputs[0].default_value = 1.0
        colorizeNode.inputs[7].default_value = (0.0, 0.0, 1.0, 1.0)

        self.outputs['Image'].default_value = imageNode.outputs[0].default_value
        self.node_tree.links.new(group_input.outputs[0], colorizeNode.inputs[7])
        self.node_tree.links.new(imageNode.outputs[0], coreBlurNode.inputs[0])
        self.node_tree.links.new(imageNode.outputs[0], glowBlurNode.inputs[0])
        self.node_tree.links.new(coreBlurNode.outputs[0], mixNode.inputs[7])
        self.node_tree.links.new(glowBlurNode.outputs[0], colorizeNode.inputs[6])
        self.node_tree.links.new(colorizeNode.outputs[2], mixNode.inputs[6])
        self.node_tree.links.new(mixNode.outputs[2], group_output.inputs[0])

        # WORKAROUND since socket update is not working
        #def update(dummy):
        #    if self.name != "":
        #        self.update_effect(bpy.context)
        #bpy.app.driver_namespace[self.name] = update
        #bpy.app.handlers.depsgraph_update_pre.append(update)
        #bpy.app.handlers.frame_change_post.append(update)
        #bpy.app.handlers.render_post.append(update)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'forking',  text='Forking', slider=1)
        row = layout.row()
        row.prop(self, 'maxForkAngle',  text='Max fork angle', slider=1)
        row = layout.row()
        row.prop(self, 'complexity',  text='Complexity', slider=1)
        row = layout.row()
        row.prop(self, 'stability', text='Stability', slider=1)
        row = layout.row()
        row.prop(self, 'falloff', text='Falloff', slider=1)
        row = layout.row()
        row.prop(self, 'thickness', text='Thickness', slider=1)
        row = layout.row()
        row.prop(self, 'perspectiveScale', text='Perspective scale', slider=1)
        row = layout.row()
        row.prop(self, 'glow', text='Glow', slider=1)
        row = layout.row()
        row.prop(self, 'coreBlur', text='Core blur', slider=1)
        row = layout.row()
        row.prop(self, 'seed', text='Seed')
        row = layout.row()
        row.prop(self, 'gpuComp', text='GPU compute')

    def copy(self, node):
        self.init(bpy.context)
        return

    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)
        img = bpy.data.images[self.name]
        img.user_clear()
        bpy.data.images.remove(img)
        #WORKAROUND TO FIX NOT UPDATING OF CUSTOM PROPERTIES
        #bpy.app.handlers.depsgraph_update_pre.remove(bpy.app.driver_namespace[self.name])
        #bpy.app.handlers.frame_change_post.remove(bpy.app.driver_namespace[self.name])
        #bpy.app.handlers.render_post.remove(bpy.app.driver_namespace[self.name])
        del bpy.app.driver_namespace[self.name]

def menu_func_input(self, context):
    self.layout.operator(
        "node.add_node",
        text="Lightning Generator"
    ).type = "LightningGen"

def register():
    bpy.utils.register_class(LightningGen)
    bpy.types.NODE_MT_category_compositor_input.append(menu_func_input)


def unregister():
    bpy.types.NODE_MT_category_compositor_input.remove(menu_func_input)
    bpy.utils.unregister_class(LightningGen)

try:
    unregister()
except:
    pass
register()
