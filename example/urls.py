from django.conf.urls import patterns, url, include

from .app.views import router

urlpatterns = patterns(
    '',
    url(r'api/', include(router.urls)),
)
