from math import sqrt, radians
import os
from typing import List, Optional, Tuple
import bpy
from mathutils import Euler, Quaternion

from ..classes.levelData import LDMeshEntry, LDUnknEntry10, LDUnknEntry18, LevelData


def importLevelData(levelDataList: List[LevelData], addonName: str):
    if len(levelDataList) > 0:
        print("Importing LevelData...")
    else:
        return
    
    rootCollectionName = "LevelData"
    if rootCollectionName not in bpy.data.collections:
        bpy.data.collections.new(rootCollectionName)
        bpy.context.scene.collection.children.link(bpy.data.collections[rootCollectionName])
    rootCollection = bpy.data.collections[rootCollectionName]

    for levelData in levelDataList:
        for ldEntry in levelData.entries:
            for ldObject in ldEntry.objects:
                if ldObject.meshEntry is not None:
                    importLdMeshEntry(ldObject.meshEntry, rootCollection, addonName)
                elif ldObject.unknEntry10 is not None:
                    importLdUnknEntry10(ldObject.unknEntry10, rootCollection, addonName)
                elif ldObject.unknEntry18 is not None:
                    importLdUnknEntry18(ldObject.unknEntry18, rootCollection, addonName)

    print("Done importing LevelData!")

def importLdMeshEntry(meshEntry: LDMeshEntry, collection: bpy.types.Collection, addonName: str):
    makeObj(
        meshEntry.pos,
        meshEntry.rot,
        meshEntry.scale,
        meshEntry.meshPath.split("/")[-1],
        collection,
        addonName,
        assetPath=meshEntry.meshPath
    )

def importLdUnknEntry10(unknEntry10: LDUnknEntry10, collection: bpy.types.Collection, addonName: str):
    makeObj(
        unknEntry10.pos,
        unknEntry10.rot,
        unknEntry10.scale,
        "UnknEntry10",
        collection,
        addonName
    )

def importLdUnknEntry18(unknEntry18: LDUnknEntry18, collection: bpy.types.Collection, addonName: str):
    makeObj(
        unknEntry18.pos,
        unknEntry18.rot,
        unknEntry18.scale,
        unknEntry18.unknPath.split("/")[-1],
        collection,
        addonName
    )

def transformCoords(coords: Tuple[float, float, float], invertY = -1):
    return (coords[0], invertY * coords[2], coords[1])

def makeObj(
    pos: Tuple[float, float, float],
    rot: Tuple[float, float, float, float],
    scale: float,
    name: str,
    collection: bpy.types.Collection,
    addonName: str,
    assetPath: Optional[str] = None,
):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.location = transformCoords(pos)
    obj.rotation_euler = transformCoords(rot[:3])
    obj.scale = (scale, scale, scale)
    if assetPath is not None:
        assetColl = linkAssetModel(assetPath, addonName)
        if assetColl is not None:
            obj.instance_collection = assetColl
            obj.instance_type = "COLLECTION"
    return obj

def linkAssetModel(assetPath: str, addonName: str) -> Optional[bpy.types.Collection]:
    prefs = bpy.context.preferences.addons[addonName].preferences
    assetsRootDir = prefs.assets_path

    assetName = os.path.basename(assetPath)
    assetCollName = assetName

    # link file for first object
    if assetCollName not in bpy.data.collections:
        assetPathParts = assetPath.split("/") if "/" in assetPath else assetPath.split("\\")
        assetPathParts[-1] = assetName + ".blend"
        filePath = os.path.join(assetsRootDir, *assetPathParts)
        if not os.path.isfile(filePath):
            return None

        if assetName in bpy.data.libraries:
            bpy.data.libraries.remove(bpy.data.libraries[assetName])
        with bpy.data.libraries.load(filepath = filePath, link = True, relative = True) as (data_from, data_to):
            data_to.collections = [assetName]
        if assetName in bpy.data.objects and bpy.data.objects[assetName].instance_type == "COLLECTION":
            bpy.data.objects.remove(bpy.data.objects[assetName], do_unlink=True)
        linkedColl = bpy.data.collections[assetName]
        linkedColl.name = assetCollName

    return bpy.data.collections[assetCollName]
