import bpy

for scene in bpy.data.scenes:
    for object in scene.objects:
        for modifier in object.modifiers:
            if modifier.type == 'FLUID':
                if modifier.fluid_type == 'DOMAIN':
                    print("Baking fluid")
                    object.select_set(True)
                    bpy.context.view_layer.objects.active = object
                    bpy.ops.fluid.bake_data()
            elif modifier.type == 'CLOTH':
                print("Baking cloth")
                override = {'scene': scene, 'active_object': object, 'point_cache': modifier.point_cache}
                bpy.ops.ptcache.free_bake(override)
                bpy.ops.ptcache.bake(override, bake=True)
            elif modifier.type == 'PARTICLE_SYSTEM':
                print("Baking particles")
                override = {'scene': scene, 'active_object': object, 'point_cache': modifier.particle_system.point_cache}
                bpy.ops.ptcache.free_bake(override)
                bpy.ops.ptcache.bake(override, bake=True)
bpy.ops.wm.save_mainfile()
