import os
import subprocess
import binascii
import bpy

from numpy import uint
from ..util import *

def construct_materials(pack_dir, material_packs):
    print("Constructing materials...")
    textures_dir = pack_dir + "\\replicant2blender_extracted\\converted\\"
    for materialPack in material_packs:
        materialAssetName = materialPack.assetPacks[0].name
        materialAssetHeader = materialPack.assetPacks[0].content.assetHeader

        b_mat_name = materialAssetName.split("_", 1)[1].split(".")[0].lower()

        if b_mat_name in bpy.data.materials:
            material = bpy.data.materials[b_mat_name]
        else:
            material = bpy.data.materials.new(b_mat_name)
        
        print("Generating material", b_mat_name)
        material.use_nodes = True
        material.node_tree.links.clear()
        material.node_tree.nodes.clear()
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        material.blend_method = 'CLIP'

        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = 1200,0
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled.location = 900,0
        output_link = links.new( principled.outputs['BSDF'], output.inputs['Surface'])

        for texture in materialAssetHeader.unknownAssets[0].textures:
            texture_filename_base = texture.filename.replace(".rtex", "")
            texture_filename = texture_filename_base + ".png"


            if texture.mapType in ["texBaseColor", "texBaseColor0"]:
                color_image = nodes.new(type='ShaderNodeTexImage')
                color_image.location = 0, 60
                color_image.image = bpy.data.images.load(textures_dir + texture_filename)
                color_image.hide = True

                albedo_principled = links.new(color_image.outputs['Color'], principled.inputs['Base Color'])
                alpha_link = links.new(color_image.outputs['Alpha'], principled.inputs['Alpha'])

            elif texture.mapType in ["texORM", "texORM0"]:
                mask_image = nodes.new(type='ShaderNodeTexImage')
                mask_image.location = 0, 0
                mask_image.image = bpy.data.images.load(textures_dir + texture_filename)
                mask_image.image.colorspace_settings.name = 'Non-Color'
                mask_image.hide = True

                sepRGB_shader = nodes.new(type="ShaderNodeSeparateRGB")
                sepRGB_shader.location = 300, 0
                sepRGB_shader.hide = True

                mask_link = links.new(mask_image.outputs['Color'], sepRGB_shader.inputs['Image'])
                roughness_link = links.new(sepRGB_shader.outputs['G'], principled.inputs['Roughness'])
                metallic_link = links.new(sepRGB_shader.outputs['B'], principled.inputs['Metallic'])

            elif texture.mapType in ["texNormal", "texNormal0"]:
                normal_image = nodes.new(type='ShaderNodeTexImage')
                normal_image.location = -300, -60
                normal_image.image = bpy.data.images.load(textures_dir + texture_filename)
                normal_image.image.colorspace_settings.name = 'Non-Color'
                normal_image.hide = True

                sepRGB_shader = nodes.new(type="ShaderNodeSeparateRGB")
                sepRGB_shader.location = -30, -60
                sepRGB_shader.hide = True

                normal_link = links.new(normal_image.outputs['Color'], sepRGB_shader.inputs['Image'])

                invert_shader = nodes.new(type="ShaderNodeInvert")
                invert_shader.location = 140, -90
                invert_shader.hide = True

                comRGB_shader = nodes.new(type="ShaderNodeCombineRGB")
                comRGB_shader.location = 300, -60
                comRGB_shader.hide = True

                r_link = links.new(sepRGB_shader.outputs['R'], comRGB_shader.inputs['R'])
                g_link = links.new(sepRGB_shader.outputs['G'], invert_shader.inputs['Color'])
                b_link = links.new(sepRGB_shader.outputs['B'], comRGB_shader.inputs['B'])

                gInverted_link = links.new(invert_shader.outputs['Color'], comRGB_shader.inputs['G'])

                normalmap_shader = nodes.new(type='ShaderNodeNormalMap')
                normalmap_shader.location = 600, -60
                normalmap_shader.hide = True
                
                combined_link = links.new(comRGB_shader.outputs['Image'], normalmap_shader.inputs['Color'])
                normalmap_link = links.new(normalmap_shader.outputs['Normal'], principled.inputs['Normal'])
                

def extract_textures(pack_dir, texture_packs, noesis_path, batch_size):
    failed_texAsset = []

    r2b_extracted_path = pack_dir + "\\" + "replicant2blender_extracted"
    converted_path = r2b_extracted_path + "\\" + "converted"

    if not os.path.isdir(r2b_extracted_path):
        os.makedirs(r2b_extracted_path)

    if not os.path.isdir(converted_path):
        os.makedirs(converted_path)

    extracted_textures_paths = []

    for texturePack in texture_packs:
        print("Extracting textures...")
        k = 0
        for assetFile in texturePack.assetFiles:
            if ".rtex" not in assetFile.name:
                    continue
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
            textureFile.write(str_to_bytes("\x07\x10\x0A\x00"))
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
            textureFile.write(str_to_bytes("\x08\x10\x04\x00"))
            # CAPS 2
            textureFile.write(uint32_to_bytes(0))
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
                print("Texture extraction failed!", assetFile.name)
                failed_texAsset.append(assetFile)
                textureFile.close()
                continue
            else:
                textureFile.write(uint32_to_bytes(format))
            # D3D10 Resource Dimension
            textureFile.write(uint32_to_bytes(3))
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

    # Noesis Converting
    argPrograms = []
    for texturePack in texture_packs:
        print("Batch converting textures from", texturePack.assetPacks[0].name, "with Noesis...")
        for texture_path in extracted_textures_paths:
            in_path = texture_path
            directory = os.path.dirname(in_path)
            converted_path = directory + "\\converted\\"
            out_path = converted_path + os.path.basename(in_path).replace(".dds", ".png")
            print("Converting", texture_path, "to", out_path)
            argProgram = []
            argProgram.append(noesis_path)
            argProgram.append("?cmode")
            argProgram.append(textureFullPath)
            argProgram.append(out_path)
            argPrograms.append(argProgram)
    
    processes = []
    while len(argPrograms) > 0:
        if len(argPrograms) < batch_size:
            for argProg in argPrograms:
                processes.append(subprocess.Popen(argProg, stdout=subprocess.DEVNULL))
            argPrograms.clear()
        else:
            for i in range(batch_size):
                processes.append(subprocess.Popen(argPrograms[i], stdout=subprocess.DEVNULL))
            del argPrograms[:batch_size]

        for p in processes:
            p.wait()

    return failed_texAsset