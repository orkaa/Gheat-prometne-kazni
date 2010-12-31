from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.simple.redirect_to', {'url' : '/kazni/'}),
    (r'^kazni/', include('gheat_kazni.kazni.urls')),
)
