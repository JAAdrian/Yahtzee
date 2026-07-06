from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django_ratelimit.decorators import ratelimit

from .models import Player


def player_list(request):
    players = Player.objects.order_by("name")
    return render(request, "users/player_list.html", {"players": players})


@login_required
@ratelimit(key="user_or_ip", rate="10/m", method=["POST"])
def player_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            player, created = Player.objects.get_or_create(
                name__iexact=name, defaults={"name": name}
            )
            if created:
                messages.success(request, f"Spieler '{player.name}' wurde angelegt.")
            else:
                messages.info(request, f"Spieler '{player.name}' existiert bereits.")
            return HttpResponseRedirect(reverse("player_list"))
        messages.error(request, "Bitte einen Namen eingeben.")
    return render(request, "users/player_form.html")


def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    return render(request, "users/player_detail.html", {"player": player})


@login_required
@ratelimit(key="user_or_ip", rate="10/m", method=["POST"])
def player_update(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            player.name = name
            player.save()
            messages.success(request, f"Spieler '{player.name}' wurde aktualisiert.")
            return HttpResponseRedirect(
                reverse("player_detail", kwargs={"pk": player.pk})
            )
        messages.error(request, "Bitte einen Namen eingeben.")
    return render(request, "users/player_form.html", {"player": player})


@login_required
@ratelimit(key="user_or_ip", rate="20/m", method=["POST"])
def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == "POST":
        player.delete()
        messages.success(request, "Spieler wurde gelöscht.")
        return HttpResponseRedirect(reverse("player_list"))
    return render(request, "users/player_confirm_delete.html", {"player": player})
