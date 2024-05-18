from ..util import *
from .bxon import *

class File:
    def __init__(self, packFile):
        self.hash = packFile.read(4)

        self.offsetToName = to_int(packFile.read(4))
        offsetName = packFile.tell() + self.offsetToName - 4

        self.fileSize = to_int(packFile.read(4))
        self.offsetToFileStart = to_int(packFile.read(4))
        offsetFileStart = packFile.tell() + self.offsetToFileStart - 4

        self.unknown0 = to_int(packFile.read(4))

        returnPos = packFile.tell()
        packFile.seek(offsetName)
        self.name = to_string(packFile.read(1024))
        
        print("\t[+]", self.name)

        packFile.seek(offsetFileStart)
        fileID = packFile.read(4)
        packFile.seek(-4, 1)
        if (fileID == b"BXON"):
            self.content = BXON(packFile)
        else:
            self.content = None
        
        packFile.seek(returnPos)
