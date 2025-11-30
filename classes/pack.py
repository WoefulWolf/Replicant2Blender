import struct
from dataclasses import dataclass
from typing import BinaryIO
from io import BytesIO

from .mesh_data import tpGxMeshData
from .tex_data import tpGxTexData

from .bxon import BXON
from .common import read_string, DataOffset, Import


@dataclass
class PackAssetPackage:
    name_hash: int
    name: str
    content_size: int
    content: BXON | None

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'PackAssetPackage':
        name_hash, = struct.unpack('<I', stream.read(4))
        name_start_offset = stream.tell()
        offset_to_name, content_size = struct.unpack('<II', stream.read(8))

        content_start_offset = stream.tell()
        offset_to_content_start, offset_to_content_end = struct.unpack('<II', stream.read(8))

        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)

        # Read BXON content
        stream.seek(content_start_offset + offset_to_content_start)
        content = BXON.from_stream(stream)

        return cls(
            name_hash=name_hash,
            name=name,
            content_size=content_size,
            content=content
        )


@dataclass
class PackFile:
    name_hash: int
    name: str
    content_size: int
    content: BXON | None
    data_offset: DataOffset

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

        # Read content
        stream.seek(content_start_offset + offset_to_content)
        content = BXON.from_stream(stream)

        stream.seek(return_pos)

        return cls(
            name_hash=name_hash,
            name=name,
            content_size=content_size,
            content=content,
            data_offset=data_offset
        )


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

    def __init__(self, file_index: int, mesh_data=None, tex_data=None):
        self.file_index = file_index
        self.mesh_data = mesh_data
        self.tex_data = tex_data


@dataclass
class Pack:
    header: PackHeader
    imports: list[Import]
    asset_packages: list[PackAssetPackage]
    files: list[PackFile]
    files_data: list[PackFileData]

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

            index = 0
            for file in files:
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
                        file_index=index,
                        mesh_data=mesh_data,
                        tex_data=tex_data
                    ))
                    index += 1

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
