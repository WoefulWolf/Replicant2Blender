from ..util import *
from .path import *
from .assetPack import *
from .file import *
from .tpGxMeshData import tpGxMeshData
from .tpGxTexData import tpGxTexData



class Pack:
    def __init__(self, packFile):
        self.id = packFile.read(4)
        self.version = to_uint(packFile.read(4))

        self.packFileTotalSize = to_uint(packFile.read(4))
        self.packFileSerializedSize = to_uint(packFile.read(4))
        self.packFileResourceSize = to_uint(packFile.read(4))

        self.pathCount = to_uint(packFile.read(4))
        self.offsetToPaths = to_uint(packFile.read(4))
        offsetPaths = packFile.tell() + self.offsetToPaths - 4

        self.assetPackCount = to_uint(packFile.read(4))
        self.offsetToAssetPacks = to_uint(packFile.read(4))
        offsetAssetPacks = packFile.tell() + self.offsetToAssetPacks - 4

        self.fileCount = to_uint(packFile.read(4))
        self.offsetToFiles = to_uint(packFile.read(4))
        offsetFiles = packFile.tell() + self.offsetToFiles - 4

        log.d(" - Pack Paths:")
        packFile.seek(offsetPaths)
        self.paths = []
        for i in range(self.pathCount):
            self.paths.append(Path(packFile))

        log.d(" - Pack AssetPacks:")
        packFile.seek(offsetAssetPacks)
        self.assetPacks: list[AssetPack] = []
        for i in range(self.assetPackCount):
            self.assetPacks.append(AssetPack(packFile))

        log.d(" - Pack Files:")
        packFile.seek(offsetFiles)
        self.assetFiles: list[File] = []
        for i in range(self.fileCount):
            self.assetFiles.append(File(packFile))

        packFile.seek(self.packFileSerializedSize)
        self.meshData = []
        self.texData = []
        self.levelData: list[LevelData] = []
        for assetFile in self.assetFiles:
            if (assetFile.content == None
                or assetFile.content.id != b"BXON"
                or assetFile.content.fileTypeName not in ["tpGxMeshHead", "tpGxTexHead", "LevelData"]):
                continue

            if (assetFile.content.fileTypeName == "tpGxMeshHead"):
                self.meshData.append(tpGxMeshData(packFile, assetFile.content.meshHead))
            elif (assetFile.content.fileTypeName == "tpGxTexHead"):
                self.texData.append(tpGxTexData(packFile, assetFile.content.texHead))
            elif (assetFile.content.fileTypeName == "LevelData"):
                self.levelData.append(assetFile.content.levelData)

            if ((packFile.tell() - self.packFileSerializedSize) % 32 != 0):
                alignRelative(packFile, self.packFileSerializedSize, 32)


        

        