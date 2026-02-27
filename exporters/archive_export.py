import os
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Optional

import bpy
from bpy.types import Operator, UILayout
from bpy_extras.io_utils import ExportHelper

import zstandard as zstd

from ..util import label_multiline, log
from ..classes.binary_writer import BinaryWriter
from ..classes.bxon import BXON
from ..classes.pack import PackHeader
from ..classes.tp_archive_file_param import (
    ArchiveLoadType,
    TpArchiveEntry,
    TpArchiveFileParam,
    TpFileEntry,
    ARC_OFFSET_SCALE,
)


SECTOR_ALIGNMENT = 16
BXON_VERSION     = 0x20090422
BXON_PROJECT_ID  = 0xD3ADC0DE
ZSTD_LEVEL       = 1
ZSTD_WINDOW_LOG  = 15          # higher causes game crash


@dataclass
class ArchiveInput:
    name: str       # Key stored in the index (forward-slash relative path)
    full_path: Path # Absolute path to the source file on disk


@dataclass
class ArchiveEntryInfo:
    name: str
    offset: int           # SeparateFrames: byte offset in .arc  |  SingleStream: offset in decompressed stream
    compressed_size: int  # 0 for SingleStream
    pack_serialized_size: int
    pack_resource_size: int


def zstd_compress(data: bytes) -> bytes:
    params = zstd.ZstdCompressionParameters.from_level(ZSTD_LEVEL, window_log=ZSTD_WINDOW_LOG)
    cctx = zstd.ZstdCompressor(compression_params=params)
    return cctx.compress(data)


def zstd_decompress(data: bytes) -> bytes:
    dctx = zstd.ZstdDecompressor()
    try:
        return dctx.decompress(data)
    except zstd.ZstdError:
        # Frame may lack embedded content size; use streaming reader
        with dctx.stream_reader(data) as reader:
            return reader.read()


def get_pack_file_sizes(filepath: Path) -> tuple[int, int, int]:
    """Return (serialized_size, resource_size, total_size) from a PACK file header."""
    with open(filepath, 'rb') as f:
        header = PackHeader.from_stream(f)
    if header.magic != b'PACK':
        raise ValueError(f"Not a PACK file (bad magic): {filepath}")
    return header.pack_serialized_size, header.pack_files_data_size, header.pack_total_size


def scan_inputs(input_dirs: list[str | Path]) -> list[ArchiveInput]:
    """Walk each directory recursively and collect ArchiveInput records."""
    inputs: list[ArchiveInput] = []
    for dir_path in input_dirs:
        dir_path = Path(dir_path)
        for root, _dirs, filenames in os.walk(dir_path):
            for filename in sorted(filenames):
                full_path = Path(root) / filename
                key = full_path.relative_to(dir_path).as_posix()
                inputs.append(ArchiveInput(name=key, full_path=full_path))
        inputs.sort(key=lambda x: x.name)
    return inputs


def build_separate_frames(output_path: Path, inputs: list[ArchiveInput]) -> list[ArchiveEntryInfo]:
    """
    SeparateFrames mode (load type 1/2 — STREAM / STREAM_ONDEMAND).

    Each input file is compressed into its own Zstd frame, written sequentially
    to output_path with 16-byte alignment padding between frames.
    The entry offset is the byte position of the frame within the .arc file.
    """
    entries: list[ArchiveEntryInfo] = []
    with open(output_path, 'wb') as arc:
        for inp in inputs:
            serialized_size, resource_size, _total = get_pack_file_sizes(inp.full_path)

            with open(inp.full_path, 'rb') as src:
                raw = src.read()

            compressed = zstd_compress(raw)
            c_size     = len(compressed)
            padding    = (SECTOR_ALIGNMENT - c_size % SECTOR_ALIGNMENT) % SECTOR_ALIGNMENT

            entry_offset = arc.tell()
            arc.write(compressed)
            if padding:
                arc.write(b'\x00' * padding)

            entries.append(ArchiveEntryInfo(
                name=inp.name,
                offset=entry_offset,
                compressed_size=c_size,
                pack_serialized_size=serialized_size,
                pack_resource_size=resource_size,
            ))

    return entries


