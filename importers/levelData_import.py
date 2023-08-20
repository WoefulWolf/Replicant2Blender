import bpy

from ..classes.levelData import LDMeshEntry, LDUnknEntry10, LDUnknEntry18, LevelData


def importLevelData(levelDataList: list[LevelData]):
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
                    importLdMeshEntry(ldObject.meshEntry, rootCollection)
                elif ldObject.unknEntry10 is not None:
                    importLdUnknEntry10(ldObject.unknEntry10, rootCollection)
                elif ldObject.unknEntry18 is not None:
                    importLdUnknEntry18(ldObject.unknEntry18, rootCollection)

    print("Done importing LevelData!")

def importLdMeshEntry(meshEntry: LDMeshEntry, collection: bpy.types.Collection):
    makeObj(
        meshEntry.pos,
        meshEntry.rot,
        meshEntry.scale,
        meshEntry.meshPath.split("/")[-1],
        collection,
    )

def importLdUnknEntry10(unknEntry10: LDUnknEntry10, collection: bpy.types.Collection):
    makeObj(
        unknEntry10.pos,
        unknEntry10.rot,
        unknEntry10.scale,
        "UnknEntry10",
        collection,
    )

def importLdUnknEntry18(unknEntry18: LDUnknEntry18, collection: bpy.types.Collection):
    makeObj(
        unknEntry18.pos,
        unknEntry18.rot,
        unknEntry18.scale,
        unknEntry18.unknPath.split("/")[-1],
        collection,
    )

def transformCoords(coords: tuple[float, float, float], invertY = -1):
    return (coords[0], invertY * coords[2], coords[1])

def makeObj(
    pos: tuple[float, float, float],
    rot: tuple[float, float, float, float],
    scale: float,
    name: str,
    collection: bpy.types.Collection,
):
    obj = bpy.data.objects.new(name, None)
    obj.location = transformCoords(pos)
    obj.rotation_euler = transformCoords(rot[:3])
    obj.scale = (scale, scale, scale)
    collection.objects.link(obj)
    return obj
