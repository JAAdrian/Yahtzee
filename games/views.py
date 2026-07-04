from django.http import HttpResponse


def game_list(request):
    return HttpResponse("Game list")


def game_create(request):
    return HttpResponse("Create game")


def game_detail(request, pk):
    return HttpResponse(f"Game detail: {pk}")


def game_add_player(request, pk):
    return HttpResponse(f"Add player to game: {pk}")


def game_score(request, pk):
    return HttpResponse(f"Score game: {pk}")


def game_finish(request, pk):
    return HttpResponse(f"Finish game: {pk}")


def game_results(request, pk):
    return HttpResponse(f"Results for game: {pk}")
