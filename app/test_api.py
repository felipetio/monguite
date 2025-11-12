import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from app.models import Biome, Community, Country, Land, Municipality, State


@pytest.fixture
def api_client():
    """Return DRF API client."""
    return APIClient()


@pytest.fixture
def country():
    """Create a test country."""
    return Country.objects.create(name="Brazil", code="BR")


@pytest.fixture
def state(country):
    """Create a test state."""
    return State.objects.create(
        name="Acre", name_local="Acre", code="AC", country=country
    )


@pytest.fixture
def municipality(state):
    """Create a test municipality."""
    return Municipality.objects.create(
        name="Rio Branco", name_local="Rio Branco", code="1200401", state=state
    )


@pytest.fixture
def biome(country):
    """Create a test biome."""
    return Biome.objects.create(
        name="Amazon",
        name_local="Amazônia",
        country=country,
        description="Amazon rainforest",
    )


@pytest.fixture
def community():
    """Create a test community."""
    return Community.objects.create(name="Ashaninka")


@pytest.fixture
def land(municipality, biome, community):
    """Create a test land."""
    land = Land.objects.create(
        name="Terra Indígena Kampa do Rio Amônia",
        municipality=municipality,
        biome=biome,
        category="TI",
        source_id="123",
        source_name="ISA",
    )
    land.communities.add(community)
    return land


