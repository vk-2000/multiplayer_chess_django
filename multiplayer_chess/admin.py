from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Gameroom)
admin.site.register(models.Player)
admin.site.register(models.Friend_Request)
