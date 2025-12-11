import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, ClassVar
from io import BytesIO

from ..classes.binary_writer import BinaryWriter

from ..util import log

from .mesh_head import Object, VertexBuffer, tpGxMeshHead, align_relative

from .common import VertexBufferType


@dataclass
class VertexDataBuffer(ABC):
    _registry: ClassVar[dict[VertexBufferType, type['VertexDataBuffer']]] = {}

    @classmethod
    def register(cls, subclass: type['VertexDataBuffer']) -> type['VertexDataBuffer']:
        cls._registry[subclass.TYPE] = subclass
        return subclass

    @classmethod
    def from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer: VertexBuffer) -> 'VertexDataBuffer':
        type_id = vertex_buffer.vertex_buffer_type

        if type_id not in cls._registry:
            log.e(f"Unknown type ({vertex_buffer.vertex_buffer_type}) for buffer: {vertex_buffer}. File offset: {hex(stream.tell())}")
            subclass = cls._registry[VertexBufferType.UNKNOWN]
            return subclass._from_stream(stream, vertex_count, vertex_buffer.vertex_buffer_size)

        subclass = cls._registry[type_id]
        return subclass._from_stream(stream, vertex_count, vertex_buffer.vertex_buffer_size)

    @classmethod
    def _from_stream(cls, _stream: BinaryIO, _vertex_count: int, _vertex_buffer_size: int) -> 'VertexDataBuffer':
        """Implemented in subclasses."""
        raise NotImplementedError

    @abstractmethod
    def write_to(self, writer: BinaryWriter, vertex_buffer_head: VertexBuffer) -> None:
        """Implemented in subclasses."""
        raise NotImplementedError

@VertexDataBuffer.register
@dataclass
class UnknownsBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.UNKNOWN

    unknowns: list[bytes]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'UnknownsBuffer':
        unknowns: list[bytes] = []
        for _ in range(vertex_count):
            unknowns.append(stream.read(vertex_buffer_size))
        return cls(unknowns=unknowns)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        for unknown in self.unknowns:
            writer.write(unknown)

@VertexDataBuffer.register
@dataclass
class PositionsBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.POSITION

    positions: list[tuple[float, float, float]]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'PositionsBuffer':
        positions: list[tuple[float, float, float]] = []
        for _ in range(vertex_count):
            x, y, z = struct.unpack('<fff', stream.read(12))
            positions.append((x, y, z))
        return cls(positions=positions)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        for pos in self.positions:
            writer.write_struct('<fff', *pos)


@VertexDataBuffer.register
@dataclass
class NormalsBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.NORMAL

    normals: list[tuple[float, float, float]]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'NormalsBuffer':
        normals: list[tuple[float, float, float]] = []
        for _ in range(vertex_count):
            x, y, z, w = struct.unpack('<bbbb', stream.read(4))
            normals.append((x/127, y/127, z/127))
        return cls(normals=normals)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        for normal in self.normals:
            x, y, z = normal
            # Convert back from float to signed byte
            writer.write_struct('<bbbb', int(x * 127), int(y * 127), int(z * 127), 0)

@VertexDataBuffer.register
@dataclass
class TangentsBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.TANGENT

    tangents: list[tuple[float, float, float, float]]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'TangentsBuffer':
        tangents: list[tuple[float, float, float, float]] = []
        for _ in range(vertex_count):
            x, y, z, w = struct.unpack('<bbbb', stream.read(4))
            tangents.append((x/127, y/127, z/127, -w/127))
        return cls(tangents=tangents)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        for tangent in self.tangents:
            x, y, z, w = tangent
            # Convert back from float to signed byte
            writer.write_struct('<bbbb', int(x * 127), int(y * 127), int(z * 127), int(w * -127))

@VertexDataBuffer.register
@dataclass
class ColorsBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.COLOR

    colors: list[tuple[float, float, float, float]]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'ColorsBuffer':
        colors: list[tuple[float, float, float, float]] = []
        for _ in range(vertex_count):
            r, g, b, a = struct.unpack('<BBBB', stream.read(4))
            colors.append((r/255, g/255, b/255, a/255))
        return cls(colors=colors)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        for color in self.colors:
            r, g, b, a = color
            # Convert back from float to unsigned byte
            writer.write_struct('<BBBB', int(r * 255), int(g * 255), int(b * 255), int(a * 255))


