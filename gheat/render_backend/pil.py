import os
from tempfile import SpooledTemporaryFile

from PIL import Image, ImageChops
from gheat import SIZE
from gheat import default_settings as gheat_settings
from gheat.opacity import OPAQUE
from gheat.render_backend import base

class ColorScheme(base.ColorScheme):
    def __init__(self, schemename, definition_png):
        super(ColorScheme,self).__init__(schemename, definition_png)
        
        self.colors = Image.open(definition_png).load()

    def get_empty(self, opacity=OPAQUE):
        color = self.colors[0, 255]
        if (type(color) is not int) and (len(color) == 4): # color map has per-pixel alpha
            (conf, pixel) = opacity, color[3] 
            opacity = int(( (conf/255.0)    # from configuration
                          * (pixel/255.0)   # from per-pixel alpha
                           ) * 255)

        if (type(color) is not int):
            color = color[:3] + (opacity,)
        
        tile = Image.new('RGBA', (SIZE, SIZE), color)
        
        tmpfile = SpooledTemporaryFile()
        tile.save(tmpfile, 'PNG')
        tmpfile.seek(0)
        
        return tmpfile

class Dot(base.Dot):
    def __init__(self, zoom):
        super(Dot, self).__init__(zoom)
        self.img = Image.open(self.definition_png)
        self.half_size = (self.img.size[0] / 2)

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
        
        # Grab a new PIL image canvas
        img = Image.new('RGBA', self.expanded_size, 'white')
        
        # Render the B&W density version of the heatmap
        for x,y in points:
            dot_placed = Image.new('RGBA', self.expanded_size, 'white')
            dot_placed.paste(self.dot, (x, y))
            img = ImageChops.multiply(img, dot_placed)

        # Crop resulting density image (which could have grown) into the
        # actual canvas size we want
        img = img.crop((self.pad, self.pad, SIZE+self.pad, SIZE+self.pad))
        img = ImageChops.duplicate(img) # converts ImageCrop => Image

        # Given the B&W density image, generate a color heatmap based on
        # this Tile's color scheme.
        _computed_opacities = dict()
        pix = img.load() # Image => PixelAccess
        for x in range(SIZE):
            for y in range(SIZE):

                # Get color for this intensity
                # ============================
                # is a value 
                val = self.schemeobj.colors[0, pix[x,y][0]]
                try:
                    pix_alpha = val[3] # the color image has transparency
                except IndexError:
                    pix_alpha = OPAQUE # it doesn't
                

                # Blend the opacities
                # ===================

                conf, pixel = self.opacity, pix_alpha
                if (conf, pixel) not in _computed_opacities:
                    opacity = int(( (conf/255.0)    # from configuration
                                  * (pixel/255.0)   # from per-pixel alpha
                                   ) * 255)
                    _computed_opacities[(conf, pixel)] = opacity
                
                pix[x,y] = val[:3] + (_computed_opacities[(conf, pixel)],)
        
        tmpfile = SpooledTemporaryFile()
        img.save(tmpfile, 'PNG')
        tmpfile.seek(0)
        
        return tmpfile
