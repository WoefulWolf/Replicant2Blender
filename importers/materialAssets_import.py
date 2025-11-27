import os
import subprocess
import binascii
from typing import List
import bpy

from ..classes.pack import Pack
from ..classes.tpGxAssetHeader import UnknownAsset
from ..classes.tpGxTexHead import tpGxTexHead
from .materials.master_rs_layer4 import master_rs_layer4
from .materials.nodes import dx_to_gl_normal, grid_location
from numpy import uint
from ..util import *

def construct_materials(pack_dir, material_packs):
    log.i("Constructing materials...")
    textures_dir = pack_dir + "\\replicant2blender_extracted\\"

    # Renamed in 5.0
    sepRGB_name = "ShaderNodeSeparateRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeSeparateColor"
    sepRGB_input = 'Image' if bpy.app.version < (5, 0, 0) else "Color"
    comRGB_name = "ShaderNodeCombineRGB" if bpy.app.version < (5, 0, 0) else "ShaderNodeCombineColor"
    comRGB_output = 'Image' if bpy.app.version < (5, 0, 0) else "Color"

    for materialPack in material_packs:
        materialAssetName = materialPack.assetPacks[0].name
        materialAssetHeader = materialPack.assetPacks[0].content.assetHeader

        b_mat_name = materialAssetName.split("_", 1)[1].split(".")[0].lower()

        materialAsset: UnknownAsset = materialAssetHeader.unknownAssets[0]

        if b_mat_name in bpy.data.materials:
            material = bpy.data.materials[b_mat_name]
            # continue
        else:
            material = bpy.data.materials.new(b_mat_name)

        log.i(f"Generating material {b_mat_name}")

        if "master_rs_layer4" in materialAsset.masterMaterialPath:
            try:
                master_rs_layer4(textures_dir, material, materialAsset)
            except Exception as e:
                log.w(f"Failed to construct material: {material.name}")
            continue

        material.use_nodes = True
        material.node_tree.links.clear()
        material.node_tree.nodes.clear()
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        material.blend_method = 'CLIP'

        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = grid_location(4, 0)
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled.location = grid_location(3, 0)
        output_link = links.new( principled.outputs['BSDF'], output.inputs['Surface'])

        for texture in materialAsset.textures:
            texture_filename_base = texture.filename.replace(".rtex", "")
            texture_filename = texture_filename_base + ".png"
            texture_file = search_texture(textures_dir, texture_filename)
            if texture_file is None:
                log.w(f"Failed to find texture: {texture_filename}")
                continue

            if texture.mapType in ["texBaseColor", "texBaseColor0"]:
                color_image = nodes.new(type='ShaderNodeTexImage')
                color_image.location = grid_location(0, 0)
                color_image.image = bpy.data.images.load(texture_file)
                color_image.hide = True

                albedo_principled = links.new(color_image.outputs['Color'], principled.inputs['Base Color'])
                alpha_link = links.new(color_image.outputs['Alpha'], principled.inputs['Alpha'])

            elif texture.mapType in ["texORM", "texORM0"]:
                mask_image = nodes.new(type='ShaderNodeTexImage')
                mask_image.location = grid_location(0, 1)
                mask_image.image = bpy.data.images.load(texture_file)
                mask_image.image.colorspace_settings.name = 'Non-Color'
                mask_image.hide = True

                sepRGB_shader = nodes.new(type=sepRGB_name)
                sepRGB_shader.location = grid_location(1, 1)
                sepRGB_shader.hide = True
                mask_link = links.new(mask_image.outputs['Color'], sepRGB_shader.inputs[sepRGB_input])

                # Ambient Occlusion
                try:
                    ao_multiply: bpy.types.ShaderNodeMixRGB = nodes.new('ShaderNodeMixRGB')
                    ao_multiply.location = grid_location(2, 0)
                    ao_multiply.hide = True
                    ao_multiply.blend_type = 'MULTIPLY'
                    ao_multiply.inputs[0].default_value = 1.0
                    links.new(color_image.outputs['Color'], ao_multiply.inputs[1])
                    links.new(sepRGB_shader.outputs['Red'], ao_multiply.inputs[2])
                    links.new(ao_multiply.outputs['Color'], principled.inputs['Base Color'])
                except:
                    log.e(f"Could not setup AO for material: {b_mat_name}")

                roughness_link = links.new(sepRGB_shader.outputs[1], principled.inputs['Roughness'])
                metallic_link = links.new(sepRGB_shader.outputs[2], principled.inputs['Metallic'])

            elif texture.mapType in ["texNormal", "texNormal0"]:
                normal_image = nodes.new(type='ShaderNodeTexImage')
                normal_image.location = grid_location(0, 2)
                normal_image.image = bpy.data.images.load(texture_file)
                normal_image.image.colorspace_settings.name = 'Non-Color'
                normal_image.hide = True

                # Convert DirectX normal to OpenGL
                normal_convert = nodes.new('ShaderNodeGroup')
                normal_convert.node_tree = dx_to_gl_normal()
                normal_convert.location = grid_location(1, 2)
                normal_convert.hide = True
                links.new(normal_image.outputs['Color'], normal_convert.inputs['Color'])

                normalmap_shader = nodes.new(type='ShaderNodeNormalMap')
                normalmap_shader.location = grid_location(2, 2)
                normalmap_shader.hide = True
                
                combined_link = links.new(normal_convert.outputs[0], normalmap_shader.inputs['Color'])
                normalmap_link = links.new(normalmap_shader.outputs['Normal'], principled.inputs['Normal'])
                

