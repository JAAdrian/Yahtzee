from django.urls import path
from . import views

urlpatterns = [
    path("", views.game_list, name="game_list"),
    path("new/", views.game_create, name="game_create"),
    path("<int:pk>/", views.game_detail, name="game_detail"),
    path("<int:pk>/add-player/", views.game_add_player, name="game_add_player"),
    path("<int:pk>/score/", views.game_score, name="game_score"),
    path("<int:pk>/finish/", views.game_finish, name="game_finish"),
    path("<int:pk>/results/", views.game_results, name="game_results"),
]
