import calendar
from datetime import date

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.utils import timezone
from .models import (
    BlogCategory,
    BlogPost,
    BlogSection,
    Destination,
    DestinationGalleryImage,
    LandingGalleryImage,
    SiteConfiguration,
    SiteHeroPair,
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
    TripBookingOption,
    TripExtra,
    TripGalleryImage,
    TripRelation,
    RewardPhase,
    RewardPhaseTrip,
    Booking,
    BookingExtra,
    BookingReward,
    BookingConfirmationEmailSettings,
    Review,
)


# -----------------------------
# Inline definitions
# -----------------------------

class DestinationGalleryImageInline(admin.TabularInline):
    model = DestinationGalleryImage
    extra = 0
    fields = ("image", "caption", "position")
    ordering = ("position", "id")


class SiteHeroPairInline(admin.StackedInline):
    model = SiteHeroPair
    extra = 0
    fields = (
        "label",
        "position",
        "hero_image",
        "hero_video",
        "hero_mobile_image",
        "hero_mobile_video",
        "overlay_image",
        "overlay_alt",
    )
    ordering = ("position", "id")


class AdminMultipleFileWidget(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if hasattr(files, "getlist"):
            return files.getlist(name)
        file = files.get(name)
        if not file:
            return []
        return [file]


class MultipleImageField(forms.ImageField):
    widget = AdminMultipleFileWidget(attrs={"multiple": True})

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]

        cleaned = []
        errors = []
        for item in data:
            try:
                cleaned.append(super().clean(item, initial))
            except ValidationError as exc:
                errors.extend(exc.error_list)

        if errors:
            raise ValidationError(errors)
        return cleaned


class DestinationAdminForm(forms.ModelForm):
    new_gallery_images = MultipleImageField(
        required=False,
        label="Add gallery images",
        help_text="Upload one or more images to append to the gallery.",
    )

    class Meta:
        model = Destination
        fields = "__all__"


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


class TripGalleryImageInline(admin.TabularInline):
    model = TripGalleryImage
    extra = 1
    fields = ("image", "caption", "position")
    ordering = ("position", "id")


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
    classes = ("collapse",)


class TripBookingOptionInline(admin.TabularInline):
    model = TripBookingOption
    extra = 0
    fields = ("name", "price_per_person", "child_price_per_person", "position")
    ordering = ("position", "id")


class TripExtraInline(admin.TabularInline):
    model = TripExtra
    extra = 0
    fields = ("name", "price", "position")
    ordering = ("position",)
    classes = ("collapse",)


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
    classes = ("collapse",)


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


class BookingRewardInline(admin.TabularInline):
    model = BookingReward
    extra = 0
    can_delete = False
    fields = (
        "reward_phase",
        "trip",
        "traveler_count",
        "discount_percent",
        "discount_amount",
        "currency",
        "applied_at",
    )
    readonly_fields = fields
    ordering = ("-applied_at",)
    verbose_name_plural = "Applied rewards"


class RewardPhaseTripInline(admin.TabularInline):
    model = RewardPhaseTrip
    extra = 0
    fields = ("trip", "position")
    ordering = ("position", "id")
    autocomplete_fields = ("trip",)


