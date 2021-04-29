from .classes.pack import *
from mathutils import Vector, Matrix
import bpy, bmesh

def get_meshAssetFiles(pack):
    meshAssetFiles = []
    for assetFile in pack.assetFiles:
        if (assetFile.content and assetFile.content.fileTypeName == "tpGxMeshHead"):
            meshAssetFiles.append(assetFile)
    return meshAssetFiles
   
def construct_meshes(pack):
    meshAssetFiles = get_meshAssetFiles(pack)

    for i, meshAsset in enumerate(meshAssetFiles):
        meshCollection = bpy.data.collections.new(meshAsset.name)
        bpy.context.scene.collection.children.link(meshCollection)

        for k, obj in enumerate(meshAsset.content.meshHead.objectGroups):
            vertices = pack.meshData[i].objectGroupVertices[k].vertexCoords
            faces = pack.meshData[i].objectGroupIndices[k].indices

            """
            normals = []
            for m in range(len(vertices)):
                nx = pack.meshData[i].objectGroupVertices[k].vertexNormals[m][0] / 255
                ny = pack.meshData[i].objectGroupVertices[k].vertexNormals[m][1] / 255
                nz = pack.meshData[i].objectGroupVertices[k].vertexNormals[m][2] / 255
                normals.append([nz, ny, nx])
            """

            objName = meshAsset.name + str(k)

            bObjMesh = bpy.data.meshes.new(objName)
            bObj = bpy.data.objects.new(objName, bObjMesh)

            #bObj.data.use_auto_smooth = True

            meshCollection.objects.link(bObj)
            bObjMesh.from_pydata(vertices, [], faces)
            #bObjMesh.normals_split_custom_set_from_vertices(normals)
            bObjMesh.update(calc_edges=True)

            for poly in bObj.data.polygons:
                poly.use_smooth = True

            # Create/Add Materials
            for m, material in enumerate(meshAsset.content.meshHead.materials):
                newMaterial = bpy.data.materials.get(material.name)
                if newMaterial is None:
                    newMaterial = bpy.data.materials.new(name=material.name)
                bObj.data.materials.append(newMaterial)
                
            # Assign UVs
            bpy.context.view_layer.objects.active = bObj
            bpy.ops.object.mode_set(mode="EDIT")
            bm = bmesh.from_edit_mesh(bObj.data)
            uv_layer = bm.loops.layers.uv.verify()
            for face in bm.faces:
                face.material_index = 0
                for l in face.loops:
                    luv = l[uv_layer]
                    ind = l.vert.index
                    luv.uv = Vector(pack.meshData[i].objectGroupVertices[k].vertexUVs[ind])

            # Assign Materials To Faces
            bm.verts.ensure_lookup_table()
            for matObjects in meshAsset.content.meshHead.objects:
                matFaces = faces[matObjects.indicesStart//3:matObjects.indicesStart//3 + matObjects.indicesCount//3]
                for matFace in matFaces:
                    bm.faces.get([bm.verts[matFace[0]], bm.verts[matFace[1]], bm.verts[matFace[2]]]).material_index = matObjects.materialIndex

            bpy.ops.object.mode_set(mode='OBJECT')
            bObj.rotation_euler = (math.radians(90),0,0)

def main(packFilePath):
    packFile = open(packFilePath, "rb")

    pack = Pack(packFile)

    construct_meshes(pack)

    packFile.close()
    return {"FINISHED"}