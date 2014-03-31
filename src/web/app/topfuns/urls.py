from django.conf.urls.defaults import *

urlpatterns = patterns('topfuns.views',
    (r'^$',  'top'),
    (r'^top/$', 'top'),
    
    (r'^actions/((?P<uid>\d+)/)?$', 'actions'),
    (r'^prizes/$', 'prizes'),    
    (r'^rules/$', 'rules'),
    
)
