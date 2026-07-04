from django.urls import path
from . import views

urlpatterns = [
    path("", views.player_list, name="player_list"),
    path("new/", views.player_create, name="player_create"),
    path("<int:pk>/", views.player_detail, name="player_detail"),
    path("<int:pk>/edit/", views.player_update, name="player_update"),
    path("<int:pk>/delete/", views.player_delete, name="player_delete"),
]
