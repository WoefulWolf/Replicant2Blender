import struct
from dataclasses import dataclass
from typing import BinaryIO

from ..classes.common import align_relative, read_string

@dataclass
class Constant:
    name_hash: int
    name: str
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
            name_hash=const_name_hash,
            name=name,
            value0=values[0],
            value1=values[1],
            value2=values[2],
            value3=values[3],
            value4=values[4],
            value5=values[5],
            byte0=values[6]
        )

    @staticmethod
    def write_list(writer, constants: list['Constant']) -> None:
        placeholders = []

        for constant in constants:
            writer.write_struct('<I', constant.name_hash)
            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)

            # Write values
            writer.write_struct('<ffffffB', constant.value0, constant.value1, constant.value2,
                               constant.value3, constant.value4, constant.value5, constant.byte0)

            writer.align_relative_proper(0, 4)

            placeholders.append((name_placeholder, name_start_offset, constant.name))

        # Write constant names
        for name_placeholder, name_start_offset, name in placeholders:
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(name)


@dataclass
class ConstantBuffer:
    name_hash: int
    name: str
    unknown_uint32_0: int
    constants: list[Constant]

    @classmethod
    def new(cls) -> 'ConstantBuffer':
        return cls(
            name_hash=0,
            name="",
            unknown_uint32_0=0,
            constants=[]
        )

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
            name_hash=cb_name_hash,
            name=name,
            unknown_uint32_0=unknown_uint32_0,
            constants=constants
        )

    @staticmethod
    def write_list(writer, constant_buffers: list['ConstantBuffer']) -> None:
        cb_placeholders = []

        # Write constant buffer structures
        for cb in constant_buffers:
            writer.write_struct('<I', cb.name_hash)
            cb_name_start_offset = writer.tell()
            cb_name_placeholder = writer.write_placeholder('<I', cb_name_start_offset)

            writer.write_struct('<I', cb.unknown_uint32_0)
            writer.write_struct('<I', len(cb.constants))
            constants_start_offset = writer.tell()
            constants_placeholder = writer.write_placeholder('<I', constants_start_offset)

            cb_placeholders.append((cb_name_placeholder, cb_name_start_offset, constants_placeholder, constants_start_offset, cb))

        # Write constants for each constant buffer
        for cb_name_placeholder, cb_name_start_offset, constants_placeholder, constants_start_offset, cb in cb_placeholders:
            writer.align_min_padding(8, 8)
            cb_name_pos = writer.tell()
            writer.patch_placeholder(cb_name_placeholder, cb_name_pos)
            writer.write_string(cb.name)
            
            if len(cb.constants) > 0:
                writer.align_min_padding(8, 8)
                constants_pos = writer.tell()
                writer.patch_placeholder(constants_placeholder, constants_pos)
                Constant.write_list(writer, cb.constants)


@dataclass
class TextureSampler:
    name_hash: int
    name: str
    texture_name_hash: int
    texture_name: str
    unknown_byte: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'TextureSampler':
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
            name_hash=sampler_hash,
            name=sampler_name,
            texture_name_hash=texture_hash,
            texture_name=texture_name,
            unknown_byte=unknown_byte
        )

    @staticmethod
    def write_list(writer, textures: list['TextureSampler']) -> None:
        placeholders = []

        # Write texture sampler structures
        for texture in textures:
            writer.write_struct('<I', texture.name_hash)
            sampler_name_start_offset = writer.tell()
            sampler_name_placeholder = writer.write_placeholder('<I', sampler_name_start_offset)

            writer.write_struct('<I', texture.texture_name_hash)
            texture_name_start_offset = writer.tell()
            texture_name_placeholder = writer.write_placeholder('<I', texture_name_start_offset)

            writer.write_struct('<B', texture.unknown_byte)
            writer.align_relative_proper(0, 4)

            placeholders.append((sampler_name_placeholder, sampler_name_start_offset,
                               texture_name_placeholder, texture_name_start_offset, texture))

        # Write texture sampler names and texture names
        for sampler_name_placeholder, sampler_name_start_offset, texture_name_placeholder, texture_name_start_offset, texture in placeholders:
            writer.align_min_padding(8, 8)
            sampler_name_pos = writer.tell()
            writer.patch_placeholder(sampler_name_placeholder, sampler_name_pos)
            writer.write_string(texture.name)

            writer.align_min_padding(8, 8)
            texture_name_pos = writer.tell()
            writer.patch_placeholder(texture_name_placeholder, texture_name_pos)
            writer.write_string(texture.texture_name)

