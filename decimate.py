bl_info = {
    "name": "Optimization Addon",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy
from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    PropertyGroup,
)
import os

##Убирает все предыдущие итерации Decimate с модели
class Optimize(Operator):
    bl_label = "Optimize"
    bl_idname = "object.optimize"
    bl_description = "Optimize models"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}
    
    decimateRatio: bpy.props.FloatProperty(name="Ratio", default=0.4, min=0, max=1)
    
    def execute(self, context):
        modifierName='DecimateMod'
        
        def cleanAllDecimateModifiers(obj):
            for m in obj.modifiers:
                if(m.type=="DECIMATE"):
                    ##print("Remove modifiers ")
                    obj.modifiers.remove(modifier=m)

        for obj in bpy.data.objects:
            if(obj.type=="MESH"):
                cleanAllDecimateModifiers(obj)
                modifier=obj.modifiers.new(modifierName,'DECIMATE')
                modifier.ratio=self.decimateRatio
                modifier.use_collapse_triangulate=True
        
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(Optimize.bl_idname)
    
def register():
    bpy.utils.register_class(Optimize)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(Optimize)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
##if name необязательно, в финальной версии уберем, позволяет запускать аддон прямо из текстового редактора Blender
if __name__ == "__main__":
    register()