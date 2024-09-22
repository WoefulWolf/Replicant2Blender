from ..util import *

class tpGxTexHead:
    def __init__(self, packFile):
        self.header = Header(packFile)

        packFile.seek(self.header.offsetMipSurfaces)
        self.mipSurfaces = []
        for i in range(self.header.numMipSurfaces):
            self.mipSurfaces.append(MipSurface(packFile))

class Header:
    def __init__(self, packFile):
        self.width = to_uint(packFile.read(4))
        self.height = to_uint(packFile.read(4))

        self.numSurfaces = to_uint(packFile.read(4))

        self.unknownUInt32_0 = to_uint(packFile.read(4))

        self.filesize = to_uint(packFile.read(4))

        self.unknownUInt32_1 = to_uint(packFile.read(4))
        
        try:
            self.XonSurfaceFormat = XonSurfaceDXGIFormat(to_uint(packFile.read(4)))
        except:
            self.XonSurfaceFormat = to_uint(packFile.read(4))

        self.numMipSurfaces = to_uint(packFile.read(4))
        offsetToMipSurfaces = to_uint(packFile.read(4))
        self.offsetMipSurfaces = packFile.tell() + offsetToMipSurfaces - 4


class MipSurface:
    def __init__(self, packFile):
        self.offset = to_uint(packFile.read(4))

        self.unknownUInt32_0 = to_uint(packFile.read(4))
        self.unknownUInt32_1 = to_uint(packFile.read(4))
        self.unknownUInt32_2 = to_uint(packFile.read(4))

        self.size = to_uint(packFile.read(4))

        self.unknownUInt32_3 = to_uint(packFile.read(4))

        self.width = to_uint(packFile.read(4))
        self.height = to_uint(packFile.read(4))

        self.unknownUInt32_4 = to_uint(packFile.read(4))
        self.unknownUInt32_5 = to_uint(packFile.read(4))