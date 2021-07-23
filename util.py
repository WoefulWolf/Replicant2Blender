#encoding = utf-8
import os
import sys
import struct
import numpy as np
import math
from enum import Enum

def to_float(bs):
	return struct.unpack("<f", bs)[0]

def to_float16(bs):
	return float(np.frombuffer(bs, np.float16)[0])

def to_int(bs):
	return (int.from_bytes(bs, byteorder='little', signed=True))

def to_uint(bs):
	return (int.from_bytes(bs, byteorder='little', signed=False))

def to_ushort(bs):
	return struct.unpack("<H", bs)[0]

def to_string(bs, encoding = 'utf8'):
	return bs.split(b'\x00')[0].decode(encoding)

def alignRelative(openFile, relativeStart, alignment):
	alignOffset = (((openFile.tell() - relativeStart) // alignment) + 1) * alignment
	openFile.seek(relativeStart + alignOffset)

def str_to_bytes(var):
	return bytearray(var, 'utf-8')

def uint32_to_bytes(var):
	return var.to_bytes(4, byteorder='little', signed=False)

def int32_to_bytes(var):
	return var.to_bytes(4, byteorder='little', signed=True)

class XonSurfaceDXGIFormat(Enum):
	UNKNOWN = 0
	R8G8B8A8_UNORM = 0x00010800
	R8G8B8A8_UNORM_SRGB = 0x00010B00
	BC1_UNORM = 0x00010F00
	BC1_UNORM_SRGB = 0x00011000
	BC2_UNORM = 0x00011100
	BC2_UNORM_SRGB = 0x00011200
	BC3_UNORM = 0x00011300
	BC3_UNORM_SRGB = 0x00011400
	BC4_UNORM = 0x00011500
	BC5_UNORM = 0x00011600
	R32G32B32A32_FLOAT = 0x00030000
	A8_UNORM = 0x00031700

def get_DXGI_Format(surfaceFormat):
	if (surfaceFormat == XonSurfaceDXGIFormat.UNKNOWN):
		return "UNKNOWN"

	if (surfaceFormat == XonSurfaceDXGIFormat.BC1_UNORM):
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

	if (surfaceFormat == XonSurfaceDXGIFormat.R32G32B32A32_FLOAT):
		return 3

	if (surfaceFormat == XonSurfaceDXGIFormat.A8_UNORM):
		return 65