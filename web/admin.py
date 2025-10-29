from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Max
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
    TripExtra,
    TripRelation,
    RewardPhase,
    RewardPhaseTrip,
    Booking,
    BookingExtra,
    BookingReward,
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
                    "hero_video",
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
        "is_service",
        "get_language_codes",
        "created_at",
    )
    list_filter = ("destination", "duration_days", "languages", "is_service")
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
    inlines = [BookingExtraInline, BookingRewardInline]

    list_display = (
        "trip",
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
    list_filter = ("trip", "travel_date", "status", "created_at")
    search_fields = ("full_name", "email", "phone", "trip__title")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    readonly_fields = (
        "base_subtotal",
        "extras_subtotal",
        "grand_total",
        "created_at",
        "status_updated_at",
    )

    actions = (
        "mark_as_received",
        "mark_as_confirmed",
        "mark_as_cancelled",
    )

    @admin.action(description="Mark selected bookings as received")
    def mark_as_received(self, request, queryset):
        count = queryset.exclude(status=Booking.Status.RECEIVED).update(
            status=Booking.Status.RECEIVED,
            status_updated_at=timezone.now(),
        )
        if count:
            self.message_user(request, f"{count} booking(s) marked as received.")

    @admin.action(description="Mark selected bookings as confirmed")
    def mark_as_confirmed(self, request, queryset):
        count = queryset.exclude(status=Booking.Status.CONFIRMED).update(
            status=Booking.Status.CONFIRMED,
            status_updated_at=timezone.now(),
        )
        if count:
            self.message_user(request, f"{count} booking(s) marked as confirmed.")

    @admin.action(description="Mark selected bookings as cancelled")
    def mark_as_cancelled(self, request, queryset):
        count = queryset.exclude(status=Booking.Status.CANCELLED).update(
            status=Booking.Status.CANCELLED,
            status_updated_at=timezone.now(),
        )
        if count:
            self.message_user(request, f"{count} booking(s) marked as cancelled.")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("trip", "rating", "author_name", "created_at")
    list_filter = ("rating", "trip", "created_at")
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
        "updated_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("name", "headline", "description")
    ordering = ("position", "id")
    readonly_fields = ("created_at", "updated_at")
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
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(RewardPhaseTrip)
class RewardPhaseTripAdmin(admin.ModelAdmin):
    list_display = ("phase", "trip", "position")
    list_filter = ("phase", "trip__destination")
    search_fields = ("phase__name", "trip__title")
    ordering = ("phase__position", "position", "id")
    autocomplete_fields = ("phase", "trip")


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
