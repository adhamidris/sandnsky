from django.urls import path
from django.views.generic import TemplateView

from .views import (
    HomePageView,
    DestinationListView,
    TripDetailView,
    TripReviewCreateView,
    TripListView,
    CartCheckoutView,
    CartQuickAddView,
    CartCheckoutSuccessView,
    BookingSuccessView,
    BookingStatusView,
    CartRewardsSummaryView,
    CartRewardsApplyView,
    CartRewardsRemoveView,
    BlogListView,
    BlogDetailView,
)

app_name = "web"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("destinations/", DestinationListView.as_view(), name="destinations"),
    path(
        "booking-terms/",
        TemplateView.as_view(template_name="booking_terms.html"),
        name="booking-terms",
    ),
    path(
        "cancellation-policy/",
        TemplateView.as_view(template_name="cancellation_policy.html"),
        name="cancellation-policy",
    ),
    path(
        "privacy-policy/",
        TemplateView.as_view(template_name="privacy_policy.html"),
        name="privacy-policy",
    ),
    path(
        "health-safety/",
        TemplateView.as_view(template_name="health_safety.html"),
        name="health-safety",
    ),
    path(
        "contact/",
        TemplateView.as_view(template_name="contact.html"),
        name="contact",
    ),
    path(
        "sahari/",
        TemplateView.as_view(template_name="sahari.html"),
        name="sahari",
    ),
    path(
        "about/",
        TemplateView.as_view(template_name="about.html"),
        name="about",
    ),
    path("blog/", BlogListView.as_view(), name="blog-list"),
    path("blog/<slug:slug>/", BlogDetailView.as_view(), name="blog-detail"),
    path("trips/", TripListView.as_view(), name="trips"),
    path(
        "trips/<slug:slug>/reviews/",
        TripReviewCreateView.as_view(),
        name="trip-review-create",
    ),
    path("trips/<slug:slug>/", TripDetailView.as_view(), name="trip-detail"),
    path(
        "booking/cart/add/<slug:slug>/",
        CartQuickAddView.as_view(),
        name="booking-cart-quick-add",
    ),
    path(
        "booking/cart/rewards/",
        CartRewardsSummaryView.as_view(),
        name="booking-cart-rewards",
    ),
    path(
        "booking/cart/rewards/apply/",
        CartRewardsApplyView.as_view(),
        name="booking-cart-rewards-apply",
    ),
    path(
        "booking/cart/rewards/remove/",
        CartRewardsRemoveView.as_view(),
        name="booking-cart-rewards-remove",
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
