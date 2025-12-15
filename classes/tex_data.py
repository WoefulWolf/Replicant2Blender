from dataclasses import dataclass
from typing import BinaryIO
from io import BytesIO

from .tex_head import tpGxTexHead

@dataclass
class tpGxTexData:
    subresource_data: list[bytes]

    @classmethod
    def from_stream(cls, stream: BinaryIO, tex_head: tpGxTexHead) -> 'tpGxTexData':
        asset_resource_start = stream.tell()
        subresource_data = []

        for subresource in tex_head.subresources:
            # Seek to the subresource offset
            stream.seek(asset_resource_start + subresource.offset)

            # Calculate total data size for this mip level
            # For 3D textures, slice_size is per-slice, so multiply by depth
            mip_level_size = subresource.slice_size * subresource.depth

            # Read the raw texture data
            data = stream.read(mip_level_size)
            subresource_data.append(data)

        return cls(subresource_data=subresource_data)

    @classmethod
    def from_bytes(cls, data: bytes, tex_head: tpGxTexHead) -> 'tpGxTexData':
        return cls.from_stream(BytesIO(data), tex_head)

    def write_to(self, writer, tex_head: tpGxTexHead) -> None:
        asset_resource_start = writer.tell()

        for i, data in enumerate(self.subresource_data):
            subresource = tex_head.subresources[i]

            # Update the subresource offset to current position
            subresource.offset = writer.tell() - asset_resource_start

            # Update the slice_size field based on actual data length
            # For 3D textures, slice_size should be per-slice, so divide by depth
            if subresource.depth > 1:
                subresource.slice_size = len(data) // subresource.depth
            else:
                subresource.slice_size = len(data)

            # Write the raw texture data
            writer.write(data)
