from ..util import *
from .cmf import CMF

class KPK:
    def __init__(self, packFile):
        basePos = packFile.tell()

        self.magic = packFile.read(4)
        self.fileCount = to_uint(packFile.read(4))
        null = packFile.read(4)

        self.fileOffsets = []
        for i in range(self.fileCount):
            self.fileOffsets.append(to_uint(packFile.read(4)))

        self.fileSizes = []
        for i in range(self.fileCount):
            self.fileSizes.append(to_uint(packFile.read(4)))

        self.files = []
        for i in range(self.fileCount):
            packFile.seek(basePos + self.fileOffsets[i])
            magic = packFile.read(4)
            packFile.seek(-4, 1)

            if (magic == b"CMF\x01"):
                self.files.append(CMF(packFile))
            else:
                print("Unknown file type:", magic)
                self.files.append(None)