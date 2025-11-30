import struct
from dataclasses import dataclass
from typing import Optional, Union, BinaryIO
from io import BytesIO

from .common import read_string


@dataclass
class BXON:
    magic: bytes
    version: int
    project_id: int
    asset_type: str
    asset_data: object | None

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'BXON | None':
        # Read header
        magic, version, project_id = struct.unpack('<4sII', stream.read(12))

        # Validate magic
        if magic != b'BXON':
            return None

        asset_type_start_offset = stream.tell()
        offset_to_type = struct.unpack('<I', stream.read(4))[0]

        asset_data_start_offset = stream.tell()
        offset_to_data = struct.unpack('<I', stream.read(4))[0]

        # Read asset type string
        stream.seek(asset_type_start_offset + offset_to_type)
        asset_type = read_string(stream)

        # Read asset data based on type
        stream.seek(asset_data_start_offset + offset_to_data)
        asset_data = None

        # Import here to avoid circular imports
        if asset_type == "tpXonAssetHeader":
            from .asset_package import tpXonAssetHeader
            asset_data = tpXonAssetHeader.from_stream(stream)
        elif asset_type == "tpGxMeshHead":
            from .mesh_head import tpGxMeshHead
            asset_data = tpGxMeshHead.from_stream(stream)
        elif asset_type == "tpGxTexHead":
            from .tex_head import tpGxTexHead
            asset_data = tpGxTexHead.from_stream(stream)
        # Other asset types can be added here (tpTandaFontSdfParam, etc.)

        return cls(
            magic=magic,
            version=version,
            project_id=project_id,
            asset_type=asset_type,
            asset_data=asset_data
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'BXON | None':
        return cls.from_stream(BytesIO(data))