def build_single_stream(output_path: Path, inputs: list[ArchiveInput]) -> list[ArchiveEntryInfo]:
    """
    SingleStream mode (load type 0 — PRELOAD_DECOMPRESS).

    All files are concatenated (with 16-byte alignment between them) and
    compressed as a single Zstd stream. The entry offset is the position of
    each file within the *decompressed* stream. compressed_size is always 0.
    """
    uncompressed = bytearray()
    entries: list[ArchiveEntryInfo] = []

    for inp in inputs:
        serialized_size, resource_size, _total = get_pack_file_sizes(inp.full_path)

        pad = (SECTOR_ALIGNMENT - len(uncompressed) % SECTOR_ALIGNMENT) % SECTOR_ALIGNMENT
        uncompressed.extend(b'\x00' * pad)

        entry_offset = len(uncompressed)

        with open(inp.full_path, 'rb') as src:
            data = src.read()
        uncompressed.extend(data)

        entries.append(ArchiveEntryInfo(
            name=inp.name,
            offset=entry_offset,
            compressed_size=0,
            pack_serialized_size=serialized_size,
            pack_resource_size=resource_size,
        ))

    compressed = zstd_compress(bytes(uncompressed))
    with open(output_path, 'wb') as arc:
        arc.write(compressed)

    return entries


def build_arc(output_path: Path | str, inputs: list[ArchiveInput], load_type: ArchiveLoadType = ArchiveLoadType.STREAM) -> list[ArchiveEntryInfo]:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if load_type == ArchiveLoadType.PRELOAD_DECOMPRESS:
        return build_single_stream(output_path, inputs)
    else:
        return build_separate_frames(output_path, inputs)


def add_archive_entry(archives: list[TpArchiveEntry], filename: str, load_type: ArchiveLoadType) -> int:
    """Return the index of an existing entry matching filename, or append a new one."""
    for i, entry in enumerate(archives):
        if entry.filename == filename:
            return i
    archives.append(TpArchiveEntry(
        filename=filename,
        load_type=int(load_type),
        arc_offset_scale=ARC_OFFSET_SCALE,
    ))
    return len(archives) - 1


def register_entries(files: list[TpFileEntry], arc_index: int, built: list[ArchiveEntryInfo]) -> None:
    """Update existing file entries or append new ones from the archive build result."""
    file_map = {f.name: f for f in files}
    for e in built:
        if e.name in file_map:
            fe = file_map[e.name]
            fe.archive_index             = arc_index
            fe.raw_offset                = e.offset
            fe.size                      = e.compressed_size
            fe.pack_file_serialized_size = e.pack_serialized_size
            fe.pack_file_resource_size   = e.pack_resource_size
        else:
            files.append(TpFileEntry(
                name=e.name,
                raw_offset=e.offset,
                size=e.compressed_size,
                pack_file_serialized_size=e.pack_serialized_size,
                pack_file_resource_size=e.pack_resource_size,
                archive_index=arc_index,
                flags=0,
            ))


def serialize_param(param: TpArchiveFileParam, bxon_version: int, bxon_project_id: int) -> bytes:
    """Serialize a TpArchiveFileParam into a BXON-wrapped, zstd-compressed index blob."""
    writer = BinaryWriter()
    BXON(magic=b'BXON', version=bxon_version, project_id=bxon_project_id,
         asset_type="tpArchiveFileParam", asset_data=param).write_to(writer)
    return zstd_compress(writer.get_bytes())


def patch_index(existing_index_path: Path | str, output_arc_path: Path | str, input_dirs: list[str | Path], load_type: ArchiveLoadType = ArchiveLoadType.STREAM, patched_index_path: Optional[Path | str] = None) -> None:
    """
    Build a .arc archive and patch its entries into an existing tpArchiveFileParam index.

    Preserves the original BXON version and project_id. If the archive filename
    already exists in the index it is reused; otherwise a new entry is appended.
    """
    existing_index_path = Path(existing_index_path)
    output_arc_path     = Path(output_arc_path)
    patched_index_path  = Path(patched_index_path) if patched_index_path else existing_index_path

    inputs = scan_inputs(input_dirs)
    if not inputs:
        raise ValueError(f"No files found in input directories: {input_dirs}")

    entries = build_arc(output_arc_path, inputs, load_type)

    with open(existing_index_path, 'rb') as f:
        compressed = f.read()
    bxon = BXON.from_bytes(zstd_decompress(compressed))
    if bxon is None or not isinstance(bxon.asset_data, TpArchiveFileParam):
        raise ValueError(f"Could not parse tpArchiveFileParam from: {existing_index_path}")

    param = bxon.asset_data
    arc_index = add_archive_entry(param.archives, output_arc_path.name, load_type)
    register_entries(param.files, arc_index, entries)

    patched_index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(patched_index_path, 'wb') as f:
        f.write(serialize_param(param, bxon.version, bxon.project_id))


