import os
import bpy
from bpy.types import Material


from ..classes.material_instance import tpGxMaterialInstanceV2
from ..classes.asset_package import tpXonAssetHeader
from ..classes.tex_head import tpGxTexHead, ResourceDimension, ResourceFormat
from ..classes.pack import Pack, PackFile

from .materials.master_rs_standard import master_rs_standard
from .materials.master_rs_layer2 import master_rs_layer2
from .materials.master_rs_layer3 import master_rs_layer3
from .materials.master_rs_layer4 import master_rs_layer4
from .materials.master_rs_hair import master_rs_hair
from .materials.master_rs_ao_sheet import master_rs_ao_sheet
from .materials.master_rs_leaf import master_rs_leaf
from .materials.master_rs_xlu_water import master_rs_xlu_water
from .materials.default import default_material
from .materials.nodes import dx_to_gl_normal, grid_location, texture_sampler
from ..util import *

# Map material type names to their handler functions
MATERIAL_HANDLERS = {
    "master_rs_standard": master_rs_standard,
    "master_rs_layer2": master_rs_layer2,
    "master_rs_layer3": master_rs_layer3,
    "master_rs_layer4": master_rs_layer4,
    "master_rs_hair": master_rs_hair,
    "master_rs_ao_sheet": master_rs_ao_sheet,
    "master_rs_leaf": master_rs_leaf,
    "master_rs_xlu_water": master_rs_xlu_water,
}

def _find_pack_path(tex_name: str, textures_dir: str, imports: list[str]) -> str | None:
    for root, dirs, files in os.walk(textures_dir):
        if any(tex_name in file for file in files):
            rel_path = os.path.relpath(root, textures_dir)
            if rel_path == '.':
                continue

            path_parts = rel_path.split(os.sep)
            for part in path_parts:
                for import_str in imports:
                    if import_str.endswith(part):
                        return import_str
    return None

def _find_texture_path(tex_name: str, textures_dir: str) -> str | None:
    matches = []
    for root, dirs, files in os.walk(textures_dir):
        for file in files:
            if tex_name in file:
                matches.append(os.path.join(root, file))

    # Prioritize PNG files
    priority_matches = [m for m in matches if m.lower().endswith('.dds')] # Temporarily prioritize DDS 
    if priority_matches:
        return priority_matches[0]
    elif matches:
        return matches[0]
    return None

def setup_material_texture_samplers(material: Material, material_asset: tpXonAssetHeader, textures_dir: str):
    material_instance: tpGxMaterialInstanceV2 = material_asset.assets[0].asset_content
    imports = [i.path for i in material_asset.imports]
    material.replicant_master_material = material_instance.parent_asset_path

    for texture in material_instance.texture_samplers:
        sampler = material.replicant_texture_samplers.add()
        sampler.name = texture.name
        sampler.previous_name = sampler.name
        tex_name = texture.texture_name.rpartition('.')[0]
        texture_path = _find_texture_path(tex_name, textures_dir)
        if texture_path:
            sampler.texture_path = texture_path
        pack_path = _find_pack_path(tex_name, textures_dir, imports)
        if pack_path:
            sampler.pack_path = pack_path

def setup_texture_sampler_dxgi_data(texture_packs: list[Pack]):
    for pack in texture_packs:
        for file in pack.files:
            if file.content.asset_type != "tpGxTexHead":
                continue
            tex_basename = file.name.replace(".rtex", "")
            tex_head: tpGxTexHead = file.content.asset_data
            dxgi_format_string = tex_head.get_format_str()
            has_multiple_mips = tex_head.mip_count > 1
            for material in bpy.data.materials:
                for sampler in material.replicant_texture_samplers:
                    if tex_basename in sampler.texture_path:
                        sampler.dxgi_format = dxgi_format_string
                        sampler.mip_maps = has_multiple_mips


def setup_custom_ui_values(material: Material, material_instance: tpGxMaterialInstanceV2):
    material.replicant_flags.cast_shadows = not material_instance.flags[0] and material_instance.flags[1]
    material.replicant_flags.draw_backfaces = material_instance.flags[4] and material_instance.flags[5]
    material.replicant_flags.enable_alpha = material_instance.flags[8] and material_instance.flags[9]

    for constant_buffer in material_instance.constant_buffers:
        cb = material.replicant_constant_buffers.add()
        cb.name = constant_buffer.name
        cb.previous_name = cb.name
        for constant in constant_buffer.constants:
            const = cb.constants.add()
            const.name = constant.name
            const.previous_name = const.name
            const.values = (constant.value0, constant.value1, constant.value2, constant.value3, constant.value4, constant.value5)
    for texture_parameter in material_instance.texture_parameters:
        tp = material.replicant_texture_parameters.add()
        tp.name = texture_parameter.name
        tp.values = (texture_parameter.value0, texture_parameter.value1, texture_parameter.value2)

