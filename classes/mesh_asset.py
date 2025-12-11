import struct
from dataclasses import dataclass, field
from typing import BinaryIO

from ..util import fnv1
from ..classes.common import align_relative, read_string


@dataclass
class MeshMaterial:
    name: str
    name_hash: int = field(init=False)
    duplicate_name_hash: int = field(init=False)
    duplicate_name: str = field(init=False)

    def __post_init__(self) -> None:
        hash = fnv1(self.name)
        self.name_hash = hash
        self.duplicate_name_hash = hash
        self.duplicate_name = self.name

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'MeshMaterial':
        name_hash = struct.unpack('<I', stream.read(4))[0]
        name_start_offset = stream.tell()
        offset_to_name = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        duplicate_name_hash = struct.unpack('<I', stream.read(4))[0]
        duplicate_name_start_offset = stream.tell()
        offset_to_duplicate_name = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(duplicate_name_start_offset + offset_to_duplicate_name)
        duplicate_name = read_string(stream)
        stream.seek(return_pos)

        # Bypass __post_init__ to use parsed values directly
        instance = cls.__new__(cls)
        instance.name_hash = name_hash
        instance.name = name
        instance.duplicate_name_hash = duplicate_name_hash
        instance.duplicate_name = duplicate_name
        return instance

    @staticmethod
    def write_list(writer, materials: list['MeshMaterial']) -> None:
        placeholders = []

        for material in materials:
            writer.write_struct('<I', material.name_hash)
            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)

            writer.write_struct('<I', material.duplicate_name_hash)
            duplicate_name_start_offset = writer.tell()
            duplicate_name_placeholder = writer.write_placeholder('<I', duplicate_name_start_offset)

            placeholders.append((name_placeholder, name_start_offset,
                               duplicate_name_placeholder, duplicate_name_start_offset, material))

        # Write material names and duplicate names
        for name_placeholder, name_start_offset, duplicate_name_placeholder, duplicate_name_start_offset, material in placeholders:
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(material.name)

            writer.align_min_padding(8, 8)
            duplicate_name_pos = writer.tell()
            writer.patch_placeholder(duplicate_name_placeholder, duplicate_name_pos)
            writer.write_string(material.duplicate_name)

@dataclass
class Mesh:
    name: str
    name_hash: int = field(init=False)
    unknown0: int = field(default=0)
    lod_distance: float = field(init=False)
    materials: list[MeshMaterial] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name_hash = fnv1(self.name)
        # Compute lod_distance based on name
        if ".lod1" in self.name:
            self.lod_distance = 1.0
        elif ".lod2" in self.name:
            self.lod_distance = 0.6
        elif ".lod3" in self.name:
            self.lod_distance = 0.3
        else:
            self.lod_distance = 0.0

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'Mesh':
        name_hash = struct.unpack('<I', stream.read(4))[0]
        name_start_offset = stream.tell()
        offset_to_name = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        unknown0 = struct.unpack('<I', stream.read(4))[0]
        lod_distance = struct.unpack('<f', stream.read(4))[0]
        material_count = struct.unpack('<I', stream.read(4))[0]
        materials_start_offset = stream.tell()
        offset_to_materials = struct.unpack('<I', stream.read(4))[0]

        # Parse materials
        materials = []
        return_pos = stream.tell()
        stream.seek(materials_start_offset + offset_to_materials)
        for _ in range(material_count):
            materials.append(MeshMaterial.from_stream(stream))
        stream.seek(return_pos)

        # Bypass __post_init__ to use parsed values directly
        instance = cls.__new__(cls)
        instance.name_hash = name_hash
        instance.name = name
        instance.unknown0 = unknown0
        instance.lod_distance = lod_distance
        instance.materials = materials
        return instance

    @staticmethod
    def write_list(writer, meshes: list['Mesh']) -> None:
        mesh_placeholders = []

        # Write mesh structures
        for mesh in meshes:
            writer.write_struct('<I', mesh.name_hash)
            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)

            writer.write_struct('<I', mesh.unknown0)
            writer.write_struct('<f', mesh.lod_distance)
            writer.write_struct('<I', len(mesh.materials))
            materials_start_offset = writer.tell()
            materials_placeholder = writer.write_placeholder('<I', materials_start_offset)

            mesh_placeholders.append((name_placeholder, name_start_offset,
                                     materials_placeholder, materials_start_offset, mesh))

        # Write mesh names and materials
        for name_placeholder, name_start_offset, materials_placeholder, materials_start_offset, mesh in mesh_placeholders:
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(mesh.name)

            if len(mesh.materials) > 0:
                writer.align_min_padding(8, 8)
                materials_pos = writer.tell()
                writer.patch_placeholder(materials_placeholder, materials_pos)
                MeshMaterial.write_list(writer, mesh.materials)


