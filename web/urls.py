from django.urls import path

from .views import (
    HomePageView,
    TripDetailView,
    TripListView,
    BookingSuccessView,
    BookingStatusView,
    BlogListView,
    BlogDetailView,
)

app_name = "web"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("blog/", BlogListView.as_view(), name="blog-list"),
    path("blog/<slug:slug>/", BlogDetailView.as_view(), name="blog-detail"),
    path("trips/", TripListView.as_view(), name="trips"),
    path("trips/<slug:slug>/", TripDetailView.as_view(), name="trip-detail"),
    path("booking/success/", BookingSuccessView.as_view(), name="booking-success"),
    path("booking/status/", BookingStatusView.as_view(), name="booking-status"),
]
