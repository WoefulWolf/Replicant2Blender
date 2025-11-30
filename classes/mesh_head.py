import struct
from dataclasses import dataclass
from typing import BinaryIO
from io import BytesIO

from .common import VertexBufferType, read_string, align_relative, DataOffset


@dataclass
class Bone:
    name: str
    parent_bone_index: int
    rotation: tuple[float, float, float, float]
    scale: tuple[float, float, float]
    position: tuple[float, float, float]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Bone':
        name_start_offset = stream.tell()
        offset_to_name, parent_bone_index = struct.unpack('<Ii', stream.read(8))

        # Read rotation quaternion
        rotation = struct.unpack('<ffff', stream.read(16))

        # Read scale
        scale = struct.unpack('<fff', stream.read(12))

        # Read position
        position = struct.unpack('<fff', stream.read(12))

        # Read name
        return_pos = stream.tell()
        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        return cls(
            name=name,
            parent_bone_index=parent_bone_index,
            rotation=rotation,
            scale=scale,
            position=position
        )


@dataclass
class BonePose:
    name: str
    unknown_index: int
    length: float
    unknown_matrix_0: list[list[float]]  # 16 floats
    unknown_matrix_1: list[list[float]]  # 16 floats

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'BonePose':
        name_start_offset = stream.tell()
        offset_to_name, unknown_index, length = struct.unpack('<Iif', stream.read(12))

        # Read matrices
        data = list(struct.unpack('<16f', stream.read(64)))
        unknown_matrix_0 = [data[i:i+4] for i in range(0, 16, 4)]
        data = list(struct.unpack('<16f', stream.read(64)))
        unknown_matrix_1 = [data[i:i+4] for i in range(0, 16, 4)]

        # Read name
        return_pos = stream.tell()
        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        return cls(
            name=name,
            unknown_index=unknown_index,
            length=length,
            unknown_matrix_0=unknown_matrix_0,
            unknown_matrix_1=unknown_matrix_1
        )


@dataclass
class VertexBuffer:
    vertex_buffer_offset: int
    unknown_uint32_1: int
    vertex_buffer_flag: int
    vertex_buffer_size: int
    vertex_buffer_type: VertexBufferType

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'VertexBuffer':
        values = struct.unpack('<IIIIB', stream.read(17))
        align_relative(stream, 0, 8)

        return cls(
            vertex_buffer_offset=values[0],
            unknown_uint32_1=values[1],
            vertex_buffer_flag=values[2],
            vertex_buffer_size=values[3],
            vertex_buffer_type=values[4]
        )


@dataclass
class Object:
    indices_start_offset: int
    unknown_uint32_1: int
    unknown_uint32_2: int
    vertex_count: int
    index_count: int
    index_buffer_size: int
    unknown_uint32_6: int
    vertex_buffers: list[VertexBuffer]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Object':
        values = struct.unpack('<IIIIIII', stream.read(28))

        vertexBufferCount = struct.unpack('<I', stream.read(4))[0]
        vertexBuffersStartOffset = stream.tell()
        offsetToVertexBuffers = struct.unpack('<I', stream.read(4))[0]

        # Read vertex buffers
        return_pos = stream.tell()
        stream.seek(vertexBuffersStartOffset + offsetToVertexBuffers)

        vertexBuffers = []
        for _ in range(vertexBufferCount):
            vertexBuffers.append(VertexBuffer.from_stream(stream))

        stream.seek(return_pos)
        align_relative(stream, 0, 8)

        return cls(
            indices_start_offset=values[0],
            unknown_uint32_1=values[1],
            unknown_uint32_2=values[2],
            vertex_count=values[3],
            index_count=values[4],
            index_buffer_size=values[5],
            unknown_uint32_6=values[6],
            vertex_buffers=vertexBuffers
        )


@dataclass
class Material:
    name: str
    unknown_uint32: int
    unknown_byte: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Material':
        name_start_offset = stream.tell()
        offset_to_name = struct.unpack('<I', stream.read(4))[0]

        unknown_byte_start_offset = stream.tell()
        offset_to_byte, unknown_uint32 = struct.unpack('<II', stream.read(8))

        # Read name
        return_pos = stream.tell()
        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)

        # Read unknown byte
        stream.seek(unknown_byte_start_offset + offset_to_byte)
        unknown_byte = struct.unpack('<B', stream.read(1))[0]

        stream.seek(return_pos)

        return cls(
            name=name,
            unknown_uint32=unknown_uint32,
            unknown_byte=unknown_byte
        )


