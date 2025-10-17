from django.contrib import admin
from .models import (
    Destination,
    TripCategory,
    Language,
    Trip,
    TripHighlight,
    TripAbout,
    TripItineraryDay,
    TripItineraryStep,
    TripInclusion,
    TripExclusion,
    TripFAQ,
    TripExtra,
    TripRelation,
    Booking,
    BookingExtra,
    Review,
)


# -----------------------------
# Inline definitions
# -----------------------------

class TripAboutInline(admin.StackedInline):
    model = TripAbout
    extra = 0
    max_num = 1
    can_delete = False


class TripHighlightInline(admin.TabularInline):
    model = TripHighlight
    extra = 0
    fields = ("text", "position")
    ordering = ("position",)


class TripInclusionInline(admin.TabularInline):
    model = TripInclusion
    extra = 0
    fields = ("text", "position")
    ordering = ("position",)


class TripExclusionInline(admin.TabularInline):
    model = TripExclusion
    extra = 0
    fields = ("text", "position")
    ordering = ("position",)


class TripFAQInline(admin.TabularInline):
    model = TripFAQ
    extra = 0
    fields = ("question", "answer", "position")
    ordering = ("position",)


class TripExtraInline(admin.TabularInline):
    model = TripExtra
    extra = 0
    fields = ("name", "price", "position")
    ordering = ("position",)


class TripRelationInline(admin.TabularInline):
    """
    Inline for "You may also like" relations from the current Trip to others.
    """
    model = TripRelation
    fk_name = "from_trip"
    extra = 0
    fields = ("to_trip", "position")
    ordering = ("position",)
    autocomplete_fields = ("to_trip",)


class TripItineraryStepInline(admin.TabularInline):
    model = TripItineraryStep
    extra = 0
    fields = ("time_label", "title", "description", "position")
    ordering = ("position",)


class BookingExtraInline(admin.TabularInline):
    model = BookingExtra
    extra = 0
    fields = ("extra", "price_at_booking")
    raw_id_fields = ("extra",)
    # If you want to prevent editing snapshot data, uncomment the next line:
    # readonly_fields = ("extra", "price_at_booking")


# -----------------------------
# ModelAdmin registrations
# -----------------------------

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured", "featured_position")
    list_editable = ("is_featured", "featured_position")
    search_fields = ("name", "slug", "tagline", "description")
    list_filter = ("is_featured",)
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name",)}),
        (
            "Overview",
            {"fields": ("tagline", "description")},
        ),
        (
            "Media",
            {"fields": ("card_image", "hero_image")},
        ),
        (
            "Hero Content",
            {"fields": ("hero_subtitle",)},
        ),
        (
            "Visibility",
            {"fields": ("is_featured", "featured_position")},
        ),
    )


@admin.register(TripCategory)
class TripCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    inlines = [
        TripAboutInline,
        TripHighlightInline,
        TripInclusionInline,
        TripExclusionInline,
        TripFAQInline,
        TripExtraInline,
        TripRelationInline,
    ]

    list_display = (
        "title",
        "destination",
        "duration_days",
        "group_size_max",
        "base_price_per_person",
        "get_language_codes",
        "created_at",
    )
    list_filter = ("destination", "duration_days", "languages")
    search_fields = ("title", "slug", "teaser", "tour_type_label", "destination__name")
    filter_horizontal = ("languages", "category_tags", "additional_destinations")
    date_hierarchy = "created_at"
    ordering = ("title",)

    autocomplete_fields = ()  # keep explicit for clarity

    def get_language_codes(self, obj):
        return ", ".join(obj.languages.values_list("code", flat=True))
    get_language_codes.short_description = "Languages"


@admin.register(TripItineraryDay)
class TripItineraryDayAdmin(admin.ModelAdmin):
    """
    Manage itinerary days here, with step inlines.
    (Django admin doesn't support nested inlines under Trip directly.)
    """
    inlines = [TripItineraryStepInline]
    list_display = ("trip", "day_number", "title")
    list_filter = ("trip",)
    search_fields = ("trip__title", "title")
    ordering = ("trip__title", "day_number")


@admin.register(TripRelation)
class TripRelationAdmin(admin.ModelAdmin):
    list_display = ("from_trip", "to_trip", "position")
    list_filter = ("from_trip",)
    search_fields = ("from_trip__title", "to_trip__title")
    ordering = ("from_trip__title", "position")
    autocomplete_fields = ("from_trip", "to_trip")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    inlines = [BookingExtraInline]

    list_display = (
        "trip",
        "travel_date",
        "full_name",
        "email",
        "phone",
        "adults",
        "children",
        "infants",
        "grand_total",
        "created_at",
    )
    list_filter = ("trip", "travel_date", "created_at")
    search_fields = ("full_name", "email", "phone", "trip__title")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    readonly_fields = (
        "base_subtotal",
        "extras_subtotal",
        "grand_total",
        "created_at",
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("trip", "rating", "author_name", "created_at")
    list_filter = ("rating", "trip", "created_at")
    search_fields = ("author_name", "body", "trip__title")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
