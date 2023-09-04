from ..util import *

class frameInterpolation:
    def __init__(self, packFile):
        self.frameCount = to_ushort(packFile.read(2))
        self.indices = [to_ushort(packFile.read(2)) for i in range(self.frameCount)]
        align = 4 - (packFile.tell() % 4)
        if align != 4:
            packFile.read(align)

        self.values = [[to_float(packFile.read(4)) for j in range(2)] for i in range(self.frameCount)]

class frameInterpolationData:
    def __init__(self, packFile, boneCount):
        basePos = packFile.tell()

        self.offsets = [to_uint(packFile.read(4)) for i in range(boneCount)]

        self.interpolations = []
        for i in range(boneCount):
            if self.offsets[i] == 0:
                self.interpolations.append(None)
                continue
            else:
                packFile.seek(basePos + self.offsets[i])
                self.interpolations.append(frameInterpolation(packFile))

class frameTransformation:
    def __init__(self, packFile):
        self.frameCount = to_ushort(packFile.read(2))
        self.indices = [to_ushort(packFile.read(2)) for i in range(self.frameCount)]
        align = 4 - (packFile.tell() % 4)
        if align != 4:
            packFile.seek(align, 1)

        self.values = [[to_float(packFile.read(4)) for j in range(3)] for i in range(self.frameCount)]

class frameTransformationData:
    def __init__(self, packFile, boneCount):
        basePos = packFile.tell()

        self.offsets = [to_uint(packFile.read(4)) for i in range(boneCount)]

        self.transformations = []
        for i in range(boneCount):
            if self.offsets[i] == 0:
                self.transformations.append(None)
                continue
            else:
                packFile.seek(basePos + self.offsets[i])
                self.transformations.append(frameTransformation(packFile))

class CMF:
    def __init__(self, packFile):
        basePos = packFile.tell()

        self.magic = packFile.read(4)
        self.framesCount = to_ushort(packFile.read(2))
        self.boneCount = to_ushort(packFile.read(2))
        self.u2 = to_uint(packFile.read(4))
        self.name = to_string(packFile.read(64))
        padding = packFile.read(32)
        self.pos = [to_float(packFile.read(4)) for i in range(3)]
        self.rot = [to_float(packFile.read(4)) for i in range(4)]
        self.scale = [to_float(packFile.read(4)) for i in range(3)]
        self.framesInterpOffset = to_uint(packFile.read(4))
        self.framesTransOffset = to_uint(packFile.read(4))
        null = packFile.read(4)
        if (packFile.tell() + 4 <= basePos + self.framesInterpOffset):
            self.boneNamesOffset = to_uint(packFile.read(4))
            print("CMF contains bone names!")

        packFile.seek(basePos + self.framesInterpOffset)
        self.framesInterpData = frameInterpolationData(packFile, self.boneCount)

        packFile.seek(basePos + self.framesTransOffset)
        self.framesTransData = frameTransformationData(packFile, self.boneCount)
        