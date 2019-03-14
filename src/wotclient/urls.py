from django.urls import path

from . import views

urlpatterns = [
    path('', views.thing_list, name='thing_list'),
    path('<thing_id>', views.thing_single_properties, name='thing_single_properties'),
    path('<thing_id>/actions', views.thing_single_actions, name='thing_single_actions'),
    path('<thing_id>/events', views.thing_single_events, name='thing_single_events'),
    path('<thing_id>/settings', views.thing_single_settings, name='thing_single_settings'),
    path('<thing_id>/schema', views.thing_single_schema, name='thing_single_schema'),
]
