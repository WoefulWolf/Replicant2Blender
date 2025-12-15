

import os
import time

import bpy
from bpy.types import Material
from puredds import DDS

from ..classes.tex_data import tpGxTexData
from ..classes.common import DataOffset
from ..classes.tex_head import Subresource, XonSurfaceFormat, tpGxTexHead, ResourceFormat, ResourceDimension
from ..classes.asset_package import tpXonAssetHeader
from ..classes.binary_writer import BinaryWriter
from ..classes.bxon import BXON
from ..classes.pack import Pack, PackAssetPackage, PackFile, PackFileData
from ..util import fnv1, get_export_collections_materials, log


def export(operator):
    texture_pack = operator.texture_pack
    filepath: str = operator.filepath
    filename = os.path.basename(filepath)

    start = time.perf_counter()

    asset_header_bxon = BXON(
        magic=b'BXON',
        version=3,
        project_id=955984368,
        asset_type="tpXonAssetHeader",
        asset_data=tpXonAssetHeader()
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

    export_materials = get_export_collections_materials()
    replicant_materials = [m for m in export_materials if m.replicant_master_material]
    texture_packs: dict[str, list[Material]] = {}
    for material in replicant_materials:
        for sampler in material.replicant_texture_samplers:
            if sampler.pack_path in texture_packs:
                if material in texture_packs[sampler.pack_path]:
                    continue
                texture_packs[sampler.pack_path].append(material)
                continue
            else:
                texture_packs[sampler.pack_path] = [material]

    materials = texture_packs[texture_pack]
    log.i(f"Found {len(materials)} materials referencing {texture_pack} with textures to export")

    pack = Pack()
    pack.asset_packages.append(asset_package)

    texture_paths = set()

    for mat in materials:
        for sampler in mat.replicant_texture_samplers:
            if sampler.texture_path in texture_paths:
                continue
            else:
                texture_paths.add(sampler.texture_path)

            try:
                with open(sampler.texture_path, 'rb') as f:
                    data = f.read()
                dds = DDS.from_bytes(data)
            except:
                log.e(f"Failed to parse DDS data file {sampler.texture_path}, is it a valid DDS?")
                operator.report({'ERROR'}, f"Failed to parse DDS data file {sampler.texture_path}, is it a valid DDS?")
                return {'CANCELLED'}

            tex_head = tpGxTexHead()
            tex_head.width = dds.get_width()
            tex_head.height = dds.get_height()
            tex_head.depth = max(dds.get_depth(), 1)
            tex_head.mip_count = dds.get_mip_count()
            tex_head.total_data_size = dds.get_size()
            dxgi_format = dds.get_dxgi_format()
            if not dxgi_format:
                log.e(f"Failed to get format of {sampler.texture_path}! Does it include a modern DXT10 header?")
                operator.report({'ERROR'}, f"Failed to get format of {sampler.texture_path}! Does it include a modern DXT10 header?")
                return {'CANCELLED'}
            tex_head.surface_format = get_xon_surface_format(dds)
            for i in range(dds.get_subresource_count()):
                tex_head.subresources.append(Subresource(
                    offset=0,
                    unknown0=0,
                    row_pitch=dds.get_subresource_row_pitch(i),
                    unknown1=0,
                    slice_size=dds.get_subresource_size(i),
                    unknown2=0,
                    width=dds.get_subresource_width(i),
                    height=dds.get_subresource_height(i),
                    depth=dds.get_subresource_depth(i),
                    row_count=dds.get_subresource_row_count(i)
                ))

            texture_basename = os.path.basename(sampler.texture_path)
            texture_filename = os.path.splitext(texture_basename)[0] + ".rtex"

            file_bxon = BXON(
                magic=b'BXON',
                version=3,
                project_id=782713094,
                asset_type="tpGxTexHead",
                asset_data=tex_head
            )
            file_bxon_bytes = BinaryWriter()
            file_bxon.write_to(file_bxon_bytes)
            
            file = PackFile(
                name_hash=fnv1(texture_filename),
                name=texture_filename,
                content=file_bxon,
                data_offset=DataOffset(0, True),
                raw_content_bytes=file_bxon_bytes.get_bytes()
            )
            
            file_data = PackFileData(
                file_index=len(pack.files),
                tex_data=tpGxTexData(dds.data)
            )

            pack.files.append(file)
            pack.files_data.append(file_data)
            log.d(f"Generated texture data for {texture_filename}")
    
    log.d(f"Successfully generated data for {len(pack.files)} texture files")

    gen_end = time.perf_counter()
    log.d(f"Finished generating data in {gen_end - start:.4f} seconds.")
    log.d("Writing new PACK file...")
    write_start = time.perf_counter()
    pack.to_file(filepath)
    end = time.perf_counter()
    log.d(f"Finished writing {filepath} in {end - write_start:.4f} seconds.")
    log.i(f"Total export time: {end - start:.4f} seconds!")
    return {'FINISHED'}

def get_xon_surface_format(dds: DDS) -> XonSurfaceFormat:
    from puredds.enums import DDS_RESOURCE_MISC

    # Map DXGI format to ResourceFormat (inverse of the mapping in tex_head.py)
    dxgi_to_resource_format = {
        2: ResourceFormat.R32G32B32A32_FLOAT,
        6: ResourceFormat.R32G32B32_FLOAT,
        16: ResourceFormat.R32G32_FLOAT,
        41: ResourceFormat.R32_FLOAT,
        10: ResourceFormat.R16G16B16A16_FLOAT,
        34: ResourceFormat.R16G16_FLOAT,
        54: ResourceFormat.R16_FLOAT,
        28: ResourceFormat.R8G8B8A8_UNORM,
        29: ResourceFormat.R8G8B8A8_UNORM_SRGB,
        49: ResourceFormat.R8G8_UNORM,
        61: ResourceFormat.R8_UNORM,
        87: ResourceFormat.B8G8R8A8_UNORM,
        91: ResourceFormat.B8G8R8A8_UNORM_SRGB,
        88: ResourceFormat.B8G8R8X8_UNORM,
        93: ResourceFormat.B8G8R8X8_UNORM_SRGB,
        71: ResourceFormat.BC1_UNORM,
        72: ResourceFormat.BC1_UNORM_SRGB,
        74: ResourceFormat.BC2_UNORM,
        75: ResourceFormat.BC2_UNORM_SRGB,
        77: ResourceFormat.BC3_UNORM,
        78: ResourceFormat.BC3_UNORM_SRGB,
        80: ResourceFormat.BC4_UNORM,
        83: ResourceFormat.BC5_UNORM,
        95: ResourceFormat.BC6H_UF16,
        96: ResourceFormat.BC6H_SF16,
        98: ResourceFormat.BC7_UNORM,
        99: ResourceFormat.BC7_UNORM_SRGB,
    }

    # Get DXGI format from DDS
    dxgi_format = dds.get_dxgi_format()
    resource_format = dxgi_to_resource_format.get(dxgi_format, ResourceFormat.UNKNOWN)

    # Determine resource dimension
    if dds.is_volume():
        resource_dimension = ResourceDimension.TEXTURE3D
    elif dds.header10 and (dds.header10.miscFlag & DDS_RESOURCE_MISC.TEXTURECUBE):
        resource_dimension = ResourceDimension.CUBEMAP
    else:
        resource_dimension = ResourceDimension.TEXTURE2D

    # Determine if texture has mipmaps
    generate_mips = dds.get_mip_count() <= 1

    # Default usage value
    usage_maybe = 0

    return XonSurfaceFormat(
        usage_maybe=usage_maybe,
        resource_format=resource_format,
        resource_dimension=resource_dimension,
        generate_mips=generate_mips
    )
