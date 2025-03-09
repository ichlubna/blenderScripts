# Some useful Blender scripts

## VFX
lightning.py - compositor node for 2D lightning effect - working but not finished since custom nodes struggle with input sockets

## LF
cameras.py - generates grid of cameras for lightfield or LKG\
pixelAnalyzer.py - analyzes pixels from LF data\
lfAssets.py - generates a virtual LF window from input grid - LF images - can be obtained from 3D scene with [this script](https://github.com/ichlubna/lfStreaming/blob/main/scripts/BlenderAddon.py)

## MISC
bakeAll.py - bakes all simulations (usage: blender untitled.blend -b -P bakeAll.py)\
matchFPS.py - transforms the imported strip in VSE into the project FPS\
scaleOptical.py - scales the selected objects according to camera\
ffExport.py - connects Blender to external ffmpeg, allowing a direct encoding to all supported formats like gif of h.265\
customNode.py - example of creating a custom material node which renders the scene and uses the render as a material texture
