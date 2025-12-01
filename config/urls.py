"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from urllib.parse import urlencode

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db.models import Count, Q
from django.urls import include, path, reverse

from web.models import Booking, RewardPhase


def _with_query(url: str, params: dict | None) -> str:
    if not params:
        return url
    query = urlencode(params)
    return f"{url}?{query}"


DASHBOARD_QUICK_LINKS = [
    {
        "label": "Add a destination",
        "description": "Create a new location with hero assets.",
        "url_name": "admin:web_destination_add",
    },
    {
        "label": "Change a booking status",
        "description": "Review requests waiting for confirmation.",
        "url_name": "admin:web_booking_changelist",
        "query": {"status__exact": Booking.Status.RECEIVED},
    },
    {
        "label": "Add a trip",
        "description": "Publish a new itinerary to the site.",
        "url_name": "admin:web_trip_add",
    },
    {
        "label": "Edit trips",
        "description": "Update pricing, content, and itineraries.",
        "url_name": "admin:web_trip_changelist",
    },
    {
        "label": "Add a blog post",
        "description": "Share news, stories, or guides.",
        "url_name": "admin:web_blogpost_add",
    },
    {
        "label": "Edit rewards",
        "description": "Adjust discount tiers and eligibility.",
        "url_name": "admin:web_rewardphase_changelist",
    },
    {
        "label": "Website gallery",
        "description": "Refresh landing imagery and captions.",
        "url_name": "admin:web_landinggalleryimage_changelist",
    },
    {
        "label": "Create staff user",
        "description": "Add a teammate with admin access.",
        "url_name": "admin:auth_user_add",
        "query": {"is_staff": "on"},
    },
]


DASHBOARD_MOST_USED_APPS = [
    {
        "label": "Bookings",
        "description": "Confirm travelers and manage payments.",
        "url_name": "admin:web_booking_changelist",
    },
    {
        "label": "Trips",
        "description": "Inventory, pricing, and itineraries.",
        "url_name": "admin:web_trip_changelist",
    },
    {
        "label": "Destinations",
        "description": "Hero assets and featured placements.",
        "url_name": "admin:web_destination_changelist",
    },
    {
        "label": "Rewards",
        "description": "Discount phases and eligibility.",
        "url_name": "admin:web_rewardphase_changelist",
    },
    {
        "label": "Website content",
        "description": "Blog posts and gallery visuals.",
        "url_name": "admin:web_blogpost_changelist",
    },
]


def _build_quick_links():
    links = []
    for item in DASHBOARD_QUICK_LINKS:
        link = item.copy()
        url_name = link.pop("url_name", None)
        if url_name:
            link["url"] = _with_query(reverse(url_name), link.pop("query", None))
        links.append(link)
    return links


def _build_most_used():
    items = []
    for item in DASHBOARD_MOST_USED_APPS:
        link = item.copy()
        url_name = link.pop("url_name", None)
        if url_name:
            link["url"] = reverse(url_name)
        items.append(link)
    return items


def _build_metric_cards():
    booking_counts = Booking.objects.aggregate(
        received=Count("id", filter=Q(status=Booking.Status.RECEIVED)),
        confirmed=Count("id", filter=Q(status=Booking.Status.CONFIRMED)),
    )
    rewards_url = reverse("admin:web_rewardphase_changelist")
    bookings_url = reverse("admin:web_booking_changelist")
    return [
        {
            "label": "New bookings",
            "value": booking_counts.get("received", 0),
            "description": "Awaiting confirmation",
            "url": _with_query(bookings_url, {"status__exact": Booking.Status.RECEIVED}),
        },
        {
            "label": "Confirmed bookings",
            "value": booking_counts.get("confirmed", 0),
            "description": "Ready for traveler comms",
            "url": _with_query(bookings_url, {"status__exact": Booking.Status.CONFIRMED}),
        },
        {
            "label": "Active rewards",
            "value": RewardPhase.objects.filter(status=RewardPhase.Status.ACTIVE).count(),
            "description": "Live discount phases",
            "url": rewards_url,
        },
    ]


_original_each_context = admin.site.each_context


def custom_each_context(request):
    context = _original_each_context(request)
    context.setdefault("dashboard_metrics", _build_metric_cards())
    context.setdefault("dashboard_quick_links", _build_quick_links())
    context.setdefault("dashboard_most_used", _build_most_used())
    return context


admin.site.each_context = custom_each_context

admin.site.site_header = "Sand & Sky Admin"
admin.site.site_title = "Sand & Sky Admin"
admin.site.index_title = "Control center"
admin.site.index_template = "admin/dashboard.html"
admin.site.enable_nav_sidebar = False

urlpatterns = [
    path("admin/seo/", include("seo.urls", namespace="seo")),
    path("admin/", admin.site.urls),
    path("", include("web.urls", namespace="web")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