def extract_textures(pack_dir, texture_packs: List[Pack]):
    failed_texAsset = []
    extracted_textures_paths = []

    for texturePack in texture_packs:
        log.i("Extracting textures...")

        asset_pack_name = texturePack.assetPacks[0].name.replace(".xap", "")

        r2b_extracted_path = pack_dir + "\\" + "replicant2blender_extracted" + "\\" + asset_pack_name
        converted_path = r2b_extracted_path + "\\" + "converted"

        if not os.path.isdir(r2b_extracted_path):
            os.makedirs(r2b_extracted_path)

        if not os.path.isdir(converted_path):
            os.makedirs(converted_path)

        k = 0
        for idx, assetFile in enumerate(texturePack.assetFiles):
            if ".rtex" not in assetFile.name:
                log.w(f"{assetFile.name} is not a texture. Skipping...")
                continue
            log.d(f"Extracting {idx+1}/{len(texturePack.assetFiles)}: {assetFile.name}")
            texHead = assetFile.content.texHead
            assetPackName = assetFile.name.replace(".rtex", "")
            textureFilename = assetPackName + ".dds"
            textureFullPath = r2b_extracted_path + "\\" + textureFilename
            textureFile = open(textureFullPath, "wb")

            # Magic
            textureFile.write(str_to_bytes("DDS\x20"))
            # HeaderSize
            textureFile.write(uint32_to_bytes(124))
            # Flags
            flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
            if texHead.header.numMipSurfaces > 1:
                flags |= 0x20000    # DDSD_MIPMAPCOUNT
            if texHead.header.numSurfaces > 1:
                flags |= 0x800000    # DDSD_DEPTH
            textureFile.write(uint32_to_bytes(flags))
            # Height
            textureFile.write(uint32_to_bytes(texHead.header.height))
            # Width
            textureFile.write(uint32_to_bytes(texHead.header.width))
            # Size
            textureFile.write(uint32_to_bytes(texHead.header.filesize))
            # Depth
            textureFile.write(uint32_to_bytes(1))
            # MipMapCount
            textureFile.write(uint32_to_bytes(texHead.header.numMipSurfaces))
            # Reserved
            for i in range(11):
                textureFile.write(uint32_to_bytes(0))

            # DDS_PIXELFORMAT
            # Size
            textureFile.write(uint32_to_bytes(32))
            # Flags
            textureFile.write(uint32_to_bytes(4))
            # fourCC
            textureFile.write(str_to_bytes("DX10"))
            # RGBBitCount
            textureFile.write(uint32_to_bytes(0))
            # RGBABitMasks
            for i in range(4):
                textureFile.write(uint32_to_bytes(0))

            # CAPS
            caps = 0x1000   # DDSCAPS_TEXTURE
            if texHead.header.numMipSurfaces > 1:
                caps |= 0x8 | 0x400000    # DDSCAPS_MIPMAP | DDSCAPS_COMPLEX
            textureFile.write(uint32_to_bytes(caps))
            # CAPS 2
            caps2 = 0x0
            if texHead.header.numSurfaces > 1:
                caps2 |= 0x200000   # DDSCAPS2_VOLUME
            textureFile.write(uint32_to_bytes(caps2))
            # CAPS 3
            textureFile.write(uint32_to_bytes(0))
            # CAPS 4
            textureFile.write(uint32_to_bytes(0))

            # Reserved
            textureFile.write(uint32_to_bytes(0))

            # DDS_HEADER_DXT10
            # DXGI Format
            format = get_DXGI_format(texHead.header.XonSurfaceFormat)
            if format == None or format == "UNKNOWN":
                log.w(f"Texture extraction failed! {assetFile.name}")
                failed_texAsset.append(assetFile)
                textureFile.close()
                if assetFile.name == "":
                    debug_dump_texture(assetPackName, r2b_extracted_path, texHead, texturePack.texData[k].data)
                k += 1
                continue
            else:
                textureFile.write(uint32_to_bytes(format))
            # D3D10 Resource Dimension
            dimension = 3
            if texHead.header.numSurfaces > 1:
                dimension = 4
            textureFile.write(uint32_to_bytes(dimension))
            # MiscFlags
            textureFile.write(uint32_to_bytes(0))
            # ArraySize
            textureFile.write(uint32_to_bytes(1))
            # MiscFlags2
            alpha_mode = get_alpha_mode(texHead.header.XonSurfaceFormat)
            textureFile.write(uint32_to_bytes(alpha_mode))

            # TextureData
            textureFile.write(texturePack.texData[k].data)
            textureFile.close()
            extracted_textures_paths.append(textureFullPath)
            k += 1

    log.i(f"Finished extracting {len(extracted_textures_paths)} textures.")

    if extracted_textures_paths:
        from puredds import DDS
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
                image.save(out_path)
            except Exception as e:
                log.e(f"Failed to convert {texture_path}! Error: {e}")
                failed_conversions += 1

        success_count = len(extracted_textures_paths) - failed_conversions
        log.i(f"Finished converting textures. Success: {success_count}/{len(extracted_textures_paths)}")
    return failed_texAsset


