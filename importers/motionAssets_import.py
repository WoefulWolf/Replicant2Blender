def get_cmfFiles(pack):
    cmfFiles = []
    for assetFile in pack.assetFiles:
        for file in assetFile.content.files:
            if (file.magic == b"CMF\x01"):
                cmfFiles.append(file)
    return cmfFiles

def import_motions(pack):
    cmfFiles = get_cmfFiles(pack)

    for file in cmfFiles:
        print(" -", file.name)