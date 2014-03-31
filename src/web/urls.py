# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
import settings
import topfuns.urls
import topfuns.views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/topfuns/download_report', topfuns.views.admin_download_report),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(topfuns.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (
         r'^media/(?P<path>.*)$',
          'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}
        ),
    )