@VertexDataBuffer.register
@dataclass
class UVsBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.UV

    uvs: list[tuple[float, float]]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'UVsBuffer':
        uvs: list[tuple[float, float]] = []
        for _ in range(vertex_count):
            u, v = struct.unpack('<ee', stream.read(4))
            uvs.append((u, 1-v))
        return cls(uvs=uvs)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        for uv in self.uvs:
            u, v = uv
            # Flip v back and write as half-float
            writer.write_struct('<ee', u, 1 - v)


@VertexDataBuffer.register
@dataclass
class BonesBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.BONES

    bones: list[tuple[int, int, int, int]]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'BonesBuffer':
        bones: list[tuple[int, int, int, int]] = []
        for _ in range(vertex_count):
            bone1, bone2, bone3, bone4 = struct.unpack('<BBBB', stream.read(4))
            bones.append((bone1, bone2, bone3, bone4))
        return cls(bones=bones)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        for bone_indices in self.bones:
            writer.write_struct('<BBBB', *bone_indices)


@VertexDataBuffer.register
@dataclass
class WeightsBuffer(VertexDataBuffer):
    TYPE: ClassVar[VertexBufferType] = VertexBufferType.WEIGHTS

    weights: list[list[float]]

    @classmethod
    def _from_stream(cls, stream: BinaryIO, vertex_count: int, vertex_buffer_size: int) -> 'WeightsBuffer':
        weights: list[list[float]] = []
        if vertex_buffer_size == 12:
            for _ in range(vertex_count):
                weight1, weight2, weight3 = struct.unpack('<fff', stream.read(12))
                weight4 = 1 - (weight1 + weight2 + weight3)
                weights.append([weight1, weight2, weight3, weight4])
        elif vertex_buffer_size == 8:
            for _ in range(vertex_count):
                weight1, weight2 = struct.unpack('<ff', stream.read(8))
                weight3 = 1 - (weight1 + weight2)
                weights.append([weight1, weight2, weight3])
        return cls(weights=weights)

    def write_to(self, writer, vertex_buffer_head: VertexBuffer) -> None:
        # Determine buffer size based on max weights across all vertices
        max_weights = max(len(w) for w in self.weights) if self.weights else 0

        if max_weights == 4:
            vertex_buffer_head.vertex_buffer_size = 12
            # Use 12-byte format (3 floats) for all vertices
            for weight_list in self.weights:
                # Ensure we have at least 3 weights (pad with 0 if needed)
                w = weight_list + [0.0] * (4 - len(weight_list))
                writer.write_struct('<fff', w[0], w[1], w[2])
        else:
            vertex_buffer_head.vertex_buffer_size = 8
            # Use 8-byte format (2 floats) for all vertices
            for weight_list in self.weights:
                # Ensure we have at least 2 weights (pad with 0 if needed)
                w = weight_list + [0.0] * (3 - len(weight_list))
                writer.write_struct('<ff', w[0], w[1])

@dataclass
class ObjectVertexBuffers:
    vertex_buffers: list[VertexDataBuffer]

    @classmethod
    def from_stream(cls, stream: BinaryIO, vertex_data_start: int, obj: Object) -> 'ObjectVertexBuffers':
        vertex_buffers: list[VertexDataBuffer] = []

        for vertex_buffer in obj.vertex_buffers:
            # Seek to the vertex data offset
            stream.seek(vertex_data_start + vertex_buffer.vertex_buffer_offset)

            # Read the vertex buffer
            vb = VertexDataBuffer.from_stream(stream, obj.vertex_count, vertex_buffer)
            vertex_buffers.append(vb)

        # Align to 4 bytes
        align_relative(stream, 0, 4)

        return cls(vertex_buffers=vertex_buffers)

    def get_buffers_of_type(self, type: VertexBufferType) -> list[VertexDataBuffer]:
        return [vb for vb in self.vertex_buffers if vb.TYPE == type]

    def write_to(self, writer, base_offset: int, object: Object) -> None:
        for i, vb in enumerate(self.vertex_buffers):
            vertex_buffer_head = object.vertex_buffers[i]
            vertex_buffer_head.vertex_buffer_offset = writer.tell() - base_offset
            vb.write_to(writer, vertex_buffer_head)
            # Align after EACH vertex buffer (relative to base_offset)
            writer.align_relative_eager(base_offset, 4)


