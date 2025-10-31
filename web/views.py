import json
from decimal import Decimal, ROUND_HALF_UP
import datetime as dt
import mimetypes
from urllib.parse import urlencode
from typing import Any, Mapping

from django.contrib import messages
from django.core import signing
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Prefetch, Q, Min, Max, Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.template.loader import render_to_string

from .forms import BookingRequestForm, BookingCartCheckoutForm
from .booking_cart import (
    add_entry,
    build_booking_help_link,
    build_cart_entry,
    clear_cart,
    compute_cart_rewards,
    get_cart,
    get_contact,
    remove_entry,
    remove_trip_entries,
    summarize_cart,
    apply_reward_selection,
    remove_reward_selection,
    update_contact,
)
from .models import (
    BlogCategory,
    BlogPost,
    BlogPostStatus,
    Booking,
    BookingExtra,
    Destination,
    DestinationGalleryImage,
    LandingGalleryImage,
    SiteConfiguration,
    Trip,
    TripCategory,
    TripItineraryDay,
    TripRelation,
    TripExtra,
    TripGalleryImage,
)
from .rewards import (
    RewardComputationError,
    calculate_entry_reward,
    build_entry_snapshot,
    persist_booking_reward,
)


CURRENCY_SYMBOLS = {"USD": "$"}
DEFAULT_CURRENCY = "USD"
BOOKING_REFERENCE_SALT = "booking-success"
BOOKING_REFERENCE_MAX_AGE = 60 * 60 * 24 * 14  # 14 days
BOOKING_CART_REFERENCE_SALT = "booking-cart-success"
BOOKING_CART_REFERENCE_MAX_AGE = BOOKING_REFERENCE_MAX_AGE


def format_currency(amount, currency=DEFAULT_CURRENCY):
    if amount is None:
        amount = Decimal("0")
    elif not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    rounded = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    symbol = CURRENCY_SYMBOLS.get(currency.upper(), "")
    formatted = f"{rounded:,.0f}"
    if symbol:
        return f"{symbol}{formatted}"
    return f"{formatted} {currency.upper()}"


def duration_label(days):
    days = int(days)
    return f"{days} day{'s' if days != 1 else ''}"


def traveler_summary(adults, children, infants, per_person_label=""):
    parts = []

    def append_part(count, label):
        if count > 0:
            suffix = "s" if count != 1 else ""
            parts.append(f"{count} {label}{suffix}")

    append_part(adults, "adult")
    append_part(children, "child")
    append_part(infants, "infant")

    if not parts:
        parts.append("0 travelers")

    if per_person_label:
        parts.append(per_person_label)

    return " · ".join(parts)


def _all_destination_names(trip):
    names = []
    if trip.destination_id and trip.destination.name not in names:
        names.append(trip.destination.name)
    for destination in trip.additional_destinations.all():
        if destination.name not in names:
            names.append(destination.name)
    return names


def _destination_hero_context(destination):
    if not destination:
        return None
    title = destination.name
    subtitle = destination.hero_subtitle.strip() if destination.hero_subtitle else ""
    return {
        "title": title,
        "subtitle": subtitle,
        "image_url": destination.hero_image.url if destination.hero_image else "",
    }


def _serialize_gallery_images(images):
    gallery = []
    for item in images:
        file_field = getattr(item, "image", None)
        if not file_field:
            continue
        width = getattr(file_field, "width", None)
        height = getattr(file_field, "height", None)
        is_landscape = False
        if width and height:
            try:
                is_landscape = (width / height) >= 1.6
            except (TypeError, ZeroDivisionError):
                is_landscape = False
        gallery.append(
            {
                "image_url": file_field.url,
                "caption": getattr(item, "caption", ""),
                "is_landscape": is_landscape,
            }
        )
    return gallery


def _destination_gallery_context(destination):
    if not destination:
        return []
    return _serialize_gallery_images(destination.gallery_images.all())


def _trip_gallery_context(trip):
    if not trip:
        return []
    return _serialize_gallery_images(trip.gallery_images.all())


def load_booking_from_token(token, *, max_age=BOOKING_REFERENCE_MAX_AGE):
    if not token:
        raise Http404("Booking reference not provided.")
    try:
        booking_id = signing.loads(
            token,
            salt=BOOKING_REFERENCE_SALT,
            max_age=max_age,
        )
    except (signing.BadSignature, signing.SignatureExpired):
        raise Http404("Booking reference invalid.")

    queryset = (
        Booking.objects.select_related("trip", "trip__destination")
        .prefetch_related(
            "trip__additional_destinations",
            "booking_extras__extra",
            "rewards__reward_phase",
        )
    )
    return get_object_or_404(queryset, pk=booking_id)


def load_cart_bookings_from_token(token, *, max_age=BOOKING_CART_REFERENCE_MAX_AGE):
    if not token:
        raise Http404("Booking reference not provided.")

    try:
        payload = signing.loads(
            token,
            salt=BOOKING_CART_REFERENCE_SALT,
            max_age=max_age,
        )
    except (signing.BadSignature, signing.SignatureExpired):
        raise Http404("Booking reference invalid.")

    contact_info = {}
    if isinstance(payload, dict):
        booking_ids = payload.get("bookings", [])
        raw_contact = payload.get("contact", {})
        if isinstance(raw_contact, dict):
            contact_info = {
                key: value for key, value in raw_contact.items() if isinstance(value, str)
            }
    else:
        booking_ids = payload

    if not isinstance(booking_ids, (list, tuple)) or not booking_ids:
        raise Http404("Booking reference invalid.")

    queryset = (
        Booking.objects.select_related("trip", "trip__destination")
        .prefetch_related(
            "trip__additional_destinations",
            "booking_extras__extra",
            "rewards__reward_phase",
        )
        .filter(pk__in=booking_ids)
    )

    bookings_map = {booking.pk: booking for booking in queryset}
    ordered_bookings = [bookings_map.get(int(pk)) for pk in booking_ids]
    ordered_bookings = [booking for booking in ordered_bookings if booking]

    if not ordered_bookings:
        raise Http404("Booking reference invalid.")

    return ordered_bookings, contact_info


def build_trip_card(trip):
    primary_category = next((category.name for category in trip.category_tags.all()), "")
    image_url = trip.card_image.url if trip.card_image else ""
    destination_names = _all_destination_names(trip)
    languages = [language.code.upper() for language in trip.languages.all() if language.code]
    if not destination_names:
        destinations_label = ""
    elif len(destination_names) == 1:
        destinations_label = destination_names[0]
    else:
        destinations_label = f"{destination_names[0]} +{len(destination_names) - 1}"
    child_price = trip.get_child_price_per_person()
    has_child_price = child_price != trip.base_price_per_person
    return {
        "slug": trip.slug,
        "title": trip.title,
        "description": trip.teaser,
        "image_url": image_url,
        "category": primary_category,
        "duration": duration_label(trip.duration_days),
        "group_size": f"Up to {trip.group_size_max} guests",
        "location": destinations_label,
        "price": format_currency(trip.base_price_per_person),
        "child_price": format_currency(child_price) if has_child_price else "",
        "has_child_price": has_child_price,
        "languages": languages,
    }


def build_service_option(trip):
    image_url = trip.card_image.url if trip.card_image else ""
    child_price = trip.get_child_price_per_person()
    has_child_price = child_price != trip.base_price_per_person
    return {
        "id": trip.pk,
        "slug": trip.slug,
        "title": trip.title,
        "description": trip.teaser,
        "image_url": image_url,
        "price": format_currency(trip.base_price_per_person),
        "child_price": format_currency(child_price) if has_child_price else "",
        "has_child_price": has_child_price,
    }


QUICK_ADD_SERVICES_LIMIT = 6
QUICK_ADD_RECOMMENDATION_LIMIT = 6


def extract_cart_trip_ids(summary):
    trip_ids = set()
    entries = summary.get("entries", []) if isinstance(summary, Mapping) else []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        trip_id = entry.get("trip_id")
        if trip_id is None:
            continue
        try:
            trip_ids.add(int(trip_id))
        except (TypeError, ValueError):
            continue
    return trip_ids


def list_quick_add_services(exclude_trip_ids, limit=QUICK_ADD_SERVICES_LIMIT):
    queryset = (
        Trip.objects.filter(is_service=True)
        .exclude(pk__in=exclude_trip_ids)
        .select_related("destination")
        .prefetch_related("category_tags", "additional_destinations", "languages")
        .order_by("title")
    )
    services = []
    for trip in queryset[:limit]:
        services.append(build_service_option(trip))
    return services


