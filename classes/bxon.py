from ..util import *
from .tpGxMeshHead import tpGxMeshHead

class BXON:
    def __init__(self, packFile):
        self.id = packFile.read(4)
        self.version = to_int(packFile.read(4))
        self.projectID = to_int(packFile.read(4))

        self.offsetToFileTypeName = to_int(packFile.read(4))
        offsetFileTypeName = packFile.tell() + self.offsetToFileTypeName - 4

        self.offsetToFileData = to_int(packFile.read(4))
        offsetFileData = packFile.tell() + self.offsetToFileData - 4

        returnPos = packFile.tell()
        packFile.seek(offsetFileTypeName)
        self.fileTypeName = to_string(packFile.read(1024))

        if (self.fileTypeName == "tpGxMeshHead"):
            packFile.seek(offsetFileData)
            self.meshHead = tpGxMeshHead(packFile)

        packFile.seek(returnPos)

        print(" >", self.fileTypeName)