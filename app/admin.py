from django.contrib import admin

from .models import Country, State, Biome, Land

admin.site.register(Country)
admin.site.register(State)
admin.site.register(Biome)
admin.site.register(Land)
