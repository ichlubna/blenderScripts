bl_info = {
    "name": "Match FPS",
    "author": "ichlubna",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "VSE > Strip > Match FPS",
    "description": "Matches the strip length and speed to render FPS settings. When having selected the strip, go to the Strip menu and hit Match FPS button.",
    "warning": "",
    "doc_url": "",
    "category": "Strip",
}

import bpy
from bpy.types import Operator

def matchFPS():
    scene = bpy.context.scene
    editor = scene.sequence_editor
    clip = editor.active_strip
    scene.sequence_editor.sequences.new_effect(type='SPEED', name="FPS_FIX",frame_start=0, frame_end=0, channel=3, seq1=clip)
    ratio = scene.render.fps/clip.elements[0].orig_fps
    clip.frame_final_duration = clip.frame_duration*(ratio)
    bpy.ops.sequencer.meta_make()    

class STRIP_OT_match_fps(Operator):
    """Match the strip length according to scene FPS"""
    bl_idname = "strp.matchfps"
    bl_label = "Match FPS"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        matchFPS()
        return {'FINISHED'}

def add_object_button(self, context):
    scene = bpy.context.scene
    editor = scene.sequence_editor
    clip = editor.active_strip
    if isinstance(clip, bpy.types.MovieSequence):
        self.layout.operator(
            STRIP_OT_match_fps.bl_idname,
            text="Match FPS")

def register():
    bpy.utils.register_class(STRIP_OT_match_fps)
    bpy.types.SEQUENCER_MT_strip.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(STRIP_OT_match_fps)
    bpy.types.SEQUENCER_MT_strip.remove(add_object_button)


if __name__ == "__main__":
    register()
