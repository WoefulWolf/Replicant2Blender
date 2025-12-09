import struct
from dataclasses import dataclass
from typing import BinaryIO
from io import BytesIO

from ..classes.binary_writer import BinaryWriter
from ..classes.tex_head import tpGxTexHead
from ..classes.mesh_head import tpGxMeshHead

from .mesh_data import tpGxMeshData
from .tex_data import tpGxTexData

from .bxon import BXON
from .common import read_string, DataOffset, Import
from .asset_package import AssetTypeHash


@dataclass
class PackAssetPackage:
    name_hash: int
    name: str
    content: BXON | None
    raw_content_bytes: bytes

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'PackAssetPackage':
        name_hash, = struct.unpack('<I', stream.read(4))
        name_start_offset = stream.tell()
        offset_to_name, content_size = struct.unpack('<II', stream.read(8))

        content_start_offset = stream.tell()
        offset_to_content_start = struct.unpack('<I', stream.read(4))[0]
        content_end_offset = stream.tell()
        offset_to_content_end = struct.unpack('<I', stream.read(4))[0]

        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)

        # Read BXON content
        content_pos = content_start_offset + offset_to_content_start
        content_end_pos = content_end_offset + offset_to_content_end

        # Store raw bytes for later serialization
        stream.seek(content_pos)
        raw_content_bytes = stream.read(content_end_pos - content_pos)

        # Parse BXON from the raw bytes
        stream.seek(content_pos)
        content = BXON.from_stream(stream)

        return cls(
            name_hash=name_hash,
            name=name,
            content=content,
            raw_content_bytes=raw_content_bytes
        )

    def write_to(self, writer: BinaryWriter) -> None:
        from .binary_writer import BinaryWriter

        writer.write_struct('<I', self.name_hash)

        name_start_offset = writer.tell()
        name_placeholder = writer.write_placeholder('<I', name_start_offset)
        writer.write_struct('<I', len(self.raw_content_bytes))

        content_start_offset = writer.tell()
        content_start_placeholder = writer.write_placeholder('<I', content_start_offset)
        content_end_offset = writer.tell()
        content_end_placeholder = writer.write_placeholder('<I', content_end_offset)

        # Write name (aligned)
        writer.align_min_padding(8, 8)
        name_pos = writer.tell()
        writer.patch_placeholder(name_placeholder, name_pos)
        writer.write_string(self.name)

        # Write raw BXON content bytes (aligned)
        writer.align_min_padding(8, 8)
        content_pos = writer.tell()
        writer.patch_placeholder(content_start_placeholder, content_pos)

        if self.content:
            if self.content.asset_type == "tpXonAssetHeader" and  all(a.asset_type_hash == AssetTypeHash.tpGxMaterialInstanceV2 for a in self.content.asset_data.assets):
                self.content.write_to(writer)
                writer.align_min_padding(8, 8)
            else:
                writer.write(self.raw_content_bytes)
        else:
            writer.write(self.raw_content_bytes)

        content_end_pos = writer.tell()
        writer.patch_placeholder(content_end_placeholder, content_end_pos)

    @staticmethod
    def write_list(writer, asset_packages: list['PackAssetPackage']) -> None:
        from .binary_writer import BinaryWriter

        for package in asset_packages:
            package.write_to(writer)


@dataclass
class PackFile:
    name_hash: int
    name: str
    content: BXON | None
    data_offset: DataOffset
    raw_content_bytes: bytes

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'PackFile':
        name_hash = struct.unpack('<I', stream.read(4))[0]
        name_start_offset = stream.tell()
        offset_to_name, content_size = struct.unpack('<II', stream.read(8))

        content_start_offset = stream.tell()
        offset_to_content = struct.unpack('<I', stream.read(4))[0]

        # Parse data offset
        data_offset = DataOffset.from_stream(stream)

        # Read name
        return_pos = stream.tell()
        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)

        # Read content and store raw bytes
        content_pos = content_start_offset + offset_to_content
        stream.seek(content_pos)

        # Store raw bytes for serialization
        raw_content_bytes = stream.read(content_size)

        # Parse BXON from raw bytes
        content = BXON.from_bytes(raw_content_bytes)

        stream.seek(return_pos)

        return cls(
            name_hash=name_hash,
            name=name,
            content=content,
            data_offset=data_offset,
            raw_content_bytes=raw_content_bytes
        )

    @staticmethod
    def write_list(writer, pack_files: list['PackFile']):
        from .binary_writer import BinaryWriter

        placeholders = []

        for pack_file in pack_files:
            writer.write_struct('<I', pack_file.name_hash)

            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)

            content_size_pos = writer.tell()
            writer.write_struct('<I', 0)  # Placeholder for content_size

            content_start_offset = writer.tell()
            content_placeholder = writer.write_placeholder('<I', content_start_offset)

            data_offset_pos = writer.tell()
            pack_file.data_offset.write_to(writer)

            placeholders.append((name_placeholder, content_placeholder, content_size_pos, pack_file.name, pack_file.content))

        for i, (name_placeholder, content_placeholder, content_size_pos, name, content) in enumerate(placeholders):
            pack_file = pack_files[i]

            # Write name (aligned)
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(name)

            # Write content (aligned)
            writer.align_min_padding(32, 8)
            content_pos = writer.tell()
            writer.patch_placeholder(content_placeholder, content_pos)

            if content is not None:
                # BXON was successfully parsed, serialize it
                content.write_to(writer)
            elif pack_file.raw_content_bytes:
                # BXON failed to parse, write raw bytes
                writer.write(pack_file.raw_content_bytes)

            # Calculate and patch content_size
            content_end_pos = writer.tell()
            actual_content_size = content_end_pos - content_pos
            writer.patch_placeholder_absolute(content_size_pos, actual_content_size, '<I')


