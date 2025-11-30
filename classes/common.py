from enum import IntEnum
import struct
from dataclasses import dataclass
from typing import BinaryIO

def read_string(stream: BinaryIO) -> str:
    chars = []
    while True:
        char = stream.read(1)
        if not char or char == b'\x00':
            break
        chars.append(char)
    return b''.join(chars).decode('utf-8', errors='replace')

@dataclass
class Import:
    path_hash: int
    path: str
    unknown0: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Import':
        path_hash = struct.unpack('<I', stream.read(4))[0]
        path_start_offset = stream.tell()
        offset_to_path, unknown0 = struct.unpack('<II', stream.read(8))

        # Read the path string
        return_pos = stream.tell()
        stream.seek(path_start_offset + offset_to_path)
        path = read_string(stream)
        stream.seek(return_pos)

        return cls(
            path_hash=path_hash,
            path=path,
            unknown0=unknown0
        )


def align_relative(stream: BinaryIO, relative_start: int, alignment: int):
    current_pos = stream.tell()
    offset_from_start = current_pos - relative_start
    aligned_offset = (((offset_from_start) // alignment) + 1) * alignment
    stream.seek(relative_start + aligned_offset)

class VertexBufferType(IntEnum):
    UNKNOWN = -1
    POSITION = 0
    NORMAL = 1
    TANGENT = 2
    COLOR = 3
    UV = 4
    BONES = 5
    WEIGHTS = 6

@dataclass
class DataOffset:
    offset: int
    has_data: bool

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'DataOffset':
        value = struct.unpack('<I', stream.read(4))[0]
        return cls(
            offset=value & 0x7FFFFFFF,  # Lower 31 bits
            has_data=bool(value >> 31)  # Upper 1 bit
        )
