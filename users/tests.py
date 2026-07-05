from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Player


class PlayerModelTests(TestCase):
    def test_str_returns_name(self):
        player = Player.objects.create(name="Alice")
        self.assertEqual(str(player), "Alice")


class PlayerViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_login(self.user)

    def test_create_player(self):
        response = self.client.post(reverse("player_create"), {"name": "Alice"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Player.objects.filter(name="Alice").exists())

    def test_create_player_is_case_insensitive_unique(self):
        Player.objects.create(name="Alice")
        response = self.client.post(reverse("player_create"), {"name": "alice"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Player.objects.count(), 1)

    def test_empty_name_shows_error(self):
        response = self.client.post(reverse("player_create"), {"name": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Player.objects.count(), 0)

    def test_update_player(self):
        player = Player.objects.create(name="Alice")
        response = self.client.post(
            reverse("player_update", kwargs={"pk": player.pk}),
            {"name": "Alicia"},
        )
        self.assertEqual(response.status_code, 302)
        player.refresh_from_db()
        self.assertEqual(player.name, "Alicia")

    def test_delete_player(self):
        player = Player.objects.create(name="Alice")
        response = self.client.post(reverse("player_delete", kwargs={"pk": player.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Player.objects.exists())
