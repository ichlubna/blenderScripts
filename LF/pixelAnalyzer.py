import bpy
import os
import mathutils
import math

sampleDensity = 9
sampleDistance = 0.05
renderInfo = bpy.data.scenes["Scene"].render

def imagePath(x,y,prefix=""):
    return originalFilePath+prefix+str(x)+"_"+str(y)+renderInfo.file_extension

def clamp(x):
    return max(min(x, 1.0), 0.0)

def getPixel(x,y,image):
    i = (y * image.size[0] + x ) * 4
    return (image.pixels[i], image.pixels[i+1], image.pixels[i+2])

def writePixel(x,y,pixels,rx,value):
    i = (y * rx + x ) * 4
    pixels[i] = value[0]
    pixels[i+1] = value[1]
    pixels[i+2] = value[2]

def saveImagePixels(pixels, width, height, path):
    pixelImage = bpy.data.images.new("pixelImage", width=width, height=height)
    pixelImage.pixels[:] = pixels
    pixelImage.update()
    pixelImage.save_render(path)
    pixelImage.buffers_free()
    bpy.data.images.remove(pixelImage)       
         
def renderSamples():
    camera = bpy.context.scene.camera
    originalBasis = camera.matrix_basis
    cornerTranslation = (sampleDensity*sampleDistance)/2
    cornerBasis = originalBasis @ mathutils.Matrix.Translation((-cornerTranslation, -cornerTranslation, 0.0))
    renderInfo.use_overwrite = True
    
    for b in range(renderInfo.resolution_y):
        pixels = [[0.0, 0.0, 0.0, 1.0]*(sampleDensity*sampleDensity)]*renderInfo.resolution_x
        renderInfo.use_border = True
        renderInfo.use_crop_to_border = False
        renderPadding = 0.01
        renderInfo.border_max_x = 1.0
        renderInfo.border_max_y = clamp(b/renderInfo.resolution_y+renderPadding)
        renderInfo.border_min_x = 0.0
        renderInfo.border_min_y = clamp(b/renderInfo.resolution_y-renderPadding)
        
        for x in range(sampleDensity):
            for y in range(sampleDensity):
                camera.matrix_basis = cornerBasis @ mathutils.Matrix.Translation((x*sampleDistance, y*sampleDistance, 0.0))
                renderInfo.filepath = originalFilePath+"test.png"
                bpy.ops.render.render( write_still=True )
                image = bpy.data.images.load(renderInfo.filepath)
                for p in range(renderInfo.resolution_x):
                    #TODO YUV?
                    pixel = getPixel(p,b,image)
                    writePixel(x, y, pixels[p], sampleDensity, pixel)       
                image.buffers_free()        
                bpy.data.images.remove(image)

        for p in range(renderInfo.resolution_x):
                saveImagePixels(pixels[p],sampleDensity,sampleDensity,imagePath(p,b))      
         
    renderInfo.filepath = originalFilePath
    camera.matrix_basis = originalBasis
    renderInfo.use_border = False
    os.remove(originalFilePath+"test.png")

def reconstruct(x,y):
    pixels = [0.0, 0.0, 0.0, 1.0]*(renderInfo.resolution_x*renderInfo.resolution_y)
    for px in range(renderInfo.resolution_x):
            for py in range(renderInfo.resolution_y):
                image = bpy.data.images.load(imagePath(px,py))
                writePixel(px,py,pixels,renderInfo.resolution_x,getPixel(x,y,image))
                image.buffers_free()  
                bpy.data.images.remove(image)
    saveImagePixels(pixels,renderInfo.resolution_x,renderInfo.resolution_y,renderInfo.filepath[:]+"reconstructed"+str(x)+"_"+str(y))       

originalFilePath = renderInfo.filepath
try:
    renderSamples()
    reconstruct(4,4)
except Exception as e:
    renderInfo.filepath = originalFilePath
    print(e)
renderInfo.filepath = originalFilePath