def list_quick_add_recommendations(cart_trip_ids, limit=QUICK_ADD_RECOMMENDATION_LIMIT):
    seen_trip_ids = set(cart_trip_ids or [])
    cards = []

    if cart_trip_ids:
        relations = (
            TripRelation.objects.filter(from_trip__in=cart_trip_ids)
            .select_related("to_trip", "to_trip__destination")
            .prefetch_related(
                "to_trip__category_tags",
                "to_trip__additional_destinations",
                "to_trip__languages",
            )
            .order_by("position", "id")
        )
        for relation in relations:
            trip = relation.to_trip
            if not trip or trip.pk in seen_trip_ids or trip.is_service:
                continue
            cards.append(build_trip_card(trip))
            seen_trip_ids.add(trip.pk)
            if len(cards) >= limit:
                break

    if len(cards) < limit:
        remaining = limit - len(cards)
        fallback_queryset = (
            Trip.objects.filter(is_service=False)
            .exclude(pk__in=seen_trip_ids)
            .select_related("destination")
            .prefetch_related("category_tags", "additional_destinations", "languages")
            .order_by("-created_at")[:remaining]
        )
        for trip in fallback_queryset:
            cards.append(build_trip_card(trip))
            seen_trip_ids.add(trip.pk)
            if len(cards) >= limit:
                break

    return cards


def contact_actions():
    return [
        {
            "label": "WhatsApp",
            "href": "https://wa.me/201234567890",
            "icon": "whatsapp",
            "aria": "Chat with us on WhatsApp",
        },
        {
            "label": "Call",
            "href": "tel:+201234567890",
            "icon": "phone",
            "aria": "Call Nile Dreams",
        },
        {
            "label": "Email",
            "href": "mailto:info@niledreams.com",
            "icon": "mail",
            "aria": "Email Nile Dreams",
        },
    ]


def _split_paragraphs(text):
    if not text:
        return []
    return [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]


def build_blog_card(post):
    image_field = post.card_image or post.hero_image
    image_url = image_field.url if image_field else ""
    return {
        "title": post.title,
        "subtitle": post.subtitle,
        "category": post.category.name if post.category_id else "",
        "image_url": image_url,
        "excerpt": post.excerpt,
        "url": post.get_absolute_url(),
        "cta_label": "Read more",
    }


def published_blog_queryset():
    now = timezone.now()
    return (
        BlogPost.objects.select_related("category")
        .filter(status=BlogPostStatus.PUBLISHED, published_at__lte=now)
    )


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_config = SiteConfiguration.get_solo()
        fallback_image = ""
        fallback_image_is_media = False
        if site_config.hero_image:
            fallback_image = site_config.hero_image.url
            fallback_image_is_media = True

        fallback_video = site_config.hero_video.url if site_config.hero_video else ""
        fallback_video_is_media = bool(site_config.hero_video)
        fallback_video_type = ""
        if site_config.hero_video:
            fallback_video_type, _ = mimetypes.guess_type(site_config.hero_video.name)

        hero_pairs = list(site_config.hero_pairs.all())

        background_image = fallback_image
        background_image_is_media = fallback_image_is_media
        background_video = fallback_video
        background_video_is_media = fallback_video_is_media
        background_video_type = fallback_video_type or "video/mp4"

        overlays: list[dict[str, str | int | bool]] = []

        for pair in hero_pairs:
            if pair.hero_image and not background_image:
                background_image = pair.hero_image.url
                background_image_is_media = True

            if pair.hero_video and not background_video:
                background_video = pair.hero_video.url
                background_video_is_media = True
                guessed_type, _ = mimetypes.guess_type(pair.hero_video.name)
                if guessed_type:
                    background_video_type = guessed_type

            overlay_image = ""
            overlay_is_media = False
            if pair.overlay_image:
                overlay_image = pair.overlay_image.url
                overlay_is_media = True
            elif pair.hero_image:
                overlay_image = pair.hero_image.url
                overlay_is_media = True

            if overlay_image:
                overlays.append(
                    {
                        "id": pair.pk,
                        "label": pair.label,
                        "image": overlay_image,
                        "image_is_media": overlay_is_media,
                        "alt": pair.overlay_alt,
                    }
                )

        if not overlays and background_image:
            overlays.append(
                {
                    "id": None,
                    "label": "",
                    "image": background_image,
                    "image_is_media": background_image_is_media,
                    "alt": "",
                }
            )

        context["hero"] = {
            "title": site_config.hero_title,
            "subtitle": site_config.hero_subtitle,
            "primary_cta": {
                "label": site_config.hero_primary_cta_label,
                "href": site_config.hero_primary_cta_href,
            },
            "secondary_cta": {
                "label": site_config.hero_secondary_cta_label,
                "href": site_config.hero_secondary_cta_href,
            },
            "background": {
                "image": background_image,
                "image_is_media": background_image_is_media,
                "video": background_video,
                "video_is_media": background_video_is_media,
                "video_type": background_video_type or "video/mp4",
            },
            "overlays": overlays,
            "has_overlay": bool(overlays),
            "overlay_interval": 6000,
        }

        context["destinations_section"] = {
            "title": "Featured Destinations",
            "subtitle": "Explore the most captivating experiences Egypt has to offer",
            "items": self._featured_destinations(),
        }
        context["trip_picks_section"] = self._trip_picks_section()

        gallery_items = self._gallery_items()
        primary_row = gallery_items[::2]
        secondary_row = gallery_items[1::2]
        gallery_rows = [primary_row]
        if secondary_row:
            gallery_rows.append(secondary_row)

        gallery_background = ""
        gallery_background_is_media = False
        if site_config.gallery_background_image:
            gallery_background = site_config.gallery_background_image.url
            gallery_background_is_media = True

        context["gallery_section"] = {
            "title": "Moments from the Sahara",
            "subtitle": "A glimpse into the landscapes and quiet rituals that shape our journeys.",
            "items": gallery_items,
            "rows": gallery_rows,
            "background_image": gallery_background,
            "background_image_is_media": gallery_background_is_media,
        }

        features = [
            {
                "badge": "EG",
                "icon": "expert-guides",
                "title": "Expert guides",
                "description": "Licensed Egyptologists and desert naturalists reveal stories beneath the dunes.",
            },
            {
                "badge": "SS",
                "icon": "licensed-operators",
                "title": "Licensed tour operators",
                "description": "Every expedition is fully permitted and supported by veteran Sahara operators.",
            },
            {
                "badge": "PS",
                "icon": "personalized-service",
                "title": "Personalized service",
                "description": "We tailor each itinerary to your pace, passions, and preferred level of adventure.",
            },
            {
                "badge": "SG",
                "icon": "comfort",
                "title": "Sleep & travel in comfort",
                "description": "Private camps, boutique lodges, and plush transfers keep every desert mile effortless.",
            },
        ]

        context["about_section"] = {
            "title": "About Sand & Sky",
            "subtitle": (
                "Sand & Sky is a boutique travel agency devoted exclusively to the magic of the Egyptian "
                "Sahara. We craft immersive journeys that capture the soul of Egypt's most breathtaking desert "
                "landscapes - from the tranquil oases of Siwa, Fayoum, Bahariya, and Farafra to the surreal beauty "
                "of the White and Black Deserts."
            ),
        }

        context["features_section"] = {
            "title": "Why travel with Sand & Sky",
            "subtitle": "Four promises that guide every journey we design.",
            "features": features,
        }

        context["contact_section"] = {
            "title": "Start Your Journey",
            "subtitle": "Ready to explore Egypt? Get in touch with our travel experts and we'll help create your perfect adventure.",
            "channels": [
                {
                    "badge": "@",
                    "title": "Email Us",
                    "value": "info@niledreams.com",
                },
                {
                    "badge": "+",
                    "title": "Call Us",
                    "value": "+20 123 456 7890",
                },
                {
                    "badge": "LV",
                    "title": "Visit Us",
                    "value": "Cairo, Egypt",
                },
            ],
            "form": {"action": "#"},
        }

        context["blog_section"] = {
            "title": "From the Journal",
            "subtitle": "Insights from our travel curators to help shape your next desert escape.",
            "items": self._recent_blog_posts(),
        }

        return context

    def _featured_destinations(self):
        featured = (
            Destination.objects.filter(is_featured=True)
            .order_by("featured_position", "name")
            .only("name", "description", "card_image", "slug", "tagline")
        )

        items = []
        for destination in featured:
            cta_href = destination.get_absolute_url()
            items.append(
                {
                    "title": destination.tagline or destination.name,
                    "description": destination.description,
                    "image_url": destination.card_image.url if destination.card_image else "",
                    "cta": {"label": destination.cta_label, "href": cta_href},
                }
        )
        return items

    def _trip_picks_section(self):
        base_queryset = (
            Trip.objects.filter(is_service=False)
            .select_related("destination")
            .prefetch_related("category_tags", "additional_destinations", "languages")
        )

        limit_per_toggle = 9
        cart_summary = summarize_cart(self.request.session)
        cart_trip_slugs = {
            entry.get("trip_slug")
            for entry in cart_summary.get("entries", [])
            if entry.get("trip_slug")
        }
        toggles_config = [
            (
                "recommended",
                "Recommended",
                base_queryset.order_by("-created_at"),
            ),
            (
                "one-day",
                "1Day Tours",
                base_queryset.filter(duration_days=1).order_by("title"),
            ),
            (
                "multi-day",
                "Multi-Days Tours",
                base_queryset.filter(duration_days__gte=2).order_by(
                    "duration_days", "title"
                ),
            ),
            (
                "luxury",
                "Luxury Tours",
                base_queryset.filter(category_tags__slug="luxury")
                .distinct()
                .order_by("-base_price_per_person"),
            ),
        ]

        toggles = []
        seen_slugs = set()
        for slug, label, queryset in toggles_config:
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            trips = [
                {
                    **build_trip_card(trip),
                    "in_cart": trip.slug in cart_trip_slugs,
                }
                for trip in queryset[:limit_per_toggle]
            ]
            toggles.append(
                {
                    "slug": slug,
                    "label": label,
                    "cards": trips,
                }
            )

        return {
            "eyebrow": "Trips",
            "title": "Our Picks for Every Kind of Traveler",
            "subtitle": (
                "Switch between curated collections to find the perfect rhythm—from quick escapes to indulgent journeys."
            ),
            "toggles": toggles,
            "view_all_href": reverse("web:trips"),
        }

    def _recent_blog_posts(self):
        posts = published_blog_queryset().order_by("-published_at", "-created_at")[:3]
        return [build_blog_card(post) for post in posts]

    def _gallery_items(self):
        landing_images = (
            LandingGalleryImage.objects.filter(is_active=True)
            .order_by("position", "id")[:12]
        )

        items = []
        for image in landing_images:
            if not image.image:
                continue
            alt_text = image.alt_text or image.title or image.caption or "Gallery image"
            items.append(
                {
                    "image_url": image.image.url,
                    "alt": alt_text,
                    "title": image.title or image.caption or "",
                    "destination": image.title or image.caption or "",
                    "caption": image.caption or "",
                }
            )

        if items:
            return items

        fallback = (
            DestinationGalleryImage.objects.select_related("destination")
            .order_by("position", "id")[:12]
        )

        for image in fallback:
            if not image.image:
                continue
            items.append(
                {
                    "image_url": image.image.url,
                    "alt": image.caption or f"{image.destination.name} gallery image",
                    "title": image.destination.name,
                    "destination": image.destination.name,
                    "caption": image.caption or "",
                }
            )
        return items


