from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from app.viewsets import CommunityViewSet, LandViewSet

# API Router
router = DefaultRouter()
router.register(r"lands", LandViewSet, basename="land")
router.register(r"communities", CommunityViewSet, basename="community")

urlpatterns = [
    path("", include("app.urls")),
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/v1/", include(router.urls)),
    # API documentation
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # MCP Server endpoint
    path("", include("mcp_server.urls")),
]

# Debug toolbar (only in development)
if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