@dataclass
class TextureParameter:
    name_hash: int
    name: str
    value0: int
    value1: int
    value2: int

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'TextureParameter':
        param_hash = struct.unpack('<I', stream.read(4))[0]
        param_name_start_offset = stream.tell()
        offset_to_name, value0, value1, value2 = struct.unpack('<IIII', stream.read(16))

        return_pos = stream.tell()
        stream.seek(param_name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        return cls(
            name_hash=param_hash,
            name=name,
            value0=value0,
            value1=value1,
            value2=value2
        )

    @staticmethod
    def write_list(writer, texture_parameters: list['TextureParameter']) -> None:
        placeholders = []

        # Write texture parameter structures
        for param in texture_parameters:
            writer.write_struct('<I', param.name_hash)
            param_name_start_offset = writer.tell()
            param_name_placeholder = writer.write_placeholder('<I', param_name_start_offset)
            writer.write_struct('<III', param.value0, param.value1, param.value2)

            placeholders.append((param_name_placeholder, param_name_start_offset, param.name))

        # Write texture parameter names
        for param_name_placeholder, param_name_start_offset, name in placeholders:
            writer.align_min_padding(8, 8)
            param_name_pos = writer.tell()
            writer.patch_placeholder(param_name_placeholder, param_name_pos)
            writer.write_string(name)

@dataclass
class tpGxMaterialInstanceV2:
    parent_asset_path_hash: int
    parent_asset_path: str
    constant_buffers: list[ConstantBuffer]
    texture_samplers: list[TextureSampler]
    texture_parameters: list[TextureParameter]
    # disableShadowCasting, forceShadowCasting, unknown, unknown, drawBackfaces0, drawBackfaces1, unknown, unknown, enableAlpha0, enableAlpha1
    flags: tuple[bool, bool, bool, bool, bool, bool, bool, bool, bool, bool]

    @classmethod
    def new(cls) -> 'tpGxMaterialInstanceV2':
        return cls(
            parent_asset_path_hash=0,
            parent_asset_path="",
            constant_buffers=[],
            texture_samplers=[],
            texture_parameters=[],
            flags = (False, True, False, False, False, False, False, False, False, False)
        )

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'tpGxMaterialInstanceV2':
        parent_asset_path_hash = struct.unpack('<I', stream.read(4))[0]

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

        flags = struct.unpack('<??????????', stream.read(10))

        # Parse constant buffers
        constant_buffers = []
        stream.seek(constant_buffers_start_offset + offset_to_constant_buffers)
        for _ in range(constant_buffers_count):
            constant_buffers.append(ConstantBuffer.from_stream(stream))

        # Parse textures
        textures = []
        stream.seek(textures_start_offset + offset_to_textures)
        for _ in range(textures_count):
            textures.append(TextureSampler.from_stream(stream))

        # Parse texture parameters
        texture_parameters = []
        stream.seek(texture_parameters_start_offset + offset_to_texture_parameters)
        for _ in range(texture_parameters_count):
            texture_parameters.append(TextureParameter.from_stream(stream))

        return cls(
            parent_asset_path_hash=parent_asset_path_hash,
            parent_asset_path=parent_asset_path,
            constant_buffers=constant_buffers,
            texture_samplers=textures,
            texture_parameters=texture_parameters,
            flags=flags
        )

    def write_to(self, writer) -> None:
        # Write parent asset path hash and placeholder
        writer.write_struct('<I', self.parent_asset_path_hash)
        parent_asset_path_start_offset = writer.tell()
        parent_asset_path_placeholder = writer.write_placeholder('<I', parent_asset_path_start_offset)

        # Write constant buffers count and placeholder
        writer.write_struct('<I', len(self.constant_buffers))
        constant_buffers_start_offset = writer.tell()
        constant_buffers_placeholder = writer.write_placeholder('<I', constant_buffers_start_offset)

        # Write textures count and placeholder
        writer.write_struct('<I', len(self.texture_samplers))
        textures_start_offset = writer.tell()
        textures_placeholder = writer.write_placeholder('<I', textures_start_offset)

        # Write texture parameters count and placeholder
        writer.write_struct('<I', len(self.texture_parameters))
        texture_parameters_start_offset = writer.tell()
        texture_parameters_placeholder = writer.write_placeholder('<I', texture_parameters_start_offset)

        # Write unknown values
        writer.write_struct('<??????????', *self.flags)

        # Write parent asset path string
        writer.align_min_padding(8, 8)
        parent_asset_path_pos = writer.tell()
        writer.patch_placeholder(parent_asset_path_placeholder, parent_asset_path_pos)
        writer.write_string(self.parent_asset_path)

        # Write constant buffers
        if len(self.constant_buffers) > 0:
            writer.align_min_padding(8, 8)
            constant_buffers_pos = writer.tell()
            writer.patch_placeholder(constant_buffers_placeholder, constant_buffers_pos)
            ConstantBuffer.write_list(writer, self.constant_buffers)

        # Write textures
        if len(self.texture_samplers) > 0:
            writer.align_min_padding(8, 8)
            textures_pos = writer.tell()
            writer.patch_placeholder(textures_placeholder, textures_pos)
            TextureSampler.write_list(writer, self.texture_samplers)

        # Write texture parameters
        if len(self.texture_parameters) > 0:
            writer.align_min_padding(8, 8)
            texture_parameters_pos = writer.tell()
            writer.patch_placeholder(texture_parameters_placeholder, texture_parameters_pos)
            TextureParameter.write_list(writer, self.texture_parameters)