class BlogListView(TemplateView):
    template_name = "blog_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.request.GET.get("category") or ""
        posts = self._published_posts()

        selected_category = None
        if category_slug:
            selected_category = get_object_or_404(BlogCategory, slug=category_slug)
            posts = posts.filter(category=selected_category)

        selected_category_info = None
        if selected_category:
            selected_category_info = {
                "name": selected_category.name,
                "slug": selected_category.slug,
            }

        context.update(
            posts=[build_blog_card(post) for post in posts],
            categories=self._category_options(),
            selected_category=selected_category_info,
        )
        return context

    def _published_posts(self):
        return published_blog_queryset().order_by("-published_at", "-created_at")

    def _category_options(self):
        now = timezone.now()
        categories = (
            BlogCategory.objects.filter(
                posts__status=BlogPostStatus.PUBLISHED,
                posts__published_at__lte=now,
            )
            .annotate(post_count=Count("posts", distinct=True))
            .order_by("name")
        )
        return [
            {
                "name": category.name,
                "slug": category.slug,
                "post_count": category.post_count,
            }
            for category in categories
        ]


class BlogDetailView(TemplateView):
    template_name = "blog_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_post()
        context.update(
            post=self._serialize_post(post),
            related_posts=self._related_posts(post),
            recommended_trips=self._recommended_trips(),
        )
        return context

    def get_post(self):
        if not hasattr(self, "_post"):
            queryset = published_blog_queryset().prefetch_related("sections")
            self._post = get_object_or_404(queryset, slug=self.kwargs.get("slug"))
        return self._post

    def _serialize_post(self, post):
        hero_image_url = post.hero_image.url if post.hero_image else ""
        card_image_url = post.card_image.url if post.card_image else ""
        sections = [
            {
                "heading": section.heading,
                "location": section.location_label,
                "body_paragraphs": _split_paragraphs(section.body),
                "image_url": section.section_image.url if section.section_image else "",
            }
            for section in post.sections.all()
        ]
        return {
            "title": post.title,
            "subtitle": post.subtitle,
            "category": post.category.name if post.category_id else "",
            "published_at": post.published_at,
            "read_time_minutes": post.read_time_minutes,
            "hero_image_url": hero_image_url,
            "card_image_url": card_image_url,
            "excerpt": post.excerpt,
            "intro_paragraphs": _split_paragraphs(post.intro),
            "sections": sections,
        }

    def _related_posts(self, post):
        related = (
            published_blog_queryset()
            .exclude(pk=post.pk)
            .order_by("-published_at", "-created_at")[:3]
        )
        return [build_blog_card(item) for item in related]

    def _recommended_trips(self):
        trips = (
            Trip.objects.select_related("destination")
            .prefetch_related("category_tags", "additional_destinations", "languages")
            .order_by("-created_at")[:3]
        )
        return [build_trip_card(trip) for trip in trips]