@dataclass
class ObjectIndicesBuffer:
    indices: list[tuple[int, int, int]]

    @classmethod
    def from_stream(cls, stream: BinaryIO, _index_data_start: int, obj: Object) -> 'ObjectIndicesBuffer':
        indices: list[tuple[int, int, int]] = []

        if obj.index_buffer_size == 2:
            for _ in range(obj.index_count//3):
                v0, v1, v2 = struct.unpack('<HHH', stream.read(6))
                indices.append((v2, v1, v0))
        elif obj.index_buffer_size == 4:
            for _ in range(obj.index_count//3):
                v0, v1, v2 = struct.unpack('<III', stream.read(12))
                indices.append((v2, v1, v0))

        # Align to 4 bytes
        align_relative(stream, 0, 4)

        return cls(indices)

    def write_to(self, writer, object: Object) -> int:
        # Determine optimal index size based on max index value
        max_index = max(max(tri) for tri in self.indices) if self.indices else 0
        index_buffer_size = 2 if max_index < 65536 else 4
        object.index_buffer_size = index_buffer_size

        if index_buffer_size == 2:
            for tri in self.indices:
                # Reverse back the winding order
                v2, v1, v0 = tri
                writer.write_struct('<HHH', v0, v1, v2)
        else:  # 4 bytes
            for tri in self.indices:
                # Reverse back the winding order
                v2, v1, v0 = tri
                writer.write_struct('<III', v0, v1, v2)


@dataclass
class tpGxMeshData:
    object_vertex_buffers: list[ObjectVertexBuffers]
    object_indices: list[ObjectIndicesBuffer]

    @classmethod
    def from_stream(cls, stream: BinaryIO, mesh_head: tpGxMeshHead) -> 'tpGxMeshData':
        file_data_start = stream.tell()

        # Parse vertex data for each object
        object_vertex_buffers: list[ObjectVertexBuffers] = []
        for obj in mesh_head.objects:
            vertex_data = ObjectVertexBuffers.from_stream(
                stream,
                file_data_start,
                obj
            )
            object_vertex_buffers.append(vertex_data)

        # Seek to index buffers offset
        stream.seek(file_data_start + mesh_head.index_buffers_offset.offset)

        # Parse index data for each object
        object_indices: list[ObjectIndicesBuffer] = []
        for obj in mesh_head.objects:
            indices = ObjectIndicesBuffer.from_stream(stream, file_data_start, obj)
            object_indices.append(indices)

        return cls(
            object_vertex_buffers=object_vertex_buffers,
            object_indices=object_indices
        )

    @classmethod
    def from_bytes(cls, data: bytes, mesh_head: tpGxMeshHead) -> 'tpGxMeshData':
        return cls.from_stream(BytesIO(data), mesh_head)

    def write_to(self, writer, base_offset, mesh_head: tpGxMeshHead) -> None:
        from .binary_writer import BinaryWriter

        # Write vertex data for each object
        vertex_buffers_start = writer.tell()
        for i, obj_vb in enumerate(self.object_vertex_buffers):
            object = mesh_head.objects[i]
            obj_vb.write_to(writer, base_offset, object)
        vertex_buffers_end = writer.tell()
        mesh_head.total_vertex_buffers_size = vertex_buffers_end - vertex_buffers_start

        # Align to 256 bytes relative to base_offset before writing first index buffer (only if not already aligned)
        writer.align_relative_proper(base_offset, 256, b'\x40')

        # Write index data for each object (tightly packed, no alignment between them)
        index_buffers_start = writer.tell()
        for i, obj_indices in enumerate(self.object_indices):
            object = mesh_head.objects[i]
            obj_indices.write_to(writer, object)
        index_buffers_end = writer.tell()        

        mesh_head.index_buffers_offset.offset = index_buffers_start - base_offset
        mesh_head.total_index_buffers_size = index_buffers_end - index_buffers_start