@dataclass
class PackHeader:
    magic: bytes
    version: int
    pack_total_size: int
    pack_serialized_size: int
    pack_files_data_size: int
    imports_count: int
    imports_offset: int
    asset_packages_count: int
    asset_packages_offset: int
    files_count: int
    files_offset: int

    @classmethod
    def new(cls) -> 'PackHeader':
        return cls(
            magic=b'PACK',
            version=4,
            pack_total_size=0,
            pack_serialized_size=0,
            pack_files_data_size=0,
            imports_count=0,
            imports_offset=0,
            asset_packages_count=0,
            asset_packages_offset=0,
            files_count=0,
            files_offset=0
        )

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'PackHeader':
        magic = struct.unpack('<4s', stream.read(4))[0]
        version = struct.unpack('<I', stream.read(4))[0]
        pack_total_size = struct.unpack('<I', stream.read(4))[0]
        pack_serialized_size = struct.unpack('<I', stream.read(4))[0]
        pack_files_data_size = struct.unpack('<I', stream.read(4))[0]
        imports_count = struct.unpack('<I', stream.read(4))[0]
        imports_start_offset = stream.tell()
        offset_to_imports = struct.unpack('<I', stream.read(4))[0]
        asset_packages_count = struct.unpack('<I', stream.read(4))[0]
        asset_packages_start_offset = stream.tell()
        offset_to_asset_packages = struct.unpack('<I', stream.read(4))[0]
        files_count = struct.unpack('<I', stream.read(4))[0]
        files_start_offset = stream.tell()
        offset_to_files = struct.unpack('<I', stream.read(4))[0]
        return cls(
            magic=magic,
            version=version,
            pack_total_size=pack_total_size,
            pack_serialized_size=pack_serialized_size,
            pack_files_data_size=pack_files_data_size,
            imports_count=imports_count,
            imports_offset=imports_start_offset+offset_to_imports,
            asset_packages_count=asset_packages_count,
            asset_packages_offset=asset_packages_start_offset+offset_to_asset_packages,
            files_count=files_count,
            files_offset=files_start_offset+offset_to_files
        )


@dataclass
class PackFileData:
    file_index: int
    mesh_data: tpGxMeshData | None  # tpGxMeshData
    tex_data: tpGxTexData | None   # tpGxTexData
    raw_data: bytes | None  # Raw bytes for non-mesh files

    def __init__(self, file_index: int, mesh_data=None, tex_data=None, raw_data=None):
        self.file_index = file_index
        self.mesh_data = mesh_data
        self.tex_data = tex_data
        self.raw_data = raw_data


