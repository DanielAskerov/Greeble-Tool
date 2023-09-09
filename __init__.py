# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

from . import greeble_tool as gt

bl_info = {
    "name" : "Greeble Tool",
    "author" : "Daniel Askerov",
    "description" : "",
    "blender" : (3, 5, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

classes = [gt.GREEBLETOOL_PT_main_panel,
           gt.GREEBLETOOL_PG_object_properties,
           gt.GREEBLETOOL_PG_scene_properties,
           gt.GREEBLETOOL_OT_greeble_ops,
           gt.GREEBLETOOL_OT_terminate,
           gt.GREEBLETOOL_OT_bake,
           gt.GREEBLETOOL_OT_export]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Object.greeble_properties = bpy.props.PointerProperty(type=gt.GREEBLETOOL_PG_object_properties)
    bpy.types.Scene.greeble_scene_properties = bpy.props.PointerProperty(type=gt.GREEBLETOOL_PG_scene_properties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Object.greeble_properties
    del bpy.types.Scene.greeble_scene_properties


if __name__ == "__main__":
    register()