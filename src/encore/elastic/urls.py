"""Elastic Views"""

from django.urls import path

import elastic.views as e_views

urlpatterns = [
    path("event/", e_views.event, name="elastic.views.event"),
    path("event/<str:event_index>/<str:event_id>/", e_views.event_info, name="elastic.views.event_info"),
    path("resolve/", e_views.resolve, name="elastic.views.resolve"),
]
