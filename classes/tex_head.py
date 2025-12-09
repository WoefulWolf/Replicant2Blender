import struct
from dataclasses import dataclass
from typing import List, BinaryIO
from io import BytesIO
from enum import IntEnum

from ..classes.binary_writer import BinaryWriter
from .common import DataOffset


class XonSurfaceDXGIFormat(IntEnum):
    UNKNOWN = 0x00000000
    R32G32B32A32_FLOAT = 0x00010000
    R8G8B8A8_UNORM_STRAIGHT= 0x00010700
    R8G8B8A8_UNORM = 0x00010800
    R8_UNORM= 0x00010a00
    R8G8B8A8_UNORM_SRGB = 0x00010B00
    BC1_UNORM = 0x00010F00
    BC1_UNORM_SRGB = 0x00011000
    BC2_UNORM = 0x00011100
    BC2_UNORM_SRGB = 0x00011200
    BC3_UNORM = 0x00011300
    BC3_UNORM_SRGB = 0x00011400
    BC4_UNORM = 0x00011500
    BC5_UNORM = 0x00011600
    BC7_UNORM = 0x00011900
    BC1_UNORM_VOLUME = 0x00021700
    BC7_UNORM_SRGB = 0x00021A00
    R32G32B32A32_UINT = 0x00030000
    BC6H_UF16 = 0x00031700

def get_dxgi_format(surfaceFormat: XonSurfaceDXGIFormat) -> int | None:
	"""Convert XonSurfaceDXGIFormat enum to DXGI format integer."""
	mapping = {
		XonSurfaceDXGIFormat.UNKNOWN: 0,
		XonSurfaceDXGIFormat.R32G32B32A32_FLOAT: 2,
		XonSurfaceDXGIFormat.R32G32B32A32_UINT: 3,
		XonSurfaceDXGIFormat.R8G8B8A8_UNORM_STRAIGHT: 28,
		XonSurfaceDXGIFormat.R8G8B8A8_UNORM: 28,
		XonSurfaceDXGIFormat.R8G8B8A8_UNORM_SRGB: 29,
		XonSurfaceDXGIFormat.R8_UNORM: 61,
		XonSurfaceDXGIFormat.BC1_UNORM: 71,
		XonSurfaceDXGIFormat.BC1_UNORM_VOLUME: 71,
		XonSurfaceDXGIFormat.BC1_UNORM_SRGB: 72,
		XonSurfaceDXGIFormat.BC2_UNORM: 74,
		XonSurfaceDXGIFormat.BC2_UNORM_SRGB: 75,
		XonSurfaceDXGIFormat.BC3_UNORM: 77,
		XonSurfaceDXGIFormat.BC3_UNORM_SRGB: 78,
		XonSurfaceDXGIFormat.BC4_UNORM: 80,
		XonSurfaceDXGIFormat.BC5_UNORM: 83,
		XonSurfaceDXGIFormat.BC6H_UF16: 95,
		XonSurfaceDXGIFormat.BC7_UNORM: 98,
		XonSurfaceDXGIFormat.BC7_UNORM_SRGB: 99,
	}

	return mapping.get(surfaceFormat, None)

def get_xon_surface_format(dxgi_format: int) -> XonSurfaceDXGIFormat:
	"""Reverse mapping from DXGI format integer to XonSurfaceDXGIFormat enum."""
	mapping = {
		0: XonSurfaceDXGIFormat.UNKNOWN,
		2: XonSurfaceDXGIFormat.R32G32B32A32_FLOAT,
		3: XonSurfaceDXGIFormat.R32G32B32A32_UINT,
		28: XonSurfaceDXGIFormat.R8G8B8A8_UNORM,
		29: XonSurfaceDXGIFormat.R8G8B8A8_UNORM_SRGB,
		61: XonSurfaceDXGIFormat.R8_UNORM,
		71: XonSurfaceDXGIFormat.BC1_UNORM,
		72: XonSurfaceDXGIFormat.BC1_UNORM_SRGB,
		74: XonSurfaceDXGIFormat.BC2_UNORM,
		75: XonSurfaceDXGIFormat.BC2_UNORM_SRGB,
		77: XonSurfaceDXGIFormat.BC3_UNORM,
		78: XonSurfaceDXGIFormat.BC3_UNORM_SRGB,
		80: XonSurfaceDXGIFormat.BC4_UNORM,
		83: XonSurfaceDXGIFormat.BC5_UNORM,
		95: XonSurfaceDXGIFormat.BC6H_UF16,
		98: XonSurfaceDXGIFormat.BC7_UNORM,
		99: XonSurfaceDXGIFormat.BC7_UNORM_SRGB,
	}

	return mapping.get(dxgi_format, XonSurfaceDXGIFormat.UNKNOWN)

def get_alpha_mode(surfaceFormat: XonSurfaceDXGIFormat):
	if (surfaceFormat == XonSurfaceDXGIFormat.R8G8B8A8_UNORM_STRAIGHT):
		return 1

	return 2

@dataclass
class Subresource:
    offset: int
    unknown0: int
    row_pitch: int
    unknown1: int
    size: int
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
            size=values[4],
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
            self.size,
            self.unknown2,
            self.width,
            self.height,
            self.depth,
            self.row_count
        )

@dataclass
class tpGxTexHead:
    width: int
    height: int
    depth: int
    mip_count: int
    size: int
    internal_offset: DataOffset
    surface_format: XonSurfaceDXGIFormat
    subresources: List[Subresource]

    def get_format_str(self) -> str:
        from puredds import DXGI_FORMAT
        return DXGI_FORMAT(get_dxgi_format(self.surface_format)).name

    @classmethod
    def new(cls) -> 'tpGxTexHead':
        return cls(
            width=0,
            height=0,
            depth=0,
            mip_count=0,
            size=0,
            internal_offset=DataOffset(0, True),
            surface_format=XonSurfaceDXGIFormat.UNKNOWN,
            subresources=[]
        )

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'tpGxTexHead':
        # Parse header
        width, height, depth, mip_count, size = struct.unpack('<IIIII', stream.read(20))

        # Parse unknown offset (bitfield)
        internal_offset = DataOffset.from_stream(stream)

        # Parse surface format
        surface_format_value = struct.unpack('<I', stream.read(4))[0]
        try:
            surface_format = XonSurfaceDXGIFormat(surface_format_value)
        except ValueError:
            surface_format = XonSurfaceDXGIFormat.UNKNOWN

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
            size=size,
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
            self.size
        )

        # Write internal offset
        self.internal_offset.write_to(writer)

        # Write surface format
        writer.write_struct('<I', self.surface_format)

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
