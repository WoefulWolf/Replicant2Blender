import struct
from dataclasses import dataclass, field
from typing import List, BinaryIO
from io import BytesIO
from enum import IntEnum

from ..classes.binary_writer import BinaryWriter
from .common import DataOffset


class ResourceDimension(IntEnum):
    TEXTURE2D = 1
    TEXTURE3D = 2
    CUBEMAP = 3


class ResourceFormat(IntEnum):
    R32G32B32A32_FLOAT = 0
    R32G32B32_FLOAT = 1
    R32G32_FLOAT = 2
    R32_FLOAT = 3
    R16G16B16A16_FLOAT = 4
    R16G16_FLOAT = 5
    R16_FLOAT = 6
    R8G8B8A8_UNORM = 7
    R8G8B8A8_UNORM_SRGB = 8
    R8G8_UNORM = 9
    R8_UNORM = 10
    B8G8R8A8_UNORM = 11
    B8G8R8A8_UNORM_SRGB = 12
    B8G8R8X8_UNORM = 13
    B8G8R8X8_UNORM_SRGB = 14
    BC1_UNORM = 15
    BC1_UNORM_SRGB = 16
    BC2_UNORM = 17
    BC2_UNORM_SRGB = 18
    BC3_UNORM = 19
    BC3_UNORM_SRGB = 20
    BC4_UNORM = 21
    BC5_UNORM = 22
    BC6H_UF16 = 23
    BC6H_SF16 = 24
    BC7_UNORM = 25
    BC7_UNORM_SRGB = 26
    UNKNOWN = 27


@dataclass
class XonSurfaceFormat:
    usage_maybe: int
    resource_format: ResourceFormat
    resource_dimension: ResourceDimension
    generate_mips: bool

    def get_dxgi_format(self) -> int:
        """Get DXGI_FORMAT integer value for DDS export."""
        dxgi_mapping = {
            ResourceFormat.R32G32B32A32_FLOAT: 2,
            ResourceFormat.R32G32B32_FLOAT: 6,
            ResourceFormat.R32G32_FLOAT: 16,
            ResourceFormat.R32_FLOAT: 41,
            ResourceFormat.R16G16B16A16_FLOAT: 10,
            ResourceFormat.R16G16_FLOAT: 34,
            ResourceFormat.R16_FLOAT: 54,
            ResourceFormat.R8G8B8A8_UNORM: 28,
            ResourceFormat.R8G8B8A8_UNORM_SRGB: 29,
            ResourceFormat.R8G8_UNORM: 49,
            ResourceFormat.R8_UNORM: 61,
            ResourceFormat.B8G8R8A8_UNORM: 87,
            ResourceFormat.B8G8R8A8_UNORM_SRGB: 91,
            ResourceFormat.B8G8R8X8_UNORM: 88,
            ResourceFormat.B8G8R8X8_UNORM_SRGB: 93,
            ResourceFormat.BC1_UNORM: 71,
            ResourceFormat.BC1_UNORM_SRGB: 72,
            ResourceFormat.BC2_UNORM: 74,
            ResourceFormat.BC2_UNORM_SRGB: 75,
            ResourceFormat.BC3_UNORM: 77,
            ResourceFormat.BC3_UNORM_SRGB: 78,
            ResourceFormat.BC4_UNORM: 80,
            ResourceFormat.BC5_UNORM: 83,
            ResourceFormat.BC6H_UF16: 95,
            ResourceFormat.BC6H_SF16: 96,
            ResourceFormat.BC7_UNORM: 98,
            ResourceFormat.BC7_UNORM_SRGB: 99,
            ResourceFormat.UNKNOWN: 0,
        }
        return dxgi_mapping.get(self.resource_format, 0)

    def get_d3d10_dimension(self) -> int:
        """Get D3D10_RESOURCE_DIMENSION value for DDS export."""
        mapping = {
            ResourceDimension.TEXTURE2D: 3,  # D3D10_RESOURCE_DIMENSION_TEXTURE2D
            ResourceDimension.TEXTURE3D: 4,  # D3D10_RESOURCE_DIMENSION_TEXTURE3D
            ResourceDimension.CUBEMAP: 3,    # D3D10_RESOURCE_DIMENSION_TEXTURE2D (with cubemap flag)
        }
        return mapping.get(self.resource_dimension, 3)

    def get_alpha_mode(self) -> int:
        """Get DDS alpha mode value."""
        # Check if format has SRGB suffix
        if "SRGB" in self.resource_format.name:
            return 1  # DDS_ALPHA_MODE_STRAIGHT
        return 0  # DDS_ALPHA_MODE_UNKNOWN

    def is_compressed(self) -> bool:
        """Check if the format is a block-compressed format."""
        return "BC" in self.resource_format.name

    def get_bytes_per_pixel(self) -> int:
        """Get bytes per pixel for uncompressed formats."""
        format_bpp = {
            ResourceFormat.R32G32B32A32_FLOAT: 16,
            ResourceFormat.R32G32B32_FLOAT: 12,
            ResourceFormat.R32G32_FLOAT: 8,
            ResourceFormat.R32_FLOAT: 4,
            ResourceFormat.R16G16B16A16_FLOAT: 8,
            ResourceFormat.R16G16_FLOAT: 4,
            ResourceFormat.R16_FLOAT: 2,
            ResourceFormat.R8G8B8A8_UNORM: 4,
            ResourceFormat.R8G8B8A8_UNORM_SRGB: 4,
            ResourceFormat.R8G8_UNORM: 2,
            ResourceFormat.R8_UNORM: 1,
            ResourceFormat.B8G8R8A8_UNORM: 4,
            ResourceFormat.B8G8R8A8_UNORM_SRGB: 4,
            ResourceFormat.B8G8R8X8_UNORM: 4,
            ResourceFormat.B8G8R8X8_UNORM_SRGB: 4,
        }
        return format_bpp.get(self.resource_format, 4)  # Default to 4 bytes

