from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),
    path('things', views.thing_list, name='thing_list'),
    path('things/<thing_id>', views.thing_single_properties, name='thing_single_properties'),
    path('things/<thing_id>/actions', views.thing_single_actions, name='thing_single_actions'),
    path('things/<thing_id>/events', views.thing_single_events, name='thing_single_events'),
    path('things/<thing_id>/settings', views.thing_single_settings, name='thing_single_settings'),
    path('things/<thing_id>/schema', views.thing_single_schema, name='thing_single_schema'),
]
