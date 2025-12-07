import os
import bpy
from bpy.types import Material

from ..classes.material_instance import tpGxMaterialInstanceV2
from ..classes.asset_package import tpXonAssetHeader
from ..classes.tex_head import get_DXGI_format, get_alpha_mode, tpGxTexHead
from ..classes.pack import Pack, PackFile

from .materials.master_rs_standard import master_rs_standard
from .materials.master_rs_layer2 import master_rs_layer2
from .materials.master_rs_layer3 import master_rs_layer3
from .materials.master_rs_layer4 import master_rs_layer4
from .materials.master_rs_hair import master_rs_hair
from .materials.master_rs_ao_sheet import master_rs_ao_sheet
from .materials.master_rs_leaf import master_rs_leaf
from .materials.master_rs_xlu_water import master_rs_xlu_water
from .materials.nodes import dx_to_gl_normal, grid_location
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

def setup_custom_ui_values(material: Material, material_instance: tpGxMaterialInstanceV2, textures_dir: str):
    material.replicant_master_material = material_instance.parent_asset_path
    for constant_buffer in material_instance.constant_buffers:
        cb = material.replicant_constant_buffers.add()
        cb.name = constant_buffer.constant_buffer_name
        cb.previous_name = cb.name
        for constant in constant_buffer.constants:
            const = cb.constants.add()
            const.name = constant.constant_name
            const.previous_name = const.name
            const.values = (constant.value0, constant.value1, constant.value2, constant.value3, constant.value4, constant.value5)
    for texture_parameter in material_instance.texture_parameters:
        tp = material.replicant_texture_parameters.add()
        tp.name = texture_parameter.parameter_name
        tp.values = (texture_parameter.value0, texture_parameter.value1, texture_parameter.value2)
    texture_node_labels = [node.label for node in material.node_tree.nodes if node.type == 'TEX_IMAGE']
    for texture in material_instance.textures:
        if texture.sampler_name in texture_node_labels:
            continue
        image_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
        image_node.location = grid_location(-5, -5)
        image_node.hide = True
        image_node.label = texture.sampler_name
        texture_filename_base = texture.texture_name.replace(".rtex", "")
        texture_filename = texture_filename_base + ".png"
        texture_file = search_texture(textures_dir, texture_filename)
        if texture_file is not None:
            image_node.image = bpy.data.images.load(texture_file)

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
            material.replicant_constant_buffers.clear()
            material.replicant_texture_parameters.clear()
        else:
            material = bpy.data.materials.new(b_mat_name)

        log.d(f"Generating material {b_mat_name}")

        try:
            handled = False
            for material_type, handler in MATERIAL_HANDLERS.items():
                if material_type in material_instance.parent_asset_path:
                    handler(textures_dir, material, material_instance)
                    setup_custom_ui_values(material, material_instance, textures_dir)
                    handled = True
                    break
            if handled:
                continue
        except Exception as e:
            log.w(f"Failed to construct shader for material: {material.name} ({e})")

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

        for texture in material_instance.textures:
            texture_filename_base = texture.texture_name.replace(".rtex", "")
            texture_filename = texture_filename_base + ".png"
            texture_file = search_texture(textures_dir, texture_filename)
            if texture_file is None:
                log.w(f"Failed to find texture: {texture_filename}")
                continue

            if texture.sampler_name in ["texBaseColor", "texBaseColor0"]:
                color_image = nodes.new(type='ShaderNodeTexImage')
                color_image.location = grid_location(0, 0)
                color_image.image = bpy.data.images.load(texture_file)
                color_image.hide = True
                color_image.label = texture.sampler_name

                albedo_principled = links.new(color_image.outputs['Color'], principled.inputs['Base Color'])
                alpha_link = links.new(color_image.outputs['Alpha'], principled.inputs['Alpha'])

            elif texture.sampler_name in ["texORM", "texORM0"]:
                mask_image = nodes.new(type='ShaderNodeTexImage')
                mask_image.location = grid_location(0, 1)
                mask_image.image = bpy.data.images.load(texture_file)
                mask_image.image.colorspace_settings.name = 'Non-Color'
                mask_image.hide = True
                mask_image.label = texture.sampler_name

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

            elif texture.sampler_name in ["texNormal", "texNormal0"]:
                normal_image = nodes.new(type='ShaderNodeTexImage')
                normal_image.location = grid_location(0, 2)
                normal_image.image = bpy.data.images.load(texture_file)
                normal_image.image.colorspace_settings.name = 'Non-Color'
                normal_image.hide = True
                normal_image.label = texture.sampler_name

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
    
        setup_custom_ui_values(material, material_instance, textures_dir)
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
            flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE
            if tex_head.mip_count > 1:
                flags |= 0x20000    # DDSD_MIPMAPCOUNT
            if tex_head.depth > 1:
                flags |= 0x800000    # DDSD_DEPTH
            texture_file.write(uint32_to_bytes(flags))
            # Height
            texture_file.write(uint32_to_bytes(tex_head.height))
            # Width
            texture_file.write(uint32_to_bytes(tex_head.width))
            # Size
            texture_file.write(uint32_to_bytes(tex_head.size))
            # Depth
            texture_file.write(uint32_to_bytes(tex_head.depth))
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
            caps = 0x1000   # DDSCAPS_TEXTURE
            if tex_head.mip_count > 1:
                caps |= 0x8 | 0x400000    # DDSCAPS_MIPMAP | DDSCAPS_COMPLEX
            texture_file.write(uint32_to_bytes(caps))
            # CAPS 2
            caps2 = 0x0
            if tex_head.depth > 1:
                caps2 |= 0x200000   # DDSCAPS2_VOLUME
            texture_file.write(uint32_to_bytes(caps2))
            # CAPS 3
            texture_file.write(uint32_to_bytes(0))
            # CAPS 4
            texture_file.write(uint32_to_bytes(0))
            # Reserved
            texture_file.write(uint32_to_bytes(0))

            # DDS_HEADER_DXT10
            # DXGI Format
            format = get_DXGI_format(tex_head.surface_format)
            if format == None or format == "UNKNOWN":
                log.w(f"Texture extraction failed! {file.name}")
                failed_texture_files.append(file)
                texture_file.close()
                k += 1
                continue
            else:
                texture_file.write(uint32_to_bytes(format))
            # D3D10 Resource Dimension
            dimension = 3
            if tex_head.depth > 1:
                dimension = 4
            texture_file.write(uint32_to_bytes(dimension))
            # MiscFlags
            texture_file.write(uint32_to_bytes(0))
            # ArraySize
            texture_file.write(uint32_to_bytes(1))
            # MiscFlags2
            alpha_mode = get_alpha_mode(tex_head.surface_format)
            texture_file.write(uint32_to_bytes(alpha_mode))

            # TextureData - find and write texture data
            for file_data in pack.files_data:
                if file_data.file_index == idx and file_data.tex_data:
                    # Concatenate all subresource data (mipmaps)
                    for subresource in file_data.tex_data.subresource_data:
                        texture_file.write(subresource)
                    break

            texture_file.close()
            extracted_textures_paths.append(texture_path)
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
    return failed_texture_files