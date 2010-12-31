import os
from tempfile import NamedTemporaryFile

import numpy
import pygame
from gheat import SIZE
from gheat.render_backend import base

WHITE = (255, 255, 255)

# Needed for colors
# =================
# 
#   http://www.pygame.org/wiki/HeadlessNoWindowsNeeded 
# 
# Beyond what is said there, also set the color depth to 32 bits.

os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.display.init()
pygame.display.set_mode((1,1), 0, 32)

class ColorScheme(base.ColorScheme):
    def __init__(self, schemename, definition_png):
        super(ColorScheme,self).__init__(schemename, definition_png)
        
        self.colors = pygame.image.load(definition_png)
        self.color_map = pygame.surfarray.pixels3d(self.colors)[0] 
        self.alpha_map = pygame.surfarray.pixels_alpha(self.colors)[0]

    def get_empty(self, opacity=OPAQUE):
        tile = pygame.Surface((SIZE,SIZE), pygame.SRCALPHA, 32)
        tile.fill(self.color_map[255])
        tile.convert_alpha()

        (conf, pixel) = opacity, self.alpha_map[255]
        opacity = int(( (conf/255.0)    # from configuration
                      * (pixel/255.0)   # from per-pixel alpha
                       ) * 255)

        pygame.surfarray.pixels_alpha(tile)[:,:] = opacity 
        
        # Save and return image
        tmpfile = NamedTemporaryFile(suffix=".png",delete=False)
        tmpfile.close()
        pygame.image.save(tile, tmpfile.name)
        
        return open(tmpfile.name, "rb")

class Dot(base.Dot):
    def __init__(self, zoom):
        super(Dot, self).__init__(zoom)
        self.img = pygame.image.load(self.definition_png)
        half_size = self.img.get_size()[0] / 2

class Tile(base.Tile):
    def __init__(self, queryset, color_scheme, dots, zoom, x, y, point_field='geometry', last_modified_field=None, density_field=None):
        super(Tile, self).__init__(queryset, color_scheme, dots, zoom, x, y, point_field, last_modified_field, density_field)
        
        _color_schemes_dir = os.path.join(gheat_settings.GHEAT_CONF_DIR, 'color-schemes')
        self.schemeobj = ColorScheme(
            self.color_scheme,
            os.path.join(_color_schemes_dir, "%s.png" % self.color_scheme)
        )


    def generate(self):
        points = self.points()
        
        # set up a canvas
        tile = pygame.Surface(self.expanded_size, 0, 32)
        tile.fill(WHITE)
        
        # Add B&W density points
        for point in points:
            tile.blit(self.dot, point, None, pygame.BLEND_MULT)
        
        # Crop down to proper size
        tile = tile.subsurface(self.pad, self.pad, SIZE, SIZE).copy()
        
        # Invert/colorize
        # ===============
        # The way this works is that we loop through all pixels in the image,
        # and set their color and their transparency based on an index image.
        # The index image can be as wide as we want; we only look at the first
        # column of pixels. This first column is considered a mapping of 256
        # gray-scale intensity values to color/alpha.

        # Optimized: I had the alpha computation in a separate function because 
        # I'm also using it above in ColorScheme (cause I couldn't get set_alpha
        # working). The inner loop runs 65536 times, and just moving the 
        # computation out of a function and inline into the loop sped things up 
        # about 50%. It sped it up another 50% to cache the values, since each
        # of the 65536 variables only ever takes one of 256 values. Not super
        # fast still, but more reasonable (1.5 seconds instead of 12).
        #
        # I would expect that precomputing the dictionary at start-up time 
        # should give us another boost, but it slowed us down again. Maybe 
        # since with precomputation we have to calculate more than we use, the 
        # size of the dictionary made a difference? Worth exploring ...

        _computed_opacities = dict()

        tile = tile.convert_alpha(self.color_scheme.colors)
        tile.lock()
        pix = pygame.surfarray.pixels3d(tile)
        alp = pygame.surfarray.pixels_alpha(tile)
        for x in range(SIZE):
            for y in range(SIZE):
                key = pix[x,y,0]

                conf, pixel = self.opacity, self.color_scheme.alpha_map[key]
                if (conf, pixel) not in _computed_opacities:
                    opacity = int(( (conf/255.0)    # from configuration
                                  * (pixel/255.0)   # from per-pixel alpha
                                   ) * 255)
                    _computed_opacities[(conf, pixel)] = opacity

                pix[x,y] = self.color_scheme.color_map[key]
                alp[x,y] = _computed_opacities[(conf, pixel)]

        tile.unlock()

        # Save image
        tmpfile = NamedTemporaryFile(suffix=".png",delete=False)
        tmpfile.close()
        pygame.image.save(tile, tmpfile.name)
        
        return open(tmpfile.name, "rb")
