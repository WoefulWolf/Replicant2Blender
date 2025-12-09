from itertools import chain
import numpy as np
import bpy, time
from dataclasses import dataclass, field
from bpy.types import Collection, Material, Mesh, Object

from ..classes.mesh_data import BonesBuffer, ColorsBuffer, NormalsBuffer, PositionsBuffer, UVsBuffer, WeightsBuffer
from ..classes.common import VertexBufferType
from ..classes.mesh_head import MaterialGroup, tpGxMeshHead
from ..classes.pack import Pack
from ..util import get_collection_objects, log

def export(operator):
    filepath: str = operator.filepath
    scene = bpy.context.scene
    # Get the original mesh pack path
    original_pack_path = scene.replicant_original_mesh_pack

    if not original_pack_path:
        operator.report({'ERROR'}, "No original mesh PACK file specified")
        return {'CANCELLED'}

    # Get collections marked for export
    collections_to_export = [col for col in scene.collection.children if any(obj.type == 'MESH' for obj in col.objects) and col.replicant_export]

    if not collections_to_export:
        operator.report({'ERROR'}, "No collections selected for export")
        return {'CANCELLED'}

    start = time.perf_counter()
    log.i(f"Opening original PACK: {original_pack_path}")
    pack = Pack.from_file(original_pack_path)
    for file_data in pack.files_data:
        file = pack.files[file_data.file_index]
        mesh_head: tpGxMeshHead = file.content.asset_data
        mesh_data = file_data.mesh_data
        if mesh_data is None:
            continue

        b_objs = get_collection_objects(collections_to_export, file.name)
        log.d(f"Found {len(b_objs)} objects to export to {file.name}")

        # Collect all necessary data
        materials: list[str] = []
        for b_obj in b_objs:
            for material in b_obj.data.materials:
                materials.append(material.name)
        log.d(f"Found {len(materials)} materials used.")

        material_groups = []
        
        log.d("Generating mesh data...")
        for i, b_obj in enumerate(b_objs):
            log.d(f"\t{b_obj.name}...")
            vertex_data = VertexData(b_obj)
            index_data, material_group = get_loops_and_material_groups(b_obj, i, materials)
            if index_data is None or material_group is None:
                log.e(f"Failed to get index/material group data for {b_obj.name}")
                operator.report({'ERROR'}, f"Failed to get index/material group data for {b_obj.name}")
                return {'CANCELLED'}
            material_groups.extend(material_group)

            mesh_head.objects[i].vertex_count = len(vertex_data.positions)
            mesh_head.objects[i].index_count = len(index_data) * 3

            mesh_data.object_indices[i].indices = index_data

            position_buffers: list[PositionsBuffer] = mesh_data.object_vertex_buffers[i].get_buffers_of_type(VertexBufferType.POSITION)
            if len(position_buffers) != 0:
                position_buffers[0].positions = vertex_data.positions
            else:
                log.w(f"{file.name}'s object {i} has no vertex position buffer, skipping!")
            normals_buffers: list[NormalsBuffer] = mesh_data.object_vertex_buffers[i].get_buffers_of_type(VertexBufferType.NORMAL)
            if len(normals_buffers) != 0:
                normals_buffers[0].normals = vertex_data.normals
            else:
                log.w(f"{file.name}'s object {i} has no vertex normal buffer, skipping!")
            tangents_buffers: list[NormalsBuffer] = mesh_data.object_vertex_buffers[i].get_buffers_of_type(VertexBufferType.TANGENT)
            if len(tangents_buffers) != 0:
                tangents_buffers[0].tangents = vertex_data.tangents
            else:
                log.w(f"{file.name}'s object {i} has no vertex tangent buffer, skipping!")
            uvs_buffers: list[UVsBuffer] = mesh_data.object_vertex_buffers[i].get_buffers_of_type(VertexBufferType.UV)
            if len(uvs_buffers) > len(vertex_data.uv_maps):
                log.e(f"{b_obj.name} doesn't have enough UV maps! Export will very likely be broken! (Expected {len(uvs_buffers)} UV maps)")
            for j in range(len(uvs_buffers)):
                if j >= len(vertex_data.uv_maps):
                    break
                uvs_buffers[j].uvs = vertex_data.uv_maps[j]
            if len(uvs_buffers) == 0:
                log.w(f"{file.name}'s object {i} has no vertex UV buffer, skipping!")
            colors_buffers: list[ColorsBuffer] = mesh_data.object_vertex_buffers[i].get_buffers_of_type(VertexBufferType.COLOR)
            if len(colors_buffers) > len(vertex_data.vertex_colors):
                log.e(f"{b_obj.name} doesn't have enough vertex color layers! Export will very likely be broken! (Expected {len(colors_buffers)} vertex color layers)")
            for j in range(len(colors_buffers)):
                if j >= len(vertex_data.vertex_colors):
                    break
                colors_buffers[j].colors = vertex_data.vertex_colors[j]
            if len(colors_buffers) == 0:
                log.w(f"{file.name}'s object {i} has no vertex colour buffer, skipping!")
            bones_buffers: list[BonesBuffer] = mesh_data.object_vertex_buffers[i].get_buffers_of_type(VertexBufferType.BONES)
            if len(bones_buffers) != 0:
                bones_buffers[0].bones = vertex_data.bones
            else:
                log.w(f"{file.name}'s object {i} has no vertex bones buffer, skipping!")
            weights_buffers: list[WeightsBuffer] = mesh_data.object_vertex_buffers[i].get_buffers_of_type(VertexBufferType.WEIGHTS)
            if len(weights_buffers) != 0:
                weights_buffers[0].weights = vertex_data.weights
            else:
                log.w(f"{file.name}'s object {i} has no vertex weights buffer, skipping!")

        mesh_head.material_groups = material_groups

    gen_end = time.perf_counter()
    log.d(f"Finished generating data in {gen_end - start:.4f} seconds.")
    log.d("Writing new PACK file...")
    write_start = time.perf_counter()
    pack.to_file(filepath)
    end = time.perf_counter()
    log.d(f"Finished writing {filepath} in {end - write_start:.4f} seconds.")
    log.i(f"Total export time: {end - start:.4f} seconds!")
    return {'FINISHED'}

