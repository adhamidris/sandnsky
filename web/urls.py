from django.urls import path

from .views import HomePageView, TripDetailView, TripListView, BookingSuccessView

app_name = "web"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("trips/", TripListView.as_view(), name="trips"),
    path("trips/<slug:slug>/", TripDetailView.as_view(), name="trip-detail"),
    path("booking/success/", BookingSuccessView.as_view(), name="booking-success"),
]
