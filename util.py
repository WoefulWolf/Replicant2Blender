#encoding = utf-8
import os
import sys
import struct
import numpy as np
import math

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