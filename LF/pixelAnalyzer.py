import bpy
import os
import shutil
import mathutils
import math
from functools import reduce

sampleDensity = 3
sampleDistance = 0.1
renderInfo = bpy.data.scenes["Scene"].render
tempRenderFile = bpy.app.tempdir+"test.png"
originalFilePath = renderInfo.filepath

def imagePath(x,y,path=originalFilePath,prefix=""):
    return path+prefix+str(x)+"_"+str(y)+renderInfo.file_extension

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
         
def renderSamplesAndSort():
    #maybe copy camera and then delete to keep the original one in case of errors
    camera = bpy.context.scene.camera
    originalBasis = camera.matrix_basis
    cornerTranslation = (sampleDensity*sampleDistance)/2
    cornerBasis = originalBasis @ mathutils.Matrix.Translation((-cornerTranslation, -cornerTranslation, 0.0))
    renderInfo.use_overwrite = True
    renderInfo.use_border = True
    renderInfo.use_crop_to_border = False
    
    for ry in range(renderInfo.resolution_y):
        pixels = [reduce(lambda x,y:x+y,[[0.0,0.0,0.0,1.0] for i in range(sampleDensity*sampleDensity)]) for i in range(renderInfo.resolution_x)]
        renderPadding = 0.03
        renderInfo.border_max_x = 1.0
        renderInfo.border_max_y = clamp(ry/renderInfo.resolution_y+renderPadding)
        renderInfo.border_min_x = 0.0
        renderInfo.border_min_y = clamp(ry/renderInfo.resolution_y-renderPadding)
        
        for x in range(sampleDensity):
            for y in range(sampleDensity):
                camera.matrix_basis = cornerBasis @ mathutils.Matrix.Translation((x*sampleDistance, y*sampleDistance, 0.0))
                renderInfo.filepath = tempRenderFile
                bpy.ops.render.render( write_still=True )
                image = bpy.data.images.load(tempRenderFile)
                for rx in range(renderInfo.resolution_x):
                    pixel = getPixel(rx, ry, image)
                    writePixel(x, y, pixels[rx], sampleDensity, pixel)       
                image.buffers_free()        
                bpy.data.images.remove(image)

        for p in range(renderInfo.resolution_x):
                saveImagePixels(pixels[p],sampleDensity,sampleDensity,imagePath(p,ry))      
         
    renderInfo.filepath = originalFilePath
    camera.matrix_basis = originalBasis
    renderInfo.use_border = False
    os.remove(tempRenderFile)
    
def renderSamplesFull(path):
    camera = bpy.context.scene.camera
    originalBasis = camera.matrix_basis.copy()
    cornerTranslation = (sampleDensity*sampleDistance)/2
    cornerBasis = originalBasis @ mathutils.Matrix.Translation((-cornerTranslation, -cornerTranslation, 0.0))
    renderInfo.use_overwrite = True
    renderInfo.use_border = False
        
    for x in range(sampleDensity):
        for y in range(sampleDensity):
            camera.matrix_basis = cornerBasis @ mathutils.Matrix.Translation((x*sampleDistance, y*sampleDistance, 0.0))
            renderInfo.filepath = imagePath(x,y,path)
            bpy.ops.render.render( write_still=True )
    camera.matrix_basis = originalBasis

def sortPixels(inputPath, outputPath):    
    for ry in range(renderInfo.resolution_y):
        pixels = [reduce(lambda x,y:x+y,[[0.0,0.0,0.0,1.0] for i in range(sampleDensity*sampleDensity)]) for i in range(renderInfo.resolution_x)]
        for x in range(sampleDensity):
            for y in range(sampleDensity):
                image = bpy.data.images.load(inputPath + imagePath(x,y))
                for rx in range(renderInfo.resolution_x):
                    pixel = getPixel(rx, ry, image)
                    writePixel(x, y, pixels[rx], sampleDensity, pixel)       
                image.buffers_free()        
                bpy.data.images.remove(image)                
        for p in range(renderInfo.resolution_x):
                saveImagePixels(pixels[p],sampleDensity,sampleDensity,imagePath(p,ry,outputPath))    

def reconstruct(x,y,inputPath):
    pixels = reduce(lambda x,y:x+y,[[0.0,0.0,0.0,1.0] for i in range(renderInfo.resolution_x*renderInfo.resolution_y)])
    for px in range(renderInfo.resolution_x):
            for py in range(renderInfo.resolution_y):
                image = bpy.data.images.load(imagePath(px,py,inputPath))
                writePixel(px,py,pixels,renderInfo.resolution_x,getPixel(x,y,image))
                image.buffers_free()  
                bpy.data.images.remove(image)
    saveImagePixels(pixels,renderInfo.resolution_x,renderInfo.resolution_y, imagePath(x,y,prefix="reconstructed"))
    
try:
    #renderSamplesAndSort()
    #renderInfo.filepath
    renderPath = "/home/ichlubna/Downloads/pav/"#bpy.app.tempdir + "render/"
    #sortPath = bpy.app.tempdir + "sort/"
    #os.mkdir(renderPath)
    #os.mkdir(sortPath)
    renderSamplesFull(renderPath)
    #sortPixels("/home/ichlubna/Downloads/lego/", sortPath)
    #reconstruct(2,2,sortPath)
except Exception as e:
    renderInfo.filepath = originalFilePath
    print(e)
renderInfo.filepath = originalFilePath