@dataclass
class Subresource:
    offset: int
    unknown0: int
    row_pitch: int
    unknown1: int
    slice_size: int
    unknown2: int
    width: int
    height: int
    depth: int
    row_count: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Subresource':
        values = struct.unpack('<IIIIIIIIII', stream.read(40))
        return cls(
            offset=values[0],
            unknown0=values[1],
            row_pitch=values[2],
            unknown1=values[3],
            slice_size=values[4],
            unknown2=values[5],
            width=values[6],
            height=values[7],
            depth=values[8],
            row_count=values[9]
        )

    def write_to(self, writer) -> None:
        writer.write_struct('<IIIIIIIIII',
            self.offset,
            self.unknown0,
            self.row_pitch,
            self.unknown1,
            self.slice_size,
            self.unknown2,
            self.width,
            self.height,
            self.depth,
            self.row_count
        )

@dataclass
class tpGxTexHead:
    width: int = field(default=0)
    height: int = field(default=0)
    depth: int = field(default=0)
    mip_count: int = field(default=0)
    total_data_size: int = field(default=0)
    internal_offset: DataOffset = field(default_factory=lambda: DataOffset(0, True))
    surface_format: XonSurfaceFormat = field(default_factory=lambda: XonSurfaceFormat(0, ResourceFormat.UNKNOWN, ResourceDimension.TEXTURE2D, False))
    subresources: List[Subresource] = field(default_factory=list)

    def get_format_str(self) -> str:
        return self.surface_format.resource_format.name

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'tpGxTexHead':
        # Parse header
        width, height, depth, mip_count, size = struct.unpack('<IIIII', stream.read(20))

        # Parse unknown offset (bitfield)
        internal_offset = DataOffset.from_stream(stream)

        # Parse surface format
        usage, res_format, res_dimension, gen_mips = struct.unpack('<BBB?', stream.read(4))
        try:
            resource_format = ResourceFormat(res_format)
        except ValueError:
            resource_format = ResourceFormat.UNKNOWN
        try:
            resource_dimension = ResourceDimension(res_dimension)
        except ValueError:
            resource_dimension = ResourceDimension.TEXTURE2D
        surface_format = XonSurfaceFormat(usage, resource_format, resource_dimension, gen_mips)

        # Get subresources info
        subresources_count = struct.unpack('<I', stream.read(4))[0]
        subresources_start_offset = stream.tell()
        offset_to_subresources = struct.unpack('<I', stream.read(4))[0]

        # Parse subresources
        subresources = []
        stream.seek(subresources_start_offset + offset_to_subresources)
        for _ in range(subresources_count):
            subresources.append(Subresource.from_stream(stream))

        return cls(
            width=width,
            height=height,
            depth=depth,
            mip_count=mip_count,
            total_data_size=size,
            internal_offset=internal_offset,
            surface_format=surface_format,
            subresources=subresources
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'tpGxTexHead':
        return cls.from_stream(BytesIO(data))

    def write_to(self, writer: BinaryWriter) -> None:
        # Write header
        writer.write_struct('<IIIII',
            self.width,
            self.height,
            self.depth,
            self.mip_count,
            self.total_data_size
        )

        # Write internal offset
        self.internal_offset.write_to(writer)

        # Write surface format
        writer.write_struct('<BBB?',
            self.surface_format.usage_maybe,
            self.surface_format.resource_format,
            self.surface_format.resource_dimension,
            self.surface_format.generate_mips
        )

        # Write subresources count
        writer.write_struct('<I', len(self.subresources))

        # Write offset to subresources (placeholder)
        subresources_start_offset = writer.tell()
        subresources_offset_placeholder = writer.write_placeholder('<I', subresources_start_offset)

        writer.align_min_padding(8, 8)

        # Write subresources
        subresources_pos = writer.tell()
        writer.patch_placeholder(subresources_offset_placeholder, subresources_pos)
        for subresource in self.subresources:
            subresource.write_to(writer)
