# Actor collisions
Some actors from the game have their collision defined in their `.bphysics` file. This allows us modders to take advantage of this functionality by defining our own collision.
## How does it work
The collision is defined by defining **shapes**. Those are defined by a certain number of **vertices**.\
The structure looks roughly like this: [Link to a whole sample file](samples/FldObj_RuinGuardian_A_01_Dynamic.physics.yml)
```yml
RigidContactInfo: !list
    objects:
        3387849585: !obj {contact_point_info_num: 0, collision_info_num: 1}
        CollisionInfo_0: !obj {name: !str32 Body, type: !str32 Body}
    lists: {}
RigidBodySet: !list
  objects: {}
  lists:
    RigidBodySet_0: !list
      objects:
        4288596824: !obj {set_name: !str32 Body, type: !str32 from_shape_type, num: 1}
      lists:
        RigidBody_0: !list
          objects:
            948250248: !obj
              rigid_body_name: !str64 Body
              motion_type: !str32 Fixed
              collision_info: !str32 Body
              shape_num: 1
            ShapeParam_0: !obj
              shape_type: !str32 polytope
              vertex_num: 8
              vertex_0: !vec3 [-30.7815, 2.0, 30.7815]
              vertex_1: !vec3 [30.7815, 2.0, 30.7815]
              vertex_2: !vec3 [-30.7815, 2.0, -30.7815]
              vertex_3: !vec3 [30.7815, 2.0, -30.7815]
              vertex_4: !vec3 [-30.7815, 0.179612, 30.7815]
              vertex_5: !vec3 [30.7815, 0.179612, 30.7815]
              vertex_6: !vec3 [-30.7815, 0.179612, -30.7815]
              vertex_7: !vec3 [30.7815, 0.179612, -30.7815]
              material: !str32 Stone
              sub_material: !str32 Stone_DgnHeavy
              wall_code: !str32 NoClimb
              floor_code: !str32 None
          lists: {}
```
The section we are the most interested in:
```yml
RigidBody_0: !list
  objects:
    948250248: !obj
      rigid_body_name: !str64 Body
      motion_type: !str32 Fixed
      collision_info: !str32 Body
      shape_num: 1
    ShapeParam_0: !obj
      shape_type: !str32 polytope
      vertex_num: 8
      vertex_0: !vec3 [-30.7815, 2.0, 30.7815]
      vertex_1: !vec3 [30.7815, 2.0, 30.7815]
      vertex_2: !vec3 [-30.7815, 2.0, -30.7815]
      vertex_3: !vec3 [30.7815, 2.0, -30.7815]
      vertex_4: !vec3 [-30.7815, 0.179612, 30.7815]
      vertex_5: !vec3 [30.7815, 0.179612, 30.7815]
      vertex_6: !vec3 [-30.7815, 0.179612, -30.7815]
      vertex_7: !vec3 [30.7815, 0.179612, -30.7815]
      material: !str32 Stone
      sub_material: !str32 Stone_DgnHeavy
      wall_code: !str32 NoClimb
      floor_code: !str32 None
```
---
There are quite a few things to note:

| Parameter       |        Description        | Values                             |
| --------------- | :-----------------------: | ---------------------------------- |
| rigid_body_name |      Rigid body name      | String                             |
| motion_type     |    Actor movement type    | [String](params/motion_types.yml)  |
| shape_num       |     number of shapes      | Integer (more info below)          |
| shape_type      |     basic shape type      | [String](params/shape_types.yml)   |
| vertex_num      |    number of vertices     | Integer (more info below)          |
| vertex_x        |    vertex coordinates     | Vector3 (more info below)          |
| material        |   material of the shape   | [String](params/materials.yml)     |
| sub_material    | sub material of the shape | [String](params/sub_materials.yml) |
| wall_code       |  wall code of the shape   | [String](params/wall_codes.yml)    |
| floor_code      |  floor code of the shape  | [String](params/floor_codes.yml)   |

for more parameters click [here](params)
___
## Shapes
Lets take a sample model from the game. A ruined Guardian with collision side-by-side:\
<img src=res/only-model.png width="400"><img src=res/only-collision.png width="400">\
___
Considering the collision is defined by **vertices** alone (which means you can consider the vertices all interconnected), this concrete shape must be sliced to two to avoid wrongly connected vertices in in-game collision.\
<img src=res/collision-error.png width="400">
___
## Shapes and vertices
Each `vertex_{}` point defines a single point in a 3-dimensional space.

I wrote a [Blender addon](blenderaddon-botw-physics-generator.zip) for exporting objects as separate shapes. For simple shapes (cubes, stairs), split them yourself for better accuracy.

For more complex ones, use [V-HACD Blender addon](https://github.com/andyp123/blender_vhacd). Here's an example of generated convex geometry:

<img src=res/example.png width="400">

___
### For now it's not recommended to change `shape_type` unless you know what you're doing.