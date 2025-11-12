from django.db.models import Count, F
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from app.filters import CommunityFilter, LandFilter
from app.models import Community, Land
from app.serializers import CommunitySerializer, LandSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all lands",
        description="Retrieve a paginated list of all indigenous lands. "
        "Supports filtering by name, category, municipality, state, biome, and community.",
        tags=["Lands"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a land",
        description="Retrieve detailed information about a specific indigenous land by ID.",
        tags=["Lands"],
    ),
)
class LandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for indigenous lands.

    Provides list and detail views with filtering capabilities.
    Uses annotations for optimal query performance.
    """

    serializer_class = LandSerializer
    filterset_class = LandFilter
    search_fields = ["name", "municipality__name", "communities__name"]
    ordering_fields = [
        "name",
        "category",
        "municipality__state__code",
        "state_code",
        "municipality_name",
        "communities_count",
    ]
    ordering = ["name"]

    def get_queryset(self):
        """
        Return queryset with annotations for flattened location fields and counts.
        This improves performance by avoiding N+1 queries.
        """
        return (
            Land.objects.select_related(
                "municipality__state__country", "biome__country"
            )
            .prefetch_related("communities")
            .annotate(
                municipality_name=F("municipality__name"),
                state_name=F("municipality__state__name"),
                state_code=F("municipality__state__code"),
                country_name=F("municipality__state__country__name"),
                country_code=F("municipality__state__country__code"),
                communities_count=Count("communities", distinct=True),
            )
        )


@extend_schema_view(
    list=extend_schema(
        summary="List all communities",
        description="Retrieve a paginated list of all indigenous communities. "
        "Supports filtering by name and lands count.",
        tags=["Communities"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a community",
        description="Retrieve detailed information about a specific indigenous community by ID.",
        tags=["Communities"],
    ),
)
class CommunityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for indigenous communities.

    Provides list and detail views with filtering capabilities.
    Uses annotations for optimal query performance.
    """

    serializer_class = CommunitySerializer
    filterset_class = CommunityFilter
    search_fields = ["name"]
    ordering_fields = ["name", "lands_count"]
    ordering = ["name"]

    def get_queryset(self):
        """
        Return queryset with annotations for counts.
        This improves performance by avoiding N+1 queries.
        """
        return Community.objects.annotate(
            lands_count=Count("lands", distinct=True)
        )
