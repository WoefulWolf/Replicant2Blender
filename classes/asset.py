from ..util import *

class Asset:
    def __init__(self, packFile):
        self.hash = packFile.read(4)

        self.offsetToName = to_int(packFile.read(4))
        offsetName = packFile.tell() + self.offsetToName - 4

        self.fileSize = to_int(packFile.read(4))
        self.offsetToContentStart = to_int(packFile.read(4))
        self.offsetToContentEnd = to_int(packFile.read(4))

        returnPos = packFile.tell()
        packFile.seek(offsetName)
        self.name = to_string(packFile.read(1024))

        packFile.seek(returnPos)

        print("[+]", self.name)