def export(operator, load_type: ArchiveLoadType = ArchiveLoadType.STREAM) -> None:
    filepath = operator.filepath
    archive_root = bpy.context.scene.replicant_archive_root
    input_dirs = [archive_root]
    start = time.perf_counter()

    output_arc_path = Path(filepath)
    index_path      = output_arc_path.parent / "info.arc"

    log.i(f"Searching {archive_root} recursively for files to add to archive...")
    inputs = scan_inputs(input_dirs)
    if not inputs:
        log.e(f"No files found in: {archive_root}")
        operator.report({'ERROR'}, f"No files found in: {archive_root}")
        return {'CANCELLED'}

    for input in inputs:
        log.d(f"Adding {input.full_path} to archive...")

    try:
        entries = build_arc(output_arc_path, inputs, load_type)
    except Exception as e:
        log.e(f"Failed to build archive: {e}")
        operator.report({'ERROR'}, f"Failed to build archive: {e}")
        return {'CANCELLED'}

    param = TpArchiveFileParam(
        archives=[TpArchiveEntry(
            filename=output_arc_path.name,
            load_type=int(load_type),
            arc_offset_scale=ARC_OFFSET_SCALE,
        )],
        files=[
            TpFileEntry(
                name=e.name,
                raw_offset=e.offset,
                size=e.compressed_size,
                pack_file_serialized_size=e.pack_serialized_size,
                pack_file_resource_size=e.pack_resource_size,
                archive_index=0,
                flags=0,
            )
            for e in entries
        ],
    )

    index_path.parent.mkdir(parents=True, exist_ok=True)

    log.d(f"Successfully generated data for archive with {len(inputs)} files")
    gen_end = time.perf_counter()

    log.d(f"Finished generating data in {gen_end - start:.4f} seconds.")
    log.d("Writing new archive file...")

    write_start = time.perf_counter()
    with open(index_path, 'wb') as f:
        f.write(serialize_param(param, BXON_VERSION, BXON_PROJECT_ID))

    end = time.perf_counter()
    log.d(f"Finished writing {filepath} and {index_path} in {end - write_start:.4f} seconds.")
    log.i(f"Total export time: {end - start:.4f} seconds!")

    return {'FINISHED'}


class EXPORT_OT_replicant_archive(Operator, ExportHelper):
    bl_idname = "export.replicant_archive"
    bl_label = "Export Archive"
    bl_description = "Export directories to NieR Replicant archive format"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".arc"

    def draw(self, context) -> None:
        layout: UILayout = self.layout
        label_multiline(context, layout, "An archive containing the following files will be created, along with an 'info.arc'. These are meant for use with the Lunar Tear Loader.")
        row = layout.row()
        op = row.operator("replicant.open_url", text="Check out Lunar Tear here")
        op.url = "https://github.com/ifa-ifa/Lunar-Tear/"

        archive_directories: dict[str, list[str]] = {}
        for root, dirs, files in os.walk(context.scene.replicant_archive_root):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, context.scene.replicant_archive_root)
                head, tail = os.path.split(relative_path)
                archive_directories.setdefault(head, []).append(tail)

        for dir in archive_directories.keys():
            dir_box = layout.box()
            dir_box.label(text=dir, icon='FILE_FOLDER')

            files_box = dir_box.box()
            for file in archive_directories[dir]:
                files_box.label(text=file, icon='DOT')

    def invoke(self, context, event):
        # Validate before opening file dialog
        scene = context.scene

        if context.scene.replicant_archive_root == "":
            self.report({'ERROR'}, "Archive root is none")
            return {'CANCELLED'}

        if not os.path.exists(context.scene.replicant_archive_root) or not os.path.isdir(context.scene.replicant_archive_root):
            self.report({'ERROR'}, "Archive root is not a directory")
            return {'CANCELLED'}

        has_files = False
        for root, dirs, files in os.walk(context.scene.replicant_archive_root):
            if files:
                has_files = True

        if not has_files:
            self.report({'ERROR'}, "No file found in archive root children")
            return {'CANCELLED'}

        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        return export(self)


def register():
    bpy.utils.register_class(EXPORT_OT_replicant_archive)


def unregister():
    bpy.utils.unregister_class(EXPORT_OT_replicant_archive)