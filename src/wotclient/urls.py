from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('things', views.thing_list, name='thing_list'),
    path('things/<thing_id>', views.thing_single, name='thing_single'),
]
