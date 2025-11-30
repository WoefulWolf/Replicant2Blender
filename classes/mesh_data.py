import struct
from dataclasses import dataclass
from typing import BinaryIO, ClassVar
from io import BytesIO

from ..util import log

from .mesh_head import Object, VertexBuffer, tpGxMeshHead

from .common import VertexBufferType, align_relative


@dataclass
class VertexDataBuffer:
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
            tangents.append((x/255, y/255, z/255, w/255))
        return cls(tangents=tangents)

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
