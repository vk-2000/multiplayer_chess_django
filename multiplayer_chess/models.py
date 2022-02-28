from django.db import models
from django.conf import settings
from django.db.models.deletion import CASCADE
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.db.models.fields import BooleanField

# Create your models here.


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    friends = models.ManyToManyField(
        "Player", blank=True, related_name="Friends")
    is_online = models.BooleanField(default=False)
    is_ingame = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.user.username


class Friend_Request(models.Model):
    from_user = models.ForeignKey(
        Player, related_name="from_user", on_delete=CASCADE)
    to_user = models.ForeignKey(
        Player, related_name="to_user", on_delete=CASCADE)


class Gameroom(models.Model):
    room_name = models.CharField(max_length=50)
    players = models.ManyToManyField(Player, related_name="played_in")
    active = models.BooleanField(default=True)
    private = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(
        Player, on_delete=CASCADE, related_name="winner", null=True)

    def __str__(self) -> str:
        return str(self.room_name) + str(self.pk)
