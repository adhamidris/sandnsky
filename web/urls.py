from django.urls import path

from .views import (
    HomePageView,
    TripDetailView,
    TripListView,
    CartCheckoutView,
    CartQuickAddView,
    CartCheckoutSuccessView,
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
    path(
        "booking/cart/add/<slug:slug>/",
        CartQuickAddView.as_view(),
        name="booking-cart-quick-add",
    ),
    path("booking/cart/", CartCheckoutView.as_view(), name="booking-cart-checkout"),
    path(
        "booking/cart/success/",
        CartCheckoutSuccessView.as_view(),
        name="booking-cart-success",
    ),
    path("booking/success/", BookingSuccessView.as_view(), name="booking-success"),
    path("booking/status/", BookingStatusView.as_view(), name="booking-status"),
]
