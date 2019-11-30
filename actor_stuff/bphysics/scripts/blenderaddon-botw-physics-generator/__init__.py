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

bl_info = {
    "name": "BotW Physics Generator",
    "author": "kreny",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

import os
import subprocess

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper


def ShowMessageBox(title, message, icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def generate_physics(context, filepath, binary=False):
    if binary:
        filepath_yml = filepath.replace(".bphysics", ".physics.yml")
        filepath_bin = filepath
    else:
        filepath_yml = filepath
    scene = bpy.context.scene
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    default_file = directory + "/default.yml"
    with open(default_file, "r") as f:
        content = f.read()
    shape_param_template = (
        "                    ShapeParam_{}: !obj # {}\n"
        "                      shape_type: !str32 polytope\n"
        "                      vertex_num: {}\n"
        "{}\n"
        "                      material: !str32 Metal\n"
        "                      sub_material: !str32 Metal_Heavy\n"
        "                      wall_code: !str32 NoClimb\n"
        "                      floor_code: !str32 None\n"
    )
    vertex_template = "                      vertex_{}: !vec3 [{}, {}, {}]"
    shapes = ""
    for i, obj in enumerate(scene.objects):
        mtx = obj.matrix_world
        v_coords = [mtx @ v.co for v in obj.data.vertices]
        shapes += shape_param_template.format(
            i,
            obj.name,
            len(obj.data.vertices),
            "\n".join(
                [
                    vertex_template.format(o, v.x, v.z, v.y)
                    for o, v in enumerate(v_coords)
                ]
            ),
        )
    output = content.format(len(scene.objects), shapes.rstrip("\n"))
    with open(filepath_yml, "w") as output_file:
        output_file.write(output)

    if binary:
        try:
            command = "aamp {} {}".format(filepath_yml, filepath_bin)
            print(subprocess.check_output(command, shell=True))
        except Exception as e:
            print(e)
            ShowMessageBox(
                "AAMP Error", "Make sure you have AAMP installed (pip install aamp)",
            )
            return {"CANCELLED"}
        finally:
            os.remove(filepath_yml)
    return {"FINISHED"}


class ExportPhysics(Operator, ExportHelper):
    """Export BotW Physics File"""

    bl_idname = "export_physics.yml"
    bl_label = "Export BotW physics file (.physics.yml)"

    # ExportHelper mixin class uses this
    filename_ext = ".physics.yml"

    filter_glob: StringProperty(default="*.physics.yml", options={"HIDDEN"})

    def execute(self, context):
        return generate_physics(context, self.filepath)


class ExportPhysicsBinary(Operator, ExportHelper):
    """Export BotW Binary Physics File"""

    bl_idname = "export_bphysics.bphysics"
    bl_label = "Export BotW binary physics file (.bphysics)"

    # ExportHelper mixin class uses this
    filename_ext = ".bphysics"

    filter_glob: StringProperty(default="*.bphysics", options={"HIDDEN"})

    def execute(self, context):
        return generate_physics(context, self.filepath, binary=True)


def MenuExport(self, context):
    self.layout.operator(
        ExportPhysics.bl_idname, text="BotW Physics File (.physics.yml)"
    )
    self.layout.operator(
        ExportPhysicsBinary.bl_idname, text="BotW Binary Physics File (.bphysics)"
    )


def register():
    bpy.utils.register_class(ExportPhysics)
    bpy.utils.register_class(ExportPhysicsBinary)
    bpy.types.TOPBAR_MT_file_export.append(MenuExport)


def unregister():
    bpy.utils.unregister_class(ExportPhysics)
    bpy.utils.unregister_class(ExportPhysicsBinary)
    bpy.types.TOPBAR_MT_file_export.remove(MenuExport)
