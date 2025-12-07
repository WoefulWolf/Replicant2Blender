import struct
from dataclasses import dataclass
from typing import List, BinaryIO
from io import BytesIO

from ..classes.material_instance import tpGxMaterialInstanceV2

from .common import read_string, align_relative, Import


@dataclass
class Asset:
    asset_type_hash: int
    asset_content: object | None

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Asset':
        asset_start_offset = stream.tell()
        offset_to_asset = struct.unpack('<I', stream.read(4))[0]
        asset_return_pos = stream.tell()
        
        stream.seek(asset_start_offset + offset_to_asset)
        asset_type_hash = struct.unpack('<I', stream.read(4))[0]

        # Only tpGxMaterialInstanceV2 (0x3ABE8760) is fully implemented
        if asset_type_hash != 0x3ABE8760:
            stream.seek(asset_return_pos)
            return cls(
                asset_type_hash=asset_type_hash,
                asset_content=None
            )
        
        material_instance = tpGxMaterialInstanceV2.from_stream(stream)
        stream.seek(asset_return_pos)

        return cls(
            asset_type_hash=asset_type_hash,
            asset_content=material_instance
        )


@dataclass
class tpXonAssetHeader:
    asset_count: int
    import_count: int

    assets: list[Asset]
    imports: list[Import]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'tpXonAssetHeader':
        # Read header
        asset_count = struct.unpack('<I', stream.read(4))[0]
        assets_start_offset = stream.tell()
        offset_to_assets = struct.unpack('<I', stream.read(4))[0]

        import_count = struct.unpack('<I', stream.read(4))[0]
        imports_start_offset = stream.tell()
        offset_to_imports = struct.unpack('<I', stream.read(4))[0]

        # Parse assets
        stream.seek(assets_start_offset + offset_to_assets)
        assets: list[Asset] = []
        for _ in range(asset_count):
            assets.append(Asset.from_stream(stream))

        # Parse imports
        imports: list[Import] = []
        if import_count > 0:
            stream.seek(imports_start_offset + offset_to_imports)
            for _ in range(import_count):
                imports.append(Import.from_stream(stream))

        return cls(
            asset_count=asset_count,
            import_count=import_count,
            assets=assets,
            imports=imports
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'tpXonAssetHeader':
        return cls.from_stream(BytesIO(data))
