from django.contrib import admin

from .models import Room, Player


# Register your models here.

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['table', 'status']
    list_filter = ['status']
    inlines = [PlayerInline]
