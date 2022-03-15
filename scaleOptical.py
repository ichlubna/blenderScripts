import bpy
import mathutils

def mix(a,b, factor):
    r = a+b
    for i in 0,1,2:
        r[i] /= factor[i]
    return r

def scaleOptical(objects, factor):
    camLoc = bpy.context.scene.camera.location
    for obj in objects:
        for vert in obj.data.vertices:
            vert.co = obj.matrix_world.inverted() @ mix(obj.matrix_world @ vert.co, camLoc, factor)
    

f = mathutils.Vector((2,2,2))
selected = bpy.context.selected_objects
scaleOptical(selected, f)


        
        
