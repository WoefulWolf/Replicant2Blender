import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import BinaryIO

from ..classes.binary_writer import BinaryWriter
from ..classes.common import read_string
from ..util import fnv1


ARC_OFFSET_SCALE = 4


class ArchiveLoadType(IntEnum):
    PRELOAD_DECOMPRESS = 0   # Single compressed stream; game decompresses all at load
    STREAM             = 1   # Separate frame per file; game streams on demand
    STREAM_ONDEMAND    = 2   # Same layout as STREAM


@dataclass
class TpArchiveEntry:
    """One row in TpArchiveFileParam's archive table."""
    filename: str
    load_type: int
    arc_offset_scale: int = ARC_OFFSET_SCALE

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'TpArchiveEntry':
        name_field_pos   = stream.tell()
        offset_to_name   = struct.unpack('<I', stream.read(4))[0]
        arc_offset_scale = struct.unpack('<I', stream.read(4))[0]
        load_type        = struct.unpack('<B', stream.read(1))[0]
        stream.read(3)   # padding

        return_pos = stream.tell()
        stream.seek(name_field_pos + offset_to_name)
        filename = read_string(stream)
        stream.seek(return_pos)

        return cls(filename=filename, load_type=load_type, arc_offset_scale=arc_offset_scale)


@dataclass
class TpFileEntry:
    """One row in TpArchiveFileParam's file table."""
    name: str
    raw_offset: int = 0
    size: int = 0            # compressed_size (0 for SingleStream)
    pack_file_serialized_size: int = 0
    pack_file_resource_size: int = 0
    archive_index: int = 0
    flags: int = 0

    @classmethod
    def from_stream(cls, stream: BinaryIO, archives: list[TpArchiveEntry]) -> 'TpFileEntry':
        _path_hash      = struct.unpack('<I', stream.read(4))[0]
        name_field_pos  = stream.tell()
        name_offset     = struct.unpack('<I', stream.read(4))[0]
        scaled_offset   = struct.unpack('<I', stream.read(4))[0]
        compressed_size = struct.unpack('<I', stream.read(4))[0]
        pack_serialized = struct.unpack('<I', stream.read(4))[0]
        pack_resource   = struct.unpack('<I', stream.read(4))[0]
        archive_index   = struct.unpack('<B', stream.read(1))[0]
        flags           = struct.unpack('<B', stream.read(1))[0]
        stream.read(2)  # padding

        return_pos = stream.tell()
        stream.seek(name_field_pos + name_offset)
        name = read_string(stream)
        stream.seek(return_pos)

        scale      = archives[archive_index].arc_offset_scale if archive_index < len(archives) else 0
        raw_offset = scaled_offset << scale

        return cls(
            name=name,
            raw_offset=raw_offset,
            size=compressed_size,
            pack_file_serialized_size=pack_serialized,
            pack_file_resource_size=pack_resource,
            archive_index=archive_index,
            flags=flags,
        )


@dataclass
class TpArchiveFileParam:
    archives: list[TpArchiveEntry]
    files: list[TpFileEntry]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'TpArchiveFileParam':
        num_archives    = struct.unpack('<I', stream.read(4))[0]
        array_base      = stream.tell()
        offset_to_array = struct.unpack('<I', stream.read(4))[0]
        num_files       = struct.unpack('<I', stream.read(4))[0]
        table_base      = stream.tell()
        offset_to_table = struct.unpack('<I', stream.read(4))[0]

        archives: list[TpArchiveEntry] = []
        if num_archives > 0:
            stream.seek(array_base + offset_to_array)
            for _ in range(num_archives):
                archives.append(TpArchiveEntry.from_stream(stream))

        files: list[TpFileEntry] = []
        if num_files > 0:
            stream.seek(table_base + offset_to_table)
            for _ in range(num_files):
                files.append(TpFileEntry.from_stream(stream, archives))

        return cls(archives=archives, files=files)

    def write_to(self, writer: BinaryWriter) -> None:
        # Header
        writer.write_struct('<I', len(self.archives))
        arc_array_base = writer.tell()
        arc_array_ph   = writer.write_placeholder('<I', arc_array_base)
        writer.write_struct('<I', len(self.files))
        file_table_base = writer.tell()
        file_table_ph   = writer.write_placeholder('<I', file_table_base)

        # Collect (placeholder_pos, string) pairs for deferred string pool
        string_refs: list[tuple[int, str]] = []

        # Archive entry array
        if self.archives:
            writer.align(16)
            writer.patch_placeholder(arc_array_ph, writer.tell())
            for entry in self.archives:
                name_field_pos = writer.tell()
                name_ph = writer.write_placeholder('<I', name_field_pos)
                writer.write_struct('<I', entry.arc_offset_scale)
                writer.write_struct('<B', entry.load_type)
                writer.write(b'\x00\x00\x00')  # padding
                string_refs.append((name_ph, entry.filename))

        # File entry table
        if self.files:
            writer.align(16)
            writer.patch_placeholder(file_table_ph, writer.tell())
            for entry in self.files:
                writer.write_struct('<I', fnv1(entry.name))
                name_field_pos = writer.tell()
                name_ph = writer.write_placeholder('<I', name_field_pos)
                scale = (
                    self.archives[entry.archive_index].arc_offset_scale
                    if entry.archive_index < len(self.archives) else 0
                )
                writer.write_struct('<I', (entry.raw_offset >> scale) & 0xFFFFFFFF)
                writer.write_struct('<I', entry.size)
                writer.write_struct('<I', entry.pack_file_serialized_size)
                writer.write_struct('<I', entry.pack_file_resource_size)
                writer.write_struct('<B', entry.archive_index)
                writer.write_struct('<B', entry.flags)
                writer.write(b'\x00\x00')  # padding
                string_refs.append((name_ph, entry.name))

        # String pool — write each unique string once, patch all referencing placeholders
        writer.align(16)
        written_strings: dict[str, int] = {}
        for ph, s in string_refs:
            if s not in written_strings:
                written_strings[s] = writer.tell()
                writer.write_string(s)
            writer.patch_placeholder(ph, written_strings[s])
