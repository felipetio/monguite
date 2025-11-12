from rest_framework import serializers

from app.models import Biome, Community, Country, Land, Municipality, State


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for Country model."""

    class Meta:
        model = Country
        fields = ["id", "name", "code"]


class StateSerializer(serializers.ModelSerializer):
    """Serializer for State model."""

    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True
    )

    class Meta:
        model = State
        fields = ["id", "name", "name_local", "code", "country", "country_id"]


class MunicipalitySerializer(serializers.ModelSerializer):
    """Serializer for Municipality model."""

    state = StateSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), source="state", write_only=True
    )

    class Meta:
        model = Municipality
        fields = ["id", "name", "name_local", "code", "state", "state_id"]


class BiomeSerializer(serializers.ModelSerializer):
    """Serializer for Biome model."""

    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True
    )

    class Meta:
        model = Biome
        fields = [
            "id",
            "name",
            "name_local",
            "description",
            "description_local",
            "country",
            "country_id",
        ]


class CommunitySerializer(serializers.ModelSerializer):
    """Serializer for Community model."""

    lands_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Community
        fields = ["id", "name", "lands_count"]


class LandSerializer(serializers.ModelSerializer):
    """Serializer for Land model."""

    biome = BiomeSerializer(read_only=True)
    biome_id = serializers.PrimaryKeyRelatedField(
        queryset=Biome.objects.all(), source="biome", write_only=True
    )
    communities = CommunitySerializer(many=True, read_only=True)
    communities_ids = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.all(),
        source="communities",
        many=True,
        write_only=True,
    )
    communities_count = serializers.IntegerField(read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    # Flattened location fields - these come from annotations in the viewset
    location = serializers.SerializerMethodField()
    source_link = serializers.SerializerMethodField()

    class Meta:
        model = Land
        fields = [
            "id",
            "name",
            "category",
            "category_display",
            "location",
            "biome",
            "biome_id",
            "communities",
            "communities_ids",
            "communities_count",
            "source_link",
        ]

    def get_location(self, obj):
        """Return flattened location information."""
        location = {}

        # Use annotated fields if available (for better performance)
        if hasattr(obj, 'municipality_name'):
            location['municipality'] = obj.municipality_name
            location['state'] = obj.state_name
            location['state_code'] = obj.state_code
            location['country'] = obj.country_name
            location['country_code'] = obj.country_code
        # Fallback to related objects if annotations not available
        elif obj.municipality:
            location['municipality'] = obj.municipality.name
            if obj.municipality.state:
                location['state'] = obj.municipality.state.name
                location['state_code'] = obj.municipality.state.code
                if obj.municipality.state.country:
                    location['country'] = obj.municipality.state.country.name
                    location['country_code'] = obj.municipality.state.country.code

        return location if location else None

    def get_source_link(self, obj):
        """Return external source link if available."""
        if obj.source_name == "ISA" and obj.source_id:
            return f"https://terrasindigenas.org.br/en/terras-indigenas/{obj.source_id}"
        return None
