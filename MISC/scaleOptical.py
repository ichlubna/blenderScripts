import bpy
import mathutils

focus = 0.19

def mix(a,b, factor):
    r = a+b
    for i in 0,1,2:
        r[i] /= factor[i]
    return r

def mixDepth(point, focus, cam, factor):
    y = factor*(point[1]-focus)+focus
    x = ((point[0]-cam[0])/(point[1]-cam[1]))*(y-cam[1])-cam[0]
    z = ((point[2]-cam[2])/(point[1]-cam[1]))*(y-cam[1])-cam[2]
    return mathutils.Vector((x,y,z))

def scaleOptical(objects, factor):
    camLoc = bpy.context.scene.camera.location
    for obj in objects:
        if obj.data:
            if hasattr(obj.data, 'vertices'):
                obj.data.vertices
                for vert in obj.data.vertices:
                    #vert.co = obj.matrix_world.inverted() @ mix(obj.matrix_world @ vert.co, camLoc, factor)
                    vert.co = obj.matrix_world.inverted() @ mixDepth(obj.matrix_world @ vert.co, focus, camLoc, factor)
        

f = mathutils.Vector((10,0,10))
selected = bpy.context.selected_objects
scaleOptical(selected, 0.25)
