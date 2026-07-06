"""
Shared views / handlers for the project.
"""

from django.shortcuts import render


def ratelimited_429(request, exception):
    """Render a friendly 429 page when django-ratelimit blocks a request."""
    return render(request, "429.html", status=429)
