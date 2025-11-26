from ..util import *

class Path:
    def __init__(self, packFile):
        self.hash = packFile.read(4)

        self.offsetToPath = to_int(packFile.read(4))
        offsetPath = packFile.tell() + self.offsetToPath - 4

        self.unknown0 = to_int(packFile.read(4))

        returnPos = packFile.tell()
        packFile.seek(offsetPath)
        self.path = to_string(packFile.read(1024))

        packFile.seek(returnPos)