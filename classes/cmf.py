from ..util import *

class frameTransformation1:
    def __init__(self, packFile):
        self.frameCount = to_ushort(packFile.read(2))
        self.indices = [to_ushort(packFile.read(2)) for i in range(self.frameCount)]
        align = 4 - (packFile.tell() % 4)
        if align != 4:
            packFile.read(align)

        self.values = [[(to_int(packFile.read(2))/0x7FFF) for j in range(4)] for i in range(self.frameCount)]

class frameTransformationData1:
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
                self.transformations.append(frameTransformation1(packFile))

class frameTransformation2:
    def __init__(self, packFile):
        self.frameCount = to_ushort(packFile.read(2))
        self.indices = [to_ushort(packFile.read(2)) for i in range(self.frameCount)]
        align = 4 - (packFile.tell() % 4)
        if align != 4:
            packFile.seek(align, 1)

        self.values = [[to_float(packFile.read(4)) for j in range(3)] for i in range(self.frameCount)]

class frameTransformationData2:
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
                self.transformations.append(frameTransformation2(packFile))

class CMF:
    def __init__(self, packFile):
        basePos = packFile.tell()

        self.magic = packFile.read(4)
        self.framesCount = to_ushort(packFile.read(2))
        self.boneCount = to_ushort(packFile.read(2))
        self.u2 = to_uint(packFile.read(4))
        self.name = to_string(packFile.read(64))
        padding = packFile.read(32)
        self.rot = [to_float(packFile.read(4)) for i in range(4)]
        self.pos = [to_float(packFile.read(4)) for i in range(3)]
        self.scale = [to_float(packFile.read(4)) for i in range(3)]
        self.framesInterpOffset = to_uint(packFile.read(4))
        self.framesTransOffset = to_uint(packFile.read(4))
        null = packFile.read(4)
        if (packFile.tell() + 4 <= basePos + self.framesInterpOffset):
            self.boneNamesOffset = to_uint(packFile.read(4))
            print("CMF contains bone names!")

        packFile.seek(basePos + self.framesInterpOffset)
        self.framesTransData1 = frameTransformationData1(packFile, self.boneCount)

        packFile.seek(basePos + self.framesTransOffset)
        self.framesTransData2 = frameTransformationData2(packFile, self.boneCount)
        