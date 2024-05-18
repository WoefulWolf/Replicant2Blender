import bpy, os
from .classes.pack import *
from .importers.motionAssets_import import import_motions

def main(packFilePath, addonName):
    pack_directory = os.path.dirname(os.path.abspath(packFilePath))

    # motionPack
    packFile = open(packFilePath, "rb")
    print("Parsing Motion PACK file...", packFilePath)
    meshPack = Pack(packFile)
    print("Importing CMF Motions...")
    import_motions(meshPack)
    packFile.close()