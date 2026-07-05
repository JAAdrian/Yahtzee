from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import Player

from .models import Game, GamePlayer, ScoreEntry


class ScoreEntryModelTests(TestCase):
    def test_fixed_category_effective_value(self):
        gp = self._create_game_player()
        entry = ScoreEntry.objects.create(
            game_player=gp,
            category=ScoreEntry.Category.FULL_HOUSE,
            state=ScoreEntry.State.FILLED,
        )
        self.assertEqual(entry.effective_value, 25)
        self.assertTrue(entry.is_filled)
        self.assertFalse(entry.is_stricken)

    def test_stricken_entry_contributes_zero(self):
        gp = self._create_game_player()
        entry = ScoreEntry.objects.create(
            game_player=gp,
            category=ScoreEntry.Category.YAHTZEE,
            state=ScoreEntry.State.STRICKEN,
        )
        self.assertEqual(entry.effective_value, 0)
        self.assertTrue(entry.is_stricken)

    def test_upper_section_entry_value(self):
        gp = self._create_game_player()
        entry = ScoreEntry.objects.create(
            game_player=gp,
            category=ScoreEntry.Category.ONES,
            value=3,
            state=ScoreEntry.State.FILLED,
        )
        self.assertEqual(entry.effective_value, 3)

    def _create_game_player(self):
        game = Game.objects.create()
        player = Player.objects.create(name="Alice")
        return GamePlayer.objects.create(game=game, player=player)


class GamePlayerScoreTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create()
        self.alice = Player.objects.create(name="Alice")
        self.gp_alice = GamePlayer.objects.create(game=self.game, player=self.alice)

    def test_upper_sum(self):
        self._set(ScoreEntry.Category.ONES, 3)
        self._set(ScoreEntry.Category.TWOS, 6)
        self._set(ScoreEntry.Category.THREES, 9)
        self._set(ScoreEntry.Category.FOURS, 12)
        self._set(ScoreEntry.Category.FIVES, 15)
        self._set(ScoreEntry.Category.SIXES, 18)
        self.assertEqual(self.gp_alice.upper_sum, 63)

    def test_bonus_at_63(self):
        self._set(ScoreEntry.Category.ONES, 3)
        self._set(ScoreEntry.Category.TWOS, 6)
        self._set(ScoreEntry.Category.THREES, 9)
        self._set(ScoreEntry.Category.FOURS, 12)
        self._set(ScoreEntry.Category.FIVES, 15)
        self._set(ScoreEntry.Category.SIXES, 18)
        self.assertEqual(self.gp_alice.bonus, 35)

    def test_no_bonus_below_63(self):
        self._set(ScoreEntry.Category.ONES, 1)
        self.assertEqual(self.gp_alice.bonus, 0)

    def test_lower_sum_with_fixed_and_free_categories(self):
        self._set(ScoreEntry.Category.FULL_HOUSE, state=ScoreEntry.State.FILLED)
        self._set(ScoreEntry.Category.SMALL_STRAIGHT, state=ScoreEntry.State.FILLED)
        self._set(ScoreEntry.Category.YAHTZEE, state=ScoreEntry.State.STRICKEN)
        self._set(ScoreEntry.Category.THREE_OF_A_KIND, value=18)
        self.assertEqual(self.gp_alice.lower_sum, 25 + 30 + 0 + 18)

    def test_total_score(self):
        self._set(ScoreEntry.Category.ONES, 3)
        self._set(ScoreEntry.Category.TWOS, 6)
        self._set(ScoreEntry.Category.THREES, 9)
        self._set(ScoreEntry.Category.FOURS, 12)
        self._set(ScoreEntry.Category.FIVES, 15)
        self._set(ScoreEntry.Category.SIXES, 18)
        self._set(ScoreEntry.Category.FULL_HOUSE, state=ScoreEntry.State.FILLED)
        self._set(ScoreEntry.Category.CHANCE, value=22)
        expected = 63 + 35 + 25 + 22
        self.assertEqual(self.gp_alice.total_score, expected)

    def _set(self, category, value=None, state=ScoreEntry.State.FILLED):
        ScoreEntry.objects.update_or_create(
            game_player=self.gp_alice,
            category=category,
            defaults={"value": value, "state": state},
        )


class GameViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_login(self.user)
        self.alice = Player.objects.create(name="Alice")
        self.bob = Player.objects.create(name="Bob")

    def test_create_game(self):
        response = self.client.post(reverse("game_create"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Game.objects.count(), 1)

    def test_add_player_to_game(self):
        game = Game.objects.create()
        response = self.client.post(
            reverse("game_add_player", kwargs={"pk": game.pk}),
            {"players": [self.alice.pk, self.bob.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(game.game_players.count(), 2)

    def test_cannot_add_player_to_finished_game(self):
        game = Game.objects.create(is_complete=True)
        response = self.client.get(reverse("game_add_player", kwargs={"pk": game.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(game.game_players.count(), 0)

    def test_score_sheet_saves_numeric_values(self):
        game = Game.objects.create()
        gp = GamePlayer.objects.create(game=game, player=self.alice)
        url = reverse("game_score", kwargs={"pk": game.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            {
                f"score_{gp.pk}_ones": "5",
                f"score_{gp.pk}_chance": "22",
            },
        )
        self.assertEqual(response.status_code, 302)
        gp.refresh_from_db()
        self.assertEqual(gp.total_score, 27)

    def test_score_sheet_saves_fixed_category_states(self):
        game = Game.objects.create()
        gp = GamePlayer.objects.create(game=game, player=self.alice)
        url = reverse("game_score", kwargs={"pk": game.pk})
        response = self.client.post(
            url,
            {
                f"state_{gp.pk}_full_house": "filled",
                f"state_{gp.pk}_yahtzee": "stricken",
            },
        )
        self.assertEqual(response.status_code, 302)
        gp.refresh_from_db()
        self.assertEqual(gp.lower_sum, 25)

    def test_numeric_zero_is_valid_score(self):
        game = Game.objects.create()
        gp = GamePlayer.objects.create(game=game, player=self.alice)
        url = reverse("game_score", kwargs={"pk": game.pk})
        response = self.client.post(
            url,
            {f"score_{gp.pk}_three_of_a_kind": "0"},
        )
        self.assertEqual(response.status_code, 302)
        entry = gp.scores.get(category=ScoreEntry.Category.THREE_OF_A_KIND)
        self.assertTrue(entry.is_filled)
        self.assertEqual(entry.value, 0)
        self.assertEqual(entry.effective_value, 0)

    def test_finish_game_redirects_to_results(self):
        game = Game.objects.create()
        response = self.client.post(reverse("game_finish", kwargs={"pk": game.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("game_results", kwargs={"pk": game.pk})))
        game.refresh_from_db()
        self.assertTrue(game.is_complete)

    def test_delete_game(self):
        game = Game.objects.create()
        response = self.client.post(reverse("game_delete", kwargs={"pk": game.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Game.objects.filter(pk=game.pk).exists())

    def test_leaderboard_counts_wins(self):
        game = Game.objects.create()
        gp_alice = GamePlayer.objects.create(game=game, player=self.alice)
        gp_bob = GamePlayer.objects.create(game=game, player=self.bob)
        ScoreEntry.objects.update_or_create(
            game_player=gp_alice,
            category=ScoreEntry.Category.ONES,
            defaults={"value": 5, "state": ScoreEntry.State.FILLED},
        )
        ScoreEntry.objects.update_or_create(
            game_player=gp_bob,
            category=ScoreEntry.Category.ONES,
            defaults={"value": 3, "state": ScoreEntry.State.FILLED},
        )
        self.client.post(reverse("game_finish", kwargs={"pk": game.pk}))

        response = self.client.get(reverse("leaderboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice")
        self.assertContains(response, "Bob")
