import os
from bmesh.types import BMesh
from bpy.types import VertexGroup

from ..classes.mesh_asset import tpGxMeshAssetV2
from ..classes.asset_package import tpXonAssetHeader
from ..classes.mesh_data import ColorsBuffer
from ..classes.common import VertexBufferType
from ..classes.mesh_data import BonesBuffer, NormalsBuffer, PositionsBuffer, UVsBuffer, WeightsBuffer, tpGxMeshData
from ..classes.mesh_head import tpGxMeshHead
from ..classes.pack import Pack, PackFile
from ..util import log

from mathutils import Vector, Matrix
import bpy, bmesh, math

def construct_meshes(pack_path: str, pack: Pack):
    log.i("Generating Blender Objects...")

    pack_filename = os.path.basename(pack_path)
    pack_collection = bpy.data.collections.new(pack_filename)
    pack_collection.replicant_original_mesh_pack = pack_path
    pack_collection.replicant_export = True
    
    bpy.context.scene.collection.children.link(pack_collection)

    for i, file in enumerate(pack.files):
        if file.content is None or file.content.asset_type != "tpGxMeshHead":
            continue
        mesh_file = file

        log.i(f"Generating object {mesh_file.name}")
        mesh_collection = bpy.data.collections.new(mesh_file.name)
        pack_collection.children.link(mesh_collection)
        mesh_collection.replicant_export = True

        asset_header: tpXonAssetHeader = pack.asset_packages[0].content.asset_data
        mesh_asset: tpGxMeshAssetV2 = asset_header.assets[0].asset_content
        for mesh in mesh_asset.meshes:
            if mesh.name == mesh_file.name:
                mesh_collection.replicant_lod_distance = mesh.lod_distance
                break

        mesh_bxon = mesh_file.content
        mesh_head: tpGxMeshHead = mesh_bxon.asset_data

        # Create Armature + Bones
        if len(mesh_head.bone_poses) > 0:
            amt_name = f"{mesh_file.name}_armature"
            amt = bpy.data.armatures.new(amt_name)
            amt_obj = bpy.data.objects.new(amt_name, amt)
            mesh_collection.objects.link(amt_obj)
            bpy.context.view_layer.objects.active = amt_obj
            bpy.ops.object.mode_set(mode="EDIT")

            safe_bones: list[str] = []
            for k, bone in enumerate(mesh_head.bone_poses):
                transform = Matrix(bone.unknown_matrix_0)

                if (bone.unknown_index == -1):
                    head = transform @ Vector((0, 0, 0, 1))
                    tail = transform @ Vector((bone.length, 0, 0, 1))
                else:
                    head = Vector((0, 0, 0))
                    tail = Vector((0, 0.05, 0))
                newBone = amt.edit_bones.new(bone.name)
                newBone.head = [head.x, head.y, head.z]
                newBone.tail = [tail.x, tail.y, tail.z]
                #newBone.roll = 90
                #newBone.parent = amt.edit_bones[meshHead.bones[bone.parentBoneIndex].name] if bone.parentBoneIndex != -1 else None
                safe_bones.append(bone.name)
            
            for k, edit_bone in enumerate(amt.edit_bones):
                for bone in mesh_head.bones:
                    if bone.name == edit_bone.name and bone.parent_bone_index != -1:
                        parent_name = mesh_head.bones[bone.parent_bone_index].name
                        if parent_name in safe_bones:
                            edit_bone.parent = amt.edit_bones[parent_name]
                        break

            bpy.ops.object.mode_set(mode='POSE')
            for pose_bone in amt_obj.pose.bones:
                for bone in mesh_head.bone_poses:
                    if bone.name == pose_bone.name:
                        if bone.unknown_index != -1:
                            transformMat = Matrix(bone.unknown_matrix_0)
                            pose_bone.matrix_basis = transformMat @ pose_bone.matrix_basis
                        break
            bpy.context.view_layer.update()
            bpy.ops.pose.armature_apply()

            bpy.ops.object.mode_set(mode='OBJECT')
            amt_obj.rotation_euler = (math.radians(90),0,0)

        # Get mesh data for this file
        mesh_data: tpGxMeshData | None = None
        for file_data in pack.files_data:
            if file_data.file_index == i and file_data.mesh_data:
                mesh_data = file_data.mesh_data
                break

        if mesh_data is None:
            continue

        # Create objects
        for k in range(len(mesh_head.objects)):
            obj_name = mesh_file.name + str(k)

            b_mesh = bpy.data.meshes.new(obj_name)
            b_obj = bpy.data.objects.new(obj_name, b_mesh)

            # Removed in 4.1
            if bpy.app.version < (4, 1, 0):
                b_obj.data.use_auto_smooth = True

            vertex_buffers = mesh_data.object_vertex_buffers[k]
            index_buffer = mesh_data.object_indices[k]

            positions_buffer: PositionsBuffer = vertex_buffers.get_buffers_of_type(VertexBufferType.POSITION)[0]
            normals_buffer: NormalsBuffer = vertex_buffers.get_buffers_of_type(VertexBufferType.NORMAL)[0]

            mesh_collection.objects.link(b_obj)
            b_mesh.from_pydata(positions_buffer.positions, [], index_buffer.indices)
            b_mesh.normals_split_custom_set_from_vertices(normals_buffer.normals)
            b_mesh.update(calc_edges=True)

            # Create vertex groups for bones
            for bone in mesh_head.bone_poses:
                b_obj.vertex_groups.new(name=bone.name)

            # Assign colors
            colors_buffers: list[ColorsBuffer] = vertex_buffers.get_buffers_of_type(VertexBufferType.COLOR)
            for m, color_buffer in enumerate(colors_buffers):
                color_layer_name = f"Color{m}"
                if color_layer_name in b_mesh.color_attributes:
                    color_layer = b_mesh.color_attributes[color_layer_name]
                else:
                    color_layer = b_mesh.color_attributes.new(
                        name=color_layer_name,
                        type='BYTE_COLOR',
                        domain='CORNER'
                    )
                colors = color_layer.data
                for loop in b_mesh.loops:
                    index = loop.vertex_index
                    colors[loop.index].color = (color_buffer.colors[index])


            # Assign weights
            used_vertex_groups = set()
            weights_buffers: list[WeightsBuffer] = vertex_buffers.get_buffers_of_type(VertexBufferType.WEIGHTS)
            bones_buffers: list[BonesBuffer] = vertex_buffers.get_buffers_of_type(VertexBufferType.BONES)
            if len(weights_buffers) > 0 and len(bones_buffers) > 0:
                weights_buffer = weights_buffers[0]
                bones_buffer = bones_buffers[0]

                for m, weight in enumerate(weights_buffer.weights):
                    # Filter out any floating point issues
                    for n, val in enumerate(weight):
                        if (val < 0.000001):
                            weight[n] = 0
                    weight = [float(n)/sum(weight) for n in weight]

                    vertex_groups: list[VertexGroup] = []
                    bone_indices: list[int] = bones_buffer.bones[m]
                    vertex_weights: list[float] = []
                    if (len(weight) == 4):
                        vertex_weights = [weight[0], weight[1], weight[2], weight[3]]
                        vertex_groups = [b_obj.vertex_groups[bone_indices[0]], b_obj.vertex_groups[bone_indices[1]], b_obj.vertex_groups[bone_indices[2]], b_obj.vertex_groups[bone_indices[3]]]
                    elif (len(weight) == 3):
                        vertex_weights = [weight[0], weight[1], weight[2]]
                        vertex_groups = [b_obj.vertex_groups[bone_indices[0]], b_obj.vertex_groups[bone_indices[1]], b_obj.vertex_groups[bone_indices[2]]]

                    for n, group in enumerate(vertex_groups):
                        if vertex_weights[n] > 0:
                            group.add([m], vertex_weights[n], "REPLACE")
                            used_vertex_groups.add(group)
            elif len(bones_buffers) > 0:
                bones_buffer = bones_buffers[0]
                for m, bone_indices in enumerate(bones_buffer.bones):
                    # No weights buffer, assume 100% weight for the first bone
                    first_bone_group = b_obj.vertex_groups[bone_indices[0]]
                    first_bone_group.add([m], 1.0, "REPLACE")
                    used_vertex_groups.add(first_bone_group)

            unused_vertex_groups = set(b_obj.vertex_groups).difference(used_vertex_groups)
            for vg in unused_vertex_groups:
                b_obj.vertex_groups.remove(vg)

            # Assign UVs
            uv_buffers: list[UVsBuffer] = vertex_buffers.get_buffers_of_type(VertexBufferType.UV)

            b_mesh = bmesh.new()
            b_mesh.from_mesh(b_obj.data)

            uv_layers = []
            for m, uv_buffer in enumerate(uv_buffers):
                if len(uv_buffer.uvs) > 0:
                    uv_layers.append(b_mesh.loops.layers.uv.new("UVMap" + str(m)))

            if len(uv_layers) > 0:
                for face in b_mesh.faces:
                    face.material_index = 0
                    for l in face.loops:
                        for m, uv_layer in enumerate(uv_layers):
                            if len(uv_buffers[m].uvs) > 0:
                                luv = l[uv_layer]
                                idx = l.vert.index
                                luv.uv = Vector(uv_buffers[m].uvs[idx])

            # Create and assign materials
            # Use ensure_lookup_table to allow direct indexing of faces
            b_mesh.faces.ensure_lookup_table()

            for material_group_index, material_group in enumerate(mesh_head.material_groups):
                if material_group.object_index != k:
                    continue
                material = mesh_head.materials[material_group.material_index]
                b_material = bpy.data.materials.get(material.name.lower())
                if b_material is None:
                    b_material = bpy.data.materials.new(name=material.name.lower())

                if b_material.name not in b_obj.data.materials:
                    b_obj.data.materials.append(b_material)

                material_index = b_obj.data.materials.find(b_material.name)
                if material_index == -1:
                    log.e(f"Could not find material {b_material.name} in {b_obj.name}!")
                    continue

                for import_path in pack.imports:
                    if b_material.name in import_path.path:
                        b_material.replicant_pack_path = import_path.path
                        break

                # Directly index faces by their position in the bmesh
                face_start = material_group.index_start // 3
                face_end = (material_group.index_start + material_group.index_count) // 3
                for face_idx in range(face_start, face_end):
                    b_mesh.faces[face_idx].material_index = material_index

            b_mesh.to_mesh(b_obj.data)
            b_mesh.free()
            b_obj.rotation_euler = (math.radians(90),0,0)

            # Parent object to armature
            if len(mesh_head.bone_poses) > 0:
                bpy.context.view_layer.objects.active = amt_obj
                b_obj.select_set(True)
                amt_obj.select_set(True)
                bpy.ops.object.parent_set(type="ARMATURE")
                b_obj.select_set(False)
                amt_obj.select_set(False)
    log.i("Blender object generation complete.")