@dataclass
class Pack:
    header: PackHeader
    imports: list[Import]
    asset_packages: list[PackAssetPackage]
    files: list[PackFile]
    files_data: list[PackFileData]

    @classmethod
    def new(cls) -> 'Pack':
        return cls(
            header=PackHeader.new(),
            imports=[],
            asset_packages=[],
            files=[],
            files_data=[]
        )

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Pack':
        # Parse header
        stream.seek(0)
        header = PackHeader.from_stream(stream)

        # Validate magic
        if header.magic != b'PACK':
            raise ValueError(f"Invalid PACK magic: {header.magic}")

        # Parse imports
        imports: list[Import] = []
        if header.imports_count > 0:
            stream.seek(header.imports_offset)
            for _ in range(header.imports_count):
                imports.append(Import.from_stream(stream))

        # Parse asset packages
        asset_packages: list[PackAssetPackage] = []
        if header.asset_packages_count > 0:
            stream.seek(header.asset_packages_offset)
            for _ in range(header.asset_packages_count):
                asset_packages.append(PackAssetPackage.from_stream(stream))

        # Parse files
        files: list[PackFile] = []
        if header.files_count > 0:
            stream.seek(header.files_offset)
            for _ in range(header.files_count):
                files.append(PackFile.from_stream(stream))

        # Parse files data (raw mesh/texture data)
        files_data = []
        if header.pack_files_data_size != 0:
            # Import here to avoid circular imports
            from .mesh_data import tpGxMeshData
            from .tex_data import tpGxTexData

            for file_index, file in enumerate(files):
                if file.data_offset.has_data:
                    # Seek to the file data
                    stream.seek(header.pack_serialized_size + file.data_offset.offset)

                    mesh_data = None
                    tex_data = None

                    # Parse based on asset type
                    if file.content and file.content.asset_type == "tpGxMeshHead":
                        mesh_data = tpGxMeshData.from_stream(stream, file.content.asset_data)
                    elif file.content and file.content.asset_type == "tpGxTexHead":
                        tex_data = tpGxTexData.from_stream(stream, file.content.asset_data)

                    files_data.append(PackFileData(
                        file_index=file_index,
                        mesh_data=mesh_data,
                        tex_data=tex_data
                    ))

        return cls(
            header=header,
            imports=imports,
            asset_packages=asset_packages,
            files=files,
            files_data=files_data
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Pack':
        return cls.from_stream(BytesIO(data))

    @classmethod
    def from_file(cls, filepath: str) -> 'Pack':
        with open(filepath, 'rb') as f:
            return cls.from_stream(f)

    def to_bytes(self) -> bytes:
        from .binary_writer import BinaryWriter

        writer = BinaryWriter()

        # Write magic and version
        writer.write_struct('<4s', b'PACK')
        writer.write_struct('<I', self.header.version)

        # Placeholders for header values
        pack_total_size_pos = writer.tell()
        writer.write_struct('<I', 0)  # pack_total_size placeholder

        pack_serialized_size_pos = writer.tell()
        writer.write_struct('<I', 0)  # pack_serialized_size placeholder

        pack_files_data_size_pos = writer.tell()
        writer.write_struct('<I', 0)  # pack_files_data_size placeholder

        # Write imports count and offset placeholder
        writer.write_struct('<I', len(self.imports))
        imports_start_offset = writer.tell()
        imports_placeholder = writer.write_placeholder('<I', imports_start_offset)

        # Write asset_packages count and offset placeholder
        writer.write_struct('<I', len(self.asset_packages))
        asset_packages_start_offset = writer.tell()
        asset_packages_placeholder = writer.write_placeholder('<I', asset_packages_start_offset)

        # Write files count and offset placeholder
        writer.write_struct('<I', len(self.files))
        files_start_offset = writer.tell()
        files_placeholder = writer.write_placeholder('<I', files_start_offset)

        # Write imports
        if self.imports:
            writer.align_min_padding(8, 8)
            imports_pos = writer.tell()
            writer.patch_placeholder(imports_placeholder, imports_pos)
            Import.write_list(writer, self.imports)

        # Write asset packages
        if self.asset_packages:
            writer.align_min_padding(8, 8)
            asset_packages_pos = writer.tell()
            writer.patch_placeholder(asset_packages_placeholder, asset_packages_pos)
            PackAssetPackage.write_list(writer, self.asset_packages)

        # Write b'\x05error'
        writer.write(b'\x05error')

        # Write files
        if self.files:
            writer.align_min_padding(8, 8)
            files_pos = writer.tell()
            writer.patch_placeholder(files_placeholder, files_pos)
            PackFile.write_list(writer, self.files)

        # Calculate pack_serialized_size (end of serialized data, before files_data)
        writer.align_min_padding(4, 0)
        pack_serialized_size = writer.tell()
        writer.patch_placeholder_absolute(pack_serialized_size_pos, pack_serialized_size, '<I')

        # Write files data (mesh/texture data)
        files_data_start = writer.tell()
        for i, file_data in enumerate(self.files_data):
            writer.align_relative_proper_null_terminated(files_data_start, 32, b'\x40')
            if file_data.mesh_data:
                file = self.files[file_data.file_index]
                file.data_offset.offset = writer.tell() - files_data_start
                mesh_head: tpGxMeshHead = file.content.asset_data
                # Record the start of this meshData for relative alignment
                mesh_data_start = writer.tell()
                file_data.mesh_data.write_to(writer, mesh_data_start, mesh_head)
            if file_data.tex_data:
                file = self.files[file_data.file_index]
                file.data_offset.offset = writer.tell() - files_data_start
                tex_head: tpGxTexHead = file.content.asset_data
                file_data.tex_data.write_to(writer, tex_head)

        writer.align_relative_proper_null_terminated(files_data_start, 4)

        # Calculate pack_files_data_size
        pack_files_data_size = writer.tell() - files_data_start
        writer.patch_placeholder_absolute(pack_files_data_size_pos, pack_files_data_size, '<I')

        # Calculate pack_total_size
        pack_total_size = writer.tell()
        writer.patch_placeholder_absolute(pack_total_size_pos, pack_total_size, '<I')

        if self.files:
            writer.seek(files_pos)
            PackFile.write_list(writer, self.files)

        return writer.get_bytes()

    def to_file(self, filepath: str) -> None:
        with open(filepath, 'wb') as f:
            f.write(self.to_bytes())
