import os
from tempfile import SpooledTemporaryFile
from django.core.cache import cache

from gheat.storage_backend.base import BaseStorage

class DjangoCacheStorage(BaseStorage):
    """
    Storage backend that stores binary image data in the cache backend defined in
    your Django project's settings.CACHE_BACKEND
    """
    def __init__(self, cache_time=None):
        self.cache_time = cache_time
    
    def key_for_tile(self, tile, mapname=""):
        key = os.path.join("gheat", mapname, tile.color_scheme, "%s-%s-%s" % (tile.zoom, tile.x, tile.y))
        return key
    
    def has_tile(self, tile, mapname=""):
        b = cache.has_key(self.key_for_tile(tile,mapname))
        return b
    
    def get_tile(self, tile, mapname=""):
        if not self.has_tile(tile,mapname):
            # Generate our empty tile
            fileobj = tile.generate()
            
            # Set it in cache
            cachekey = self.key_for_tile(tile,mapname)
            cache.set(cachekey, fileobj.read(), self.cache_time)
            
            # Rewind our in-memory image pseudofile and return it
            fileobj.seek(0)
            return fileobj
        else:
            # Get data from cache
            tile_data = self.get_tile_bytes(tile, mapname)
            
            # Return it as a file-like object
            tmpfile = SpooledTemporaryFile()
            tmpfile.write(tile_data)
            tmpfile.seek(0)
            return tmpfile

    def get_tile_bytes(self, tile, mapname=""):
        cachekey = self.key_for_tile(tile,mapname)
        if not self.has_tile(tile,mapname):
            # Generate our empty tile
            fileobj = tile.generate()
            
            # Set it in cache
            cache.set(cachekey, fileobj.read(), self.cache_time)
            
            # Rewind our in-memory image pseudofile and return the data
            fileobj.seek(0)
            return fileobj.read()
        else:
            # Get data from cache
            tile_data = cache.get(cachekey)
            return tile_data
            
    def get_emptytile(self, tile):
        tile_key = os.path.join("gheat", "empty_tiles", tile.color_scheme, "%s-%s-%s" % (tile.zoom, tile.x, tile.y))
        if not cache.has_key(tile_key):
            # Generate our empty tile
            fileobj = tile.get_empty()
            
            # Set it in cache
            cache.set(tile_key, fileobj.read(), self.cache_time)
            
            # Rewind our in-memory image pseudofile and return it
            fileobj.seek(0)
            return fileobj
        else:
            # Get data from cache
            tile_data = self.get_emptytile_bytes(tile, mapname)
            
            # Return it as a file-like object
            tmpfile = SpooledTemporaryFile()
            tmpfile.write(tile_data)
            tmpfile.seek(0)
            return tmpfile

    def get_emptytile_bytes(self, tile):
        tile_key = os.path.join("gheat", "empty_tiles", tile.color_scheme, "%s-%s-%s" % (tile.zoom, tile.x, tile.y))
        if not cache.has_key(tile_key):
            # Generate our empty tile
            fileobj = tile.get_empty()
            
            # Set it in cache
            cache.set(tile_key, fileobj.read(), self.cache_time)
            
            # Rewind our in-memory image pseudofile and return it
            fileobj.seek(0)
            return fileobj
        else:
            # Cache file exists, so return a file pointer to that
            tile_data = cache.get(tile_key)
            return tile_data
