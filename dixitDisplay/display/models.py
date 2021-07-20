from django.db import models
import random
from . import clue_generation
import random
import random
import os


class Game(models.Model):
    deck = models.CharField(max_length= 500)
    game_log = models.CharField(max_length=10000)
    n_players = models.IntegerField(default=1)
    first_load = models.CharField(max_length=1000, default='[]')
    loading_agent = models.CharField(max_length = 10, default='False')
    player_ids = models.CharField(max_length=1000)
    scores = models.CharField(max_length = 1000)
    used_cards = models.CharField(max_length=5000, default='')
    state = models.CharField(max_length=100, default="{'round': 0, 'turn': ''}")

class Player(models.Model):
    description = "A Dixit Player"
    player_name = models.CharField(max_length= 20, unique=True, primary_key=True)
    cards = models.CharField(max_length= 500, default='')
    role = models.CharField(max_length=20, default='Guesser')
    game_foreign_key = models.ManyToManyField(Game)
