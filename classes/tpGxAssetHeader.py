from struct import pack
from typing import List
from ..util import *

class tpGxAssetHeader:
    def __init__(self, packFile):
        self.header = Header(packFile)

        packFile.seek(self.header.offsetUnknownAssets)
        self.unknownAssets: List[UnknownAsset] = []
        for i in range(self.header.numUnknownAssets):
            self.unknownAssets.append(UnknownAsset(packFile))

class Header:
    def __init__(self, packFile):
        self.numUnknownAssets = to_uint(packFile.read(4))
        offsetToUnknownAssets = to_uint(packFile.read(4))
        self.offsetUnknownAssets = packFile.tell() + offsetToUnknownAssets - 4

        self.numUnknownPaths = to_uint(packFile.read(4))
        offsetToUnknownPaths = to_uint(packFile.read(4))
        self.offsetUnknownPaths = packFile.tell() + offsetToUnknownPaths - 4

class UnknownAsset:
    def __init__(self, packFile):
        offsetToUnknownHash = to_uint(packFile.read(4))
        self.offsetUnknownHash = packFile.tell() + offsetToUnknownHash - 4
        packFile.seek(self.offsetUnknownHash)
        self.unknownHash = packFile.read(4)
        self.unknownFlag = to_uint(packFile.read(4))
        
        self.textures: List[Texture] = []

        if (self.unknownFlag == 0):
            return

        offsetToMasterMaterialPath = to_uint(packFile.read(4))
        self.offsetMasterMaterialPath = packFile.tell() + offsetToMasterMaterialPath - 4

        returnPos = packFile.tell()
        packFile.seek(self.offsetMasterMaterialPath)
        self.masterMaterialPath = to_string(packFile.read(1024))
        packFile.seek(returnPos)

        self.numMaterialParams = to_uint(packFile.read(4))
        offsetToMaterialParams = to_uint(packFile.read(4))
        self.offsetMaterialParams = packFile.tell() + offsetToMaterialParams - 4

        self.numTextures = to_uint(packFile.read(4))
        offsetToTextures = to_uint(packFile.read(4))
        self.offsetTextures = packFile.tell() + offsetToTextures - 4

        self.numTPVars = to_uint(packFile.read(4))
        offsetToTPVars = to_uint(packFile.read(4))
        self.offsetTPVars = packFile.tell() + offsetToTPVars - 4

        self.unknownUInt32_0 = to_uint(packFile.read(4))
        self.unknownUInt32_1 = to_uint(packFile.read(4))
        self.unknownShort = to_ushort(packFile.read(2))

        fileSize = packFile.seek(0, os.SEEK_END)
        packFile.seek(self.offsetMaterialParams)
        self.materialParamHeaders: List[MaterialParamsHeader] = []
        for i in range(self.numMaterialParams):
            paramHeader = MaterialParamsHeader(packFile)
            if paramHeader.offsetParameters > fileSize:
                print("[-] Material parameter offset exceeds file size!")
                print("[-] Stopping parsing of material parameters.")
                break
            self.materialParamHeaders.append(paramHeader)

        for materialParamHeader in self.materialParamHeaders:
            packFile.seek(materialParamHeader.offsetParameters)
            self.parameters: List[MaterialParameter] = []
            for i in range(materialParamHeader.numParameters):
                self.parameters.append(MaterialParameter(packFile))

        packFile.seek(self.offsetTextures)
        for i in range(self.numTextures):
            texture = Texture(packFile)
            if texture.offsetFileName > fileSize:
                print("[-] Texture filename offset exceeds file size!")
                print("[-] Stopping parsing of texture filenames.")
                break
            self.textures.append(texture)

        packFile.seek(self.offsetTPVars)
        self.tpVars: List[TPVar] = []
        for i in range(self.numTPVars):
            tpVar = TPVar(packFile)
            if tpVar.offsetName > fileSize:
                print("[-] TPVar name offset exceeds file size!")
                print("[-] Stopping parsing of TPVar names.")
                break
            self.tpVars.append(tpVar)


class MaterialParamsHeader:
    def __init__(self, packFile):
        self.unknownHash = packFile.read(4)

        offsetToUnknownString = to_uint(packFile.read(4))
        self.offsetUnknownString = packFile.tell() + offsetToUnknownString - 4

        returnPos = packFile.tell()
        packFile.seek(self.offsetUnknownString)
        self.unknownString = to_string(packFile.read(1024))
        packFile.seek(returnPos)

        self.unknownUInt32 = to_uint(packFile.read(4))

        self.numParameters = to_uint(packFile.read(4))

        offsetToParameters = to_uint(packFile.read(4))
        self.offsetParameters = packFile.tell() + offsetToParameters - 4

class MaterialParameter:
    def __init__(self, packFile):
        self.unknownHash = packFile.read(4)

        offsetToName = to_uint(packFile.read(4))
        self.offsetName = packFile.tell() + offsetToName - 4

        returnPos = packFile.tell()
        packFile.seek(self.offsetName)
        self.name = to_string(packFile.read(1024))
        packFile.seek(returnPos)

        self.unknownFlag = packFile.read(4)

        self.unknownUInt32_0 = to_uint(packFile.read(4))
        self.unknownUInt32_1 = to_uint(packFile.read(4))
        self.unknownUInt32_2 = to_uint(packFile.read(4))
        self.unknownUInt32_3 = to_uint(packFile.read(4))
        self.unknownUInt32_4 = to_uint(packFile.read(4))

        self.unknownByte = packFile.read(1)

        alignRelative(packFile, 0, 4)

class Texture:
    def __init__(self, packFile):
        self.unknownHash = packFile.read(4)

        offsetToMapType = to_uint(packFile.read(4))
        self.offsetMapType = packFile.tell() + offsetToMapType - 4

        returnPos = packFile.tell()
        packFile.seek(self.offsetMapType)
        self.mapType = to_string(packFile.read(1024))
        packFile.seek(returnPos)

        self.unknownHash2 = packFile.read(4)

        offsetToFilename = to_uint(packFile.read(4))
        self.offsetFileName = packFile.tell() + offsetToFilename - 4

        returnPos = packFile.tell()
        packFile.seek(self.offsetFileName)
        self.filename = to_string(packFile.read(1024))
        packFile.seek(returnPos)

        self.unknownByte = packFile.read(1)
        alignRelative(packFile, 0, 4)

class TPVar:
    def __init__(self, packFile):
        self.unknownHash = packFile.read(4)

        offsetToName = to_uint(packFile.read(4))
        self.offsetName = packFile.tell() + offsetToName - 4

        returnPos = packFile.tell()
        packFile.seek(self.offsetName)
        self.name = to_string(packFile.read(1024))
        packFile.seek(returnPos)

        self.unknownUInt32_0 = to_uint(packFile.read(4))
        self.unknownUInt32_1 = to_uint(packFile.read(4))
        self.unknownUInt32_2 = to_uint(packFile.read(4))