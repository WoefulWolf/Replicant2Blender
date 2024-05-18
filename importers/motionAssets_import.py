import bpy, math

def get_cmfFiles(pack):
    cmfFiles = []
    for assetFile in pack.assetFiles:
        for file in assetFile.content.files:
            if (file.magic in [b"CMF\x01", b"CMF\x03"]):
                cmfFiles.append(file)
    return cmfFiles

def import_motions(pack):
    cmfFiles = get_cmfFiles(pack)

    # Get active armature object
    armature = bpy.context.active_object
    if armature.type != 'ARMATURE':
        raise Exception("Active object is not an armature")

    for cmf in cmfFiles:
        # Print CMF name
        print(" -", cmf.name)

        # Check if the action already exists, then remove it
        if cmf.name in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[cmf.name])

        # Create new action
        action = bpy.data.actions.new(cmf.name)

        # Check if object has animation_data, if not, add it
        if not armature.animation_data:
            armature.animation_data_create()

        # Assign action to armature
        armature.animation_data.action = action

        # Compare cmf bone count with armature bone count
        cmf_boneCount = cmf.boneCount
        armature_boneCount = len(armature.data.bones)
        
        # For each bone transformation frames
        for i, transData in enumerate(cmf.framesTransData1.transformations):
            if transData == None:
                continue
            
            # Get pose bone
            poseBone = armature.pose.bones[i]
            # Clear any rotation on the bone
            poseBone.rotation_euler = (0, 0, 0)
            # Clear any location on the bone
            poseBone.location = (0, 0, 0)
            # Clear any scale on the bone
            poseBone.scale = (1, 1, 1)
            # Set rotation mode to euler
            poseBone.rotation_mode = 'QUATERNION'

            for frame_index, value in zip(transData.indices, transData.values):
                rot_value = [value[3], value[0], value[1], value[2]]
                poseBone.rotation_quaternion = rot_value
                # Insert keyframe
                poseBone.keyframe_insert(data_path="rotation_quaternion", frame=frame_index)