from django.contrib import admin
from django.utils.html import format_html

from .models import Country, State, Biome, Land


@admin.register(Biome)
class BiomeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "total_area",
        "preserved_area",
        "preserved_rate",
        "lands_count",
    )

    def lands_count(self, obj):
        return obj.lands.count()

    lands_count.short_description = "Lands Count"

    def preserved_rate(self, obj):
        if obj.preserved_area:
            try:
                return "%d%%" % (100 * obj.preserved_area / obj.total_area)
            except (ValueError, ZeroDivisionError):
                return None
        return None


@admin.register(Land)
class LandAdmin(admin.ModelAdmin):
    list_display = ("name", "total_area", "biome", "category", "isa_link")
    list_filter = ("biome", "category")

    def isa_link(self, obj):
        if not obj.isa_id:
            return None
        isa_url = "https://terrasindigenas.org.br/en/terras-indigenas/"
        return format_html(
            "<a href='%s%s' target='_blank'>source link</a>" % (isa_url, obj.isa_id)
        )

    isa_link.allow_tags = True
    isa_link.short_description = "External link"
