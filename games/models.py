from django.db import models
from django.urls import reverse


class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Spiel #{self.id}"  # type: ignore

    def get_absolute_url(self):
        return reverse("game_detail", kwargs={"pk": self.pk})

    def ranked_players(self):
        """Return game players ordered by total score descending."""
        return sorted(self.game_players.all(), key=lambda gp: gp.total_score, reverse=True)


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

    @property
    def scores_by_category(self):
        """Return a dict mapping category value to ScoreEntry."""
        return {entry.category: entry for entry in self.scores.all()}

    def _entry_value(self, category):
        entry = self.scores_by_category.get(category)
        if entry and entry.is_filled:
            return entry.effective_value
        return 0

    @property
    def upper_sum(self):
        return sum(
            self._entry_value(cat)
            for cat in ScoreEntry.UPPER_SECTION_CATEGORIES
        )

    @property
    def bonus(self):
        return 35 if self.upper_sum >= 63 else 0

    @property
    def lower_sum(self):
        return sum(
            self._entry_value(cat)
            for cat in ScoreEntry.LOWER_SECTION_CATEGORIES
        )

    @property
    def total_score(self):
        return self.upper_sum + self.bonus + self.lower_sum


class ScoreEntry(models.Model):
    """A single score entry for one player in one game in one Yahtzee category."""

    class Category(models.TextChoices):
        ONES = "ones", "Einsen"
        TWOS = "twos", "Zweien"
        THREES = "threes", "Dreien"
        FOURS = "fours", "Vieren"
        FIVES = "fives", "Fünfen"
        SIXES = "sixes", "Sechsen"
        THREE_OF_A_KIND = "three_of_a_kind", "Dreierpasch"
        FOUR_OF_A_KIND = "four_of_a_kind", "Viererpasch"
        FULL_HOUSE = "full_house", "Full House"
        SMALL_STRAIGHT = "small_straight", "Kleine Straße"
        LARGE_STRAIGHT = "large_straight", "Große Straße"
        YAHTZEE = "yahtzee", "Kniffel"
        CHANCE = "chance", "Chance"

    UPPER_SECTION_CATEGORIES = [
        Category.ONES,
        Category.TWOS,
        Category.THREES,
        Category.FOURS,
        Category.FIVES,
        Category.SIXES,
    ]

    LOWER_SECTION_CATEGORIES = [
        Category.THREE_OF_A_KIND,
        Category.FOUR_OF_A_KIND,
        Category.FULL_HOUSE,
        Category.SMALL_STRAIGHT,
        Category.LARGE_STRAIGHT,
        Category.YAHTZEE,
        Category.CHANCE,
    ]

    # Fixed points for special lower-section categories.
    FIXED_POINTS = {
        Category.FULL_HOUSE: 25,
        Category.SMALL_STRAIGHT: 30,
        Category.LARGE_STRAIGHT: 40,
        Category.YAHTZEE: 50,
    }

    class State(models.TextChoices):
        EMPTY = "empty", "Leer"
        FILLED = "filled", "Belegt"
        STRICKEN = "stricken", "Gestrichen"

    game_player = models.ForeignKey(
        GamePlayer, on_delete=models.CASCADE, related_name="scores"
    )
    category = models.CharField(max_length=30, choices=Category.choices)
    value = models.IntegerField(null=True, blank=True)
    state = models.CharField(
        max_length=10, choices=State.choices, default=State.EMPTY
    )

    class Meta:
        unique_together = ("game_player", "category")

    def __str__(self):
        return f"{self.game_player} - {self.category_label()}: {self.display_value}"

    def category_label(self):
        return self.Category(self.category).label

    @property
    def is_empty(self):
        return self.state == self.State.EMPTY

    @property
    def is_filled(self):
        return self.state == self.State.FILLED

    @property
    def is_stricken(self):
        return self.state == self.State.STRICKEN

    @property
    def effective_value(self):
        """Return the points this entry contributes to the total."""
        if self.is_stricken:
            return 0
        if self.category in self.FIXED_POINTS:
            return self.FIXED_POINTS[self.category]
        return self.value or 0

    @property
    def display_value(self):
        """Human-readable representation for templates."""
        if self.is_stricken:
            return "—"
        if self.is_empty:
            return ""
        if self.category in self.FIXED_POINTS:
            return self.FIXED_POINTS[self.category]
        return self.value
