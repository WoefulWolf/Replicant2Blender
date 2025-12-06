import struct
from dataclasses import dataclass
from typing import List, BinaryIO
from io import BytesIO

from .common import read_string, align_relative, Import


@dataclass
class Constant:
    constant_name_hash: int
    constant_name: str
    value0: float
    value1: float
    value2: float
    value3: float
    value4: float
    value5: float
    byte0: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Constant':
        const_name_hash = struct.unpack('<I', stream.read(4))[0]
        constant_name_start_offset = stream.tell()
        offset_to_name = struct.unpack('<I', stream.read(4))[0]

        # Read values
        values = struct.unpack('<ffffffB', stream.read(25))

        align_relative(stream, 0, 4)

        # Read name
        return_pos = stream.tell()
        stream.seek(constant_name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        return cls(
            constant_name_hash=const_name_hash,
            constant_name=name,
            value0=values[0],
            value1=values[1],
            value2=values[2],
            value3=values[3],
            value4=values[4],
            value5=values[5],
            byte0=values[6]
        )


@dataclass
class ConstantBuffer:
    constant_buffer_name_hash: int
    constant_buffer_name: str
    unknown_uint32_0: int
    constants: List[Constant]

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'ConstantBuffer':
        cb_name_hash = struct.unpack('<I', stream.read(4))[0]
        cb_name_start_offset = stream.tell()
        offset_to_name = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(cb_name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        unknown_uint32_0, constants_count = struct.unpack('<II', stream.read(8))
        constants_start_offset = stream.tell()
        offset_to_constants = struct.unpack('<I', stream.read(4))[0]

        # Parse constants
        constants = []
        return_pos = stream.tell()
        stream.seek(constants_start_offset + offset_to_constants)
        for _ in range(constants_count):
            constants.append(Constant.from_stream(stream))
        stream.seek(return_pos)

        return cls(
            constant_buffer_name_hash=cb_name_hash,
            constant_buffer_name=name,
            unknown_uint32_0=unknown_uint32_0,
            constants=constants
        )


@dataclass
class Texture:
    sampler_name_hash: int
    sampler_name: str
    texture_name_hash: int
    texture_name: str
    unknown_byte: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Texture':
        sampler_hash = struct.unpack('<I', stream.read(4))[0]
        sampler_name_start_offset = stream.tell()
        offset_to_sampler = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(sampler_name_start_offset + offset_to_sampler)
        sampler_name = read_string(stream)
        stream.seek(return_pos)

        texture_hash = struct.unpack('<I', stream.read(4))[0]
        texture_name_start_offset = stream.tell()
        offset_to_texture = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(texture_name_start_offset + offset_to_texture)
        texture_name = read_string(stream)
        stream.seek(return_pos)

        unknown_byte = struct.unpack('<B', stream.read(1))[0]
        align_relative(stream, 0, 4)

        return cls(
            sampler_name_hash=sampler_hash,
            sampler_name=sampler_name,
            texture_name_hash=texture_hash,
            texture_name=texture_name,
            unknown_byte=unknown_byte
        )


@dataclass
class TextureParameter:
    parameter_name_hash: int
    parameter_name: str
    value0: int
    value1: int
    value2: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'TextureParameter':
        param_name_start_offset = stream.tell()
        param_hash, offset_to_name, value0, value1, value2 = struct.unpack('<IIIII', stream.read(20))

        return_pos = stream.tell()
        stream.seek(param_name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        return cls(
            parameter_name_hash=param_hash,
            parameter_name=name,
            value0=value0,
            value1=value1,
            value2=value2
        )


@dataclass
class Asset:
    asset_type_hash: int
    parent_asset_path_hash: int
    parent_asset_path: str
    constant_buffers: list[ConstantBuffer]
    textures: list[Texture]
    texture_parameters: list[TextureParameter]
    unknown_uint32s: list[int]
    unknown_short: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Asset':
        asset_start_offset = stream.tell()
        offset_to_asset = struct.unpack('<I', stream.read(4))[0]
        asset_return_pos = stream.tell()
        
        stream.seek(asset_start_offset + offset_to_asset)
        asset_type_hash = struct.unpack('<I', stream.read(4))[0]

        # Only material instances (0x3ABE8760) are fully implemented
        if asset_type_hash != 0x3ABE8760:
            stream.seek(asset_return_pos)
            return cls(
                asset_type_hash=asset_type_hash,
                parent_asset_path_hash=0,
                parent_asset_path="",
                constant_buffers=[],
                textures=[],
                texture_parameters=[],
                unknown_uint32s=[],
                unknown_short=0
            )

        parent_asset_path_hash = struct.unpack('<I', stream.read(4))[0]

        if parent_asset_path_hash == 0:
            stream.seek(asset_return_pos)
            return cls(
                asset_type_hash=asset_type_hash,
                parent_asset_path_hash=0,
                parent_asset_path="",
                constant_buffers=[],
                textures=[],
                texture_parameters=[],
                unknown_uint32s=[],
                unknown_short=0
            )

        parent_asset_path_start_offset = stream.tell()
        offset_to_parent_asset_path = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(parent_asset_path_start_offset + offset_to_parent_asset_path)
        parent_asset_path = read_string(stream)
        stream.seek(return_pos)

        # Read counts and offsets
        constant_buffers_count = struct.unpack('<I', stream.read(4))[0]
        constant_buffers_start_offset = stream.tell()
        offset_to_constant_buffers = struct.unpack('<I', stream.read(4))[0]

        textures_count = struct.unpack('<I', stream.read(4))[0]
        textures_start_offset = stream.tell()
        offset_to_textures = struct.unpack('<I', stream.read(4))[0]

        texture_parameters_count = struct.unpack('<I', stream.read(4))[0]
        texture_parameters_start_offset = stream.tell()
        offset_to_texture_parameters = struct.unpack('<I', stream.read(4))[0]

        unknown_uint32s = list(struct.unpack('<II', stream.read(8)))
        unknown_short = struct.unpack('<H', stream.read(2))[0]

        # Parse constant buffers
        constant_buffers = []
        stream.seek(constant_buffers_start_offset + offset_to_constant_buffers)
        for _ in range(constant_buffers_count):
            constant_buffers.append(ConstantBuffer.from_stream(stream))

        # Parse textures
        textures = []
        stream.seek(textures_start_offset + offset_to_textures)
        for _ in range(textures_count):
            textures.append(Texture.from_stream(stream))

        # Parse texture parameters
        texture_parameters = []
        stream.seek(texture_parameters_start_offset + offset_to_texture_parameters)
        for _ in range(texture_parameters_count):
            texture_parameters.append(TextureParameter.from_stream(stream))

        stream.seek(asset_return_pos)

        return cls(
            asset_type_hash=asset_type_hash,
            parent_asset_path_hash=parent_asset_path_hash,
            parent_asset_path=parent_asset_path,
            constant_buffers=constant_buffers,
            textures=textures,
            texture_parameters=texture_parameters,
            unknown_uint32s=unknown_uint32s,
            unknown_short=unknown_short
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
