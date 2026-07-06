from django.contrib import admin

from .models import Game, GamePlayer, ScoreEntry


class ScoreEntryInline(admin.TabularInline):
    model = ScoreEntry
    extra = 0
    can_delete = True


class GamePlayerInline(admin.TabularInline):
    model = GamePlayer
    extra = 0
    can_delete = True
    show_change_link = True


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "finished_at", "is_complete", "player_count")
    list_filter = ("is_complete",)
    inlines = (GamePlayerInline,)

    @admin.display(description="Spieler")
    def player_count(self, obj):
        return obj.game_players.count()


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "player", "total_score")
    list_filter = ("game",)
    inlines = (ScoreEntryInline,)
    actions = ("cleanup_orphaned_gameplayers",)

    @admin.action(description="Verwaiste Spieler-Einträge löschen")
    def cleanup_orphaned_gameplayers(self, request, queryset):
        valid_games = set(Game.objects.values_list("id", flat=True))
        orphaned_ids = list(
            queryset.exclude(game__id__in=valid_games).values_list("id", flat=True)
        )
        queryset.filter(id__in=orphaned_ids).delete()
        self.message_user(
            request, f"{len(orphaned_ids)} verwaiste Spieler-Einträge gelöscht."
        )


@admin.register(ScoreEntry)
class ScoreEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "game_player", "category", "value", "state")
    list_filter = ("category", "state")
    actions = ("cleanup_orphaned_scoreentries",)

    @admin.action(description="Verwaiste Punkte-Einträge löschen")
    def cleanup_orphaned_scoreentries(self, request, queryset):
        valid_gameplayers = set(GamePlayer.objects.values_list("id", flat=True))
        orphaned_ids = list(
            queryset.exclude(game_player__id__in=valid_gameplayers).values_list(
                "id", flat=True
            )
        )
        queryset.filter(id__in=orphaned_ids).delete()
        self.message_user(
            request, f"{len(orphaned_ids)} verwaiste Punkte-Einträge gelöscht."
        )