def debug_dump_texture(assetPackName, r2b_extracted_path, texHead: tpGxTexHead, texData):
    log.d(f"Dumping textures for {assetPackName}")

    debug_extracted_path = r2b_extracted_path + "\\debug"

    if not os.path.isdir(debug_extracted_path):
        os.makedirs(debug_extracted_path)

    extracted_textures_paths = []
    for k in range(100):
        for a in range(1,2):
            textureFilename = assetPackName + "_" + str(k) + "_" + str(a) + ".dds"
            textureFullPath = debug_extracted_path + "\\" + textureFilename
            textureFile = open(textureFullPath, "wb")

            # Magic
            textureFile.write(str_to_bytes("DDS\x20"))
            # HeaderSize
            textureFile.write(uint32_to_bytes(124))
            # Flags
            flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
            if texHead.header.numMipSurfaces > 1:
                flags |= 0x20000    # DDSD_MIPMAPCOUNT
            if texHead.header.numSurfaces > 1:
                flags |= 0x800000    # DDSD_DEPTH
            textureFile.write(uint32_to_bytes(flags))
            # Height
            textureFile.write(uint32_to_bytes(texHead.header.height))
            # Width
            textureFile.write(uint32_to_bytes(texHead.header.width))
            # Size
            textureFile.write(uint32_to_bytes(texHead.header.filesize))
            # Depth
            textureFile.write(uint32_to_bytes(texHead.header.numSurfaces))
            # MipMapCount
            textureFile.write(uint32_to_bytes(texHead.header.numMipSurfaces))
            # Reserved
            for i in range(11):
                textureFile.write(uint32_to_bytes(0))

            # DDS_PIXELFORMAT
            # Size
            textureFile.write(uint32_to_bytes(32))
            # Flags
            textureFile.write(uint32_to_bytes(4))
            # fourCC
            textureFile.write(str_to_bytes("DX10"))
            # RGBBitCount
            textureFile.write(uint32_to_bytes(0))
            # RGBABitMasks
            for i in range(4):
                textureFile.write(uint32_to_bytes(0))

            # CAPS
            caps = 0x1000   # DDSCAPS_TEXTURE
            if texHead.header.numMipSurfaces > 1:
                caps |= 0x8 | 0x400000    # DDSCAPS_MIPMAP | DDSCAPS_COMPLEX
            textureFile.write(uint32_to_bytes(caps))
            # CAPS 2
            caps2 = 0x0
            if texHead.header.numSurfaces > 1:
                caps2 |= 0x200000   # DDSCAPS2_VOLUME
            textureFile.write(uint32_to_bytes(caps2))
            # CAPS 3
            textureFile.write(uint32_to_bytes(0))
            # CAPS 4
            textureFile.write(uint32_to_bytes(0))

            # Reserved
            textureFile.write(uint32_to_bytes(0))

            # DDS_HEADER_DXT10
            # DXGI Format
            textureFile.write(uint32_to_bytes(k))
            # D3D10 Resource Dimension
            dimension = 3
            if texHead.header.numSurfaces > 1:
                dimension = 4
            textureFile.write(uint32_to_bytes(dimension))
            # MiscFlags
            textureFile.write(uint32_to_bytes(0))
            # ArraySize
            textureFile.write(uint32_to_bytes(1))
            # MiscFlags2
            textureFile.write(uint32_to_bytes(a))

            # TextureData
            textureFile.write(texData)
            textureFile.close()
            extracted_textures_paths.append(textureFullPath)

    if extracted_textures_paths:
        from puredds import DDS
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
                image.save(out_path)
            except Exception as e:
                log.e(f"Failed to convert {texture_path}! Error: {e}")
                failed_conversions += 1

        success_count = len(extracted_textures_paths) - failed_conversions
        log.i(f"Finished converting textures. Success: {success_count}/{len(extracted_textures_paths)}")