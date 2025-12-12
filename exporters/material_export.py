

import os
import time

from ..classes.material_instance import Constant, ConstantBuffer, TextureParameter, TextureSampler, tpGxMaterialInstanceV2
from ..classes.bxon import BXON
from ..classes.binary_writer import BinaryWriter
from ..classes.asset_package import Asset, tpXonAssetHeader
from ..classes.common import Import
from ..classes.pack import Pack, PackAssetPackage
from ..util import fnv1, get_export_collections_materials, log


def export(operator):
    directory = operator.directory

    start = time.perf_counter()

    packs: list[tuple[str, Pack]] = []
    materials = [m for m in get_export_collections_materials() if m.replicant_master_material and m.replicant_export]

    log.i(f"Found {len(materials)} material instances to export")
    for mat in materials:
        filename = os.path.basename(mat.replicant_pack_path)
        filepath = os.path.join(directory, filename)
        
        import_paths: set[str] = set()

        for sampler in mat.replicant_texture_samplers:
            import_paths.add(sampler.pack_path)
        import_paths.add(mat.replicant_master_material)

        material_instance = tpGxMaterialInstanceV2(mat.replicant_master_material)
        material_instance.flags = (
            not mat.replicant_flags.cast_shadows,
            mat.replicant_flags.cast_shadows,
            False,
            False,
            mat.replicant_flags.draw_backfaces,
            mat.replicant_flags.draw_backfaces,
            False,
            False,
            mat.replicant_flags.enable_alpha,
            mat.replicant_flags.enable_alpha
        )

        for buffer in mat.replicant_constant_buffers:
            constant_buffer = ConstantBuffer(buffer.name)
            for const in buffer.constants:
                constant = Constant(
                    name_hash=fnv1(const.name),
                    name=const.name,
                    value0=const.values[0],
                    value1=const.values[1],
                    value2=const.values[2],
                    value3=const.values[3],
                    value4=const.values[4],
                    value5=const.values[5],
                    byte0=0
                )
                constant_buffer.constants.append(constant)
            material_instance.constant_buffers.append(constant_buffer)

        for sampler in mat.replicant_texture_samplers:
            texture_basename = os.path.basename(sampler.texture_path)
            texture_filename = os.path.splitext(texture_basename)[0] + ".rtex"
            texture_sampler = TextureSampler(
                name_hash=fnv1(sampler.name),
                name=sampler.name,
                texture_name_hash=fnv1(texture_filename),
                texture_name=texture_filename,
                unknown_byte=0
            )
            material_instance.texture_samplers.append(texture_sampler)

        for param in mat.replicant_texture_parameters:
            texture_parameter = TextureParameter(
                name_hash=fnv1(param.name),
                name=param.name,
                value0=param.values[0],
                value1=param.values[1],
                value2=param.values[2]
            )
            material_instance.texture_parameters.append(texture_parameter)

        asset = Asset(
            asset_type_hash=985565024,
            asset_content=material_instance
        )

        asset_header = tpXonAssetHeader()
        asset_header.assets.append(asset)
        for path in import_paths:
            asset_header.imports.append(Import(path))

        asset_header_bxon = BXON(
            magic=b'BXON',
            version=3,
            project_id=955984368,
            asset_type="tpXonAssetHeader",
            asset_data=asset_header
        )
        asset_header_bxon_bytes = BinaryWriter()
        asset_header_bxon.write_to(asset_header_bxon_bytes)
        asset_package_name = filename + ".xap"
        asset_package = PackAssetPackage(
            name_hash=fnv1(asset_package_name),
            name=asset_package_name,
            content=asset_header_bxon,
            raw_content_bytes=asset_header_bxon_bytes.get_bytes()
        )

        pack = Pack()
        for path in import_paths:
            pack.imports.append(Import(path))
        pack.asset_packages.append(asset_package)
        packs.append((filepath, pack))
        log.d(f"Generated material instance data for {filename}")

    gen_end = time.perf_counter()
    log.d(f"Finished generating data in {gen_end - start:.4f} seconds.")
    log.d("Writing new PACK file(s)...")
    write_start = time.perf_counter()
    for filepath, pack in packs:
        pack.to_file(filepath)
        log.d(f"Finished writing {filepath}...")
    end = time.perf_counter()
    log.d(f"Finished writing {len(packs)} PACK(s) in {end - write_start:.4f} seconds.")
    log.i(f"Total export time: {end - start:.4f} seconds!")
    return {'FINISHED'}