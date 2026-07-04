from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from users.models import Player

from .models import Game, GamePlayer, ScoreEntry


# Display order matching a real German Yahtzee score sheet.
SCORE_SHEET_ORDER = [
    ScoreEntry.Category.ONES,
    ScoreEntry.Category.TWOS,
    ScoreEntry.Category.THREES,
    ScoreEntry.Category.FOURS,
    ScoreEntry.Category.FIVES,
    ScoreEntry.Category.SIXES,
    ScoreEntry.Category.THREE_OF_A_KIND,
    ScoreEntry.Category.FOUR_OF_A_KIND,
    ScoreEntry.Category.FULL_HOUSE,
    ScoreEntry.Category.SMALL_STRAIGHT,
    ScoreEntry.Category.LARGE_STRAIGHT,
    ScoreEntry.Category.YAHTZEE,
    ScoreEntry.Category.CHANCE,
]


def game_list(request):
    active_games = Game.objects.filter(is_complete=False).order_by("-created_at")
    finished_games = Game.objects.filter(is_complete=True).order_by("-finished_at")
    return render(
        request,
        "games/game_list.html",
        {"active_games": active_games, "finished_games": finished_games},
    )


def game_create(request):
    if request.method == "POST":
        game = Game.objects.create()
        messages.success(request, f"Spiel #{game.id} wurde gestartet.")
        return HttpResponseRedirect(game.get_absolute_url())
    return render(request, "games/game_create.html")


def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)
    return render(request, "games/game_detail.html", {"game": game})


