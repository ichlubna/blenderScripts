import bpy
import os
import mathutils
import math

sampleDensity = 8
sampleDistance = 0.05
renderInfo = bpy.data.scenes["Scene"].render

def imagePath(x,y,prefix=""):
    return renderInfo.filepath[:]+prefix+str(x)+"_"+str(y)

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


def renderSamples():
    camera = bpy.context.scene.camera
    originalBasis = camera.matrix_basis
    cornerTranslation = (sampleDensity*sampleDistance)/2
    cornerBasis = originalBasis @ mathutils.Matrix.Translation((-cornerTranslation, -cornerTranslation, 0.0))
    renderInfo.use_overwrite = True
    
    for b in range(renderInfo.resolution_y):
        pixels = [[[0.0, 0.0, 0.0, 1.0]*(sampleDensity*sampleDensity)]*3]*renderInfo.resolution_x
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
                    pixel = getPixel(p, b, image)
                    for i in range(3):
                        writePixel(x, y, pixels[p][i], sampleDensity, [pixel[i]*3])
                    
                bpy.data.images.remove(image)

        for p in range(renderInfo.resolution_x):
            for i in range(3):
                pixelImage = bpy.data.images.new("pixelImage", width=sampleDensity, height=sampleDensity)
                pixelImage.pixels[:] = pixels[p][i]
                pixelImage.update()
                pixelImage.save_render(imagePath(p,b,"ch"+str(i)))
                bpy.data.images.remove(pixelImage)       
         
    renderInfo.filepath = originalFilePath
    camera.matrix_basis = originalBasis
    os.remove(originalFilePath+"test.png")



originalFilePath = renderInfo.filepath
try:
    renderSamples()
    #reconstruct(0,0)
except Exception as e:
    renderInfo.filepath = originalFilePath
    print(e)
