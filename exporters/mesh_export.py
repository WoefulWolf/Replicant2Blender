from itertools import chain
import os
import numpy as np
import bpy, time
from dataclasses import dataclass, field
from bpy.types import Collection, Material, Mesh, Object

from ..classes.mesh_asset import ImportedMaterial, tpGxMeshAssetV2
from ..classes.mesh_asset import MeshMaterial as MeshAssetMaterial
from ..classes.mesh_asset import Mesh as MeshAssetMesh
from ..classes.mesh_data import BonesBuffer, ColorsBuffer, NormalsBuffer, PositionsBuffer, UVsBuffer, WeightsBuffer
from ..classes.common import Import, VertexBufferType
from ..classes.mesh_head import MaterialGroup, tpGxMeshHead
from ..classes.mesh_head import Material as MeshHeadMaterial
from ..classes.pack import Pack, PackFile
from ..classes.asset_package import tpXonAssetHeader
from ..util import fnv1, get_collection_objects, get_export_collections, log

def export(operator):
    directory: str = operator.directory
    scene = bpy.context.scene

    export_collections = get_export_collections()
    if not export_collections:
        operator.report({'ERROR'}, "No collections selected for export")
        return {'CANCELLED'}

    start = time.perf_counter()

    packs: list[tuple[str, Pack]] = []

    for root, collections in export_collections.items():
        # Get the original mesh pack path
        original_pack_path = root.replicant_original_mesh_pack

        if not original_pack_path:
            operator.report({'ERROR'}, "No original mesh PACK file specified")
            return {'CANCELLED'}

        filepath = os.path.join(directory, root.name)

        log.i(f"Opening original PACK: {original_pack_path}")

        pack = Pack.from_file(original_pack_path)
        pack.imports.clear()

        asset_header: tpXonAssetHeader = pack.asset_packages[0].content.asset_data
        mesh_asset: tpGxMeshAssetV2 = asset_header.assets[0].asset_content
        mesh_asset.meshes.clear()
        mesh_asset.imported_materials.clear()

        for file_data in pack.files_data:
            file: PackFile = pack.files[file_data.file_index]
            mesh_head: tpGxMeshHead = file.content.asset_data
            mesh_data = file_data.mesh_data
            if mesh_data is None:
                continue

            b_objs = get_collection_objects(collections, file.name)
            log.d(f"Found {len(b_objs)} objects to export to {file.name}")

            update_mesh_asset(mesh_asset, file.name, b_objs, collections)

            # Collect all necessary data
            mesh_head.materials.clear()
            materials: list[str] = []
            for b_obj in b_objs:
                for material in b_obj.data.materials:
                    if material.name in materials:
                        continue
                    materials.append(material.name)
                    mesh_head.materials.append(MeshHeadMaterial(
                        name=material.name,
                        unknown_uint32=4,
                        unknown_byte=0
                    ))
            log.d(f"Found {len(materials)} materials used.")

            material_groups = []
            
            log.d("Generating mesh data...")
            for i, b_obj in enumerate(b_objs):
                log.d(f"\t{b_obj.name}...")
                update_imports(pack, b_obj)

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

        packs.append((filepath, pack))
        log.d(f"Generated mesh data for {root.name}")

    gen_end = time.perf_counter()
    log.d(f"Finished generating data in {gen_end - start:.4f} seconds.")
    log.d("Writing new PACK file(s)...")
    write_start = time.perf_counter()
    for filepath, pack in packs:
        pack.to_file(filepath)
        log.d(f"Finished writing {filepath}...")
    end = time.perf_counter()
    log.d(f"Finished writing {len(packs)} PACK(s) in {end - write_start:.4f} seconds.")
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

        # Get armature for bone index mapping
        armature = None
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE':
                armature = modifier.object
                break

        # Build vertex group name to bone index mapping
        vg_to_bone_idx = {}
        if armature:
            bone_names = {bone.name: i for i, bone in enumerate(armature.data.bones)}
            for vg in obj.vertex_groups:
                if vg.name in bone_names:
                    vg_to_bone_idx[vg.index] = bone_names[vg.name]

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
                # Map vertex group indices to armature bone indices
                bone_weights: list[tuple[int, float]] = []
                for g in vert.groups:
                    if g.group in vg_to_bone_idx:
                        bone_idx = vg_to_bone_idx[g.group]
                        bone_weights.append((bone_idx, g.weight))

                # Sort by weight descending and take top 4 strongest
                bone_weights.sort(key=lambda x: x[1], reverse=True)
                bone_weights = bone_weights[:4]  # Limit to 4 bones

                # Bones always have exactly 4 ints, pad with zeros
                vertex_bones: list[int] = [0, 0, 0, 0]
                vertex_weights: list[float] = []

                for i, (bone_idx, weight) in enumerate(bone_weights):
                    vertex_bones[i] = bone_idx
                    vertex_weights.append(weight)

                vertex_data[vert_index]['bones'] = vertex_bones
                vertex_data[vert_index]['weights'] = [float(i)/sum(vertex_weights) for i in vertex_weights] # Normalize weights

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

def update_imports(pack: Pack, obj: Object):
    asset_header: tpXonAssetHeader = pack.asset_packages[0].content.asset_data
    pack_import_paths = [p.path for p in pack.imports]
    asset_import_paths = [p.path for p in asset_header.imports]
    for material in obj.data.materials:
        if material.replicant_pack_path != "":
            new_import = Import(path=material.replicant_pack_path,)
            if material.replicant_pack_path not in asset_import_paths:
                asset_header.imports.append(new_import)
            if material.replicant_pack_path not in pack_import_paths:
                pack.imports.append(new_import)
            
def update_mesh_asset(mesh_asset: tpGxMeshAssetV2, name: str, objects: list[Object], collections: list[Collection]):
    imported_materials = set([(m.name, m.path) for m in mesh_asset.imported_materials])

    mesh = MeshAssetMesh(name)
    added_materials = set()
    for obj in objects:
        for mat in obj.data.materials:
            if mat.name not in added_materials:
                mesh.materials.append(MeshAssetMaterial(mat.name))
                added_materials.add(mat.name)
            if (mat.name, mat.replicant_pack_path) in imported_materials:
                continue
            mesh_asset.imported_materials.append(ImportedMaterial(
                mat.name,
                mat.replicant_pack_path
            ))
            imported_materials.add((mat.name, mat.replicant_pack_path))
    for col in collections:
        if name == col.name:
            mesh.lod_distance = col.replicant_lod_distance
            break
    mesh_asset.meshes.append(mesh)
    return