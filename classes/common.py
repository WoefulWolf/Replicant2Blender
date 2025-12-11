from enum import IntEnum
import struct
from dataclasses import dataclass, field
from typing import BinaryIO

from ..util import fnv1

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
    path: str
    path_hash: int = field(init=False)
    unknown0: int = field(default=0)

    def __post_init__(self) -> None:
        self.path_hash = fnv1(self.path)

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Import':
        path_hash = struct.unpack('<I', stream.read(4))[0]
        path_start_offset = stream.tell()
        offset_to_path, unknown0 = struct.unpack('<II', stream.read(8))

        return_pos = stream.tell()
        stream.seek(path_start_offset + offset_to_path)
        path = read_string(stream)
        stream.seek(return_pos)

        # Bypass __post_init__ to use parsed path_hash directly
        instance = cls.__new__(cls)
        instance.path_hash = path_hash
        instance.path = path
        instance.unknown0 = unknown0
        return instance

    @staticmethod
    def write_list(writer, imports: list['Import']) -> None:
        placeholders = []

        for import_item in imports:
            writer.write_struct('<I', import_item.path_hash)
            path_start_offset = writer.tell()
            path_placeholder = writer.write_placeholder('<I', path_start_offset)
            writer.write_struct('<I', import_item.unknown0)
            placeholders.append((path_placeholder, path_start_offset, import_item.path))

        for path_placeholder, path_start_offset, path in placeholders:
            writer.align_min_padding(8, 8)
            path_pos = writer.tell()
            writer.patch_placeholder(path_placeholder, path_pos)
            writer.write_string(path)


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

    def write_to(self, writer) -> None:
        value = self.offset & 0x7FFFFFFF
        if self.has_data:
            value |= 0x80000000
        writer.write_struct('<I', value)