def construct_materials(pack_dir: str, material_packs: list[Pack]):
    log.i("Generating Blender materials...")
    textures_dir = pack_dir + "\\replicant2blender_extracted\\"

    # Renamed in 5.0
    sepRGB_name = "ShaderNodeSeparateRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeSeparateColor"
    sepRGB_input = 'Image' if bpy.app.version < (5, 0, 0) else "Color"
    comRGB_name = "ShaderNodeCombineRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeCombineColor"
    comRGB_output = 'Image' if bpy.app.version < (5, 0, 0) else "Color"

    for pack in material_packs:
        material_name = pack.asset_packages[0].name
        material_asset_header: tpXonAssetHeader = pack.asset_packages[0].content.asset_data
        material_instance: tpGxMaterialInstanceV2 = material_asset_header.assets[0].asset_content

        b_mat_name = material_name.split("_", 1)[1].split(".")[0].lower()

        if b_mat_name in bpy.data.materials:
            material = bpy.data.materials[b_mat_name]
            material.replicant_texture_samplers.clear()
            material.replicant_constant_buffers.clear()
            material.replicant_texture_parameters.clear()
        else:
            material = bpy.data.materials.new(b_mat_name)

        log.d(f"Generating material {b_mat_name}")

        setup_material_texture_samplers(material, material_asset_header, textures_dir)

        try:
            handled = False
            for material_type, handler in MATERIAL_HANDLERS.items():
                if material_type in material_instance.parent_asset_path:
                    handler(textures_dir, material, material_instance)
                    setup_custom_ui_values(material, material_instance)
                    handled = True
                    break
            if handled:
                continue
        except Exception as e:
            log.e(f"Failed to construct shader for material: {material.name} ({e})")

        # Use default material generation
        default_material(textures_dir, material, material_instance)
        setup_custom_ui_values(material, material_instance)
    log.i("Blender material generation complete.")
                