@dataclass
class VertexData:
    positions: list[tuple[float, float, float]] = field(default_factory=list)
    normals: list[tuple[float, float, float]] = field(default_factory=list)
    tangents: list[tuple[float, float, float]] = field(default_factory=list)
    uv_maps: list[list[tuple[float, float]]] = field(default_factory=list)
    vertex_colors: list[list[tuple[float, float, float, float]]] = field(default_factory=list)
    bones: list[list[int]] = field(default_factory=list)
    weights: list[list[float]] = field(default_factory=list)

    def __init__(self, obj):
        if obj.type != 'MESH':
            log.e("Object is not a mesh")
            return

        mesh = obj.data

        # Ensure mesh has tangents calculated
        mesh.calc_tangents()

        # Get UV layers
        uv_layers = mesh.uv_layers

        # Get vertex color layers
        color_layers = mesh.vertex_colors

        # Initialize lists
        self.positions = []
        self.normals = []
        self.tangents = []
        self.uv_maps = [ [] for _ in range(len(uv_layers)) ]
        self.vertex_colors = [ [] for _ in range(len(color_layers)) ]
        self.bones = []
        self.weights = []

        # Dictionary to store data per vertex index
        vertex_data = {}

        # Iterate through loops to get the data
        for poly in mesh.polygons:
            for loop_index in poly.loop_indices:
                loop = mesh.loops[loop_index]
                vert_index = loop.vertex_index

                # Skip if we already have data for this vertex
                if vert_index in vertex_data:
                    continue

                vert = mesh.vertices[vert_index]

                vertex_data[vert_index] = {
                    'position': tuple(vert.co),
                    'normal': tuple(loop.normal),
                    'tangent': tuple(loop.tangent),
                    'bitangent_sign': loop.bitangent_sign,
                    'uv_maps': {},
                    'vertex_colors': {},
                    'bones': [],
                    'weights': []
                }

                # Get UV coordinates for all UV maps
                for uv_layer in uv_layers:
                    uv_coord = list(uv_layer.data[loop_index].uv)
                    vertex_data[vert_index]['uv_maps'][uv_layer.name] = tuple(uv_coord)

                # Get vertex colors for all color layers
                for color_layer in color_layers:
                    color = color_layer.data[loop_index].color
                    vertex_data[vert_index]['vertex_colors'][color_layer.name] = tuple(color)

                # Get bone weights (from vertex groups)
                # Sort by bone index ascending and take top 4
                bone_weights = [(g.group, g.weight) for g in vert.groups]
                bone_weights.sort(key=lambda x: x[0])
                bone_weights = bone_weights[:4]  # Limit to 4 bones

                # Bones always have exactly 4 ints, pad with zeros
                vertex_bones = [0, 0, 0, 0]
                vertex_weights = []

                for i, (bone_idx, weight) in enumerate(bone_weights):
                    vertex_bones[i] = bone_idx
                    vertex_weights.append(weight)

                vertex_data[vert_index]['bones'] = vertex_bones
                vertex_data[vert_index]['weights'] = vertex_weights

        # Convert to sorted lists
        for vert_index in sorted(vertex_data.keys()):
            vert_dict = vertex_data[vert_index]
            self.positions.append(vert_dict['position'])
            self.normals.append(vert_dict['normal'])
            self.tangents.append(vert_dict['tangent'] + (vert_dict['bitangent_sign'],))

            for i, uv_coord in enumerate(vert_dict['uv_maps'].values()):
                self.uv_maps[i].append(uv_coord)

            for i, color in enumerate(vert_dict['vertex_colors'].values()):
                self.vertex_colors[i].append(color)

            self.bones.append(vert_dict['bones'])
            self.weights.append(vert_dict['weights'])

