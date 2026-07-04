from django.http import HttpResponse


def player_list(request):
    return HttpResponse("Player list")


def player_create(request):
    return HttpResponse("Create player")


def player_detail(request, pk):
    return HttpResponse(f"Player detail: {pk}")


def player_update(request, pk):
    return HttpResponse(f"Update player: {pk}")


def player_delete(request, pk):
    return HttpResponse(f"Delete player: {pk}")
