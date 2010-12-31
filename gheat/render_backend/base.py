import datetime
import os
import stat

from django.core.exceptions import ImproperlyConfigured
from django.contrib.gis.geos import Polygon

import gheat
import gheat.opacity
from gheat import default_settings as gheat_settings
from gheat import gmerc
from gheat import BUILD_EMPTIES, SIZE, log


class ColorScheme(object):
    """
    Base class for color scheme representations.
    """

    def __init__(self, schemename, definition_png):
        """
        Takes the name and filesystem path of the defining PNG.
        """
        self.definition_png = definition_png

    def get_empty(self, opacity):
        """
        Returns file-like object, representing the PNG image file for the
        'empty tile' for this color scheme.
        """
        raise NotImplementedError
    
    #def build_empties(self):
    #    """Build empty tiles for this color scheme.
    #    """
    #    empties_dir = self.empties_dir
    #
    #    if not BUILD_EMPTIES:
    #        log.info("not building empty tiles for %s " % self)
    #    else:    
    #        if not os.path.isdir(empties_dir):
    #            os.makedirs(empties_dir, DIRMODE)
    #        if not os.access(empties_dir, os.R_OK|os.W_OK|os.X_OK):
    #            raise ImproperlyConfigured( "Permissions too restrictive on "
    #                                    + "empties directory "
    #                                    + "(%s)." % empties_dir
    #                                     )
    #        for fname in os.listdir(empties_dir):
    #            if fname.endswith('.png'):
    #                os.remove(os.path.join(empties_dir, fname))
    #        for zoom, opacity in gheat.opacity.zoom_to_opacity.items():
    #            empty_png = os.path.join(empties_dir, str(zoom)+'.png')
    #            self.hook_build_empty(opacity, empty_png)
    #        
    #        log.info("building empty tiles in %s" % empties_dir)

class Dot(object):
    """
    Base class for a dot representation for a given zoomlevel.
    """

    def __init__(self, zoom):
        name = 'dot%d.png' % zoom
        self.definition_png = os.path.join(gheat_settings.GHEAT_CONF_DIR, 'dots', name)

class Tile(object):
    """
    Base class for tile representations.
    """
    img = None

    def __init__(self, queryset, color_scheme, dots, zoom, x, y, point_field='geometry', last_modified_field=None, density_field=None):
        """
        x and y are tile coords per Google Maps.
        """
        
        # Calculate some things.
        # ======================
        
        dot = dots[zoom]
        
        # Translate tile to pixel coords.
        # -------------------------------

        x1 = x * SIZE
        x2 = x1 + 255
        y1 = y * SIZE
        y2 = y1 + 255
    
    
        # Expand bounds by one-half dot width.
        # ------------------------------------
    
        x1 = x1 - dot.half_size
        x2 = x2 + dot.half_size
        y1 = y1 - dot.half_size
        y2 = y2 + dot.half_size
        expanded_size = (x2-x1, y2-y1)
    
    
        # Translate new pixel bounds to lat/lng.
        # --------------------------------------
    
        n, w = gmerc.px2ll(x1, y1, zoom)
        s, e = gmerc.px2ll(x2, y2, zoom)


        # Save
        # ====

        self.dot = dot.img
        self.pad = dot.half_size

        self.x = x
        self.y = y

        self.x1 = x1
        self.y1 = y1

        self.x2 = x2
        self.y2 = y2

        self.expanded_size = expanded_size
        self.bbox = Polygon.from_bbox((w,s,e,n))
        self.zoom = zoom
        self.opacity = gheat.opacity.zoom_to_opacity[zoom]
        self.color_scheme = color_scheme
        self.queryset = queryset
        self.point_field = point_field
        self.last_modified_field = last_modified_field
        self.density_field = density_field
        
        _color_schemes_dir = os.path.join(gheat_settings.GHEAT_CONF_DIR, 'color-schemes')
        self.schemeobj = ColorScheme(
            self.color_scheme,
            os.path.join(_color_schemes_dir, "%s.png" % self.color_scheme)
        )
        
    def get_empty(self, opacity=gheat.opacity.OPAQUE):
        return self.schemeobj.get_empty(opacity)

    def features_inside(self):
        return self.queryset.filter(**{self.point_field + "__intersects": self.bbox})

    def is_empty(self):
        """With attributes set on self, return a boolean.

        Calc lat/lng bounds of this tile (include half-dot-width of padding)
        SELECT count(uid) FROM points
        """
        return not bool(self.features_inside()[:1])


    def is_stale(self):
        """With attributes set on self, return a boolean.

        Calc lat/lng bounds of this tile (include half-dot-width of padding)
        SELECT count(uid) FROM points WHERE modtime < modtime_tile
        """
        return True
        #if not self.last_modified_field or not os.path.isfile(self.fspath):
        #    return True
        #
        #timestamp = os.stat(self.fspath)[stat.ST_MTIME]
        #modtime = datetime.datetime.fromtimestamp(timestamp)
        #
        #return bool(self.features_inside().filter(**{self.last_modified_field + "__gt":modtime})[:1])

    def points(self):
        fields = [self.point_field]
        if self.density_field:
            fields.append(self.density_field)
        _points = self.features_inside().values(*fields)
        
        result = []
        for feature_dict in _points:
            point = feature_dict[self.point_field]
            x, y = gmerc.ll2px(point.y, point.x, self.zoom)
            x = x - self.x1 # account for tile offset relative to
            y = y - self.y1 #  overall map
            point_density = feature_dict.get(self.density_field, 1)
            for i in range(point_density):
                result.append((x-self.pad,y-self.pad))
        return result

    def generate(self):
        """Rebuild the image at self.img. Real work delegated to subclasses.
        """
        raise NotImplementedError
