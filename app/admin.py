from django.contrib import admin
from django.utils.html import format_html

from .models import Country, State, Biome, Land, Municipality, Community


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    ordering = ("name",)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "name_local", "code", "country")
    list_filter = ("country",)
    ordering = ("name",)


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ("name", "name_local", "code", "state")
    list_filter = ("state",)
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Biome)
class BiomeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "name_local",
        "country",
        "lands_count",
    )
    list_filter = ("country",)
    ordering = ("name",)

    def lands_count(self, obj):
        return obj.lands.count()

    lands_count.short_description = "Lands Count"


@admin.register(Land)
class LandAdmin(admin.ModelAdmin):
    list_display = ("name", "municipality", "biome", "category", "communities_list", "source_name", "isa_link")
    list_filter = ("biome", "category", "source_name")
    search_fields = ("name", "source_id")
    autocomplete_fields = ("communities",)
    ordering = ("name",)
    readonly_fields = (
        "source_id",
        "source_name",
        "source_updated_at",
        "source_last_synced_at",
        "source_raw_data",
    )

    def communities_list(self, obj):
        """Display comma-separated list of communities"""
        return ", ".join([c.name for c in obj.communities.all()])

    communities_list.short_description = "Communities"

    def isa_link(self, obj):
        if not obj.source_id or obj.source_name != "ISA":
            return None
        isa_url = "https://terrasindigenas.org.br/en/terras-indigenas/"
        return format_html(
            "<a href='%s%s' target='_blank'>source link</a>" % (isa_url, obj.source_id)
        )

    isa_link.allow_tags = True
    isa_link.short_description = "External link"


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "lands_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

    def lands_count(self, obj):
        return obj.lands.count()

    lands_count.short_description = "Lands Count"