def extract_textures(pack_dir: str, texture_packs: list[Pack]):
    failed_texture_files: list[PackFile] = []
    extracted_textures_paths: list[str] = []

    for pack in texture_packs:
        log.i("Extracting textures...")

        asset_pack_name = pack.asset_packages[0].name.replace(".xap", "")

        r2b_extracted_path = pack_dir + "\\" + "replicant2blender_extracted" + "\\" + asset_pack_name
        converted_path = r2b_extracted_path + "\\" + "converted"

        if not os.path.isdir(r2b_extracted_path):
            os.makedirs(r2b_extracted_path)

        if not os.path.isdir(converted_path):
            os.makedirs(converted_path)

        k = 0
        for idx, file in enumerate(pack.files):
            if ".rtex" not in file.name:
                log.w(f"{file.name} is not a texture. Skipping...")
                continue
            log.d(f"Extracting {idx+1}/{len(pack.files)}: {file.name}")
            tex_head: tpGxTexHead = file.content.asset_data
            file_name = file.name.replace(".rtex", "")
            texture_filename = file_name + ".dds"
            texture_path = r2b_extracted_path + "\\" + texture_filename
            texture_file = open(texture_path, "wb")

            # Magic
            texture_file.write(str_to_bytes("DDS\x20"))
            # HeaderSize
            texture_file.write(uint32_to_bytes(124))

            # Flags
            is_compressed = tex_head.surface_format.is_compressed()
            is_3d_texture = tex_head.surface_format.resource_dimension == ResourceDimension.TEXTURE3D
            flags = 0x1 | 0x2 | 0x4 | 0x1000    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
            if is_compressed:
                flags |= 0x80000    # DDSD_LINEARSIZE
            else:
                flags |= 0x8        # DDSD_PITCH
            if tex_head.mip_count > 1:
                flags |= 0x20000    # DDSD_MIPMAPCOUNT
            if is_3d_texture and tex_head.depth > 1:
                flags |= 0x800000    # DDSD_DEPTH
            texture_file.write(uint32_to_bytes(flags))

            # Height
            texture_file.write(uint32_to_bytes(tex_head.height))
            # Width
            texture_file.write(uint32_to_bytes(tex_head.width))

            # Pitch or LinearSize
            if is_compressed:
                # For compressed formats, use the total size
                texture_file.write(uint32_to_bytes(tex_head.total_data_size))
            else:
                # For uncompressed formats, calculate pitch (bytes per scanline)
                bytes_per_pixel = tex_head.surface_format.get_bytes_per_pixel()
                pitch = tex_head.width * bytes_per_pixel
                texture_file.write(uint32_to_bytes(pitch))

            # Depth (only for 3D/volume textures, otherwise 0)
            depth_value = tex_head.depth if is_3d_texture else 0
            texture_file.write(uint32_to_bytes(depth_value))

            # MipMapCount
            texture_file.write(uint32_to_bytes(tex_head.mip_count))

            # Reserved
            for i in range(11):
                texture_file.write(uint32_to_bytes(0))

            # DDS_PIXELFORMAT
            # Size
            texture_file.write(uint32_to_bytes(32))
            # Flags
            texture_file.write(uint32_to_bytes(4))
            # fourCC
            texture_file.write(str_to_bytes("DX10"))
            # RGBBitCount
            texture_file.write(uint32_to_bytes(0))
            # RGBABitMasks
            for i in range(4):
                texture_file.write(uint32_to_bytes(0))

            # CAPS
            is_cubemap = tex_head.surface_format.resource_dimension == ResourceDimension.CUBEMAP
            caps = 0x1000   # DDSCAPS_TEXTURE
            if tex_head.mip_count > 1 or is_cubemap:
                caps |= 0x8 | 0x400000    # DDSCAPS_MIPMAP | DDSCAPS_COMPLEX
            texture_file.write(uint32_to_bytes(caps))

            # CAPS 2
            caps2 = 0x0
            if is_3d_texture:
                caps2 |= 0x200000   # DDSCAPS2_VOLUME
            if is_cubemap:
                caps2 |= 0x200 | 0xFE00    # DDSCAPS2_CUBEMAP | all 6 faces (POSITIVEX, NEGATIVEX, POSITIVEY, NEGATIVEY, POSITIVEZ, NEGATIVEZ)
            texture_file.write(uint32_to_bytes(caps2))
            # CAPS 3
            texture_file.write(uint32_to_bytes(0))
            # CAPS 4
            texture_file.write(uint32_to_bytes(0))
            # Reserved
            texture_file.write(uint32_to_bytes(0))

            # DDS_HEADER_DXT10
            # DXGI Format
            dxgi_format = tex_head.surface_format.get_dxgi_format()
            if dxgi_format == 0:  # DXGI_FORMAT_UNKNOWN
                log.w(f"Texture extraction failed! {file.name} - Unknown format: {tex_head.surface_format.resource_format.name}")
                failed_texture_files.append(file)
                texture_file.close()
                k += 1
                continue
            texture_file.write(uint32_to_bytes(dxgi_format))

            # D3D10 Resource Dimension
            dimension = tex_head.surface_format.get_d3d10_dimension()
            texture_file.write(uint32_to_bytes(dimension))

            # MiscFlags
            misc_flags = 0
            if tex_head.surface_format.resource_dimension == ResourceDimension.CUBEMAP:
                misc_flags = 0x4  # D3D11_RESOURCE_MISC_TEXTURECUBE
            texture_file.write(uint32_to_bytes(misc_flags))

            # ArraySize
            texture_file.write(uint32_to_bytes(1))

            # MiscFlags2 (alpha mode)
            alpha_mode = tex_head.surface_format.get_alpha_mode()
            texture_file.write(uint32_to_bytes(alpha_mode))

            # TextureData - find and write texture data
            for file_data in pack.files_data:
                if file_data.file_index == idx and file_data.tex_data:
                    # Write all subresource data (all mip levels and depth slices)
                    for subresource_data in file_data.tex_data.subresource_data:
                        texture_file.write(subresource_data)
                    break

            texture_file.close()
            extracted_textures_paths.append(texture_path)
            k += 1

    log.i(f"Finished extracting {len(extracted_textures_paths)} textures.")

    if extracted_textures_paths:
        from puredds import DDS
        import imageio
        log.i(f"Converting {len(extracted_textures_paths)} textures...")

        failed_conversions = 0
        for idx, texture_path in enumerate(extracted_textures_paths):
            try:
                directory = os.path.dirname(texture_path)
                converted_path = directory + "\\converted\\"
                out_path = converted_path + os.path.basename(texture_path).replace(".dds", ".png")

                log.d(f"Converting {idx+1}/{len(extracted_textures_paths)}: {os.path.basename(texture_path)}")

                with open(texture_path, 'rb') as f:
                    data = f.read()
                dds = DDS.from_bytes(data)
                image = dds.to_image()
                imageio.imwrite(out_path, image)
            except Exception as e:
                log.e(f"Failed to convert {texture_path}! Error: {e}")
                failed_conversions += 1

        success_count = len(extracted_textures_paths) - failed_conversions
        log.i(f"Finished converting textures. Success: {success_count}/{len(extracted_textures_paths)}")
    return failed_texture_files