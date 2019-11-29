import bpy

scene = bpy.context.scene

objs = [obj for obj in scene.objects]

output = ""

for i, obj in enumerate(objs):
    output += f"ShapeParam_{i}: !obj # {obj.name} <- Remove this once done editing. (WITH THE HASHTAG)\n"
    output += "  shape_type: !str32 polytope\n"
    output += f"  vertex_num: {len(obj.data.vertices)}\n"
    for i, vertex in enumerate(obj.data.vertices):
        output += f"  vertex_{i}: !vec3 [{vertex.co.x}, {vertex.co.y}, {vertex.co.z}]\n"
    output += "  material: !str32 Stone\n"
    output += "  sub_material: !str32 Stone_DgnHeavy\n"
    output += "  wall_code: !str32 NoClimb\n"
    output += "  floor_code: !str32 None\n"

print(output)
