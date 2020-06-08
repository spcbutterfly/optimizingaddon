bl_info = {
    "name": "Optimization Addon: Inner Geom",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy, bmesh
from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    PropertyGroup,
)

#=============== АЛГОРИТМ ===============

# получить лист исходных моделей
# проверка если количество исходников меньше 2
# получить лист BMesh из исходных моделей
# создать лист множеств bm_verts
# создать лист множеств to_delete_verts
# развесить всем исходникам модификатор boolean intersect

# в цикле i k попарно делаем следующее:
# 
# исходнику i в boolean добавляем исходник k
# берём BMesh из полученного i, назовём inner_geom
# создаём множество same_verts
# в цикле по вершинам inner_geom сравниваем координаты с вершинами из BMesh
# если такая вершина есть, то добавляем её в same_verts
# same_verts добавляем в to_delete_verts[i]
# исходнику i в boolean убираем объект k
#
# соответственно делаем наоборот k i

# в цикле по BMesh удаляем невидимые трисы
# выделяем все трисы, у которых вершины невидимые
# удаляем невидимые трисы

# убрать все модификаторы boolean
# применить все BMesh к исходникам
# освободить все BMesh

class Optimize_geom(Operator):
    bl_label = "Delete_inner_geom"
    bl_idname = "object.optimize_geom"
    bl_description = "Optimize models with inner geom"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self,context):
        def del_inner_geom():
            # получить лист исходных моделей
            bpy.ops.object.select_by_type(type='MESH')
            mesh_origins = tuple(bpy.context.selected_objects)

            # проверка если количество исходников меньше 2
            if len(mesh_origins) < 2:
                print('There should be at least 2 MESH objects.')
                return False

            # получить лист BMesh из исходных моделей
            bm_list = list()
            for i in range(len(mesh_origins)):
                bm_list.append(bmesh.new()) # create an empty BMesh
                bm_list[i].from_object(mesh_origins[i], bpy.context.evaluated_depsgraph_get(), deform=True, cage=False, face_normals=True) # fill it in from a Mesh

        	# создать лист множеств bm_verts
            bm_verts = [set() for i in range(len(mesh_origins))]
            for i in range(len(bm_list)):
                for v in bm_list[i].verts:
                    bm_verts[i].add((v.co.x, v.co.y, v.co.z))
            bm_verts = tuple(bm_verts)
                        
            # создать лист множеств to_delete_verts
            to_delete_verts = [set() for i in range(len(mesh_origins))]
                
            # развесить всем исходникам модификатор boolean intersect
            mods_list = list()
            for i in range(len(mesh_origins)):
                mods_list.append(mesh_origins[i].modifiers.new(type='BOOLEAN', name='bool intersect'))
                mods_list[i].operation = 'INTERSECT'
                    
            def get_to_del_verts(a, b):
                # исходнику a в boolean добавляем исходник b
                mods_list[a].object = mesh_origins[b]
                mods_list[b].object = None
                    
            # берём BMesh из полученного a, назовём inner_geom
                inner_geom = bmesh.new()
                inner_geom.from_object(mesh_origins[a], bpy.context.evaluated_depsgraph_get(), deform=True, cage=False, face_normals=True)
                    
                # создаём множество same_verts
                same_verts = set()
                    
                # в цикле по вершинам inner_geom сравниваем координаты с вершинами из BMesh
                for v in inner_geom.verts:
                    if (v.co.x, v.co.y, v.co.z) in bm_verts[a]:
                        # если такая вершина есть, то добавляем её в same_verts
                        same_verts.add((v.co.x, v.co.y, v.co.z))
                            
                # same_verts добавляем в to_delete_verts[a]
                to_delete_verts[a] = to_delete_verts[a].union(same_verts)
                    
                # исходнику a в boolean убираем объект b
                mods_list[a].object = None
                    
                        
            # цикл проходит попарно по всем мешам
            for i in range(len(mesh_origins)-1):
                for k in range(i+1, len(mesh_origins)):
                    get_to_del_verts(i, k)
                    get_to_del_verts(k, i)
            to_delete_verts = tuple(to_delete_verts)
                   
            # в цикле по BMesh удаляем невидимые трисы
            for i in range(len(bm_list)):
                bm_list[i].select_mode = {'VERT', 'EDGE', 'FACE'}
                for f in bm_list[i].faces:
                    f.select = False
                for e in bm_list[i].edges:
                    e.select = False
                for v in bm_list[i].verts:
                    if (v.co.x, v.co.y, v.co.z) in to_delete_verts[i]:
                        v.select = True
                    else:
                        v.select = False
                    
                # выделяем все трисы, у которых вершины невидимые
                bm_list[i].select_flush_mode()
                faces = [f for f in bm_list[i].faces if f.select]
                
                # удаляем невидимые трисы
                bmesh.ops.delete(bm_list[i], geom=faces, context='FACES')
                
            # убрать все модификаторы boolean
            for obj in mesh_origins:
                for m in obj.modifiers:
                    if(m.type=='BOOLEAN'):
                        obj.modifiers.remove(modifier=m)
                
            # применить все BMesh к исходникам
            for i in range(len(mesh_origins)):
                bm_list[i].to_mesh(mesh_origins[i].data)
            
            # освободить все BMesh
            for i in range(len(bm_list)):
                bm_list[i].free()
            return True
        del_inner_geom()    
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(Optimize_geom.bl_idname)
	
def register():
    bpy.utils.register_class(Optimize_geom)
    bpy.types.VIEW3D_MT_object.append(menu_func)	
	
def unregister():
    bpy.utils.unregister_class(Optimize_geom)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
##if name необязательно, позволяет запускать аддон прямо из текстового редактора Blender
if __name__ == "__main__":
    register()	

