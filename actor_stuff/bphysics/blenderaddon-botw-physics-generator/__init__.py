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
    "category": "Collision",
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


def parse_physics(context, filepath):
    filepath_obj = filepath + ".obj"
    output = ""
    obj_num = 0
    obj_template = "o Shape_{}\n"
    vert_template = "v {} {} {}\n"

    with open(filepath, "r") as f:
        for line in f.readlines():
            line = line.lstrip()
            if line.startswith("vertex_num"):
                output += obj_template.format(obj_num)
                obj_num += 1
            elif line.startswith("vertex_"):
                split = line.split("[")
                strip = split[1].rstrip("\n")
                strip = strip.rstrip("]")
                coords = strip.split(", ")
                output += vert_template.format(*coords)

    with open(filepath_obj, "w") as f:
        f.write(output)

    try:
        bpy.ops.import_scene.obj("EXEC_DEFAULT", filepath=filepath_obj)
    except Exception as e:
        print(e)
        ShowMessageBox(".OBJ Import Error", f"{e}")
        return {"CANCELLED"}
    #try:
    #    os.remove(filepath_obj)
    #except Exception as e:
    #    print(e)
    return {"FINISHED"}


def generate_physics(context, filepath, binary=False):
    if binary:
        filepath_yml = filepath.replace(".bphysics", ".physics.yml")
        filepath_bin = filepath
        filepath_obj = filepath + ".obj"
    else:
        filepath_yml = filepath
        filepath_obj = filepath + ".obj"
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    default_file = directory + "/default.yml"
    with open(default_file, "r") as f:
        content = f.read()

    try:
        bpy.ops.export_scene.obj(
            filepath=filepath_obj,
            check_existing=True,
            axis_forward="-Z",
            axis_up="Y",
            filter_glob="*.obj;*.mtl",
            use_selection=False,
            use_animation=False,
            use_mesh_modifiers=True,
            use_edges=False,
            use_smooth_groups=False,
            use_smooth_groups_bitflags=False,
            use_normals=False,
            use_uvs=False,
            use_materials=False,
            use_triangles=True,
            use_nurbs=False,
            use_vertex_groups=False,
            use_blen_objects=True,
            group_by_object=False,
            group_by_material=False,
            keep_vertex_order=False,
            global_scale=1,
            path_mode="AUTO",
        )
    except Exception as e:
        print(e)
        ShowMessageBox(".OBJ Export Error", f"{e}")
        return {"CANCELLED"}

    with open(filepath_obj, "r") as obj_file:
        shapes = []
        verts = []
        pruned = ""
        for line in obj_file.readlines():
            if line.startswith("o ") or line.startswith("v "):
                pruned += line
        for line in pruned.splitlines():
            if line.startswith("o "):
                if verts:
                    try:
                        shapes.append(verts)
                        verts = []
                        continue
                    except Exception as e:
                        ShowMessageBox(
                            "OBJ Parsing Error", f"{e}",
                        )
                        return {"CANCELLED"}
            elif line.startswith("v "):
                line = line.lstrip("v ")
                coords = line.split(" ")
                verts.append(coords)
            else:
                ShowMessageBox("???", "Why did this happen?")
                return {"CANCELLED"}
        if verts:
            shapes.append(verts)

    shape_param_template = (
        "                    ShapeParam_{}: !obj\n"
        "                      shape_type: !str32 polytope\n"
        "                      vertex_num: {}\n"
        "{}\n"
        "                      material: !str32 Metal\n"
        "                      sub_material: !str32 Metal_Heavy\n"
        "                      wall_code: !str32 NoClimb\n"
        "                      floor_code: !str32 None\n"
    )
    vertex_template = "                      vertex_{}: !vec3 [{}, {}, {}]"
    shapes_result = ""
    for i, shape in enumerate(shapes):
        shapes_result += shape_param_template.format(
            i,
            len(shape),
            "\n".join(
                [
                    vertex_template.format(o, vert[0], vert[1], vert[2])
                    for o, vert in enumerate(shape)
                ]
            ),
        )
    output = content.format(len(shapes), shapes_result.rstrip("\n"))
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
    os.remove(filepath_obj)
    return {"FINISHED"}


class ImportPhysics(Operator, ExportHelper):
    """Import BotW Physics File"""

    bl_idname = "import_physics.yml"
    bl_label = "Import BotW physics file (.yml)"
    filename_ext = ".yml"

    filter_glob: StringProperty(default="*.yml", options={"HIDDEN"})

    def execute(self, context):
        return parse_physics(context, self.filepath)


class ExportPhysics(Operator, ExportHelper):
    """Export BotW Physics File"""

    bl_idname = "export_physics.yml"
    bl_label = "Export BotW physics file (.physics.yml)"
    filename_ext = ".physics.yml"

    filter_glob: StringProperty(default="*.physics.yml", options={"HIDDEN"})

    def execute(self, context):
        return generate_physics(context, self.filepath)


class ExportPhysicsBinary(Operator, ExportHelper):
    """Export BotW Binary Physics File"""

    bl_idname = "export_bphysics.bphysics"
    bl_label = "Export BotW binary physics file (.bphysics)"
    filename_ext = ".bphysics"

    filter_glob: StringProperty(default="*.bphysics", options={"HIDDEN"})

    def execute(self, context):
        return generate_physics(context, self.filepath, binary=True)


def MenuImport(self, context):
    self.layout.operator(ImportPhysics.bl_idname, text="BotW Physics File (.yml)")


def MenuExport(self, context):
    self.layout.operator(
        ExportPhysics.bl_idname, text="BotW Physics File (.physics.yml)"
    )
    self.layout.operator(
        ExportPhysicsBinary.bl_idname, text="BotW Binary Physics File (.bphysics)"
    )


def register():
    bpy.utils.register_class(ImportPhysics)
    bpy.utils.register_class(ExportPhysics)
    bpy.utils.register_class(ExportPhysicsBinary)
    bpy.types.TOPBAR_MT_file_import.append(MenuImport)
    bpy.types.TOPBAR_MT_file_export.append(MenuExport)


def unregister():
    bpy.utils.unregister_class(ImportPhysics)
    bpy.utils.unregister_class(ExportPhysics)
    bpy.utils.unregister_class(ExportPhysicsBinary)
    bpy.types.TOPBAR_MT_file_import.remove(MenuImport)
    bpy.types.TOPBAR_MT_file_export.remove(MenuExport)