class TripListView(TemplateView):
    template_name = "trips.html"

    DURATION_BUCKETS = [
        {"value": "1-3", "label": "1 – 3 days", "min": 1, "max": 3},
        {"value": "4-7", "label": "4 – 7 days", "min": 4, "max": 7},
        {"value": "8-10", "label": "8 – 10 days", "min": 8, "max": 10},
        {"value": "11+", "label": "11+ days", "min": 11, "max": None},
    ]

    GROUP_SIZE_BUCKETS = [
        {"value": "small", "label": "Up to 8 guests", "max": 8},
        {"value": "medium", "label": "9 – 16 guests", "min": 9, "max": 16},
        {"value": "large", "label": "17+ guests", "min": 17, "max": None},
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_config = SiteConfiguration.get_solo()
        destination_slug = self.request.GET.get("destination")
        trips = self._base_queryset()

        selected_destination = None
        destination_hero = None
        if destination_slug:
            selected_destination = get_object_or_404(
                Destination.objects.prefetch_related("gallery_images"),
                slug=destination_slug,
            )
            trips = trips.filter(
                Q(destination=selected_destination)
                | Q(additional_destinations=selected_destination)
            ).distinct()
            destination_hero = _destination_hero_context(selected_destination)

        filter_values = self._extract_filter_values()
        trips = self._apply_filters(trips, filter_values)

        paginator = Paginator(trips, 10)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        filter_query_params = [
            (key, value)
            for key in self.request.GET
            for value in self.request.GET.getlist(key)
            if key != "page"
        ]
        query_string = urlencode(filter_query_params, doseq=True)
        page_query_prefix = f"{query_string}&" if query_string else ""

        cart_summary = summarize_cart(self.request.session)
        cart_trip_slugs = {
            entry.get("trip_slug")
            for entry in cart_summary.get("entries", [])
            if entry.get("trip_slug")
        }

        context["trips"] = [
            {
                **build_trip_card(trip),
                "in_cart": trip.slug in cart_trip_slugs,
            }
            for trip in page_obj.object_list
        ]
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["is_paginated"] = page_obj.has_other_pages()
        context["page_query_prefix"] = page_query_prefix
        context["total_trip_count"] = paginator.count
        context["cart_trip_slugs"] = cart_trip_slugs
        context["selected_destination"] = selected_destination
        context["destination_hero"] = destination_hero
        context["contact_actions"] = contact_actions()
        context["destination_gallery"] = _destination_gallery_context(selected_destination)
        context["filter_options"] = self._filter_options(selected_destination)
        context["active_filters"] = filter_values
        context["default_trips_hero_image"] = (
            site_config.trips_hero_image.url if site_config.trips_hero_image else ""
        )
        return context

    def _base_queryset(self):
        return (
            Trip.objects.select_related("destination")
            .prefetch_related("category_tags", "additional_destinations", "languages")
            .order_by("title")
        )

    def _extract_filter_values(self):
        params = self.request.GET

        def parse_decimal(value):
            if value in {None, ""}:
                return None
            try:
                return Decimal(value)
            except (ArithmeticError, ValueError):
                return None

        def parse_int(value):
            if value in {None, ""}:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        duration_choices = {bucket["value"] for bucket in self.DURATION_BUCKETS}
        group_choices = {bucket["value"] for bucket in self.GROUP_SIZE_BUCKETS}

        return {
            "search": (params.get("search") or "").strip(),
            "destination": params.get("destination", ""),
            "price_min": parse_decimal(params.get("price_min")),
            "price_max": parse_decimal(params.get("price_max")),
            "duration_ranges": [
                value
                for value in params.getlist("duration")
                if value in duration_choices
            ],
            "categories": [
                value
                for value in params.getlist("category")
                if value
            ],
            "group_sizes": [
                value
                for value in params.getlist("group_size")
                if value in group_choices
            ],
        }

    def _apply_filters(self, queryset, filters):
        needs_distinct = False
        price_min = filters.get("price_min")
        price_max = filters.get("price_max")
        if price_min is not None:
            queryset = queryset.filter(base_price_per_person__gte=price_min)
        if price_max is not None:
            queryset = queryset.filter(base_price_per_person__lte=price_max)

        durations = filters.get("duration_ranges", [])
        if durations:
            duration_q = Q()
            for bucket in self.DURATION_BUCKETS:
                if bucket["value"] in durations:
                    min_days = bucket["min"]
                    max_days = bucket["max"]
                    condition = Q(duration_days__gte=min_days)
                    if max_days is not None:
                        condition &= Q(duration_days__lte=max_days)
                    duration_q |= condition
            queryset = queryset.filter(duration_q)

        categories = filters.get("categories", [])
        if categories:
            queryset = queryset.filter(category_tags__slug__in=categories)
            needs_distinct = True

        group_sizes = filters.get("group_sizes", [])
        if group_sizes:
            group_q = Q()
            for bucket in self.GROUP_SIZE_BUCKETS:
                if bucket["value"] in group_sizes:
                    min_size = bucket.get("min", 0)
                    max_size = bucket.get("max")
                    condition = Q(group_size_max__gte=min_size)
                    if max_size is not None:
                        condition &= Q(group_size_max__lte=max_size)
                    group_q |= condition
            queryset = queryset.filter(group_q)

        search = filters.get("search")
        if search:
            terms = [term for term in search.split() if term]
            for term in terms:
                term_condition = (
                    Q(title__icontains=term)
                    | Q(teaser__icontains=term)
                    | Q(destination__name__icontains=term)
                    | Q(additional_destinations__name__icontains=term)
                    | Q(category_tags__name__icontains=term)
                )
                queryset = queryset.filter(term_condition)
            if terms:
                needs_distinct = True

        if needs_distinct:
            queryset = queryset.distinct()

        return queryset

    def _filter_options(self, selected_destination):
        trips = self._base_queryset()
        if selected_destination:
            trips = trips.filter(
                Q(destination=selected_destination)
                | Q(additional_destinations=selected_destination)
            ).distinct()

        price_bounds = trips.aggregate(
            min_price=Min("base_price_per_person"),
            max_price=Max("base_price_per_person"),
        )

        destinations = (
            Destination.objects.filter(Q(trips__isnull=False) | Q(additional_trips__isnull=False))
            .distinct()
            .order_by("name")
        )
        categories = (
            TripCategory.objects.filter(trips__isnull=False)
            .distinct()
            .order_by("name")
        )

        return {
            "destinations": [
                {"slug": destination.slug, "name": destination.name}
                for destination in destinations
            ],
            "categories": [
                {"slug": category.slug, "name": category.name}
                for category in categories
            ],
            "price": {
                "min": price_bounds.get("min_price") or Decimal("0"),
                "max": price_bounds.get("max_price") or Decimal("0"),
            },
            "durations": self.DURATION_BUCKETS,
            "group_sizes": self.GROUP_SIZE_BUCKETS,
        }


class TripDetailView(TemplateView):
    template_name = "trip_detail.html"

    def get_trip_queryset(self):
        return (
            Trip.objects.select_related("destination", "about")
            .prefetch_related(
                "additional_destinations",
                "languages",
                "category_tags",
                "highlights",
                "inclusions",
                "exclusions",
                "faqs",
                "extras",
                "reviews",
                Prefetch(
                    "itinerary_days",
                    queryset=TripItineraryDay.objects.order_by("day_number").prefetch_related("steps"),
                ),
                Prefetch(
                    "related_to",
                    queryset=TripRelation.objects.select_related("to_trip__destination")
                    .prefetch_related("to_trip__category_tags", "to_trip__additional_destinations")
                    .order_by("position", "id"),
                ),
                Prefetch(
                    "gallery_images",
                    queryset=TripGalleryImage.objects.order_by("position", "id"),
                ),
            )
        )

    def get_trip(self):
        if not hasattr(self, "_trip"):
            self._trip = get_object_or_404(
                self.get_trip_queryset(), slug=self.kwargs.get("slug")
            )
        return self._trip

    def get_form(self, data=None, *, require_contact=True):
        trip = self.get_trip()
        extra_choices = [
            (str(extra.pk), extra.name)
            for extra in trip.extras.order_by("position", "id")
        ]
        if data is not None:
            initial = None
        else:
            initial = {"date": timezone.localdate()}
            contact_initial = get_contact(self.request.session)
            for field in ("name", "email", "phone"):
                value = contact_initial.get(field)
                if value:
                    initial[field] = value
        return BookingRequestForm(
            data=data,
            initial=initial,
            extra_choices=extra_choices,
            require_contact=require_contact,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or self.get_form()
        trip = self.get_trip()

        pricing = self._pricing_context(trip, form)
        other_trips = self._serialize_related_trips(trip)
        trip_context = self._serialize_trip(trip, other_trips)
        trip_context["extras"] = pricing["extras"]

        context.update(
            trip=trip_context,
            form=form,
            pricing={k: v for k, v in pricing.items() if k != "extras"},
            other_trips=other_trips,
        )

        try:
            cart_summary = summarize_cart(self.request.session)
        except Exception:  # pragma: no cover - defensive
            cart_summary = {"entries": [], "count": 0}

        trip_in_cart = any(
            entry.get("trip_slug") == trip.slug
            for entry in cart_summary.get("entries", [])
        )

        cart_count = cart_summary.get("count", 0)
        other_cart_count = cart_count - 1 if trip_in_cart and cart_count else cart_count

        context.update(
            trip_in_cart=trip_in_cart,
            trip_cart_count=cart_count,
            trip_cart_other_count=max(other_cart_count, 0),
        )
        return context

    def post(self, request, *args, **kwargs):
        trip = self.get_trip()
        action = request.POST.get("action") or "book_only"

        if action == "add_to_list":
            form = self.get_form(request.POST, require_contact=False)
            if form.is_valid():
                remove_trip_entries(request.session, trip.pk)
                entry = build_cart_entry(trip, form.cleaned_data)
                add_entry(request.session, entry, contact={})
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in (request.headers.get("Accept") or ""):
                    summary = summarize_cart(request.session)
                    cart_label = (
                        "No trips yet"
                        if summary["count"] == 0
                        else f"{summary['count']} trip{'s' if summary['count'] != 1 else ''}"
                    )
                    panel_html = render_to_string(
                        "includes/navigation_cart_panel.html",
                        {
                            "booking_cart_entries": summary["entries"],
                            "booking_cart_currency": summary["currency"],
                            "booking_cart_total_display": summary["total_display"],
                            "booking_cart_help_link": build_booking_help_link(summary["entries"]),
                        },
                        request=request,
                    )
                    toast_message = (
                        "Trip removed from list"
                        if summary["count"] == 0
                        else f"Trip added. {summary['count']} trip{'s' if summary['count'] != 1 else ''} saved."
                    )
                    return JsonResponse(
                        {
                            "in_cart": True,
                            "cart_count": summary["count"],
                            "cart_label": cart_label,
                            "panel_html": panel_html,
                            "toast_message": toast_message,
                        }
                    )
                return redirect(reverse("web:trips"))

            return self.render_to_response(self.get_context_data(form=form))

        form = self.get_form(request.POST, require_contact=True)
        if form.is_valid():
            contact_details = {
                key: form.cleaned_data.get(key, "")
                for key in ("name", "email", "phone")
            }
            remove_trip_entries(request.session, trip.pk)
            entry = build_cart_entry(trip, form.cleaned_data)
            add_entry(request.session, entry, contact=contact_details)
            return redirect(reverse("web:booking-cart-checkout"))

        return self.render_to_response(self.get_context_data(form=form))

    def _pricing_context(self, trip, form):
        currency = getattr(trip, "currency", DEFAULT_CURRENCY)
        adult_price = trip.base_price_per_person
        child_price = trip.get_child_price_per_person()

        def extract_int(field_name, fallback):
            value = form[field_name].value()
            try:
                return max(int(value), 0)
            except (TypeError, ValueError):
                return fallback

        adults = max(extract_int("adults", form.fields["adults"].initial), 1)
        children = extract_int("children", form.fields["children"].initial)
        infants = extract_int("infants", form.fields["infants"].initial)

        billed_traveler_count = max(adults + children, 1)
        adult_total = adult_price * Decimal(adults)
        child_total = child_price * Decimal(children)
        base_total = adult_total + child_total

        selected_extra_ids = {
            int(value)
            for value in (form["extras"].value() or [])
            if value not in {None, ""}
        }

        extras_total = Decimal("0")
        extras_with_state = []
        for extra in trip.extras.order_by("position", "id"):
            selected = extra.pk in selected_extra_ids
            if selected:
                extras_total += extra.price
            extras_with_state.append(
                {
                    "id": extra.pk,
                    "label": extra.name,
                    "price": extra.price,
                    "selected": selected,
                    "price_display": format_currency(extra.price, currency),
                }
            )

        total = base_total + extras_total

        if billed_traveler_count:
            per_person_total = total / billed_traveler_count
            per_traveler_phrase = f"{format_currency(per_person_total, currency)} per paying traveler"
        else:
            per_person_total = Decimal("0")
            per_traveler_phrase = ""

        traveler_summary_display = traveler_summary(
            adults, children, infants, per_traveler_phrase
        )

        return {
            "currency": currency,
            "currency_symbol": CURRENCY_SYMBOLS.get(currency.upper(), ""),
            "base_price": adult_price,
            "base_price_display": format_currency(adult_price, currency),
            "adult_price": adult_price,
            "adult_price_display": format_currency(adult_price, currency),
            "child_price": child_price,
            "child_price_display": format_currency(child_price, currency),
            "has_child_price": child_price != adult_price,
            "traveler_count": billed_traveler_count,
            "billed_traveler_count": billed_traveler_count,
            "adults": adults,
            "children": children,
            "infants": infants,
            "adult_total": adult_total,
            "adult_total_display": format_currency(adult_total, currency),
            "child_total": child_total,
            "child_total_display": format_currency(child_total, currency),
            "base_total": base_total,
            "base_total_display": format_currency(base_total, currency),
            "extras_total": extras_total,
            "extras_total_display": format_currency(extras_total, currency),
            "total": total,
            "total_display": format_currency(total, currency),
            "per_person_total": per_person_total,
            "per_person_display": format_currency(per_person_total, currency),
            "traveler_summary_display": traveler_summary_display,
            "extras": extras_with_state,
        }


    def _serialize_trip(self, trip, other_trips):
        languages_label = self._languages_label(trip)
        highlights = [highlight.text for highlight in trip.highlights.all()]
        overview_paragraphs = self._overview_paragraphs(trip)
        itinerary_days = self._serialize_itinerary_days(trip)
        included = [item.text for item in trip.inclusions.all()]
        excluded = [item.text for item in trip.exclusions.all()]
        faqs = [
            {"question": faq.question, "answer": faq.answer}
            for faq in trip.faqs.all()
        ]
        reviews = list(trip.reviews.all())
        review_summary, has_reviews = self._review_summary(reviews)

        destinations_label = " • ".join(_all_destination_names(trip))
        gallery_items = _trip_gallery_context(trip)

        trip_data = {
            "title": trip.title,
            "slug": trip.slug,
            "hero_image_url": trip.hero_image.url if trip.hero_image else "",
            "card_image_url": trip.card_image.url if trip.card_image else "",
            "breadcrumbs": self._breadcrumbs(trip),
            "review_summary": review_summary,
            "tour_length": duration_label(trip.duration_days),
            "primary_destination": destinations_label,
            "key_facts": self._key_facts(trip, languages_label),
            "lead": getattr(trip, "lead", trip.teaser),
            "overview_paragraphs": overview_paragraphs,
            "highlights": highlights,
            "itinerary_days": itinerary_days,
            "included": included,
            "not_included": excluded,
            "faqs": faqs,
            "has_reviews": has_reviews,
            "contact_actions": contact_actions(),
            "destinations": destinations_label,
            "gallery": gallery_items,
        }
        trip_data["anchor_nav"] = self._anchor_nav(trip_data, other_trips)
        return trip_data

    def _serialize_related_trips(self, trip):
        curated_relations = list(trip.related_to.all())
        if curated_relations:
            return [build_trip_card(relation.to_trip) for relation in curated_relations[:3]]

        fallback_trips = (
            Trip.objects.exclude(pk=trip.pk)
            .select_related("destination")
            .prefetch_related("category_tags", "additional_destinations", "languages")
            .order_by("title")[:3]
        )
        return [build_trip_card(item) for item in fallback_trips]

    def _serialize_itinerary_days(self, trip):
        days = []
        for day in trip.itinerary_days.all():
            activities = [
                {
                    "time": step.time_label,
                    "title": step.title,
                    "description": step.description,
                }
                for step in day.steps.all()
            ]
            days.append(
                {
                    "title": f"Day {day.day_number}",
                    "summary": day.title,
                    "activities": activities,
                }
            )
        return days

    def _languages_label(self, trip):
        languages = [language.code.upper() for language in trip.languages.all() if language.code]
        return " • ".join(languages)

    def _overview_paragraphs(self, trip):
        about = getattr(trip, "about", None)
        if not about or not about.body:
            return []
        return [
            paragraph.strip()
            for paragraph in about.body.split("\n\n")
            if paragraph.strip()
        ]

    def _review_summary(self, reviews):
        if not reviews:
            return "New — be the first to review", False
        count = len(reviews)
        average = sum(review.rating for review in reviews) / count
        summary = f"Rated {average:.1f} / 5 • {count} review{'s' if count != 1 else ''}"
        return summary, True

    def _breadcrumbs(self, trip):
        breadcrumbs = [
            {"label": "Home", "url": reverse("web:home")},
        ]
        destination_names = _all_destination_names(trip)
        destination_label = destination_names[0] if destination_names else "Trips"
        breadcrumbs.append({"label": destination_label, "url": reverse("web:trips")})
        breadcrumbs.append({"label": trip.title, "url": ""})
        return breadcrumbs

    def _key_facts(self, trip, languages_label):
        facts = [
            {"icon": "⏱", "label": duration_label(trip.duration_days), "sr": "Duration"},
            {"icon": "🧭", "label": trip.tour_type_label, "sr": "Tour type"},
            {"icon": "👥", "label": f"Up to {trip.group_size_max} guests", "sr": "Group size"},
        ]
        if languages_label:
            facts.append({"icon": "🗣", "label": languages_label, "sr": "Languages"})
        return facts

    def _anchor_nav(self, trip_data, other_trips):
        nav = []
        if trip_data.get("highlights"):
            nav.append({"label": "Highlights", "target": "highlights"})
        if trip_data.get("gallery"):
            nav.append({"label": "Gallery", "target": "gallery"})
        if trip_data.get("overview_paragraphs"):
            nav.append({"label": "About", "target": "about"})
        if trip_data.get("itinerary_days"):
            nav.append({"label": "Itinerary", "target": "itinerary"})
        if trip_data.get("included") or trip_data.get("not_included"):
            nav.append({"label": "What's Included", "target": "included"})
        if trip_data.get("faqs"):
            nav.append({"label": "FAQs", "target": "faqs"})
        nav.append({"label": "Reviews", "target": "reviews"})
        if other_trips:
            nav.append({"label": "Related trips", "target": "related"})
        return nav


class CartQuickAddView(View):
    http_method_names = ["post"]

    DEFAULT_ADULTS = 2

    @staticmethod
    def _find_entry_id(summary: Mapping[str, Any], trip_id: int) -> str | None:
        entries = summary.get("entries", [])
        if not isinstance(entries, list):
            return None
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            if entry.get("trip_id") == trip_id:
                entry_id = entry.get("id")
                if entry_id:
                    return str(entry_id)
        return None

    def _auto_apply_reward(
        self,
        request,
        *,
        summary: Mapping[str, Any],
        trip_id: int,
        entry_id: str,
    ) -> int | None:
        rewards = summary.get("rewards", {})
        if not isinstance(rewards, Mapping):
            return None
        phases = rewards.get("phases", [])
        if not isinstance(phases, list):
            return None

        for phase in phases:
            if not isinstance(phase, Mapping):
                continue
            if not phase.get("unlocked"):
                continue
            options = [
                option
                for option in phase.get("trip_options", [])
                if isinstance(option, Mapping)
            ]
            if not options:
                continue
            if not any(option.get("trip_id") == trip_id for option in options):
                continue
            phase_id = int(phase.get("id") or 0)
            if phase_id <= 0:
                continue
            apply_reward_selection(
                request.session,
                entry_id=entry_id,
                phase_id=phase_id,
                trip_id=trip_id,
            )
            return phase_id
        return None

    @staticmethod
    def _remove_other_reward_entries(
        request,
        *,
        summary: Mapping[str, Any],
        phase_id: int | None,
        keep_entry_id: str,
    ) -> bool:
        entries = summary.get("entries", [])
        if not isinstance(entries, list):
            return False
        removed = False
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            entry_id = entry.get("id")
            if not entry_id or str(entry_id) == str(keep_entry_id):
                continue
            applied_reward = entry.get("applied_reward")
            if not isinstance(applied_reward, Mapping):
                continue
            applied_phase_id = int(applied_reward.get("phase_id") or 0)
            if phase_id is not None and applied_phase_id != phase_id:
                continue
            remove_entry(request.session, entry_id)
            removed = True
        return removed

    def post(self, request, slug):
        if not hasattr(request, "session"):
            raise Http404("Bookings require session support.")

        trip = get_object_or_404(
            Trip.objects.select_related("destination").prefetch_related("extras"),
            slug=slug,
        )

        cart = get_cart(request.session)
        entries = cart.get("entries", [])
        has_trip = any(entry.get("trip_id") == trip.pk for entry in entries)

        if has_trip:
            remove_trip_entries(request.session, trip.pk)
            toast_message = f"Removed \"{trip.title}\""
            in_cart = False
        else:
            cleaned_data = {
                "date": timezone.localdate(),
                "adults": self.DEFAULT_ADULTS,
                "children": 0,
                "infants": 0,
                "extras": [],
                "message": "",
            }

            date_raw = request.POST.get("date")
            if date_raw:
                try:
                    parsed_date = dt.datetime.strptime(date_raw, "%Y-%m-%d").date()
                except (TypeError, ValueError):
                    parsed_date = timezone.localdate()
                else:
                    today = timezone.localdate()
                    if parsed_date < today:
                        parsed_date = today
                cleaned_data["date"] = parsed_date

            max_group_size_raw = getattr(trip, "group_size_max", None)
            try:
                max_group_size_int = int(max_group_size_raw)
            except (TypeError, ValueError):
                max_group_size_int = None
            else:
                if max_group_size_int <= 0:
                    max_group_size_int = None

            adults_count = cleaned_data["adults"]
            adults_raw = request.POST.get("adults")
            if adults_raw is not None:
                try:
                    adults_count = int(adults_raw)
                except (TypeError, ValueError):
                    adults_count = self.DEFAULT_ADULTS
                else:
                    if adults_count < 1:
                        adults_count = 1
                    if max_group_size_int:
                        adults_count = min(adults_count, max_group_size_int)
                    else:
                        adults_count = min(adults_count, 16)
            if max_group_size_int and adults_count > max_group_size_int:
                adults_count = max_group_size_int
            cleaned_data["adults"] = adults_count

            children_count = cleaned_data["children"]
            children_raw = request.POST.get("children")
            if children_raw is not None:
                try:
                    children_count = int(children_raw)
                except (TypeError, ValueError):
                    children_count = 0
            if children_count < 0:
                children_count = 0
            if max_group_size_int:
                available_children = max_group_size_int - adults_count
                if available_children < 0:
                    available_children = 0
                children_count = min(children_count, available_children)
            else:
                children_count = min(children_count, 12)
            cleaned_data["children"] = children_count

            infants_count = cleaned_data["infants"]
            infants_raw = request.POST.get("infants")
            if infants_raw is not None:
                try:
                    infants_count = int(infants_raw)
                except (TypeError, ValueError):
                    infants_count = 0
            if infants_count < 0:
                infants_count = 0
            infants_count = min(infants_count, 6)
            cleaned_data["infants"] = infants_count

            # ensure unique by clearing any lingering duplicates
            remove_trip_entries(request.session, trip.pk)

            entry = build_cart_entry(trip, cleaned_data)
            contact = get_contact(request.session)
            add_entry(request.session, entry, contact=contact)
            toast_message = f"Added \"{trip.title}\""
            in_cart = True

        summary = summarize_cart(request.session)
        added_entry_id: str | None = None
        replacement_performed = False
        if in_cart:
            added_entry_id = self._find_entry_id(summary, trip.pk)
            if added_entry_id:
                applied_phase_id = self._auto_apply_reward(
                    request,
                    summary=summary,
                    trip_id=trip.pk,
                    entry_id=added_entry_id,
                )
                if applied_phase_id is not None:
                    summary = summarize_cart(request.session)
                    if self._remove_other_reward_entries(
                        request,
                        summary=summary,
                        phase_id=None,
                        keep_entry_id=added_entry_id,
                    ):
                        replacement_performed = True
                        summary = summarize_cart(request.session)
                    if replacement_performed:
                        toast_message = f'Reward switched to "{trip.title}"'
                    else:
                        toast_message = f'Reward applied to "{trip.title}"'

        cart_trip_ids = extract_cart_trip_ids(summary)
        services = list_quick_add_services(cart_trip_ids)
        recommendations = list_quick_add_recommendations(cart_trip_ids)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in (request.headers.get("Accept") or "")

        if is_ajax:
            cart_label = (
                "No trips yet"
                if summary["count"] == 0
                else f"{summary['count']} trip{'s' if summary['count'] != 1 else ''}"
            )

            panel_html = render_to_string(
                "includes/navigation_cart_panel.html",
                {
                    "booking_cart_entries": summary["entries"],
                    "booking_cart_currency": summary["currency"],
                    "booking_cart_total_display": summary["total_display"],
                    "booking_cart_help_link": build_booking_help_link(summary["entries"]),
                },
                request=request,
            )

            return JsonResponse(
                {
                    "in_cart": in_cart,
                    "cart_count": summary["count"],
                    "cart_label": cart_label,
                    "trip_id": trip.pk,
                    "added_entry_id": added_entry_id,
                    "cart_summary": summary,
                    "panel_html": panel_html,
                    "toast_message": toast_message,
                    "quick_add_services": services,
                    "quick_add_recommendations": recommendations,
                }
            )

        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
        if not next_url or not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = reverse("web:trips")
        return redirect(next_url)


class CartCheckoutView(TemplateView):
    template_name = "booking_cart_checkout.html"
    form_class = BookingCartCheckoutForm
    SERVICES_LIMIT = QUICK_ADD_SERVICES_LIMIT
    RECOMMENDED_LIMIT = QUICK_ADD_RECOMMENDATION_LIMIT

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, "session"):
            raise Http404("Bookings require session support.")
        return super().dispatch(request, *args, **kwargs)

    def get_summary(self):
        summary = summarize_cart(self.request.session)
        if summary:
            return summary
        return {
            "entries": [],
            "contact": {},
            "count": 0,
            "currency": DEFAULT_CURRENCY,
            "total_cents": 0,
            "total_display": "0.00",
        }

    def get_initial(self, summary):
        contact = summary.get("contact", {}) or {}
        return {
            "name": contact.get("name", ""),
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "notes": contact.get("notes", ""),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = kwargs.pop("summary", None)
        if summary is None:
            summary = self.get_summary()
        cart_trip_ids = extract_cart_trip_ids(summary)
        form = kwargs.get("form") or self.form_class(initial=self.get_initial(summary))
        context.update(
            form=form,
            cart_summary=summary,
            cart_entries=summary.get("entries", []),
            cart_contact=summary.get("contact", {}),
            cart_total_display=summary.get("total_display", "0.00"),
            cart_currency=summary.get("currency", DEFAULT_CURRENCY),
            cart_has_entries=bool(summary.get("entries")),
            quick_add_services=list_quick_add_services(cart_trip_ids, self.SERVICES_LIMIT),
            quick_add_recommendations=list_quick_add_recommendations(cart_trip_ids, self.RECOMMENDED_LIMIT),
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "remove":
            entry_id = request.POST.get("entry_id")
            if entry_id:
                remove_entry(request.session, entry_id)
                messages.info(request, "Trip removed from your booking list.")
            else:
                messages.error(request, "Unable to remove that trip. Please try again.")
            return redirect(reverse("web:booking-cart-checkout"))

        if action and action != "confirm":
            return redirect(reverse("web:booking-cart-checkout"))

        summary = summarize_cart(request.session)
        form = self.form_class(data=request.POST)

        if not summary.get("entries"):
            messages.error(request, "Add at least one trip before confirming your booking list.")
            return redirect(reverse("web:booking-cart-checkout"))

        if form.is_valid():
            cleaned = form.cleaned_data
            update_contact(
                request.session,
                name=cleaned.get("name"),
                email=cleaned.get("email"),
                phone=cleaned.get("phone"),
                notes=cleaned.get("notes"),
            )

            cart = get_cart(request.session)
            try:
                bookings = self._create_bookings(cart, cleaned)
            except Http404 as exc:
                messages.error(request, str(exc))
                return redirect(reverse("web:booking-cart-checkout"))

            if not bookings:
                messages.error(request, "We couldn't process your booking list. Please try again.")
                return redirect(reverse("web:booking-cart-checkout"))

            booking_ids = [booking.pk for booking in bookings]
            contact_payload = {
                key: cleaned.get(key, "")
                for key in ("name", "email", "phone", "notes")
            }
            token = signing.dumps(
                {"bookings": booking_ids, "contact": contact_payload},
                salt=BOOKING_CART_REFERENCE_SALT,
            )

            clear_cart(request.session)
            success_url = f"{reverse('web:booking-success')}?ref={token}"
            return redirect(success_url)

        return self.render_to_response(
            self.get_context_data(form=form, summary=summary)
        )

    def _create_bookings(self, cart, contact):
        entries = cart.get("entries", [])
        if not entries:
            return []

        name = (contact.get("name") or "").strip()
        email = (contact.get("email") or "").strip()
        phone = (contact.get("phone") or "").strip()
        notes = (contact.get("notes") or "").strip()

        if not (name and email and phone):
            return []

        rewards_state = compute_cart_rewards(cart)

        trip_ids = {
            entry.get("trip_id")
            for entry in entries
            if isinstance(entry, Mapping) and entry.get("trip_id") is not None
        }
        trips = Trip.objects.filter(pk__in=trip_ids)
        trip_map = {trip.pk: trip for trip in trips}

        created_bookings = []
        group_reference = None

        def cents_to_decimal(value):
            try:
                return (Decimal(str(value)) / Decimal("100")).quantize(Decimal("0.01"))
            except (TypeError, ValueError, ArithmeticError):
                return Decimal("0")

        with transaction.atomic():
            for entry in entries:
                trip_id = entry.get("trip_id")
                trip = trip_map.get(trip_id)
                if trip is None:
                    raise Http404("One of the trips in your list is no longer available.")

                travel_date_raw = entry.get("travel_date")
                if isinstance(travel_date_raw, dt.date):
                    travel_date = travel_date_raw
                elif isinstance(travel_date_raw, str):
                    try:
                        travel_date = dt.date.fromisoformat(travel_date_raw)
                    except ValueError as exc:
                        raise Http404("One of the trip dates is invalid. Please review your list.") from exc
                else:
                    raise Http404("One of the trip dates is invalid. Please review your list.")

                adults = max(int(entry.get("adults") or 0), 0)
                children = max(int(entry.get("children") or 0), 0)
                infants = max(int(entry.get("infants") or 0), 0)
                if adults + children <= 0:
                    adults = 1

                pricing = entry.get("pricing") or {}
                base_total = cents_to_decimal(pricing.get("base_total_cents"))
                extras_total = cents_to_decimal(pricing.get("extras_total_cents"))
                grand_total = cents_to_decimal(pricing.get("grand_total_cents"))

                entry_id = str(entry.get("id", ""))
                calculation = rewards_state.calculations.get(entry_id)
                snapshot = rewards_state.snapshots.get(entry_id)

                if calculation is not None and snapshot is not None:
                    base_total = cents_to_decimal(calculation.updated_base_total_cents)
                    extras_total = cents_to_decimal(snapshot.extras_total_cents)
                    grand_total = cents_to_decimal(calculation.updated_grand_total_cents)

                if grand_total == Decimal("0"):
                    adult_price = getattr(trip, "base_price_per_person", Decimal("0"))
                    child_price = trip.get_child_price_per_person()
                    if not isinstance(adult_price, Decimal):
                        adult_price = Decimal(str(adult_price or 0))
                    if not isinstance(child_price, Decimal):
                        child_price = Decimal(str(child_price or 0))
                    if adults + children <= 0:
                        adults = 1
                    base_total = (adult_price * Decimal(adults) + child_price * Decimal(children)).quantize(Decimal("0.01"))
                    extras_total = Decimal("0")
                    for extra_data in entry.get("extras", []):
                        extras_total += cents_to_decimal(extra_data.get("price_cents"))
                    grand_total = (base_total + extras_total).quantize(Decimal("0.01"))

                entry_message = (entry.get("message") or "").strip()
                note_sections = []
                if entry_message:
                    note_sections.append(entry_message)
                if notes:
                    note_sections.append(f"Additional notes:\n{notes}")
                special_requests = "\n\n".join(note_sections)

                create_kwargs = dict(
                    trip=trip,
                    travel_date=travel_date,
                    adults=adults,
                    children=children,
                    infants=infants,
                    full_name=name,
                    email=email,
                    phone=phone,
                    special_requests=special_requests,
                    base_subtotal=base_total,
                    extras_subtotal=extras_total,
                    grand_total=grand_total,
                )

                if group_reference:
                    create_kwargs["group_reference"] = group_reference

                booking = Booking.objects.create(**create_kwargs)

                if group_reference is None:
                    group_reference = booking.reference_code
                elif booking.group_reference != group_reference:
                    Booking.objects.filter(pk=booking.pk).update(group_reference=group_reference)
                    booking.group_reference = group_reference

                extras_data = entry.get("extras") or []
                extra_ids = {
                    extra.get("id")
                    for extra in extras_data
                    if extra.get("id") is not None
                }
                extras_queryset = TripExtra.objects.filter(trip=trip, pk__in=extra_ids)
                extras_map = {extra.pk: extra for extra in extras_queryset}

                booking_extras = []
                for extra_data in extras_data:
                    extra_id = extra_data.get("id")
                    extra = extras_map.get(extra_id)
                    if not extra:
                        continue
                    price_cents = extra_data.get("price_cents")
                    if price_cents is None:
                        price_value = extra.price
                    else:
                        price_value = cents_to_decimal(price_cents)
                    booking_extras.append(
                        BookingExtra(
                            booking=booking,
                            extra=extra,
                            price_at_booking=price_value,
                        )
                    )

                if booking_extras:
                    BookingExtra.objects.bulk_create(booking_extras)

                if calculation is not None and snapshot is not None:
                    phase = rewards_state.phase_map.get(calculation.phase_id)
                    if phase is not None:
                        persist_booking_reward(
                            booking=booking,
                            phase=phase,
                            calculation=calculation,
                        )

                created_bookings.append(booking)

        return created_bookings


class CartRewardsPayloadMixin:
    @staticmethod
    def _parse_payload(request):
        content_type = (request.content_type or "").lower()
        if "application/json" in content_type:
            try:
                raw_body = request.body.decode("utf-8") if request.body else ""
            except UnicodeDecodeError:
                return {}
            try:
                data = json.loads(raw_body or "{}")
            except ValueError:
                return {}
            if isinstance(data, dict):
                return data
            return {}
        return request.POST

    @staticmethod
    def _positive_int(value):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed

    @staticmethod
    def _json_error(message, status=400):
        return JsonResponse({"error": message}, status=status)


class CartRewardsSummaryView(CartRewardsPayloadMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if not hasattr(request, "session"):
            return self._json_error("Session support required.", status=400)
        summary = summarize_cart(request.session)
        return JsonResponse({"cart_summary": summary})


class CartRewardsApplyView(CartRewardsPayloadMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if not hasattr(request, "session"):
            return self._json_error("Session support required.", status=400)

        payload = self._parse_payload(request)
        entry_id = str(payload.get("entry_id") or "")
        phase_id = self._positive_int(payload.get("phase_id"))
        trip_id = self._positive_int(payload.get("trip_id"))

        if not entry_id or phase_id is None or trip_id is None:
            return self._json_error("Invalid reward selection payload.")

        cart = get_cart(request.session)
        entries = cart.get("entries", [])
        entry_record = None
        for entry in entries or []:
            if str(entry.get("id", "")) == entry_id:
                entry_record = entry
                break
        if entry_record is None:
            return self._json_error("That trip is no longer in your booking list.", status=404)

        rewards_state = compute_cart_rewards(cart)
        phase = rewards_state.phase_map.get(phase_id)
        if phase is None:
            return self._json_error("Reward phase not found.", status=404)

        if phase.id not in set(rewards_state.unlocked_phase_ids):
            return self._json_error("This reward has not been unlocked yet.", status=400)

        snapshot = rewards_state.snapshots.get(entry_id)
        if snapshot is None:
            try:
                snapshot = build_entry_snapshot(entry_record)
            except RewardComputationError:
                return self._json_error("Unable to evaluate this reward for the selected trip.", status=400)

        if snapshot.trip_id != trip_id:
            return self._json_error("Reward selection does not match the chosen trip.", status=400)

        try:
            calculate_entry_reward(snapshot=snapshot, phase=phase)
        except RewardComputationError as exc:
            message = str(exc) or "Unable to apply that reward."
            return self._json_error(message, status=400)

        apply_reward_selection(
            request.session,
            entry_id=entry_id,
            phase_id=phase_id,
            trip_id=trip_id,
        )
        summary = summarize_cart(request.session)
        return JsonResponse({"cart_summary": summary})


class CartRewardsRemoveView(CartRewardsPayloadMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if not hasattr(request, "session"):
            return self._json_error("Session support required.", status=400)

        payload = self._parse_payload(request)
        entry_id = str(payload.get("entry_id") or "")
        if not entry_id:
            return self._json_error("Entry identifier is required.")

        remove_reward_selection(request.session, entry_id)
        summary = summarize_cart(request.session)
        return JsonResponse({"cart_summary": summary})


class BookingSuccessView(TemplateView):
    template_name = "booking_success.html"
    SINGLE_MAX_AGE = BOOKING_REFERENCE_MAX_AGE
    MULTI_MAX_AGE = BOOKING_CART_REFERENCE_MAX_AGE

    def _load_success_payload(self):
        token = self.request.GET.get("ref")
        if not token:
            raise Http404("Booking reference not provided.")

        try:
            booking = load_booking_from_token(token, max_age=self.SINGLE_MAX_AGE)
        except Http404:
            booking = None

        if booking is not None:
            contact_details = {
                "name": booking.full_name,
                "email": booking.email,
                "phone": booking.phone,
                "notes": booking.special_requests,
            }
            return [booking], contact_details

        bookings, contact_info = load_cart_bookings_from_token(
            token, max_age=self.MULTI_MAX_AGE
        )
        return bookings, contact_info

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookings, contact_info = self._load_success_payload()

        if not bookings:
            raise Http404("Booking reference invalid.")

        primary_booking = bookings[0]
        primary_trip = primary_booking.trip

        summary_base = Decimal("0")
        summary_extras = Decimal("0")
        summary_total = Decimal("0")
        summary_discount = Decimal("0")
        bookings_detail = []
        latest_status_update = primary_booking.status_updated_at

        for booking in bookings:
            trip = booking.trip
            billed_travelers = max(booking.adults + booking.children, 1)
            if billed_travelers:
                per_person_total = booking.grand_total / billed_travelers
                per_person_phrase = (
                    f"{format_currency(per_person_total, DEFAULT_CURRENCY)} per paying traveler"
                )
            else:
                per_person_phrase = ""

            traveler_summary_display = traveler_summary(
                booking.adults,
                booking.children,
                booking.infants,
                per_person_phrase,
            )

            extras = [
                {
                    "name": record.extra.name,
                    "price": record.price_at_booking,
                    "price_display": format_currency(
                        record.price_at_booking, DEFAULT_CURRENCY
                    ),
                }
                for record in booking.booking_extras.select_related("extra")
            ]

            additional_destinations = [
                destination.name for destination in trip.additional_destinations.all()
            ]

            reward_records = list(booking.rewards.all())
            discount_total = Decimal("0")
            applied_rewards = []
            reward_currency = DEFAULT_CURRENCY
            for reward_record in reward_records:
                discount_amount = reward_record.discount_amount or Decimal("0")
                discount_total += discount_amount
                currency = (reward_record.currency or DEFAULT_CURRENCY).upper()
                if applied_rewards:
                    # Preserve currency from the first reward for consistent formatting
                    pass
                else:
                    reward_currency = currency
                applied_rewards.append(
                    {
                        "phase_name": getattr(reward_record.reward_phase, "name", ""),
                        "discount_percent": reward_record.discount_percent,
                        "discount_display": format_currency(
                            discount_amount, currency
                        ),
                        "currency": currency,
                    }
                )

            pre_discount_base = booking.base_subtotal + discount_total
            pre_discount_total = booking.grand_total + discount_total

            pricing = {
                "base": booking.base_subtotal,
                "base_display": format_currency(
                    booking.base_subtotal, DEFAULT_CURRENCY
                ),
                "extras": booking.extras_subtotal,
                "extras_display": format_currency(
                    booking.extras_subtotal, DEFAULT_CURRENCY
                ),
                "total": booking.grand_total,
                "total_display": format_currency(
                    booking.grand_total, DEFAULT_CURRENCY
                ),
                "currency": DEFAULT_CURRENCY,
                "discount": discount_total,
                "discount_display": format_currency(
                    discount_total, reward_currency
                )
                if discount_total
                else "",
                "pre_discount_base": pre_discount_base,
                "pre_discount_base_display": format_currency(
                    pre_discount_base, DEFAULT_CURRENCY
                ),
                "pre_discount_total": pre_discount_total,
                "pre_discount_total_display": format_currency(
                    pre_discount_total, DEFAULT_CURRENCY
                ),
                "has_discount": discount_total > 0,
            }

            bookings_detail.append(
                {
                    "reference": booking.reference_code,
                    "trip_title": trip.title,
                    "trip_slug": trip.slug,
                    "trip_url": reverse("web:trip-detail", args=[trip.slug]),
                    "destination_name": trip.destination.name if trip.destination else "",
                    "additional_destinations": additional_destinations,
                    "travel_date_display": booking.travel_date.strftime("%b %d, %Y"),
                    "traveler_summary": traveler_summary_display,
                    "pricing": pricing,
                    "extras": extras,
                    "special_requests": (booking.special_requests or "").strip(),
                    "applied_rewards": applied_rewards,
                }
            )

            summary_base += booking.base_subtotal
            summary_extras += booking.extras_subtotal
            summary_total += booking.grand_total
            summary_discount += discount_total

            if booking.status_updated_at and (
                latest_status_update is None
                or booking.status_updated_at > latest_status_update
            ):
                latest_status_update = booking.status_updated_at

        summary_pre_discount_total = summary_total + summary_discount

        summary_pricing = {
            "base": summary_base,
            "base_display": format_currency(summary_base, DEFAULT_CURRENCY),
            "extras": summary_extras,
            "extras_display": format_currency(summary_extras, DEFAULT_CURRENCY),
            "total": summary_total,
            "total_display": format_currency(summary_total, DEFAULT_CURRENCY),
            "currency": DEFAULT_CURRENCY,
            "discount": summary_discount,
            "discount_display": format_currency(summary_discount, DEFAULT_CURRENCY)
            if summary_discount
            else "",
            "pre_discount_total": summary_pre_discount_total,
            "pre_discount_total_display": format_currency(
                summary_pre_discount_total, DEFAULT_CURRENCY
            ),
            "has_discount": summary_discount > 0,
        }

        reference_codes = [booking.reference_code for booking in bookings]
        unique_reference_codes = list(dict.fromkeys(reference_codes))
        primary_reference = unique_reference_codes[0]
        additional_reference_codes = unique_reference_codes[1:]
        reference_copy = "\n".join(unique_reference_codes)

        contact_details = {
            "name": (contact_info.get("name") if isinstance(contact_info, dict) else None)
            or primary_booking.full_name,
            "email": (contact_info.get("email") if isinstance(contact_info, dict) else None)
            or primary_booking.email,
            "phone": (contact_info.get("phone") if isinstance(contact_info, dict) else None)
            or primary_booking.phone,
            "notes": (contact_info.get("notes") if isinstance(contact_info, dict) else None)
            or (primary_booking.special_requests or ""),
        }

        status = {
            "code": primary_booking.status,
            "label": primary_booking.get_status_display(),
            "note": primary_booking.status_note,
            "updated_at": latest_status_update,
        }

        primary_details = bookings_detail[0]
        all_applied_rewards = [
            reward
            for booking_detail in bookings_detail
            for reward in booking_detail.get("applied_rewards", [])
        ]

        context.update(
            booking=primary_booking,
            primary_booking=primary_booking,
            trip=primary_trip,
            primary_trip=primary_trip,
            primary_trip_url=reverse("web:trip-detail", args=[primary_trip.slug]),
            traveler_summary=primary_details["traveler_summary"],
            bookings_detail=bookings_detail,
            additional_bookings=bookings_detail[1:],
            bookings_count=len(bookings_detail),
            multi_booking=len(bookings_detail) > 1,
            summary_pricing=summary_pricing,
            primary_reference=primary_reference,
            additional_reference_codes=additional_reference_codes,
            reference_copy=reference_copy,
            contact_details=contact_details,
            contact_actions=contact_actions(),
            additional_destinations=primary_details["additional_destinations"],
            booking_status=status,
            booking_created_at=primary_booking.created_at,
            primary_details=primary_details,
            primary_travel_date_display=primary_details["travel_date_display"],
            reward_savings_total=summary_discount,
            reward_savings_total_display=format_currency(
                summary_discount, DEFAULT_CURRENCY
            )
            if summary_discount
            else "",
            reward_savings_applied=summary_discount > 0,
            applied_rewards=all_applied_rewards,
        )
        return context


class CartCheckoutSuccessView(BookingSuccessView):
    """Legacy endpoint retained for backwards compatibility."""

    template_name = "booking_success.html"


class BookingStatusView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        token = request.GET.get("ref")
        if not token:
            return JsonResponse({"error": "Missing booking reference."}, status=400)

        try:
            booking = load_booking_from_token(token)
        except Http404 as exc:
            message = str(exc) or "Booking not found."
            return JsonResponse({"error": message}, status=404)

        traveler_count = max(booking.adults + booking.children, 1)

        payload = {
            "reference": booking.reference_code,
            "status": {
                "code": booking.status,
                "label": booking.get_status_display(),
                "note": booking.status_note,
                "updated_at": booking.status_updated_at.isoformat() if booking.status_updated_at else None,
            },
            "booking": {
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
                "travel_date": booking.travel_date.isoformat() if booking.travel_date else None,
                "adults": booking.adults,
                "children": booking.children,
                "infants": booking.infants,
                "traveler_summary": traveler_summary(
                    booking.adults,
                    booking.children,
                    booking.infants,
                    "",
                ),
                "grand_total": str(booking.grand_total),
                "currency": DEFAULT_CURRENCY,
                "per_person_total": str(booking.grand_total / traveler_count) if traveler_count else None,
            },
            "trip": {
                "title": booking.trip.title,
                "slug": booking.trip.slug,
            },
        }

        return JsonResponse(payload)
