# Let the developer to override generic values for the gheat settings 
# Normally set on a localsettings.py file or the same settings.py of your
# home project
from django.conf import settings
from os.path import dirname, abspath, join

# ===== Some constants =====
STORAGES = range(0,0+3)
STORAGE_DUMMY, STORAGE_FILESYSTEM, STORAGE_DJANGO_CACHE = STORAGES

RENDERERS = range(100,100+2)
RENDERER_PIL, RENDERER_PYGAME = RENDERERS

# ===== Storage backends =====
GHEAT_STORAGE_BACKEND = getattr(settings, 'GHEAT_STORAGE_BACKEND', STORAGE_DJANGO_CACHE)

# Filesystem-specific:
GHEAT_FILESYSTEM_STORAGE_DIR = getattr(settings, 'GHEAT_FILESYSTEM_STORAGE_DIR', None)

# ===== Image rendering backends =====
GHEAT_RENDER_BACKEND = getattr(settings, 'GHEAT_RENDER_BACKEND','PIL')

# ===== General settings =====
GHEAT_ZOOM_OPAQUE=getattr(settings, 'GHEAT_ZOOM_OPAQUE', -1)
GHEAT_ZOOM_TRANSPARENT=getattr(settings, 'GHEAT_ZOOM_TRANSPARENT', 17)
GHEAT_FULL_OPAQUE=getattr(settings, 'GHEAT_FULL_OPAQUE', True)
GHEAT_BUILD_EMPTIES=getattr(settings, 'GHEAT_BUILD_EMPTIES', True)
GHEAT_ALWAYS_BUILD=getattr(settings, 'GHEAT_ALWAYS_BUILD', True)

# ===== Internals =====
GHEAT_CONF_DIR = getattr(settings, 'GHEAT_CONF_DIR', join(dirname(abspath(__file__)), 'etc'))
DEBUG = settings.DEBUG

# Use settings-defined loglevel, if available. Otherwise, default to 'DEBUG' or 'ERROR'-only for non-debug
GHEAT_LOG_LEVEL = getattr(settings, 'GHEAT_LOG_LEVEL', None)
if not GHEAT_LOG_LEVEL and DEBUG:
    GHEAT_LOG_LEVEL = 'DEBUG'
else:
    GHEAT_LOG_LEVEL = 'ERROR'
