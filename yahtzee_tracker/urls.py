"""
URL configuration for yahtzee_tracker project.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from yahtzee_tracker import settings

urlpatterns = [
    path("", RedirectView.as_view(url="/games/", permanent=False)),
    path(settings.ADMIN_URL, admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("users/", include("users.urls")),
    path("games/", include("games.urls")),
]