@pytest.mark.django_db
class TestLandAPI:
    """Tests for Land API endpoints."""

    def test_list_lands(self, api_client, land):
        """Test listing all lands."""
        url = reverse("land-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == land.name

    def test_retrieve_land(self, api_client, land):
        """Test retrieving a specific land."""
        url = reverse("land-detail", kwargs={"pk": land.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == land.name
        assert response.data["category"] == "TI"
        assert response.data["category_display"] == "Terra Indígena"

    def test_land_includes_related_data(self, api_client, land, community):
        """Test that land detail includes location, biome, and communities."""
        url = reverse("land-detail", kwargs={"pk": land.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Check flattened location structure
        assert "location" in response.data
        location = response.data["location"]
        assert location["municipality"] == "Rio Branco"
        assert location["state"] == "Acre"
        assert location["state_code"] == "AC"
        assert location["country"] == "Brazil"
        assert location["country_code"] == "BR"

        # Check biome
        assert "biome" in response.data
        assert response.data["biome"]["name"] == "Amazon"

        # Check communities
        assert "communities" in response.data
        assert len(response.data["communities"]) == 1
        assert response.data["communities"][0]["name"] == community.name

        # Check communities_count
        assert "communities_count" in response.data
        assert response.data["communities_count"] == 1

        # Check source_link (ISA land should have link)
        assert "source_link" in response.data
        assert (
            response.data["source_link"]
            == "https://terrasindigenas.org.br/en/terras-indigenas/123"
        )

        # Ensure source_id and source_name are not in response
        assert "source_id" not in response.data
        assert "source_name" not in response.data

    def test_land_without_isa_source(self, api_client, municipality, biome):
        """Test that lands without ISA source return null for source_link."""
        # Create land without source info
        land = Land.objects.create(
            name="Land Without Source",
            municipality=municipality,
            biome=biome,
            category="TI",
        )

        url = reverse("land-detail", kwargs={"pk": land.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["source_link"] is None

        # Create land with non-ISA source
        land2 = Land.objects.create(
            name="Land With Other Source",
            municipality=municipality,
            biome=biome,
            category="TI",
            source_id="456",
            source_name="OTHER",
        )

        url = reverse("land-detail", kwargs={"pk": land2.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["source_link"] is None

    def test_filter_land_by_name(self, api_client, land):
        """Test filtering lands by name."""
        url = reverse("land-list")
        response = api_client.get(url, {"name": "Kampa"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        response = api_client.get(url, {"name": "NonExistent"})
        assert len(response.data["results"]) == 0

    def test_filter_land_by_category(self, api_client, land):
        """Test filtering lands by category."""
        url = reverse("land-list")
        response = api_client.get(url, {"category": "TI"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        response = api_client.get(url, {"category": "DI"})
        assert len(response.data["results"]) == 0

    def test_filter_land_by_state_code(self, api_client, land):
        """Test filtering lands by state code."""
        url = reverse("land-list")
        response = api_client.get(url, {"state_code": "AC"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_filter_land_by_community(self, api_client, land):
        """Test filtering lands by community name."""
        url = reverse("land-list")
        response = api_client.get(url, {"community": "Ashaninka"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_land(self, api_client, land):
        """Test searching lands."""
        url = reverse("land-list")
        response = api_client.get(url, {"search": "Kampa"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_ordering_lands(self, api_client, land, municipality, biome, community):
        """Test ordering lands."""
        # Create another land
        land2 = Land.objects.create(
            name="Aldeia Test",
            municipality=municipality,
            biome=biome,
            category="PI",
        )

        url = reverse("land-list")
        response = api_client.get(url, {"ordering": "name"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "Aldeia Test"
        assert response.data["results"][1]["name"] == land.name

        # Test reverse ordering
        response = api_client.get(url, {"ordering": "-name"})
        assert response.data["results"][0]["name"] == land.name
        assert response.data["results"][1]["name"] == "Aldeia Test"

    def test_filter_land_by_communities_count(self, api_client, municipality, biome):
        """Test filtering lands by communities count."""
        community1 = Community.objects.create(name="Community 1")
        community2 = Community.objects.create(name="Community 2")

        # Land with 2 communities
        land1 = Land.objects.create(
            name="Land 1",
            municipality=municipality,
            biome=biome,
            category="TI",
        )
        land1.communities.add(community1, community2)

        # Land with 1 community
        land2 = Land.objects.create(
            name="Land 2",
            municipality=municipality,
            biome=biome,
            category="TI",
        )
        land2.communities.add(community1)

        # Land with no communities
        land3 = Land.objects.create(
            name="Land 3",
            municipality=municipality,
            biome=biome,
            category="TI",
        )

        url = reverse("land-list")

        # Filter exact count
        response = api_client.get(url, {"communities_count": 2})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Land 1"

        # Filter minimum count
        response = api_client.get(url, {"communities_count_min": 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

        # Filter maximum count
        response = api_client.get(url, {"communities_count_max": 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_ordering_lands_by_communities_count(self, api_client, municipality, biome):
        """Test ordering lands by communities count."""
        community1 = Community.objects.create(name="Community 1")
        community2 = Community.objects.create(name="Community 2")
        community3 = Community.objects.create(name="Community 3")

        # Create lands with different community counts
        land1 = Land.objects.create(
            name="Land 1",
            municipality=municipality,
            biome=biome,
            category="TI",
        )
        land1.communities.add(community1, community2, community3)

        land2 = Land.objects.create(
            name="Land 2",
            municipality=municipality,
            biome=biome,
            category="TI",
        )
        land2.communities.add(community1)

        land3 = Land.objects.create(
            name="Land 3",
            municipality=municipality,
            biome=biome,
            category="TI",
        )

        url = reverse("land-list")

        # Order by communities_count ascending
        response = api_client.get(url, {"ordering": "communities_count"})
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["communities_count"] == 0
        assert results[1]["communities_count"] == 1
        assert results[2]["communities_count"] == 3

        # Order by communities_count descending
        response = api_client.get(url, {"ordering": "-communities_count"})
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["communities_count"] == 3
        assert results[1]["communities_count"] == 1
        assert results[2]["communities_count"] == 0

    def test_land_read_only(self, api_client, land):
        """Test that land endpoints are read-only."""
        url = reverse("land-list")

        # Test POST
        response = api_client.post(url, {"name": "New Land"})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test PUT
        detail_url = reverse("land-detail", kwargs={"pk": land.id})
        response = api_client.put(detail_url, {"name": "Updated Land"})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test PATCH
        response = api_client.patch(detail_url, {"name": "Updated Land"})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test DELETE
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestCommunityAPI:
    """Tests for Community API endpoints."""

    def test_list_communities(self, api_client, community):
        """Test listing all communities."""
        url = reverse("community-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == community.name

    def test_retrieve_community(self, api_client, community):
        """Test retrieving a specific community."""
        url = reverse("community-detail", kwargs={"pk": community.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == community.name
        assert "slug" not in response.data  # Slug should not be in response

    def test_community_lands_count(self, api_client, community, land):
        """Test that community includes lands count."""
        url = reverse("community-detail", kwargs={"pk": community.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "lands_count" in response.data
        assert response.data["lands_count"] == 1

    def test_filter_community_by_name(self, api_client, community):
        """Test filtering communities by name."""
        url = reverse("community-list")
        response = api_client.get(url, {"name": "Asha"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        response = api_client.get(url, {"name": "NonExistent"})
        assert len(response.data["results"]) == 0

    def test_filter_land_by_location(self, api_client, land):
        """Test filtering lands by location fields."""
        url = reverse("land-list")

        # Test municipality filter
        response = api_client.get(url, {"municipality": "Rio Branco"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        # Test state filter
        response = api_client.get(url, {"state": "Acre"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        # Test country filter
        response = api_client.get(url, {"country": "Brazil"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        # Test country_code filter
        response = api_client.get(url, {"country_code": "BR"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_community(self, api_client, community):
        """Test searching communities."""
        url = reverse("community-list")
        response = api_client.get(url, {"search": "Asha"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_ordering_communities(self, api_client, community):
        """Test ordering communities."""
        # Create another community
        community2 = Community.objects.create(name="Yanomami")

        url = reverse("community-list")
        response = api_client.get(url, {"ordering": "name"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "Ashaninka"
        assert response.data["results"][1]["name"] == "Yanomami"

        # Test reverse ordering
        response = api_client.get(url, {"ordering": "-name"})
        assert response.data["results"][0]["name"] == "Yanomami"
        assert response.data["results"][1]["name"] == "Ashaninka"

    def test_ordering_lands_by_location(self, api_client, land, municipality, biome):
        """Test ordering lands by location fields."""
        # Create another land with different name
        land2 = Land.objects.create(
            name="Aldeia Test",
            municipality=municipality,
            biome=biome,
            category="PI",
        )

        url = reverse("land-list")
        # Order by municipality_name (using annotated field)
        response = api_client.get(url, {"ordering": "municipality_name"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_community_by_lands_count(self, api_client, community, land):
        """Test filtering communities by lands count."""
        # Create another community with no lands
        community2 = Community.objects.create(name="Yanomami")

        url = reverse("community-list")

        # Filter exact count
        response = api_client.get(url, {"lands_count": 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == community.name

        # Filter minimum count
        response = api_client.get(url, {"lands_count_min": 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        # Filter maximum count
        response = api_client.get(url, {"lands_count_max": 0})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == community2.name

    def test_ordering_communities_by_lands_count(self, api_client, municipality, biome):
        """Test ordering communities by lands count."""
        # Create communities with different land counts
        community1 = Community.objects.create(name="Community A")
        community2 = Community.objects.create(name="Community B")
        community3 = Community.objects.create(name="Community C")

        # Create lands with different community associations
        land1 = Land.objects.create(
            name="Land 1",
            municipality=municipality,
            biome=biome,
            category="TI",
        )
        land1.communities.add(community1, community2)

        land2 = Land.objects.create(
            name="Land 2",
            municipality=municipality,
            biome=biome,
            category="TI",
        )
        land2.communities.add(community1)

        url = reverse("community-list")

        # Order by lands_count ascending
        response = api_client.get(url, {"ordering": "lands_count"})
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["lands_count"] == 0  # Community C
        assert results[1]["lands_count"] == 1  # Community B
        assert results[2]["lands_count"] == 2  # Community A

        # Order by lands_count descending
        response = api_client.get(url, {"ordering": "-lands_count"})
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["lands_count"] == 2  # Community A
        assert results[1]["lands_count"] == 1  # Community B
        assert results[2]["lands_count"] == 0  # Community C

    def test_community_read_only(self, api_client, community):
        """Test that community endpoints are read-only."""
        url = reverse("community-list")

        # Test POST
        response = api_client.post(url, {"name": "New Community"})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test PUT
        detail_url = reverse("community-detail", kwargs={"pk": community.id})
        response = api_client.put(detail_url, {"name": "Updated Community"})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test PATCH
        response = api_client.patch(detail_url, {"name": "Updated Community"})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test DELETE
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestAPIPagination:
    """Tests for API pagination."""

    def test_lands_pagination(self, api_client, municipality, biome):
        """Test that lands list is paginated."""
        # Create multiple lands
        for i in range(10):
            Land.objects.create(
                name=f"Land {i}",
                municipality=municipality,
                biome=biome,
                category="TI",
            )

        url = reverse("land-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_communities_pagination(self, api_client):
        """Test that communities list is paginated."""
        # Create multiple communities
        for i in range(10):
            Community.objects.create(name=f"Community {i}")

        url = reverse("community-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data
        assert response.data["count"] == 10
