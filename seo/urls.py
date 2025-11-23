from django.urls import path

from .views import SeoDashboardDetailView, SeoDashboardOverviewView

app_name = "seo"

urlpatterns = [
    path("dashboard/", SeoDashboardOverviewView.as_view(), name="dashboard"),
    path("dashboard/<int:pk>/", SeoDashboardDetailView.as_view(), name="dashboard-detail"),
]
