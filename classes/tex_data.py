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
            # Read the raw texture data
            data = stream.read(subresource.size)
            subresource_data.append(data)

        return cls(subresource_data=subresource_data)

    @classmethod
    def from_bytes(cls, data: bytes, tex_head: tpGxTexHead) -> 'tpGxTexData':
        return cls.from_stream(BytesIO(data), tex_head)
