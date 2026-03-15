"""URL configuration for Sherpa Tax Rule Studio."""
from django.contrib import admin
from django.http import HttpResponse
from django.conf import settings
from django.urls import include, path, re_path


def spa_view(request):
    """Serve the React SPA index.html for all non-API routes."""
    index_path = settings.SPA_INDEX
    if index_path.exists():
        return HttpResponse(index_path.read_text(), content_type="text/html")
    if settings.DEBUG:
        return HttpResponse(
            "<h1>Frontend not built</h1>"
            "<p>Run <code>cd client && npm run build</code> or use the Vite dev server.</p>",
            content_type="text/html",
        )
    return HttpResponse("Not found", status=404)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("specs.urls")),
    path("api/", include("sources.urls")),
    # SPA catch-all — must be last
    re_path(r"^(?!api/|admin/|assets/).*$", spa_view),
]
