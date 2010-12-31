class BaseStorage(object):
    """
    Dummy storage class, which defines the API for storage backends. This is usable
    as-is, although tiles are never stored/cached.
    """
    def has_tile(self, tile, mapname=""):
        """
        Subclasses should actually implement this so that tiles are not generated on
        every call.
        """
        return False
        
    def get_tile(self, tile, mapname=""):
        """
        Returns the given tile as a file-like object representing PNG image data.
        """
        return tile.generate()
    
    def get_tile_bytes(self, tile, mapname=""):
        """
        Returns the given tile as raw binary PNG data.
        """
        return self.get_tile(tile, mapname).read()
    
    def get_emptytile(self, tile):
        """
        Returns the 'empty tile' a file-like object.
        """
        return tile.get_empty()
    
    def get_emptytile_bytes(self, tile):
        """
        Returns the 'empty tile' as raw PNG image data.
        """
        return self.get_emptytile(tile).read()
