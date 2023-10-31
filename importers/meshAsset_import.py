from mathutils import Vector, Matrix, Quaternion
import bpy, bmesh, numpy, math
from operator import add

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

        # Create Armature + Bones
        if meshAsset.content.meshHead.header.boneDataCount > 0:
            amtName = meshAsset.name + "_armature"
            amt = bpy.data.armatures.new(amtName)
            amtObj = bpy.data.objects.new(amtName, amt)
            meshCollection.objects.link(amtObj)
            bpy.context.view_layer.objects.active = amtObj
            bpy.ops.object.mode_set(mode="EDIT")
            for k, bone in enumerate(meshAsset.content.meshHead.bonesData):
                transform = Matrix(bone.unknownMatrix0)

                if (bone.unknownParentIndex == -1):
                    head = transform @ Vector((0, 0, 0, 1))
                    tail = transform @ Vector((bone.length, 0, 0, 1))
                else:
                    head = Vector((0, 0, 0))
                    tail = Vector((0, 0.05, 0))
                newBone = amt.edit_bones.new(bone.name)
                newBone.head = [head.x, head.y, head.z]
                newBone.tail = [tail.x, tail.y, tail.z]
                #newBone.roll = 90
                #newBone.parent = amt.edit_bones[meshAsset.content.meshHead.bones[bone.parentBoneIndex].name] if bone.parentBoneIndex != -1 else None
            
            safeBones = []
            for bone in meshAsset.content.meshHead.bonesData:
                safeBones.append(bone.name)
            for k, edit_bone in enumerate(amt.edit_bones):
                for bone in meshAsset.content.meshHead.bones:
                    if bone.name == edit_bone.name and bone.parentBoneIndex != -1:
                        parentIndex = bone.parentBoneIndex
                        parentName = meshAsset.content.meshHead.bones[bone.parentBoneIndex].name
                        if parentName in safeBones:
                            edit_bone.parent = amt.edit_bones[parentName]
                        break

            bpy.ops.object.mode_set(mode='POSE')
            for pose_bone in amtObj.pose.bones:
                for bone in meshAsset.content.meshHead.bonesData:
                    if bone.name == pose_bone.name:
                        if bone.unknownParentIndex != -1:
                            transformMat = Matrix(bone.unknownMatrix0)
                            pose_bone.matrix_basis = transformMat @ pose_bone.matrix_basis
                        break
            bpy.context.view_layer.update()
            bpy.ops.pose.armature_apply()
            
            bpy.ops.object.mode_set(mode='OBJECT')
            amtObj.rotation_euler = (math.radians(90),0,0)

        # Create objects
        for k, obj in enumerate(meshAsset.content.meshHead.objectGroups):
            vertices = pack.meshData[i].objectGroupVertices[k].vertexCoords
            faces = pack.meshData[i].objectGroupIndices[k].indices
            weights = pack.meshData[i].objectGroupVertices[k].vertexWeights
            boneIndices = pack.meshData[i].objectGroupVertices[k].vertexBoneIndices
            
            normals = []
            for m in range(len(vertices)):
                nx = pack.meshData[i].objectGroupVertices[k].vertexNormals[m][0] / 127
                ny = pack.meshData[i].objectGroupVertices[k].vertexNormals[m][1] / 127
                nz = pack.meshData[i].objectGroupVertices[k].vertexNormals[m][2] / 127
                normals.append([nx, ny, nz])
            

            objName = meshAsset.name + str(k)

            bObjMesh = bpy.data.meshes.new(objName)
            bObj = bpy.data.objects.new(objName, bObjMesh)

            bObj.data.use_auto_smooth = True

            meshCollection.objects.link(bObj)
            bObjMesh.from_pydata(vertices, [], faces)
            bObjMesh.normals_split_custom_set_from_vertices(normals)
            bObjMesh.update(calc_edges=True)

            #for poly in bObj.data.polygons:
            #    poly.use_smooth = True

            # Create/Add Materials
            for m, material in enumerate(meshAsset.content.meshHead.materials):
                newMaterial = bpy.data.materials.get(material.name.lower())
                if newMaterial is None:
                    newMaterial = bpy.data.materials.new(name=material.name.lower())
                bObj.data.materials.append(newMaterial)

            # Create vertex groups for bones
            for bone in meshAsset.content.meshHead.bonesData:
                bObj.vertex_groups.new(name=bone.name)

            # Assign weights
            for m, weight in enumerate(weights):
                vertexGroups = []
                vertexBoneIndices = boneIndices[m]
                if (len(weight) == 4):
                    vertexWeights = [weight[0], weight[1], weight[2], weight[3]]
                    vertexGroups = [bObj.vertex_groups[vertexBoneIndices[0]], bObj.vertex_groups[vertexBoneIndices[1]], bObj.vertex_groups[vertexBoneIndices[2]], bObj.vertex_groups[vertexBoneIndices[3]]]
                elif (len(weight) == 3):
                    vertexWeights = [weight[0], weight[1], weight[2]]
                    vertexGroups = [bObj.vertex_groups[vertexBoneIndices[0]], bObj.vertex_groups[vertexBoneIndices[1]], bObj.vertex_groups[vertexBoneIndices[2]]]

                for n, group in enumerate(vertexGroups):
                    if vertexWeights[n] > 0:
                        group.add([m], vertexWeights[n], "REPLACE")
                
            # Assign UVs
            bpy.context.view_layer.objects.active = bObj
            bpy.ops.object.mode_set(mode="EDIT")
            bm = bmesh.from_edit_mesh(bObj.data)
            uv_layers = [bm.loops.layers.uv.verify()]
            for m, uvMap in enumerate(pack.meshData[i].objectGroupVertices[k].vertexUVMaps):
                if m > 0 and len(pack.meshData[i].objectGroupVertices[k].vertexUVMaps[m]) > 0:
                    uv_layers.append(bm.loops.layers.uv.new("UVMap" + str(m)))

            for face in bm.faces:
                face.material_index = 0
                for l in face.loops:
                    for m, uv_layer in enumerate(uv_layers):
                        if len(pack.meshData[i].objectGroupVertices[k].vertexUVMaps[m]) > 0:
                            luv = l[uv_layer]
                            idx = l.vert.index
                            luv.uv = Vector(pack.meshData[i].objectGroupVertices[k].vertexUVMaps[m][idx])

            # Assign Materials To Faces
            bm.verts.ensure_lookup_table()
            for matObjects in meshAsset.content.meshHead.objects:
                if matObjects.objectGroupIndex != k:
                    continue
                matFaces = faces[matObjects.indicesStart//3:matObjects.indicesStart//3 + matObjects.indicesCount//3]
                for matFace in matFaces:
                    if (bm.verts[matFace[0]] != bm.verts[matFace[1]] and bm.verts[matFace[0]] != bm.verts[matFace[2]] and bm.verts[matFace[1]] != bm.verts[matFace[2]]):
                        face = bm.faces.get([bm.verts[matFace[0]], bm.verts[matFace[1]], bm.verts[matFace[2]]]).material_index = matObjects.materialIndex

            bpy.ops.object.mode_set(mode='OBJECT')
            bObj.rotation_euler = (math.radians(90),0,0)

            # Parent object to armature
            if meshAsset.content.meshHead.header.boneDataCount > 0:
                bpy.context.view_layer.objects.active = amtObj
                bObj.select_set(True)
                amtObj.select_set(True)
                bpy.ops.object.parent_set(type="ARMATURE")
                bObj.select_set(False)
                amtObj.select_set(False)