import struct
from dataclasses import dataclass
from typing import List, BinaryIO
from io import BytesIO
from enum import IntEnum

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

def get_DXGI_format(surfaceFormat: XonSurfaceDXGIFormat) -> int | None:
	if (surfaceFormat == XonSurfaceDXGIFormat.UNKNOWN):
		return 0
	
	if (surfaceFormat == XonSurfaceDXGIFormat.R32G32B32A32_FLOAT):
		return 2
	
	if (surfaceFormat == XonSurfaceDXGIFormat.R32G32B32A32_UINT):
		return 3
	
	if (surfaceFormat == XonSurfaceDXGIFormat.R8G8B8A8_UNORM_STRAIGHT):
		return 28
	
	if (surfaceFormat == XonSurfaceDXGIFormat.R8G8B8A8_UNORM):
		return 28
	
	if (surfaceFormat == XonSurfaceDXGIFormat.R8G8B8A8_UNORM_SRGB):
		return 29
	
	if (surfaceFormat == XonSurfaceDXGIFormat.R8_UNORM):
		return 61

	if (surfaceFormat == XonSurfaceDXGIFormat.BC1_UNORM or surfaceFormat == XonSurfaceDXGIFormat.BC1_UNORM_VOLUME):
		return 71

	if (surfaceFormat == XonSurfaceDXGIFormat.BC1_UNORM_SRGB):
		return 72

	if (surfaceFormat == XonSurfaceDXGIFormat.BC2_UNORM):
		return 74

	if (surfaceFormat == XonSurfaceDXGIFormat.BC2_UNORM_SRGB):
		return 75

	if (surfaceFormat == XonSurfaceDXGIFormat.BC3_UNORM):
		return 77

	if (surfaceFormat == XonSurfaceDXGIFormat.BC3_UNORM_SRGB):
		return 78
	
	if (surfaceFormat == XonSurfaceDXGIFormat.BC4_UNORM):
		return 80

	if (surfaceFormat == XonSurfaceDXGIFormat.BC5_UNORM):
		return 83
	
	if (surfaceFormat == XonSurfaceDXGIFormat.BC6H_UF16):
		return 95
	
	if (surfaceFormat == XonSurfaceDXGIFormat.BC7_UNORM):
		return 98
	
	if (surfaceFormat == XonSurfaceDXGIFormat.BC7_UNORM_SRGB):
		return 99

	return None

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


@dataclass
class tpGxTexHead:
    width: int
    height: int
    depth: int
    mip_count: int
    size: int
    unknown_offset: DataOffset
    surface_format: XonSurfaceDXGIFormat
    subresources: List[Subresource]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'tpGxTexHead':
        # Parse header
        width, height, depth, mip_count, size = struct.unpack('<IIIII', stream.read(20))

        # Parse unknown offset (bitfield)
        unknown_offset = DataOffset.from_stream(stream)

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
            unknown_offset=unknown_offset,
            surface_format=surface_format,
            subresources=subresources
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'tpGxTexHead':
        return cls.from_stream(BytesIO(data))
