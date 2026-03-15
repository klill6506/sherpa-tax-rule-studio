"""API routes for authority sources: /api/sources/ and related endpoints."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"sources", views.AuthoritySourceViewSet, basename="authoritysource")
router.register(r"topics", views.AuthorityTopicViewSet, basename="authoritytopic")
router.register(r"source-topics", views.AuthoritySourceTopicViewSet, basename="authoritysourcetopic")
router.register(r"form-links", views.AuthorityFormLinkViewSet, basename="authorityformlink")
router.register(r"rule-links", views.RuleAuthorityLinkViewSet, basename="ruleauthoritylink")
router.register(r"conformity", views.JurisdictionConformitySourceViewSet, basename="conformity")
router.register(r"feeds", views.SourceFeedDefinitionViewSet, basename="sourcefeed")

# Nested routes under /api/sources/{source_pk}/
_actions = {"get": "list", "post": "create"}
_detail = {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}

source_children = [
    path("excerpts/", views.AuthorityExcerptViewSet.as_view(_actions), name="source-excerpts-list"),
    path("excerpts/<uuid:pk>/", views.AuthorityExcerptViewSet.as_view(_detail), name="source-excerpts-detail"),
    path("versions/", views.AuthorityVersionViewSet.as_view(_actions), name="source-versions-list"),
    path("versions/<uuid:pk>/", views.AuthorityVersionViewSet.as_view(_detail), name="source-versions-detail"),
    path("versions/<uuid:pk>/mark_current/", views.AuthorityVersionViewSet.as_view({"post": "mark_current"}), name="source-versions-mark-current"),
]

urlpatterns = [
    path("", include(router.urls)),
    path("sources/<uuid:source_pk>/", include(source_children)),
    path("excerpts/search/", views.ExcerptSearchView.as_view(), name="excerpt-search"),
]
