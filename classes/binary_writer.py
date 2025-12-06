import struct
from io import BytesIO


class BinaryWriter:
    def __init__(self):
        self.buffer = BytesIO()
        self.placeholders: dict[int, tuple[int, str]] = {}  # position -> (base_position, format)

    def tell(self) -> int:
        return self.buffer.tell()

    def seek(self, offset) -> int:
        return self.buffer.seek(offset)

    def write(self, data: bytes):
        self.buffer.write(data)

    def write_struct(self, format_str: str, *values):
        self.buffer.write(struct.pack(format_str, *values))

    def write_string(self, s: str):
        self.buffer.write(s.encode('utf-8'))
        self.buffer.write(b'\x00')

    def write_placeholder(self, format_str: str, base_position: int) -> int:
        placeholder_pos = self.tell()
        self.placeholders[placeholder_pos] = (base_position, format_str)

        # Write zeros as placeholder
        size = struct.calcsize(format_str)
        self.buffer.write(b'\x00' * size)

        return placeholder_pos

    def patch_placeholder(self, placeholder_pos: int, target_pos: int):
        if placeholder_pos not in self.placeholders:
            raise ValueError(f"No placeholder at position {placeholder_pos}")

        base_position, format_str = self.placeholders[placeholder_pos]
        offset = target_pos - base_position

        # Save current position
        current_pos = self.tell()

        # Seek to placeholder and write the offset
        self.buffer.seek(placeholder_pos)
        self.buffer.write(struct.pack(format_str, offset))

        # Restore position
        self.buffer.seek(current_pos)

    def patch_placeholder_absolute(self, placeholder_pos: int, value: int, format_str: str = '<I'):
        # Save current position
        current_pos = self.tell()

        # Seek to placeholder and write the value
        self.buffer.seek(placeholder_pos)
        self.buffer.write(struct.pack(format_str, value))

        # Restore position
        self.buffer.seek(current_pos)

    def align(self, alignment: int):
        current_pos = self.tell()
        aligned_pos = ((current_pos + alignment - 1) // alignment) * alignment
        padding = aligned_pos - current_pos
        if padding > 0:
            self.buffer.write(b'\x00' * padding)

    def align_relative_eager(self, base_position: int, alignment: int, padding_byte: bytes = b'\x00'):
        current_pos = self.tell()
        offset_from_base = current_pos - base_position
        aligned_offset = ((offset_from_base // alignment) + 1) * alignment
        padding = aligned_offset - offset_from_base
        self.buffer.write(padding_byte * padding)

    def align_relative_proper(self, base_position: int, alignment: int, padding_byte: bytes = b'\x00'):
        current_pos = self.tell()
        offset_from_base = current_pos - base_position
        aligned_offset = ((offset_from_base + alignment - 1) // alignment) * alignment
        padding = aligned_offset - offset_from_base
        if padding > 0:
            self.buffer.write(padding_byte * padding)

    def align_relative_proper_null_terminated(self, base_position: int, alignment: int, padding_byte: bytes = b'\x00'):
        current_pos = self.tell()
        offset_from_base = current_pos - base_position
        aligned_offset = ((offset_from_base + alignment - 1) // alignment) * alignment
        padding = aligned_offset - offset_from_base
        if padding > 0:
            null_bytes = min(padding, 4)
            self.buffer.write(b'\x00' * null_bytes)
            if padding > 4:
                self.buffer.write(padding_byte * (padding - 4))

    def align_min_padding(self, alignment: int, min_padding: int):
        current_pos = self.tell()
        target_pos = current_pos + min_padding
        aligned_pos = ((target_pos + alignment - 1) // alignment) * alignment
        padding = aligned_pos - current_pos
        if padding > 0:
            first_chunk = min(padding, min_padding)
            self.buffer.write(b'\x26' * first_chunk)
            if padding > min_padding:
                self.buffer.write(b'\x40' * (padding - min_padding))

    def get_bytes(self) -> bytes:
        return self.buffer.getvalue()
