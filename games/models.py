from django.db import models


class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Game #{self.id}"  # type: ignore


class GamePlayer(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="game_players"
    )
    player = models.ForeignKey(
        "users.Player", on_delete=models.CASCADE, related_name="game_entries"
    )

    class Meta:
        unique_together = ("game", "player")

    def __str__(self):
        return f"{self.player} in {self.game}"


class ScoreEntry(models.Model):
    class Category(models.TextChoices):
        ONES = "ones", "Ones"
        TWOS = "twos", "Twos"

    game_player = models.ForeignKey(
        GamePlayer, on_delete=models.CASCADE, related_name="scores"
    )
    category = models.CharField(max_length=30, choices=Category.choices)

    def __str__(self):
        return f"{self.game_player} - {self.category}: {self.value}"  # type: ignore
