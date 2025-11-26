import bpy, os

from .importers.levelData_import import importLevelData
from .classes.pack import *
from .importers.meshAsset_import import construct_meshes
from .importers.materialAssets_import import construct_materials, extract_textures
from .util import log

imported_texturePacks = []
failed_texturePacks = []
imported_materialPacks = []

def clear_importLists():
    imported_materialPacks.clear()
    imported_texturePacks.clear()

def main(packFilePath, do_extract_textures, do_construct_materials, addon_name):
    pack_directory = os.path.dirname(os.path.abspath(packFilePath))

    # meshPack
    log.i(f"Parsing Mesh PACK file... {packFilePath}")
    with open(packFilePath, "rb") as packFile:
        meshPack = Pack(packFile)
    log.i("Constructing Blender Objects...")
    construct_meshes(meshPack)
    importLevelData(meshPack.levelData, addon_name)
    log.i("Blender object construction complete.")

    # Import materials + textures
    failedTexturesAssets = []
    if do_extract_textures or do_construct_materials:

        # materialPacks
        materialPacks = []
        for path in meshPack.paths:
            materialPackFilename = path.path.split('/')[-1]

            materialPackFullPath = pack_directory + "\\" + materialPackFilename

            if not os.path.isfile(materialPackFullPath):
                if os.path.isfile(materialPackFullPath + ".xap"):
                    materialPackFullPath += ".xap"
                else:
                    log.w(f"Failed to find material PACK file: {materialPackFilename}")
                    continue
            
            if (materialPackFullPath not in imported_materialPacks):
                imported_materialPacks.append(materialPackFullPath)
                log.i(f"Parsing Material PACK file... {path.path}")
                with open(materialPackFullPath, "rb") as packFile:
                    materialPacks.append(Pack(packFile))

        #texturePacks
        texturePacks = []
        for materialPack in materialPacks:
            for path in materialPack.paths:
                texturePackFilename = path.path.split('/')[-1]

                texturePackFullPath = pack_directory + "\\" + texturePackFilename

                if not os.path.isfile(texturePackFullPath):
                    if os.path.isfile(texturePackFullPath + ".xap"):
                        texturePackFullPath += ".xap"
                    else:
                        if (texturePackFullPath not in failed_texturePacks):
                            failed_texturePacks.append(texturePackFullPath)
                            log.w(f"Failed to find texture PACK file: {texturePackFilename}")
                        continue

                if (texturePackFullPath not in imported_texturePacks):
                    imported_texturePacks.append(texturePackFullPath)
                    log.i(f"Parsing Texture PACK file... {path.path}")
                    with open(texturePackFullPath, "rb") as packFile:
                        texturePacks.append(Pack(packFile))

        if do_extract_textures:
            failedTexturesAssets = extract_textures(pack_directory, texturePacks)

        if do_construct_materials:
            construct_materials(pack_directory, materialPacks)

    if len(failedTexturesAssets) > 0:
        log.e("Some textures failed to extract!")
        log.e("Report this issue @ https://github.com/WoefulWolf/Replicant2Blender/issues")
        log.e("Please include the unknown formats logged below and the path of the file you were trying to import.")
        for assetFile in failedTexturesAssets:
            texHead = assetFile.content.texHead
            log.e(f"{assetFile.name} {hex(texHead.header.XonSurfaceFormat)}")
    else:
        log.i('Importing finished. ;)')

def only_extract_textures(packFilePath, addon_name):
    pack_directory = os.path.dirname(os.path.abspath(packFilePath))

    packFile = open(packFilePath, "rb")
    texturePack = Pack(packFile)
    packFile.close()
    failedTexturesAssets = extract_textures(pack_directory, [texturePack])

    if len(failedTexturesAssets) > 0:
        log.e("Some textures failed to extract!")
        log.e("Report this issue @ https://github.com/WoefulWolf/Replicant2Blender/issues")
        log.e("Please include the unknown formats logged below and the path of the file you were trying to import.")
        for assetFile in failedTexturesAssets:
            texHead = assetFile.content.texHead
            log.e(f"{assetFile.name} {hex(texHead.header.XonSurfaceFormat)}")
    else:
        log.i('Extraction finished. ;)')

    