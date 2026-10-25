from django.urls import path
from . import views
urlpatterns=[path('',views.index), path('library/',views.index), path('api/health/',views.health), path('api/tracks/',views.tracks),
path('api/generate/',views.generate), path('api/tracks/<uuid:pk>/status/',views.status),
path('api/tracks/<uuid:pk>/delete/',views.delete), path('api/tracks/<uuid:pk>/audio/',views.audio)]
