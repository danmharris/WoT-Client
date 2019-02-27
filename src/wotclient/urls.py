from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('things', views.thing_list, name='thing_list'),
    path('things/<thing_id>', views.thing_single_properties, name='thing_single_properties'),
    path('things/<thing_id>/actions', views.thing_single_actions, name='thing_single_actions')
]
