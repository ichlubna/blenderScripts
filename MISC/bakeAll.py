import bpy

for scene in bpy.data.scenes:
    for object in scene.objects:
        for modifier in object.modifiers:
            if modifier.type == 'SMOKE':
                if modifier.smoke_type == 'DOMAIN':
                    print("Baking smoke")
                    override = {'scene': scene, 'active_object': object, 'point_cache': modifier.domain_settings.point_cache}
                    bpy.ops.ptcache.free_bake(override)
                    bpy.ops.ptcache.bake(override, bake=True)
            elif modifier.type == 'FLUID_SIMULATION':
                if modifier.settings.type == 'DOMAIN':
                    print("Baking fluid")
                    override = {'scene': scene, 'active_object': object}
                    bpy.ops.fluid.bake(override)
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
