"""API routes for form specifications: /api/forms/ and nested children."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"forms", views.TaxFormViewSet, basename="taxform")
router.register(r"flow-assertions", views.FlowAssertionViewSet, basename="flow-assertion")

# Nested routes under /api/forms/{form_pk}/
_actions = {"get": "list", "post": "create"}
_detail = {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}

form_children = [
    path("facts/", views.FormFactViewSet.as_view(_actions), name="form-facts-list"),
    path("facts/<uuid:pk>/", views.FormFactViewSet.as_view(_detail), name="form-facts-detail"),
    path("rules/", views.FormRuleViewSet.as_view(_actions), name="form-rules-list"),
    path("rules/<uuid:pk>/", views.FormRuleViewSet.as_view(_detail), name="form-rules-detail"),
    path("lines/", views.FormLineViewSet.as_view(_actions), name="form-lines-list"),
    path("lines/<uuid:pk>/", views.FormLineViewSet.as_view(_detail), name="form-lines-detail"),
    path("diagnostics/", views.FormDiagnosticViewSet.as_view(_actions), name="form-diagnostics-list"),
    path("diagnostics/<uuid:pk>/", views.FormDiagnosticViewSet.as_view(_detail), name="form-diagnostics-detail"),
    path("tests/", views.TestScenarioViewSet.as_view(_actions), name="form-tests-list"),
    path("tests/<uuid:pk>/", views.TestScenarioViewSet.as_view(_detail), name="form-tests-detail"),
]

urlpatterns = [
    path("", include(router.urls)),
    # Lookup by form number (must come BEFORE uuid paths)
    path("forms/lookup/<str:form_number>/", views.form_lookup, name="form-lookup"),
    path("forms/lookup/<str:form_number>/export/", views.form_lookup_export, name="form-lookup-export"),
    path("forms/<uuid:form_pk>/", include(form_children)),
]
