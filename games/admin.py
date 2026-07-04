from django.contrib import admin
from .models import Game, GamePlayer, ScoreEntry

admin.site.register(Game)
admin.site.register(GamePlayer)
admin.site.register(ScoreEntry)
