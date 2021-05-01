from ..util import *

class Header:
    def __init__(self, packFile):
        self.boundingBoxCoord1 = [to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4))]
        self.boundingBoxCoord2 = [to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4))]

        self.totalVertexDataSize = to_uint(packFile.read(4))
        self.unknownFlag = to_uint(packFile.read(4))
        self.totalIndicesDataSize = to_uint(packFile.read(4))

        self.unknownShort0 = to_ushort(packFile.read(2))
        self.unknownShort1 = to_ushort(packFile.read(2))

        self.unknownFloat = to_float(packFile.read(4))

        self.boneCount = to_uint(packFile.read(4))
        offsetToBones = to_uint(packFile.read(4))
        self.offsetBones = packFile.tell() + offsetToBones - 4

        self.boneDataCount = to_uint(packFile.read(4))
        offsetToBonesData = to_uint(packFile.read(4))
        self.offsetBonesData = packFile.tell() + offsetToBonesData - 4

        self.objectGroupCount = to_uint(packFile.read(4))
        offsetToObjectGroups = to_uint(packFile.read(4))
        self.offsetObjectGroups = packFile.tell() + offsetToObjectGroups - 4

        self.materialCount = to_uint(packFile.read(4))
        offsetToMaterials = to_uint(packFile.read(4))
        self.offsetMaterials = packFile.tell() + offsetToMaterials - 4

        self.objectCount = to_uint(packFile.read(4))
        offsetToObjects = to_uint(packFile.read(4))
        self.offsetObjects = packFile.tell() + offsetToObjects - 4

class Bone:
    def __init__(self, packFile):
        offsetToName = to_uint(packFile.read(4))
        self.offsetName = packFile.tell() + offsetToName - 4

        self.parentBoneIndex = to_int(packFile.read(4))

        self.unknownFloat0 = to_float(packFile.read(4))
        self.unknownFloat1 = to_float(packFile.read(4))
        self.unknownFloat2 = to_float(packFile.read(4))
        self.unknownFloat3 = to_float(packFile.read(4))
        self.unknownFloat4 = to_float(packFile.read(4))
        self.unknownFloat5 = to_float(packFile.read(4))
        self.unknownFloat6 = to_float(packFile.read(4))
        self.unknownFloat7 = to_float(packFile.read(4))
        self.unknownFloat8 = to_float(packFile.read(4))
        self.unknownFloat9 = to_float(packFile.read(4))

        returnPos = packFile.tell()
        packFile.seek(self.offsetName)
        self.name = to_string(packFile.read(1024))
        packFile.seek(returnPos)

class BoneData:
    def __init__(self, packFile):
        offsetToName = to_uint(packFile.read(4))
        self.offsetName = packFile.tell() + offsetToName - 4

        self.unknownParentIndex = to_int(packFile.read(4))
        self.length = to_float(packFile.read(4))

        self.unknownMatrix0 = []
        for i in range(4):
            self.unknownMatrix0.append([to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4))])

        self.unknownMatrix1 = []
        for i in range(4):
            self.unknownMatrix1.append([to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4))])

        returnPos = packFile.tell()
        packFile.seek(self.offsetName)
        self.name = to_string(packFile.read(1024))
        packFile.seek(returnPos)

class VertexData:
    def __init__(self, packFile):
        self.objectGroupVertexDataOffset = to_uint(packFile.read(4))

        self.unknownUInt_32_0 = to_uint(packFile.read(4))
        self.unknownUInt_32_1 = to_uint(packFile.read(4))

        self.vertexStructSize = to_uint(packFile.read(4))
        self.vertexStructFlag = to_uint(packFile.read(1))

        alignRelative(packFile, 0, 8)

class ObjectGroup:
    def __init__(self, packFile):
        self.indicesStartOffset = to_uint(packFile.read(4))

        self.unknownUInt32_0 = to_uint(packFile.read(4))
        self.unknownUInt32_1 = to_uint(packFile.read(4))

        self.vertexCount = to_uint(packFile.read(4))
        self.indicesCount = to_uint(packFile.read(4))
        self.indicesStructSize = to_uint(packFile.read(4))

        self.unknownUInt32_3 = to_uint(packFile.read(4))

        self.vertexDataCount = to_uint(packFile.read(4))
        offsetToVertexData = to_uint(packFile.read(4))
        self.offsetVertexData = packFile.tell() + offsetToVertexData - 4

        returnPos = packFile.tell()
        packFile.seek(self.offsetVertexData)
        self.vertexData = []
        for i in range(self.vertexDataCount):
            self.vertexData.append(VertexData(packFile))

        packFile.seek(returnPos)
        alignRelative(packFile, 0, 8)

class Material:
    def __init__(self, packFile):
        offsetToName = to_uint(packFile.read(4))
        self.offsetName = packFile.tell() + offsetToName - 4

        offsetToUnknownByte = to_uint(packFile.read(4))
        self.offsetUnknownByte = packFile.tell() + offsetToUnknownByte - 4

        self.unknownUInt32 = to_uint(packFile.read(4))

        returnPos = packFile.tell()
        packFile.seek(self.offsetName)
        self.name = to_string(packFile.read(1024))

        packFile.seek(self.offsetUnknownByte)
        self.unknownByte = packFile.read(1)

        packFile.seek(returnPos)

class Object:
    def __init__(self, packFile):
        self.objectGroupIndex = to_uint(packFile.read(4))
        self.materialIndex = to_uint(packFile.read(4))
        self.indicesStart = to_uint(packFile.read(4))
        self.indicesCount = to_uint(packFile.read(4))

        self.boundingBoxCoord1 = [to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4))]
        self.boundingBoxCoord2 = [to_float(packFile.read(4)), to_float(packFile.read(4)), to_float(packFile.read(4))]

class tpGxMeshHead:
    def __init__(self, packFile):
        self.header = Header(packFile)

        packFile.seek(self.header.offsetBones)
        self.bones = []
        for i in range(self.header.boneCount):
            self.bones.append(Bone(packFile))

        packFile.seek(self.header.offsetBonesData)
        self.bonesData = []
        for i in range(self.header.boneDataCount):
            self.bonesData.append(BoneData(packFile))

        packFile.seek(self.header.offsetObjectGroups)
        self.objectGroups = []
        for i in range(self.header.objectGroupCount):
            self.objectGroups.append(ObjectGroup(packFile))

        packFile.seek(self.header.offsetMaterials)
        self.materials = []
        for i in range(self.header.materialCount):
            self.materials.append(Material(packFile))

        packFile.seek(self.header.offsetObjects)
        self.objects = []
        for i in range(self.header.objectCount):
            self.objects.append(Object(packFile))