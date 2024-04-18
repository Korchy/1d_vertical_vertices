# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_vertical_vertices

import bpy
from bpy.props import FloatProperty
from bpy.types import Operator, Panel, Scene
from bpy.utils import register_class, unregister_class
from mathutils import kdtree, Vector

bl_info = {
    "name": "Vertical Vertices",
    "description": "Selects all vertices which have nearest coordinates in x-y projection",
    "author": "Nikita Akimov, Paul Kotelevets",
    "version": (1, 0, 2),
    "blender": (2, 79, 0),
    "location": "View3D > Tool panel > 1D > Vertical Vertices",
    "doc_url": "https://github.com/Korchy/1d_vertical_vertices",
    "tracker_url": "https://github.com/Korchy/1d_vertical_vertices",
    "category": "All"
}


# MAIN CLASS

class VerticalVertices:

    @classmethod
    def select_verticals(cls, context, threshold):
        # select vertical vertices
        # edit/object mode
        mode = context.active_object.mode
        if context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        # process
        selected_vertices = [v for v in context.object.data.vertices if v.select]
        # crete kdtree for quick finding nearest vertices
        size = len(selected_vertices)
        kd = kdtree.KDTree(size)
        # for i, v in enumerate(selected_vertices):
        for v in selected_vertices:
            kd.insert(Vector((v.co.x, v.co.y, 0.0)), v.index)
        kd.balance()
        # for each selected vertex find nearest
        nearest_groups = []
        while selected_vertices:
            vert = selected_vertices.pop(0)     # get first from list
            # find all nearest by x-y vertices
            #   return a list of nearest vertices like: [(Vector(x, y, z), index, distance), ...]
            nearest_to_vert = kd.find_range(
                co=Vector((vert.co.x, vert.co.y, 0.0)),
                radius=threshold
            )
            if len(nearest_to_vert) > 1:    # source vertex included too
                # nearest vertices was found
                # get mesh vertices by index in nearest_to_vert
                nearest_vertices = [context.object.data.vertices[i] for i in [vert[1] for vert in nearest_to_vert]]
                # save them to group
                nearest_groups.append(nearest_vertices)
                # remove all these vertices - they don't need to be processed one more time
                selected_vertices = list(set(selected_vertices).difference(set(nearest_vertices)))
        # test print
        # for group in nearest_groups:
        #     print('group')
        #     print(group)
        cls._deselect_all(obj=context.active_object)
        # select all vertices from groups except with max z coordinate
        for group in nearest_groups:
            # find vertex with max z coordinate in group
            max_z_vert = max(group, key=lambda vertex: vertex.co.z)
            # select all in group except max_z_vert
            for vert in group:
                if vert.index != max_z_vert.index:
                    vert.select = True
        # return mode back
        bpy.ops.object.mode_set(mode=mode)

    @staticmethod
    def _deselect_all(obj):
        # remove all selection
        for polygon in obj.data.polygons:
            polygon.select = False
        for edge in obj.data.edges:
            edge.select = False
        for vertex in obj.data.vertices:
            vertex.select = False

    @staticmethod
    def ui(layout, context):
        # ui panel
        layout.prop(
            data=context.scene,
            property='vertical_vertices_threshold'
        )
        op = layout.operator(
            operator='verticalvertices.vertical_verts',
            icon='LINKED'
        )
        op.threshold = context.scene.vertical_vertices_threshold


# OPERATORS

class VerticalVertices_OT_vertical_verts(Operator):
    bl_idname = 'verticalvertices.vertical_verts'
    bl_label = 'Filter Vertical Vertices'
    bl_description = 'Filter vertices that have duplicates along the Z axis, except the top one'
    bl_options = {'REGISTER', 'UNDO'}

    threshold = FloatProperty(
        name='Threshold',
        default=0.1,
        min=0.0001,
        subtype='UNSIGNED'
    )

    def execute(self, context):
        VerticalVertices.select_verticals(
            context=context,
            threshold=self.threshold
        )
        return {'FINISHED'}


# PANELS

class VerticalVertices_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Vertical Vertices"
    bl_category = '1D'

    def draw(self, context):
        VerticalVertices.ui(
            layout=self.layout,
            context=context
        )


# REGISTER

def register(ui=True):
    Scene.vertical_vertices_threshold = FloatProperty(
        name='Threshold',
        description='Radius tolerance',
        default=0.1,
        min=0.0001,
        subtype='UNSIGNED'
    )
    register_class(VerticalVertices_OT_vertical_verts)
    if ui:
        register_class(VerticalVertices_PT_panel)


def unregister(ui=True):
    if ui:
        unregister_class(VerticalVertices_PT_panel)
    unregister_class(VerticalVertices_OT_vertical_verts)
    del Scene.vertical_vertices_threshold


if __name__ == "__main__":
    register()
