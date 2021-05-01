from ..util import *

class objectGroupVertexData:
    def __init__(self, packFile, meshDataStartOffset, objectGroup):

        self.vertexCoords = []
        self.vertexWeights = []
        self.vertexNormals = []
        self.vertexUVs = []
        self.vertexBoneIndices = []

        for i in range(objectGroup.vertexDataCount):
            packFile.seek(meshDataStartOffset + objectGroup.vertexData[i].objectGroupVertexDataOffset)
            if (objectGroup.vertexData[i].vertexStructSize == 12):

                if (objectGroup.vertexData[i].vertexStructFlag == 0):
                    for k in range(objectGroup.vertexCount):
                        x = to_float(packFile.read(4))
                        y = to_float(packFile.read(4))
                        z = to_float(packFile.read(4))
                        self.vertexCoords.append([x, y, z])

                elif (objectGroup.vertexData[i].vertexStructFlag == 6):
                    for k in range(objectGroup.vertexCount):
                        w0 = to_float(packFile.read(4))
                        w1 = to_float(packFile.read(4))
                        w2 = to_float(packFile.read(4))
                        w3 = 1 - w0 - w1 - w2
                        self.vertexWeights.append([w0, w1, w2, w3])

                else:
                    for k in range(objectGroup.vertexCount):
                        packFile.seek(12, 1)

            elif (objectGroup.vertexData[i].vertexStructSize == 8):

                if (objectGroup.vertexData[i].vertexStructFlag == 6):
                    for k in range(objectGroup.vertexCount):
                        w0 = to_float(packFile.read(4))
                        w1 = to_float(packFile.read(4))
                        w2 = 1 - w0 - w1
                        self.vertexWeights.append([w0, w1, w2])
                else:
                    for k in range(objectGroup.vertexCount):
                        packFile.seek(8, 1)

            elif (objectGroup.vertexData[i].vertexStructSize == 4):

                if (objectGroup.vertexData[i].vertexStructFlag == 1):
                    for k in range(objectGroup.vertexCount):
                        nx = to_int(packFile.read(1))
                        ny = to_int(packFile.read(1))
                        nz = to_int(packFile.read(1))
                        dummy = to_int(packFile.read(1))
                        self.vertexNormals.append([nx, ny, nz, dummy])

                elif (objectGroup.vertexData[i].vertexStructFlag == 2):
                    for k in range(objectGroup.vertexCount):
                        # TODO Perhaps tangents
                        packFile.seek(4, 1)

                elif (objectGroup.vertexData[i].vertexStructFlag == 4):
                    for k in range(objectGroup.vertexCount):
                        u = to_float16(packFile.read(2))
                        v = 1 - to_float16(packFile.read(2))
                        self.vertexUVs.append([u, v])
                
                elif (objectGroup.vertexData[i].vertexStructFlag == 5):
                    for k in range(objectGroup.vertexCount):
                        b0 = to_int(packFile.read(1))
                        b1 = to_int(packFile.read(1))
                        b2 = to_int(packFile.read(1))
                        b3 = to_int(packFile.read(1))
                        self.vertexBoneIndices.append([b0, b1, b2, b3])

                else:
                    for k in range(objectGroup.vertexCount):
                        packFile.seek(4, 1)
        
        alignRelative(packFile, 0, 4)

class objectGroupIndicesData:
    def __init__(self, packFile, objectGroup):
        self.indices = []

        if (objectGroup.indicesStructSize == 2):
            for i in range(round(objectGroup.indicesCount / 3)):
                v0 = to_ushort(packFile.read(2))
                v1 = to_ushort(packFile.read(2))
                v2 = to_ushort(packFile.read(2))
                self.indices.append([v2, v1, v0])           # Uses reversed index order compared to Blender

        else:
            for i in range(round(objectGroup.indicesCount / 3)):
                v0 = to_int(packFile.read(4))
                v1 = to_int(packFile.read(4))
                v2 = to_int(packFile.read(4))
                self.indices.append([v2, v1, v0])           # Uses reversed index order compared to Blender

        alignRelative(packFile, 0, 4)

        
class tpGxMeshData:
    def __init__(self, packFile, meshHead):
        meshDataStartOffset = packFile.tell()

        self.objectGroupVertices = []
        for objectGroup in meshHead.objectGroups:
            self.objectGroupVertices.append(objectGroupVertexData(packFile, meshDataStartOffset, objectGroup))

        if ((packFile.tell() - meshDataStartOffset) % 256 != 0):
            alignRelative(packFile, meshDataStartOffset, 256)

        self.objectGroupIndices = []
        for objectGroup in meshHead.objectGroups:
            self.objectGroupIndices.append(objectGroupIndicesData(packFile, objectGroup))

        self.meshVertexCoords = []
        self.meshVertexWeights = []
        self.meshVertexNormals = []
        self.meshVertexUVs = []
        self.meshVertexBoneIndices = []
        self.meshIndices = []

        for group in self.objectGroupVertices:
            self.meshVertexCoords += group.vertexCoords
            self.meshVertexWeights += group.vertexWeights
            self.meshVertexNormals += group.vertexNormals
            self.meshVertexUVs += group.vertexUVs
            self.meshVertexBoneIndices += group.vertexBoneIndices
        
        for group in self.objectGroupIndices:
            self.meshIndices += group.indices