@dataclass
class MaterialGroup:
    object_index: int
    material_index: int
    index_start: int
    index_count: int
    bounding_box_coord1: tuple[float, float, float]
    bounding_box_coord2: tuple[float, float, float]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'MaterialGroup':
        values = struct.unpack('<IIII', stream.read(16))
        bbox1 = struct.unpack('<fff', stream.read(12))
        bbox2 = struct.unpack('<fff', stream.read(12))

        return cls(
            object_index=values[0],
            material_index=values[1],
            index_start=values[2],
            index_count=values[3],
            bounding_box_coord1=bbox1,
            bounding_box_coord2=bbox2
        )


@dataclass
class tpGxMeshHead:
    bounding_box_coord1: tuple[float, float, float]
    bounding_box_coord2: tuple[float, float, float]
    total_vertex_buffers_size: int
    vertex_buffers_offset: DataOffset
    total_index_buffers_size: int
    index_buffers_offset: DataOffset
    unknown_float: float
    bones: list[Bone]
    bone_poses: list[BonePose]
    objects: list[Object]
    materials: list[Material]
    material_groups: list[MaterialGroup]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'tpGxMeshHead':
        start_offset = stream.tell()

        # Parse bounding boxes
        bbox1 = struct.unpack('<fff', stream.read(12))
        bbox2 = struct.unpack('<fff', stream.read(12))

        # Parse header
        total_vertex_buffers_size = struct.unpack('<I', stream.read(4))[0]
        vertex_buffers_offset = DataOffset.from_stream(stream)
        total_index_buffers_size = struct.unpack('<I', stream.read(4))[0]
        index_buffers_offset = DataOffset.from_stream(stream)
        unknown_float = struct.unpack('<f', stream.read(4))[0]

        # Read counts and offsets
        bone_count = struct.unpack('<I', stream.read(4))[0]
        bones_start_offset = stream.tell()
        offset_to_bones = struct.unpack('<I', stream.read(4))[0]

        bone_pose_count = struct.unpack('<I', stream.read(4))[0]
        bone_poses_start_offset = stream.tell()
        offset_to_bone_poses = struct.unpack('<I', stream.read(4))[0]

        object_count = struct.unpack('<I', stream.read(4))[0]
        objects_start_offset = stream.tell()
        offset_to_objects = struct.unpack('<I', stream.read(4))[0]

        material_count = struct.unpack('<I', stream.read(4))[0]
        materials_start_offset = stream.tell()
        offset_to_materials = struct.unpack('<I', stream.read(4))[0]

        material_group_count = struct.unpack('<I', stream.read(4))[0]
        material_groups_start_offset = stream.tell()
        offset_to_material_groups = struct.unpack('<I', stream.read(4))[0]

        # Parse bones
        bones = []
        stream.seek(bones_start_offset + offset_to_bones)
        for _ in range(bone_count):
            bones.append(Bone.from_stream(stream))

        # Parse bone poses
        bone_poses = []
        stream.seek(bone_poses_start_offset + offset_to_bone_poses)
        for _ in range(bone_pose_count):
            bone_poses.append(BonePose.from_stream(stream))

        # Parse objects
        objects = []
        stream.seek(objects_start_offset + offset_to_objects)
        for _ in range(object_count):
            objects.append(Object.from_stream(stream))

        # Parse materials
        materials = []
        stream.seek(materials_start_offset + offset_to_materials)
        for _ in range(material_count):
            materials.append(Material.from_stream(stream))

        # Parse material groups
        material_groups = []
        stream.seek(material_groups_start_offset + offset_to_material_groups)
        for _ in range(material_group_count):
            material_groups.append(MaterialGroup.from_stream(stream))

        return cls(
            bounding_box_coord1=bbox1,
            bounding_box_coord2=bbox2,
            total_vertex_buffers_size=total_vertex_buffers_size,
            vertex_buffers_offset=vertex_buffers_offset,
            total_index_buffers_size=total_index_buffers_size,
            index_buffers_offset=index_buffers_offset,
            unknown_float=unknown_float,
            bones=bones,
            bone_poses=bone_poses,
            objects=objects,
            materials=materials,
            material_groups=material_groups
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'tpGxMeshHead':
        return cls.from_stream(BytesIO(data))
