from decimal import Decimal

from django.contrib import messages
from django.db.models import Prefetch, Q, Min, Max
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView

from .forms import BookingRequestForm
from .models import (
    Destination,
    SiteConfiguration,
    Trip,
    TripCategory,
    TripItineraryDay,
    TripRelation,
)


CURRENCY_SYMBOLS = {"USD": "$"}
DEFAULT_CURRENCY = "USD"


def format_currency(amount, currency=DEFAULT_CURRENCY):
    symbol = CURRENCY_SYMBOLS.get(currency.upper(), "")
    if symbol:
        return f"{symbol}{amount:,.2f}"
    return f"{amount:,.2f} {currency.upper()}"


def duration_label(days):
    days = int(days)
    return f"{days} day{'s' if days != 1 else ''}"


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


def _destination_gallery_context(destination):
    if not destination:
        return []
    gallery = []
    for image in destination.gallery_images.all():
        if not image.image:
            continue
        width = getattr(image.image, "width", None)
        height = getattr(image.image, "height", None)
        is_landscape = False
        if width and height:
            try:
                is_landscape = (width / height) >= 1.6
            except (TypeError, ZeroDivisionError):
                is_landscape = False
        gallery.append(
            {
                "image_url": image.image.url,
                "caption": image.caption,
                "is_landscape": is_landscape,
            }
        )
    return gallery


def build_trip_card(trip):
    primary_category = next((category.name for category in trip.category_tags.all()), "")
    image_url = trip.card_image.url if trip.card_image else ""
    destinations_label = " • ".join(_all_destination_names(trip))
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
    }


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


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_config = SiteConfiguration.get_solo()
        hero_image = site_config.hero_image.url if site_config.hero_image else "img/hero-pyramids.jpg"
        hero_image_is_media = bool(site_config.hero_image)
        context["hero"] = {
            "title": site_config.hero_title,
            "subtitle": site_config.hero_subtitle,
            "image": hero_image,
            "image_is_media": hero_image_is_media,
            "primary_cta": {
                "label": site_config.hero_primary_cta_label,
                "href": site_config.hero_primary_cta_href,
            },
            "secondary_cta": {
                "label": site_config.hero_secondary_cta_label,
                "href": site_config.hero_secondary_cta_href,
            },
        }

        context["destinations_section"] = {
            "title": "Featured Destinations",
            "subtitle": "Explore the most captivating experiences Egypt has to offer",
            "items": self._featured_destinations(),
        }

        context["about_section"] = {
            "title": "About Sand & Sky",
            "subtitle": (
                "Sand & Sky is a boutique travel agency devoted exclusively to the magic of the Egyptian "
                "Sahara. We craft immersive journeys that capture the soul of Egypt's most breathtaking desert "
                "landscapes - from the tranquil oases of Siwa, Fayoum, Bahariya, and Farafra to the surreal beauty "
                "of the White and Black Deserts."
            ),
            "features": [
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
            ],
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

        context["trips"] = [build_trip_card(trip) for trip in trips]
        context["selected_destination"] = selected_destination
        context["destination_hero"] = destination_hero
        context["contact_actions"] = contact_actions()
        context["destination_gallery"] = _destination_gallery_context(selected_destination)
        context["filter_options"] = self._filter_options(selected_destination)
        context["active_filters"] = filter_values
        return context

    def _base_queryset(self):
        return (
            Trip.objects.select_related("destination")
            .prefetch_related("category_tags", "additional_destinations")
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

        if filters.get("categories"):
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
            )
        )

    def get_trip(self):
        if not hasattr(self, "_trip"):
            self._trip = get_object_or_404(
                self.get_trip_queryset(), slug=self.kwargs.get("slug")
            )
        return self._trip

    def get_form(self, data=None):
        trip = self.get_trip()
        extra_choices = [
            (str(extra.pk), extra.name)
            for extra in trip.extras.order_by("position", "id")
        ]
        return BookingRequestForm(data=data, extra_choices=extra_choices)

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
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "Thanks for your request! A travel specialist will contact you shortly to confirm details.",
            )
            form = self.get_form()
        else:
            messages.error(request, "Please correct the errors below before submitting.")
        return self.render_to_response(self.get_context_data(form=form))

    def _pricing_context(self, trip, form):
        currency = getattr(trip, "currency", DEFAULT_CURRENCY)
        base_price = trip.base_price_per_person

        def extract_int(field_name, fallback):
            value = form[field_name].value()
            try:
                return max(int(value), 0)
            except (TypeError, ValueError):
                return fallback

        adults = max(extract_int("adults", form.fields["adults"].initial), 1)
        children = extract_int("children", form.fields["children"].initial)
        infants = extract_int("infants", form.fields["infants"].initial)

        traveler_count = max(adults + children, 1)
        base_total = base_price * traveler_count

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

        return {
            "currency": currency,
            "currency_symbol": CURRENCY_SYMBOLS.get(currency.upper(), ""),
            "base_price": base_price,
            "base_price_display": format_currency(base_price, currency),
            "traveler_count": traveler_count,
            "adults": adults,
            "children": children,
            "infants": infants,
            "base_total": base_total,
            "base_total_display": format_currency(base_total, currency),
            "extras_total": extras_total,
            "extras_total_display": format_currency(extras_total, currency),
            "total": total,
            "total_display": format_currency(total, currency),
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
            .prefetch_related("category_tags", "additional_destinations")
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
        languages = [language.name for language in trip.languages.all()]
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
