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

    @staticmethod
    def write_list(writer, assets: list['Asset']) -> None:
        from ..classes.binary_writer import BinaryWriter

        placeholders = []

        for asset in assets:
            asset_start_offset = writer.tell()
            asset_placeholder = writer.write_placeholder('<I', asset_start_offset)
            placeholders.append((asset_placeholder, asset))

        writer.align_min_padding(8, 8)
        for asset_placeholder, asset in placeholders:
            asset_pos = writer.tell()
            writer.patch_placeholder(asset_placeholder, asset_pos)

            # Write asset type hash
            writer.write_struct('<I', asset.asset_type_hash)

            # Write asset content if it exists and has a write_to method
            if asset.asset_content is not None and hasattr(asset.asset_content, 'write_to'):
                asset.asset_content.write_to(writer)


@dataclass
class tpXonAssetHeader:
    asset_count: int
    import_count: int

    assets: list[Asset]
    imports: list[Import]

    @classmethod
    def new(cls) -> 'tpXonAssetHeader':
        return cls(
            asset_count=0,
            import_count=0,
            assets=[],
            imports=[]
        )

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

    def write_to(self, writer) -> None:
        from ..classes.binary_writer import BinaryWriter

        # Write asset count and offset placeholder
        writer.write_struct('<I', len(self.assets))
        assets_start_offset = writer.tell()
        assets_placeholder = writer.write_placeholder('<I', assets_start_offset)

        # Write import count and offset placeholder
        writer.write_struct('<I', len(self.imports))
        imports_start_offset = writer.tell()
        imports_placeholder = writer.write_placeholder('<I', imports_start_offset)

        # Write assets
        if len(self.assets) > 0:
            writer.align_min_padding(8, 8)
            assets_pos = writer.tell()
            writer.patch_placeholder(assets_placeholder, assets_pos)
            Asset.write_list(writer, self.assets)

        # Write imports
        if len(self.imports) > 0:
            writer.align_min_padding(8, 8)
            imports_pos = writer.tell()
            writer.patch_placeholder(imports_placeholder, imports_pos)
            Import.write_list(writer, self.imports)