@admin.register(LandingGalleryImage)
class LandingGalleryImageAdmin(admin.ModelAdmin):
    list_display = ("title_display", "position", "is_active", "updated_at")
    list_editable = ("position", "is_active")
    search_fields = ("title", "caption")
    ordering = ("position", "id")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("image", "title", "caption", "alt_text")}),
        ("Display", {"fields": ("position", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def title_display(self, obj):
        return obj.title or obj.caption or obj.image.name

    title_display.short_description = "Title"


class BlogSectionInline(admin.StackedInline):
    model = BlogSection
    extra = 0
    fields = ("position", "heading", "location_label", "body", "section_image")
    ordering = ("position", "id")


# -----------------------------
# ModelAdmin registrations
# -----------------------------


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    inlines = [BlogSectionInline]
    list_display = ("title", "category", "status", "published_at", "updated_at")
    list_filter = ("status", "category")
    search_fields = ("title", "subtitle", "excerpt", "intro")
    ordering = ("-published_at", "-created_at")
    readonly_fields = ("slug", "created_at", "updated_at")
    list_select_related = ("category",)
    fieldsets = (
        (None, {"fields": ("title", "subtitle", "category", "status")}),
        (
            "Content",
            {"fields": ("excerpt", "intro")},
        ),
        (
            "Media",
            {"fields": ("hero_image", "card_image")},
        ),
        (
            "Publishing",
            {"fields": ("published_at", "read_time_minutes")},
        ),
        (
            "SEO",
            {"fields": ("seo_title", "seo_description")},
        ),
        (
            "Meta",
            {"fields": ("slug", "created_at", "updated_at")},
        ),
    )
    date_hierarchy = "published_at"


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    form = DestinationAdminForm
    inlines = [DestinationGalleryImageInline]
    list_display = ("name", "classification", "is_featured", "featured_position")
    list_editable = ("is_featured", "featured_position")
    search_fields = ("name", "slug", "tagline", "description")
    list_filter = ("classification", "is_featured")
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name",)}),
        (
            "Overview",
            {"fields": ("tagline", "description")},
        ),
        ("Classification", {"fields": ("classification",)}),
        (
            "Media",
            {"fields": ("card_image", "hero_image", "hero_image_mobile")},
        ),
        (
            "Hero Content",
            {"fields": ("hero_subtitle",)},
        ),
        (
            "Gallery",
            {"fields": ("new_gallery_images",)},
        ),
        (
            "Visibility",
            {"fields": ("is_featured", "featured_position")},
        ),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        new_images = form.cleaned_data.get("new_gallery_images") or []
        if not new_images:
            return

        destination = form.instance
        current_max = (
            destination.gallery_images.aggregate(max_pos=Max("position"))
            .get("max_pos")
            or 0
        )

        created = 0
        for offset, image_file in enumerate(new_images, start=1):
            DestinationGalleryImage.objects.create(
                destination=destination,
                image=image_file,
                position=current_max + offset,
            )
            created += 1

        self.message_user(
            request,
            f"Added {created} new gallery image{'s' if created != 1 else ''}.",
        )


@admin.register(DestinationGalleryImage)
class DestinationGalleryImageAdmin(admin.ModelAdmin):
    list_display = ("destination", "position", "caption")
    list_filter = ("destination",)
    search_fields = ("destination__name", "caption", "image")
    ordering = ("destination__name", "position", "id")
    list_select_related = ("destination",)


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    inlines = [SiteHeroPairInline]
    fieldsets = (
        (
            "Landing Hero",
            {
                "fields": (
                    "hero_title",
                    "hero_subtitle",
                    "hero_primary_cta_label",
                    "hero_primary_cta_href",
                    "hero_secondary_cta_label",
                    "hero_secondary_cta_href",
                ),
                "description": "Hero pairs (see inline section) handle imagery; configure copy and links here.",
            },
        ),
        (
            "Hero Media Fallback",
            {
                "fields": (
                    "hero_image",
                    "hero_mobile_image",
                    "hero_video",
                    "hero_mobile_video",
                ),
                "description": "Optional default media used only if no hero pairs exist.",
                "classes": ("collapse",),
            },
        ),
        (
            "Trips Hero",
            {
                "fields": (
                    "trips_hero_image",
                    "trips_hero_image_mobile",
                )
            },
        ),
        (
            "Gallery",
            {
                "fields": (
                    "gallery_background_image",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        if SiteConfiguration.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(BookingConfirmationEmailSettings)
class BookingConfirmationEmailSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Delivery",
            {
                "fields": (
                    "is_enabled",
                    "from_email",
                    "reply_to_email",
                    "cc_addresses",
                    "bcc_addresses",
                ),
                "description": (
                    "Configure who sends and receives booking confirmation emails."
                ),
            },
        ),
        (
            "Templates",
            {
                "fields": (
                    "subject_template",
                    "body_text_template",
                    "body_html_template",
                ),
                "description": (
                    "Templates use Django syntax ({{ booking.reference_code }}, {{ trip.title }}, etc.)."
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        if BookingConfirmationEmailSettings.objects.exists():
            return False
        return super().has_add_permission(request)


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
        TripGalleryImageInline,
        TripInclusionInline,
        TripExclusionInline,
        TripFAQInline,
        TripBookingOptionInline,
        TripExtraInline,
        TripRelationInline,
    ]

    list_display = (
        "title",
        "destination",
        "destination_order",
        "duration_days",
        "group_size_max",
        "base_price_per_person",
        "child_price_per_person",
        "is_service",
        "get_language_codes",
        "created_at",
    )
    list_filter = ("destination", "duration_days", "languages", "is_service")
    search_fields = ("title", "slug", "teaser", "tour_type_label", "destination__name")
    filter_horizontal = ("languages", "category_tags", "additional_destinations")
    date_hierarchy = "created_at"
    ordering = ("destination", "destination_order", "title")
    list_editable = ("destination_order",)

    autocomplete_fields = ()  # keep explicit for clarity

    save_on_top = True
    readonly_fields = ("slug", "created_at", "updated_at")
    fieldsets = (
        (
            "Basics",
            {
                "fields": (
                    "title",
                    ("destination", "additional_destinations"),
                    "tour_type_label",
                    "teaser",
                )
            },
        ),
        (
            "Pricing & capacity",
            {
                "fields": (
                    ("base_price_per_person", "child_price_per_person"),
                    ("duration_days", "group_size_max"),
                    ("allow_children", "allow_infants", "minimum_age"),
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "card_image",
                    "hero_image",
                    "hero_image_mobile",
                )
            },
        ),
        (
            "Tagging & visibility",
            {
                "fields": (
                    "category_tags",
                    "languages",
                    "is_service",
                    "destination_order",
                )
            },
        ),
        (
            "Meta",
            {
                "fields": ("slug", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

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


class TravelDateWindowFilter(admin.SimpleListFilter):
    title = "travel window"
    parameter_name = "travel_window"

    def lookups(self, request, model_admin):
        return (
            ("this_month", "Traveling this month"),
            ("next_month", "Traveling next month"),
            ("future", "Upcoming (after today)"),
            ("past", "Past trips"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        today = timezone.localdate()

        if value == "this_month":
            start = today.replace(day=1)
            _, last_day = calendar.monthrange(today.year, today.month)
            end = start.replace(day=last_day)
            return queryset.filter(travel_date__range=(start, end))

        if value == "next_month":
            year = today.year + (1 if today.month == 12 else 0)
            month = 1 if today.month == 12 else today.month + 1
            start = date(year, month, 1)
            _, last_day = calendar.monthrange(start.year, start.month)
            end = start.replace(day=last_day)
            return queryset.filter(travel_date__range=(start, end))

        if value == "future":
            return queryset.filter(travel_date__gt=today)

        if value == "past":
            return queryset.filter(travel_date__lt=today)

        return queryset


@admin.register(TripRelation)
class TripRelationAdmin(admin.ModelAdmin):
    list_display = ("from_trip", "to_trip", "position")
    list_filter = ("from_trip",)
    search_fields = ("from_trip__title", "to_trip__title")
    ordering = ("from_trip__title", "position")
    autocomplete_fields = ("from_trip", "to_trip")
    list_select_related = ("from_trip", "to_trip")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    inlines = [BookingExtraInline, BookingRewardInline]

    list_display = (
        "reference_code",
        "trip",
        "trip_option_label",
        "travel_date",
        "status",
        "full_name",
        "email",
        "phone",
        "adults",
        "children",
        "infants",
        "grand_total",
        "status_updated_at",
        "created_at",
    )
    list_filter = (TravelDateWindowFilter, "status", "trip", "created_at")
    search_fields = ("full_name", "email", "phone", "trip__title", "group_reference")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("trip", "trip_option")
    autocomplete_fields = ("trip",)

    readonly_fields = (
        "reference_code",
        "base_subtotal",
        "extras_subtotal",
        "grand_total",
        "trip_option",
        "trip_option_label",
        "trip_option_price_per_person",
        "created_at",
        "status_updated_at",
    )

    fieldsets = (
        (
            "Reference & status",
            {
                "fields": (
                    "reference_code",
                    "group_reference",
                    ("status", "status_note"),
                    "status_updated_at",
                )
            },
        ),
        (
            "Trip & option",
            {
                "fields": (
                    "trip",
                    "trip_option",
                    "trip_option_label",
                    "trip_option_price_per_person",
                )
            },
        ),
        (
            "Travelers",
            {
                "fields": (
                    "travel_date",
                    ("adults", "children", "infants"),
                    "special_requests",
                )
            },
        ),
        (
            "Contact",
            {"fields": ("full_name", "email", "phone")},
        ),
        (
            "Pricing snapshot",
            {"fields": ("base_subtotal", "extras_subtotal", "grand_total")},
        ),
        (
            "Meta",
            {"fields": ("created_at",)},
        ),
    )

    actions = (
        "mark_as_received",
        "mark_as_confirmed",
        "mark_as_cancelled",
    )

    def _mass_update_status(self, queryset, status):
        updated = 0
        for booking in queryset.exclude(status=status):
            booking.status = status
            booking.save(update_fields=["status", "status_updated_at"])
            updated += 1
        return updated

    @admin.action(description="Mark selected bookings as received")
    def mark_as_received(self, request, queryset):
        count = self._mass_update_status(queryset, Booking.Status.RECEIVED)
        if count:
            self.message_user(request, f"{count} booking(s) marked as received.")

    @admin.action(description="Mark selected bookings as confirmed")
    def mark_as_confirmed(self, request, queryset):
        count = self._mass_update_status(queryset, Booking.Status.CONFIRMED)
        if count:
            self.message_user(request, f"{count} booking(s) marked as confirmed.")

    @admin.action(description="Mark selected bookings as cancelled")
    def mark_as_cancelled(self, request, queryset):
        count = self._mass_update_status(queryset, Booking.Status.CANCELLED)
        if count:
            self.message_user(request, f"{count} booking(s) marked as cancelled.")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("trip", "author_name", "created_at")
    list_filter = ("trip", "created_at")
    search_fields = ("author_name", "body", "trip__title")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(RewardPhase)
class RewardPhaseAdmin(admin.ModelAdmin):
    inlines = [RewardPhaseTripInline]
    list_display = (
        "name",
        "status",
        "threshold_amount",
        "discount_percent",
        "currency",
        "position",
        "eligible_trip_count",
        "updated_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("name", "headline", "description")
    ordering = ("position", "id")
    readonly_fields = ("eligible_trips_preview", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "status",
                    "position",
                )
            },
        ),
        (
            "Reward configuration",
            {
                "fields": (
                    ("threshold_amount", "discount_percent", "currency"),
                    "headline",
                    "description",
                )
            },
        ),
        (
            "Eligibility",
            {
                "fields": ("eligible_trips_preview",),
                "description": "Quick glance at trips linked to this reward phase.",
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(trip_count=Count("phase_trips"))

    def eligible_trip_count(self, obj):
        return getattr(obj, "trip_count", None) or obj.phase_trips.count()

    eligible_trip_count.short_description = "Eligible trips"
    eligible_trip_count.admin_order_field = "trip_count"

    def eligible_trips_preview(self, obj):
        trips = (
            obj.phase_trips.select_related("trip")
            .order_by("position", "id")
            .values_list("trip__title", flat=True)[:5]
        )
        preview = ", ".join(trips)
        if obj.phase_trips.count() > 5:
            preview = f"{preview}, …"
        return preview or "No trips linked yet."


@admin.register(RewardPhaseTrip)
class RewardPhaseTripAdmin(admin.ModelAdmin):
    list_display = ("phase", "trip", "position")
    list_filter = ("phase", "trip__destination")
    search_fields = ("phase__name", "trip__title")
    ordering = ("phase__position", "position", "id")
    autocomplete_fields = ("phase", "trip")
    list_select_related = ("phase", "trip", "trip__destination")


@admin.register(BookingReward)
class BookingRewardAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "reward_phase",
        "trip",
        "traveler_count",
        "discount_percent",
        "discount_amount",
        "currency",
        "applied_at",
    )
    list_filter = ("reward_phase", "currency", "applied_at")
    search_fields = (
        "booking__full_name",
        "booking__email",
        "booking__trip__title",
        "reward_phase__name",
        "trip__title",
    )
    date_hierarchy = "applied_at"
    ordering = ("-applied_at",)
    list_select_related = ("booking", "reward_phase", "trip")