def game_add_player(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if game.is_complete:
        messages.error(request, "Abgeschlossene Spiele können nicht mehr bearbeitet werden.")
        return HttpResponseRedirect(game.get_absolute_url())

    if request.method == "POST":
        player_ids = request.POST.getlist("players")
        if not player_ids:
            messages.error(request, "Bitte mindestens einen Spieler auswählen.")
        else:
            added = 0
            for pid in player_ids:
                try:
                    player = Player.objects.get(pk=int(pid))
                    _, created = GamePlayer.objects.get_or_create(game=game, player=player)
                    if created:
                        added += 1
                except (ValueError, Player.DoesNotExist):
                    continue
            if added:
                messages.success(request, f"{added} Spieler hinzugefügt.")
            else:
                messages.info(request, "Alle ausgewählten Spieler sind bereits im Spiel.")
            return HttpResponseRedirect(game.get_absolute_url())

    already_in = set(gp.player_id for gp in game.game_players.all())
    available_players = Player.objects.exclude(pk__in=already_in).order_by("name")
    return render(
        request,
        "games/game_add_player.html",
        {"game": game, "available_players": available_players},
    )


def _ensure_score_entries(game_player):
    """Create missing ScoreEntry rows for all editable categories."""
    existing = set(game_player.scores.values_list("category", flat=True))
    missing = [cat for cat in SCORE_SHEET_ORDER if cat not in existing]
    ScoreEntry.objects.bulk_create(
        [ScoreEntry(game_player=game_player, category=cat) for cat in missing]
    )


def _parse_score_entry(entry, raw_value, raw_state):
    """Update entry value/state from form POST data.

    Fixed lower-section categories (Full House, straights, Yahtzee) use a state
    dropdown: empty, filled (awards fixed points) or stricken (0 points).

    All numeric categories (upper section and free lower-section categories)
    simply use a numeric input; 0 is a normal score, empty means not yet entered.
    """
    if entry.category in ScoreEntry.FIXED_POINTS:
        entry.value = None
        if raw_state == "filled":
            entry.state = ScoreEntry.State.FILLED
        elif raw_state == "stricken":
            entry.state = ScoreEntry.State.STRICKEN
        else:
            entry.state = ScoreEntry.State.EMPTY
        return True

    # Numeric categories: just a number, empty = not entered.
    if raw_value == "":
        entry.value = None
        entry.state = ScoreEntry.State.EMPTY
        return True

    try:
        entry.value = int(raw_value)
        entry.state = ScoreEntry.State.FILLED
        return True
    except ValueError:
        return False


def game_score(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if game.is_complete:
        messages.error(request, "Abgeschlossene Spiele können nicht mehr bearbeitet werden.")
        return HttpResponseRedirect(game.get_absolute_url())

    players = list(game.game_players.select_related("player").prefetch_related("scores"))
    if not players:
        messages.error(request, "Füge zuerst Spieler zum Spiel hinzu.")
        return HttpResponseRedirect(game.get_absolute_url())

    for gp in players:
        _ensure_score_entries(gp)

    # Re-fetch so that prefetched scores include all newly created rows.
    players = list(game.game_players.select_related("player").prefetch_related("scores"))

    if request.method == "POST":
        entries_to_create = []
        entries_to_update = []
        for gp in players:
            scores_by_cat = gp.scores_by_category
            for cat in SCORE_SHEET_ORDER:
                entry = scores_by_cat.get(cat)
                is_new = entry is None
                if is_new:
                    entry = ScoreEntry(game_player=gp, category=cat)

                value_field = f"score_{gp.pk}_{cat}"
                state_field = f"state_{gp.pk}_{cat}"
                raw_value = request.POST.get(value_field, "").strip()
                raw_state = request.POST.get(state_field, "").strip()

                if not _parse_score_entry(entry, raw_value, raw_state):
                    messages.error(
                        request,
                        f"Ungültiger Wert bei {gp.player.name} / {ScoreEntry.Category(cat).label}.",
                    )
                    # Re-fetch so the template sees current data including new rows.
                    players = list(
                        game.game_players.select_related("player").prefetch_related("scores")
                    )
                    return render(
                        request,
                        "games/game_score.html",
                        {
                            "game": game,
                            "players": players,
                            "categories": SCORE_SHEET_ORDER,
                            "fixed_points": ScoreEntry.FIXED_POINTS,
                        },
                    )
                if is_new:
                    entries_to_create.append(entry)
                else:
                    entries_to_update.append(entry)

        if entries_to_create:
            ScoreEntry.objects.bulk_create(entries_to_create)
        if entries_to_update:
            ScoreEntry.objects.bulk_update(entries_to_update, ["value", "state"])
        messages.success(request, "Punkte wurden gespeichert.")
        return HttpResponseRedirect(game.get_absolute_url())

    # Re-fetch after ensuring rows exist.
    players = list(game.game_players.select_related("player").prefetch_related("scores"))
    return render(
        request,
        "games/game_score.html",
        {
            "game": game,
            "players": players,
            "categories": SCORE_SHEET_ORDER,
            "fixed_points": ScoreEntry.FIXED_POINTS,
        },
    )


def game_finish(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == "POST":
        with transaction.atomic():
            game.is_complete = True
            game.finished_at = timezone.now()
            game.save()
        messages.success(request, f"Spiel #{game.id} wurde abgeschlossen.")
        return HttpResponseRedirect(reverse("game_results", kwargs={"pk": game.pk}))
    return render(request, "games/game_finish.html", {"game": game})


def game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == "POST":
        game.delete()
        messages.success(request, f"Spiel #{game.id} wurde gelöscht.")
        return HttpResponseRedirect(reverse("game_list"))
    return render(request, "games/game_delete.html", {"game": game})


def game_results(request, pk):
    game = get_object_or_404(Game, pk=pk)
    ranked = game.ranked_players()
    return render(request, "games/game_results.html", {"game": game, "ranked": ranked})


def leaderboard(request):
    """Eternal leaderboard: players ranked by completed-game wins."""
    players = Player.objects.order_by("name")
    stats = []
    for player in players:
        wins = 0
        games_played = player.game_entries.filter(game__is_complete=True).count()
        for gp in player.game_entries.filter(game__is_complete=True).prefetch_related("game__game_players"):
            ranked = gp.game.ranked_players()
            if ranked and ranked[0].pk == gp.pk:
                wins += 1
        stats.append({"player": player, "wins": wins, "games_played": games_played})

    stats.sort(key=lambda s: (-s["wins"], -s["games_played"], s["player"].name))
    return render(request, "games/leaderboard.html", {"stats": stats})
