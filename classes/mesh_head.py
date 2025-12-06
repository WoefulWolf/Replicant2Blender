import struct
from dataclasses import dataclass
from typing import BinaryIO
from io import BytesIO

from .common import VertexBufferType, read_string, DataOffset, align_relative


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

    @staticmethod
    def write_list(writer, bones: list['Bone']) -> None:
        from .binary_writer import BinaryWriter

        placeholders = []

        for bone in bones:
            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)
            writer.write_struct('<i', bone.parent_bone_index)

            # Write rotation quaternion
            writer.write_struct('<ffff', *bone.rotation)

            # Write scale
            writer.write_struct('<fff', *bone.scale)

            # Write position
            writer.write_struct('<fff', *bone.position)

            placeholders.append((name_placeholder, bone.name))

        for name_placeholder, name in placeholders:
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(name)


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

    @staticmethod
    def write_list(writer, bone_poses: list['BonePose']) -> None:
        from .binary_writer import BinaryWriter

        placeholders = []

        for bone_pose in bone_poses:
            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)
            writer.write_struct('<if', bone_pose.unknown_index, bone_pose.length)

            # Write matrices (flatten 4x4 matrices)
            matrix_0_flat = [val for row in bone_pose.unknown_matrix_0 for val in row]
            writer.write_struct('<16f', *matrix_0_flat)

            matrix_1_flat = [val for row in bone_pose.unknown_matrix_1 for val in row]
            writer.write_struct('<16f', *matrix_1_flat)

            placeholders.append((name_placeholder, bone_pose.name))

        for name_placeholder, name in placeholders:
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(name)


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

    def write_to(self, writer) -> None:
        from .binary_writer import BinaryWriter

        writer.write_struct('<IIIIB',
            self.vertex_buffer_offset,
            self.unknown_uint32_1,
            self.vertex_buffer_flag,
            self.vertex_buffer_size,
            self.vertex_buffer_type
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

    @staticmethod
    def write_list(writer, objects: list['Object']) -> None:
        from .binary_writer import BinaryWriter

        vb_placeholders = []

        for obj in objects:
            writer.write_struct('<IIIIIII',
                obj.indices_start_offset,
                obj.unknown_uint32_1,
                obj.unknown_uint32_2,
                obj.vertex_count,
                obj.index_count,
                obj.index_buffer_size,
                obj.unknown_uint32_6
            )

            writer.write_struct('<I', len(obj.vertex_buffers))
            vb_start_offset = writer.tell()
            vb_placeholder = writer.write_placeholder('<I', vb_start_offset)

            vb_placeholders.append((vb_placeholder, obj.vertex_buffers))
            writer.align_min_padding(8, 0)

        writer.align_min_padding(8, 8)
        for vb_placeholder, vertex_buffers in vb_placeholders:
            vb_pos = writer.tell()
            writer.patch_placeholder(vb_placeholder, vb_pos)

            for vb in vertex_buffers:
                vb.write_to(writer)
                writer.align_min_padding(8, 0)


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

    @staticmethod
    def write_list(writer, materials: list['Material']) -> None:
        from .binary_writer import BinaryWriter

        placeholders = []

        for material in materials:
            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)

            byte_start_offset = writer.tell()
            byte_placeholder = writer.write_placeholder('<I', byte_start_offset)
            writer.write_struct('<I', material.unknown_uint32)

            placeholders.append((name_placeholder, byte_placeholder, material.name, material.unknown_byte))

        for name_placeholder, byte_placeholder, name, byte_val in placeholders:
            # Write name (aligned)
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(name)

            # Write byte (aligned)
            writer.align_min_padding(8, 8)
            byte_pos = writer.tell()
            writer.patch_placeholder(byte_placeholder, byte_pos)
            writer.write_struct('<B', byte_val)


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

    @staticmethod
    def write_list(writer, material_groups: list['MaterialGroup']) -> None:
        from .binary_writer import BinaryWriter

        for mg in material_groups:
            writer.write_struct('<IIII',
                mg.object_index,
                mg.material_index,
                mg.index_start,
                mg.index_count
            )
            writer.write_struct('<fff', *mg.bounding_box_coord1)
            writer.write_struct('<fff', *mg.bounding_box_coord2)


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

    def write_to(self, writer) -> None:
        from .binary_writer import BinaryWriter

        start_offset = writer.tell()

        # Write bounding boxes
        writer.write_struct('<fff', *self.bounding_box_coord1)
        writer.write_struct('<fff', *self.bounding_box_coord2)

        # Write header (all values should be pre-calculated)
        writer.write_struct('<I', self.total_vertex_buffers_size)
        self.vertex_buffers_offset.write_to(writer)
        writer.write_struct('<I', self.total_index_buffers_size)
        self.index_buffers_offset.write_to(writer)
        writer.write_struct('<f', self.unknown_float)

        # Write counts and offset placeholders
        writer.write_struct('<I', len(self.bones))
        bones_start_offset = writer.tell()
        bones_placeholder = writer.write_placeholder('<I', bones_start_offset)

        writer.write_struct('<I', len(self.bone_poses))
        bone_poses_start_offset = writer.tell()
        bone_poses_placeholder = writer.write_placeholder('<I', bone_poses_start_offset)

        writer.write_struct('<I', len(self.objects))
        objects_start_offset = writer.tell()
        objects_placeholder = writer.write_placeholder('<I', objects_start_offset)

        writer.write_struct('<I', len(self.materials))
        materials_start_offset = writer.tell()
        materials_placeholder = writer.write_placeholder('<I', materials_start_offset)

        writer.write_struct('<I', len(self.material_groups))
        material_groups_start_offset = writer.tell()
        material_groups_placeholder = writer.write_placeholder('<I', material_groups_start_offset)

        # Write bones
        writer.align_min_padding(8, 8)
        bones_pos = writer.tell()
        writer.patch_placeholder(bones_placeholder, bones_pos)
        Bone.write_list(writer, self.bones)

        # Write bone poses
        writer.align_min_padding(8, 8)
        bone_poses_pos = writer.tell()
        writer.patch_placeholder(bone_poses_placeholder, bone_poses_pos)
        BonePose.write_list(writer, self.bone_poses)

        # Write objects
        writer.align_min_padding(8, 8)
        objects_pos = writer.tell()
        writer.patch_placeholder(objects_placeholder, objects_pos)
        Object.write_list(writer, self.objects)

        # Write materials
        writer.align_min_padding(8, 8)
        materials_pos = writer.tell()
        writer.patch_placeholder(materials_placeholder, materials_pos)
        Material.write_list(writer, self.materials)

        # Write material groups
        writer.align_min_padding(8, 8)
        material_groups_pos = writer.tell()
        writer.patch_placeholder(material_groups_placeholder, material_groups_pos)
        MaterialGroup.write_list(writer, self.material_groups)
