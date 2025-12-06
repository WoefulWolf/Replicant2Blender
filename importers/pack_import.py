import os, bpy

from .levelData_import import importLevelData
from ..classes.pack import *
from .mesh_import import construct_meshes
from .material_import import construct_materials, extract_textures, tpGxTexHead
from ..util import log

imported_texture_packs = []
failed_texture_packs = []
imported_material_packs = []

def clear_import_lists():
    imported_material_packs.clear()
    imported_texture_packs.clear()

def main(pack_path: str, do_extract_textures: bool, do_construct_materials: bool, addon_name: str):
    pack_directory = os.path.dirname(os.path.abspath(pack_path))

    # Import meshes
    log.i(f"Parsing Mesh PACK file... {pack_path}")
    pack = Pack.from_file(pack_path)

    if any(file.content is not None and file.content.asset_type == 'tpGxMeshHead' for file in pack.files):
        bpy.context.scene.replicant_original_mesh_pack = pack_path

    construct_meshes(pack)
    # importLevelData(pack.levelData, addon_name)

    # Import materials + textures
    failed_texture_files = []
    if do_extract_textures or do_construct_materials:
        material_packs: list[Pack] = []
        for import_entry in pack.imports:
            material_pack_filename = import_entry.path.split('/')[-1]
            material_pack_path = pack_directory + "\\" + material_pack_filename

            if not os.path.isfile(material_pack_path):
                if os.path.isfile(material_pack_path + ".xap"):
                    material_pack_path += ".xap"
                else:
                    log.w(f"Failed to find material PACK file: {material_pack_path}")
                    continue
            
            if (material_pack_path not in imported_material_packs):
                imported_material_packs.append(material_pack_path)
                log.i(f"Parsing Material PACK file... {import_entry.path}")
                material_packs.append(Pack.from_file(material_pack_path))

        texture_packs: list[Pack] = []
        for material_pack in material_packs:
            for import_entry in material_pack.imports:
                texture_pack_filename = import_entry.path.split('/')[-1]
                texture_pack_path = pack_directory + "\\" + texture_pack_filename

                if not os.path.isfile(texture_pack_path):
                    if os.path.isfile(texture_pack_path + ".xap"):
                        texture_pack_path += ".xap"
                    else:
                        if (texture_pack_path not in failed_texture_packs):
                            failed_texture_packs.append(texture_pack_path)
                            log.w(f"Failed to find texture PACK file: {texture_pack_filename}")
                        continue

                if (texture_pack_path not in imported_texture_packs):
                    imported_texture_packs.append(texture_pack_path)
                    log.i(f"Parsing Texture PACK file... {import_entry.path}")
                    texture_packs.append(Pack.from_file(texture_pack_path))

        if do_extract_textures:
            failed_texture_files: list[PackFile] = extract_textures(pack_directory, texture_packs)

        if do_construct_materials:
            construct_materials(pack_directory, material_packs)

    if len(failed_texture_files) > 0:
        report_failed_textures(failed_texture_files)
    else:
        log.i('Importing finished. ;)')

def only_extract_textures(pack_path: str, addon_name: str):
    pack_directory = os.path.dirname(os.path.abspath(pack_path))

    texturePack = Pack.from_file(pack_path)
    failed_texture_files: list[PackFile] = extract_textures(pack_directory, [texturePack])

    if len(failed_texture_files) > 0:
        report_failed_textures(failed_texture_files)
    else:
        log.i('Importing finished. ;)')

def report_failed_textures(failed_texture_files: list[PackFile]):
    log.e("Some textures failed to extract!")
    log.e("Report this issue @ https://github.com/WoefulWolf/Replicant2Blender/issues")
    log.e("Please include the unknown formats logged below and the path of the file you were trying to import.")
    for file in failed_texture_files:
        tex_head: tpGxTexHead = file.content.asset_data
        log.e(f"{file.name} {hex(tex_head.surface_format)}")