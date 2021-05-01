from ..util import *
from .path import *
from .asset import *
from .file import *
from .tpGxMeshData import tpGxMeshData

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

        self.assetCount = to_uint(packFile.read(4))
        self.offsetToAssets = to_uint(packFile.read(4))
        offsetAssets = packFile.tell() + self.offsetToAssets - 4

        self.fileCount = to_uint(packFile.read(4))
        self.offsetToFiles = to_uint(packFile.read(4))
        offsetFiles = packFile.tell() + self.offsetToFiles - 4

        print("\nPack Paths:")
        packFile.seek(offsetPaths)
        self.paths = []
        for i in range(self.pathCount):
            self.paths.append(Path(packFile))
        
        print("\nPack Assets:")
        packFile.seek(offsetAssets)
        self.assets = []
        for i in range(self.assetCount):
            self.assets.append(Asset(packFile))

        print("\nPack Files:")
        packFile.seek(offsetFiles)
        self.assetFiles = []
        for i in range(self.fileCount):
            self.assetFiles.append(File(packFile))

        packFile.seek(self.packFileSerializedSize)
        self.meshData = []
        for assetFile in self.assetFiles:
            if (assetFile.content == None or assetFile.content.fileTypeName != "tpGxMeshHead"):
                continue

            self.meshData.append(tpGxMeshData(packFile, assetFile.content.meshHead))
            if ((packFile.tell() - self.packFileSerializedSize) % 32 != 0):
                alignRelative(packFile, self.packFileSerializedSize, 32)


        

        