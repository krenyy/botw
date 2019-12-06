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
    "name": "Physics Generator",
    "author": "kreny",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 7),
    "location": "",
    "warning": "",
    "category": "Breath of the Wild",
}

import os
import subprocess
from math import radians

import bpy
import mathutils
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
    try:
        os.remove(filepath_obj)
    except Exception as e:
        print(e)
    return {"FINISHED"}


def generate_physics(context, filepath, vhacd, remove_hulls_after_export, binary=False):
    scene = bpy.context.scene

    if vhacd:
        try:
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.vhacd('EXEC_DEFAULT')
        except Exception as e:
            ShowMessageBox("V-HACD Error", f"{e}")
            return {"CANCELLED"}
    else:
        objects = [obj for obj in scene.objects if "_hull_" in obj.name]
        if not objects:
            ShowMessageBox("No convex hulls found", "You probably didn't generate your collisions, dummy.")
            return {"CANCELLED"}

    if binary:
        filepath_yml = filepath.replace(".bphysics", ".physics.yml")
        filepath_bin = filepath
    else:
        filepath_yml = filepath
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    default_file = directory + "/default.yml"
    with open(default_file, "r") as f:
        content = f.read()

    rigid_body_template = (
        "                RigidBody_{0}: !list\n"
        "                  objects:\n"
        "                    948250248: !obj\n"
        "                      rigid_body_name: !str64 {1}\n"
        "                      mass: 10000.0\n"
        "                      inertia: !vec3 [6666.67, 6666.67, 6666.67]\n"
        "                      linear_damping: 0.0\n"
        "                      angular_damping: 0.05\n"
        "                      max_impulse: 10000.0\n"
        "                      col_impulse_scale: 1.0\n"
        "                      ignore_normal_for_impulse: false\n"
        "                      volume: 8.0\n"
        "                      toi: true\n"
        "                      center_of_mass: !vec3 [0.0, 1.0, 0.0]\n"
        "                      max_linear_velocity: 200.0\n"
        "                      bounding_center: !vec3 [0.0, 1.0, 0.0]\n"
        "                      bounding_extents: !vec3 [2.0, 2.0, 2.0]\n"
        "                      max_angular_velocity_rad: 198.968\n"
        "                      motion_type: !str32 Fixed\n"
        "                      contact_point_info: !str32 Body\n"
        "                      collision_info: !str32 Body\n"
        "                      bone: !str64 \n"
        "                      water_buoyancy_scale: 1.0\n"
        "                      water_flow_effective_rate: 1.0\n"
        "                      layer: !str32 EntityGroundObject\n"
        "                      no_hit_ground: false\n"
        "                      no_hit_water: false\n"
        "                      groundhit: !str32 HitAll\n"
        "                      use_ground_hit_type_mask: false\n"
        "                      no_char_standing_on: false\n"
        "                      navmesh: !str32 STATIC_WALKABLE_AND_CUTTING\n"
        "                      navmesh_sub_material: !str32 \n"
        "                      link_matrix: ''\n"
        "                      magne_mass_scaling_factor: 1.0\n"
        "                      always_character_mass_scaling: false\n"
        "                      shape_num: {2}\n"
        "{3}\n"
        "                  lists: {{}}"
    )

    shape_param_template = (
        "                    ShapeParam_{}: !obj #{}\n"
        "                      shape_type: !str32 polytope\n"
        "                      vertex_num: {}\n"
        "{}\n"
        "                      material: !str32 Metal\n"
        "                      sub_material: !str32 Metal_Heavy\n"
        "                      wall_code: !str32 NoClimb\n"
        "                      floor_code: !str32 None\n"
    )

    vertex_template = "                      vertex_{}: !vec3 [{}, {}, {}]"

    result = ""

    rigid_bodies = ""

    non_hull_objects = [obj for obj in scene.objects if not ("_hull_" in obj.name)]
    non_hull_index = 0
    hulls = []
    for obj in non_hull_objects:
        if obj.type == "MESH":
            shape_hull_index = 0
            shapes = ""
            for shape_hull in set(scene.objects) - set(non_hull_objects):
                if not (shape_hull.name.split("_hull_")[0] == obj.name): continue
                hulls.append(shape_hull)
                mtx = mathutils.Matrix.Rotation(radians(-90.0), 4, 'X') @ shape_hull.matrix_world
                verts = [mtx@v.co for v in shape_hull.data.vertices]
                shapes += shape_param_template.format(
                    shape_hull_index,
                    shape_hull.name,
                    len(verts),
                    "\n".join(
                        [
                            vertex_template.format(o, co.x, co.y, co.z)
                            for o, co in enumerate(verts)
                        ]
                    ),
                )
                shape_hull_index += 1
            rigid_bodies += rigid_body_template.format(non_hull_index, obj.name, shape_hull_index, shapes)
            non_hull_index += 1
    output = content.format(non_hull_index, rigid_bodies.rstrip("\n"))
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
    if vhacd and remove_hulls_after_export:
        bpy.ops.object.select_all(action='DESELECT')
        for hull in hulls:
            hull.select_set(True)
        bpy.ops.object.delete()
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

    vhacd: BoolProperty(
        name='Use V-HACD',
        description='Auto-generate collision using V-HACD (Disable if generated manually)',
        default=True
    )

    remove_hulls_after_export: BoolProperty(
        name="Remove hulls after export",
        description= "Remove convex hulls generated by V-HACD after exporting the physics file (doesn't matter if you don't use V-HACD)",
        default=True
    )

    def execute(self, context):
        return generate_physics(context, self.filepath, vhacd=self.vhacd, remove_hulls_after_export=self.remove_hulls_after_export)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='Additional options:')
        col.prop(self, 'vhacd')
        col.prop(self, 'remove_hulls_after_export')


class ExportPhysicsBinary(Operator, ExportHelper):
    """Export BotW Binary Physics File"""

    bl_idname = "export_bphysics.bphysics"
    bl_label = "Export BotW binary physics file (.bphysics)"
    filename_ext = ".bphysics"

    filter_glob: StringProperty(default="*.bphysics", options={"HIDDEN"})

    vhacd: BoolProperty(
        name='Use V-HACD',
        description='Auto-generate collision using V-HACD (Disable if generated manually)',
        default=True
    )

    remove_hulls_after_export: BoolProperty(
        name="Remove hulls after export",
        description= "Remove convex hulls generated by V-HACD after exporting the physics file (doesn't matter if you don't use V-HACD)",
        default=True
    )

    def execute(self, context):
        return generate_physics(context, self.filepath, binary=True, vhacd=self.vhacd, remove_hulls_after_export=self.remove_hulls_after_export)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='Additional options:')
        col.prop(self, 'vhacd')
        col.prop(self, 'remove_hulls_after_export')


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