def get_loops_and_material_groups(obj: Object, obj_index: int, materials: list[str]) -> tuple[list[tuple[int, int, int]], list[MaterialGroup]] | tuple[None, None]:
    if obj.type != 'MESH':
        log.e("Object is not a mesh")
        return None

    mesh: Mesh = obj.data

    # Calculate loop triangles (automatically triangulates the mesh)
    mesh.calc_loop_triangles()

    # Group triangles by material index
    material_groups = {}

    for tri in mesh.loop_triangles:
        mat_index = tri.material_index
        if mat_index not in material_groups:
            material_groups[mat_index] = []

        # Get vertex indices for this triangle
        vertices = tuple(tri.vertices)
        material_groups[mat_index].append(vertices)

    # Initialize
    loops: list[tuple[int, int, int]] = []
    material_offsets: dict[str, tuple[int, int]] = {}

    current_index = 0

    # Sort by material index and add to loops in order
    for mat_index in sorted(material_groups.keys()):
        # Get material name
        if mat_index < len(obj.material_slots) and obj.material_slots[mat_index].material:
            mat_name = obj.material_slots[mat_index].material.name
        else:
            mat_name = f"Material_{mat_index}"

        triangles = material_groups[mat_index]
        loop_count = len(triangles)
        index_count = loop_count * 3

        # Store offset (start_index, index_count)
        material_offsets[mat_name] = (current_index, index_count)

        # Add loops
        loops.extend(triangles)

        current_index += index_count

    indices = list(chain.from_iterable(loops))

    material_groups = []
    for material, (start, count) in material_offsets.items():
        object_index = obj_index
        material_index = materials.index(material)
        index_start = start
        index_count = count
        group_indices = indices[start:start+count]
        coords = np.array([mesh.vertices[i].co for i in group_indices])
        bbox_min = tuple(coords.min(axis=0).tolist())
        bbox_max = tuple(coords.max(axis=0).tolist())
        material_groups.append(MaterialGroup(
            obj_index,
            material_index,
            index_start,
            index_count,
            bbox_min,
            bbox_max
        ))


    return loops, material_groups