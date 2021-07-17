from ..util import *
        
class tpGxTexData:
    def __init__(self, packFile, texHead):
        texDataStartOffset = packFile.tell()
        self.data = packFile.read(texHead.header.filesize)
