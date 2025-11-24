from django.urls import path
from django.views.generic import TemplateView

from .views import (
    HomePageView,
    DestinationListView,
    DestinationPageView,
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
    SahariPageView,
    StaticSeoTemplateView,
)

app_name = "web"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("destinations/", DestinationListView.as_view(), name="destinations"),
    path("destinations/<slug:slug>/page/", DestinationPageView.as_view(), name="destination-page"),
    path(
        "booking-terms/",
        StaticSeoTemplateView.as_view(
            template_name="booking_terms.html",
            seo_page_code="booking_terms",
        ),
        name="booking-terms",
    ),
    path(
        "cancellation-policy/",
        StaticSeoTemplateView.as_view(
            template_name="cancellation_policy.html",
            seo_page_code="cancellation_policy",
        ),
        name="cancellation-policy",
    ),
    path(
        "privacy-policy/",
        StaticSeoTemplateView.as_view(
            template_name="privacy_policy.html",
            seo_page_code="privacy_policy",
        ),
        name="privacy-policy",
    ),
    path(
        "health-safety/",
        StaticSeoTemplateView.as_view(
            template_name="health_safety.html",
            seo_page_code="health_safety",
        ),
        name="health-safety",
    ),
    path(
        "contact/",
        StaticSeoTemplateView.as_view(
            template_name="contact.html",
            seo_page_code="contact",
        ),
        name="contact",
    ),
    path("sahari/", SahariPageView.as_view(), name="sahari"),
    path(
        "about/",
        StaticSeoTemplateView.as_view(
            template_name="about.html",
            seo_page_code="about",
        ),
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
