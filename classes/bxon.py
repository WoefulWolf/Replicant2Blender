from .levelData import LevelData
from ..util import *
from .tpGxAssetHeader import tpGxAssetHeader
from .tpGxMeshHead import tpGxMeshHead
from .tpGxTexHead import tpGxTexHead

class BXON:
    def __init__(self, packFile):
        self.id = packFile.read(4)
        self.version = to_int(packFile.read(4))
        self.projectID = to_int(packFile.read(4))

        self.offsetToFileTypeName = to_int(packFile.read(4))
        offsetFileTypeName = packFile.tell() + self.offsetToFileTypeName - 4

        self.offsetToAssetData = to_int(packFile.read(4))
        offsetAssetData = packFile.tell() + self.offsetToAssetData - 4

        returnPos = packFile.tell()
        packFile.seek(offsetFileTypeName)
        self.fileTypeName = to_string(packFile.read(1024))

        packFile.seek(offsetAssetData)
        if (self.fileTypeName == "tpXonAssetHeader"):
            self.assetHeader = tpGxAssetHeader(packFile)
        elif (self.fileTypeName == "tpGxMeshHead"):
            self.meshHead = tpGxMeshHead(packFile)
        elif (self.fileTypeName == "tpGxTexHead"):
            self.texHead = tpGxTexHead(packFile)
        elif (self.fileTypeName == "LevelData"):
            self.levelData = LevelData(packFile)

        packFile.seek(returnPos)

        log.d(f"\t\t> {self.fileTypeName}")