@dataclass
class ImportedMaterial:
    name: str
    path: str
    name_hash: int = field(init=False)
    path_hash: int = field(init=False)

    def __post_init__(self) -> None:
        self.name_hash = fnv1(self.name)
        self.path_hash = fnv1(self.path)

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'ImportedMaterial':
        name_hash = struct.unpack('<I', stream.read(4))[0]
        name_start_offset = stream.tell()
        offset_to_name = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(name_start_offset + offset_to_name)
        name = read_string(stream)
        stream.seek(return_pos)

        path_hash = struct.unpack('<I', stream.read(4))[0]
        path_start_offset = stream.tell()
        offset_to_path = struct.unpack('<I', stream.read(4))[0]

        return_pos = stream.tell()
        stream.seek(path_start_offset + offset_to_path)
        path = read_string(stream)
        stream.seek(return_pos)

        # Bypass __post_init__ to use parsed values directly
        instance = cls.__new__(cls)
        instance.name_hash = name_hash
        instance.name = name
        instance.path_hash = path_hash
        instance.path = path
        return instance

    @staticmethod
    def write_list(writer, imported_materials: list['ImportedMaterial']) -> None:
        placeholders = []

        # Write imported material structures
        for material in imported_materials:
            writer.write_struct('<I', material.name_hash)
            name_start_offset = writer.tell()
            name_placeholder = writer.write_placeholder('<I', name_start_offset)

            writer.write_struct('<I', material.path_hash)
            path_start_offset = writer.tell()
            path_placeholder = writer.write_placeholder('<I', path_start_offset)

            placeholders.append((name_placeholder, name_start_offset,
                               path_placeholder, path_start_offset, material))

        # Write imported material names and paths
        for name_placeholder, name_start_offset, path_placeholder, path_start_offset, material in placeholders:
            writer.align_min_padding(8, 8)
            name_pos = writer.tell()
            writer.patch_placeholder(name_placeholder, name_pos)
            writer.write_string(material.name)

            writer.align_min_padding(8, 8)
            path_pos = writer.tell()
            writer.patch_placeholder(path_placeholder, path_pos)
            writer.write_string(material.path)


@dataclass
class tpGxMeshAssetV2:
    unknown0: int = field(default=0)
    meshes: list[Mesh] = field(default_factory=list)
    imported_materials: list[ImportedMaterial] = field(default_factory=list)

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> 'tpGxMeshAssetV2':
        unknown0 = struct.unpack('<I', stream.read(4))[0]
        mesh_count = struct.unpack('<I', stream.read(4))[0]
        meshes_start_offset = stream.tell()
        offset_to_meshes = struct.unpack('<I', stream.read(4))[0]

        imported_material_count = struct.unpack('<I', stream.read(4))[0]
        imported_materials_start_offset = stream.tell()
        offset_to_imported_materials = struct.unpack('<I', stream.read(4))[0]

        # Parse meshes
        meshes = []
        stream.seek(meshes_start_offset + offset_to_meshes)
        for _ in range(mesh_count):
            meshes.append(Mesh.from_stream(stream))

        # Parse imported materials
        imported_materials = []
        stream.seek(imported_materials_start_offset + offset_to_imported_materials)
        for _ in range(imported_material_count):
            imported_materials.append(ImportedMaterial.from_stream(stream))

        return cls(
            unknown0=unknown0,
            meshes=meshes,
            imported_materials=imported_materials
        )

    def write_to(self, writer) -> None:
        # Write header
        writer.write_struct('<I', self.unknown0)
        writer.write_struct('<I', len(self.meshes))
        meshes_start_offset = writer.tell()
        meshes_placeholder = writer.write_placeholder('<I', meshes_start_offset)

        writer.write_struct('<I', len(self.imported_materials))
        imported_materials_start_offset = writer.tell()
        imported_materials_placeholder = writer.write_placeholder('<I', imported_materials_start_offset)

        # Write meshes
        if len(self.meshes) > 0:
            writer.align_min_padding(8, 8)
            meshes_pos = writer.tell()
            writer.patch_placeholder(meshes_placeholder, meshes_pos)
            Mesh.write_list(writer, self.meshes)

        # Write imported materials
        if len(self.imported_materials) > 0:
            writer.align_min_padding(8, 8)
            imported_materials_pos = writer.tell()
            writer.patch_placeholder(imported_materials_placeholder, imported_materials_pos)
            ImportedMaterial.write_list(writer, self.imported_materials)
