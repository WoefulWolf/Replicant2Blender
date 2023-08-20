from typing import BinaryIO
import os

from ..util import readFloatX4, readString, to_float, to_string, to_uint, readFloatX3

def skip(file: BinaryIO, count: int):
    file.seek(count, os.SEEK_CUR)

def skipPadding(file: BinaryIO, alignment: int):
    padding = alignment - (file.tell() % alignment)
    if (padding != alignment):
        file.seek(padding, os.SEEK_CUR)

def seekToRelOffset(file: BinaryIO, ownOffset: int = -4):
    offset = to_uint(file.read(4))
    file.seek(offset + ownOffset, 1)

def readStringFromOffset(file: BinaryIO, ownOffset: int = -4):
    offset = to_uint(file.read(4))
    returnPos = file.tell()
    file.seek(offset + ownOffset, 1)
    string = readString(file)
    file.seek(returnPos)
    return string

class LDMeshEntry:
    def __init__(self, packFile: BinaryIO):
        self.pos = readFloatX3(packFile)
        self.rot = readFloatX4(packFile)
        self.scale = to_float(packFile.read(4))
        self.unkn0 = to_uint(packFile.read(4))
        self.unkn1 = to_uint(packFile.read(4))
        self.unkn2 = to_float(packFile.read(4))
        self.unkn3 = readFloatX3(packFile)
        self.unkn4 = readFloatX3(packFile)
        self.unkn5 = to_float(packFile.read(4))
        self.unkn6 = to_float(packFile.read(4))
        self.unkn7 = to_float(packFile.read(4))
        self.unkn8 = to_float(packFile.read(4))
        self.unkn9 = to_float(packFile.read(4))
        self.null0 = to_uint(packFile.read(2))
        self.unkn10 = to_uint(packFile.read(1))
        self.unkn11 = to_uint(packFile.read(1))
        self.unkn12 = to_uint(packFile.read(4))
        self.null1 = to_uint(packFile.read(1))
        skipPadding(packFile, 4)
        skip(packFile, 8)
        skipPadding(packFile, 8)
        self.meshPath = readString(packFile)

class LDUnknEntry10:
    def __init__(self, packFile: BinaryIO):
        self.pos = readFloatX3(packFile)
        self.rot = readFloatX4(packFile)
        self.scale = to_float(packFile.read(4))
        ...

class LDUnknEntry18:
    def __init__(self, packFile: BinaryIO):
        self.pos = readFloatX3(packFile)
        self.rot = readFloatX4(packFile)
        self.scale = to_float(packFile.read(4))
        self.unkn0 = to_uint(packFile.read(4))
        self.unknPath = readStringFromOffset(packFile)
        ...

class LDObject:
    meshEntry: LDMeshEntry|None
    unknEntry18: LDUnknEntry18|None
    unknEntry10: LDUnknEntry10|None

    def __init__(self, packFile: BinaryIO):
        returnPos = packFile.tell() + 4
        seekToRelOffset(packFile)

        objType = to_uint(packFile.read(4))
        unkn0 = to_uint(packFile.read(4))

        self.meshEntry = None
        self.unknEntry10 = None
        self.unknEntry18 = None
        if (objType == 8):
            self.meshEntry = LDMeshEntry(packFile)
        elif (objType == 10):
            self.unknEntry10 = LDUnknEntry10(packFile)
        elif (objType == 18):
            self.unknEntry18 = LDUnknEntry18(packFile)
        # else:
        #     raise Exception(f"Unknown object type {objType} at {returnPos}")

        packFile.seek(returnPos)

class LDEntry:
    objects: list[LDObject]

    def __init__(self, packFile: BinaryIO):
        skip(packFile, 4)

        # entryCount = to_uint(packFile.read(4))
        skip(packFile, 4)

        seekToRelOffset(packFile)
        skip(packFile, 4)

        entryCount = to_uint(packFile.read(4))

        seekToRelOffset(packFile)
        self.objects = []
        for i in range(entryCount):
            self.objects.append(LDObject(packFile))


class LevelData:
    entries: list[LDEntry]

    def __init__(self, packFile: BinaryIO):
        # header = packFile.read(18)
        # if to_string(header) != "LevelData":
        #     raise Exception("LevelData header not found")
        # skipPadding(packFile, 8)

        entryCount = to_uint(packFile.read(4))

        seekToRelOffset(packFile)
        self.entries = []
        for i in range(entryCount):
            self.entries.append(LDEntry(packFile))

