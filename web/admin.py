import calendar
from datetime import date

from django import forms
from django.contrib import admin, messages
from django.core import signing
from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
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


def _render_image_preview(image_field, label):
    if not image_field:
        return "—"
    try:
        url = image_field.url
    except ValueError:
        return "—"
    return format_html(
        '<img src="{}" alt="{} preview" class="admin-thumb" />',
        url,
        label,
    )

class DestinationGalleryImageInline(admin.TabularInline):
    model = DestinationGalleryImage
    extra = 0
    show_change_link = True
    fields = ("image_preview", "image", "caption", "position")
    readonly_fields = ("image_preview",)
    ordering = ("position", "id")
    classes = ("collapse",)

    @admin.display(description="Preview")
    def image_preview(self, obj):
        return _render_image_preview(getattr(obj, "image", None), "Gallery image")


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


class TripAdminForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = "__all__"
        widgets = {
            "additional_destinations": forms.CheckboxSelectMultiple,
        }


class TripAboutInline(admin.StackedInline):
    model = TripAbout
    extra = 0
    max_num = 1
    can_delete = False
    show_change_link = True


class TripHighlightInline(admin.TabularInline):
    model = TripHighlight
    extra = 0
    fields = ("text", "position")
    ordering = ("position",)
    show_change_link = True


class TripGalleryImageInline(admin.TabularInline):
    model = TripGalleryImage
    extra = 0
    fields = ("image_preview", "image", "caption", "position")
    readonly_fields = ("image_preview",)
    ordering = ("position", "id")
    show_change_link = True

    @admin.display(description="Preview")
    def image_preview(self, obj):
        return _render_image_preview(getattr(obj, "image", None), "Trip gallery image")


class TripInclusionInline(admin.TabularInline):
    model = TripInclusion
    extra = 0
    fields = ("text", "position")
    ordering = ("position",)
    show_change_link = True


class TripExclusionInline(admin.TabularInline):
    model = TripExclusion
    extra = 0
    fields = ("text", "position")
    ordering = ("position",)
    show_change_link = True


class TripFAQInline(admin.TabularInline):
    model = TripFAQ
    extra = 0
    fields = ("question", "answer", "position")
    ordering = ("position",)
    classes = ("collapse",)
    show_change_link = True


class TripBookingOptionInline(admin.TabularInline):
    model = TripBookingOption
    extra = 0
    fields = ("name", "price_per_person", "child_price_per_person", "position")
    ordering = ("position", "id")
    show_change_link = True


class TripExtraInline(admin.TabularInline):
    model = TripExtra
    extra = 0
    fields = ("name", "price", "position")
    ordering = ("position",)
    classes = ("collapse",)
    show_change_link = True


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
    show_change_link = True


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
    readonly_fields = ("extra", "price_at_booking")
    classes = ("collapse",)
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
    classes = ("collapse",)


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
    list_display_links = ("name",)
    search_fields = ("name", "slug", "tagline", "description")
    list_filter = ("classification", "is_featured")
    ordering = ("name",)
    readonly_fields = (
        "card_image_preview",
        "hero_image_preview",
        "hero_image_mobile_preview",
    )
    fieldsets = (
        (
            "Basics",
            {"fields": ("name", "classification", ("is_featured", "featured_position"))},
        ),
        (
            "Overview",
            {"fields": ("tagline", "description")},
        ),
        (
            "Media",
            {
                "fields": (
                    ("card_image", "card_image_preview"),
                    ("hero_image", "hero_image_preview"),
                    ("hero_image_mobile", "hero_image_mobile_preview"),
                ),
                "description": "Previews refresh after saving.",
            },
        ),
        (
            "Hero Content",
            {"fields": ("hero_subtitle",)},
        ),
        (
            "Gallery uploads",
            {"fields": ("new_gallery_images",)},
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

    @admin.display(description="Card image preview")
    def card_image_preview(self, obj):
        return _render_image_preview(getattr(obj, "card_image", None), "Card image")

    @admin.display(description="Hero image preview")
    def hero_image_preview(self, obj):
        return _render_image_preview(getattr(obj, "hero_image", None), "Hero image")

    @admin.display(description="Hero mobile preview")
    def hero_image_mobile_preview(self, obj):
        return _render_image_preview(
            getattr(obj, "hero_image_mobile", None), "Hero mobile image"
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

    def has_module_permission(self, request):
        return False


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)

    def has_module_permission(self, request):
        return False


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    form = TripAdminForm
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
    filter_horizontal = ("languages", "category_tags")
    date_hierarchy = "created_at"
    ordering = ("destination", "destination_order", "title")
    list_editable = ("destination_order",)

    autocomplete_fields = ()  # keep explicit for clarity

    save_on_top = True
    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
        "card_image_preview",
        "hero_image_preview",
        "hero_image_mobile_preview",
        "itinerary_manager_link",
        "content_shortcuts",
    )
    fieldsets = (
        (
            "At a glance",
            {
                "fields": (
                    ("title", "tour_type_label"),
                    ("destination", "additional_destinations"),
                    "teaser",
                    ("is_service", "destination_order"),
                )
            },
        ),
        (
            "Pricing & capacity",
            {
                "fields": (
                    ("base_price_per_person", "child_price_per_person"),
                    ("duration_days", "group_size_max"),
                )
            },
        ),
        (
            "Audience rules",
            {
                "fields": (
                    ("allow_children", "allow_infants"),
                    "minimum_age",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    ("card_image", "card_image_preview"),
                    ("hero_image", "hero_image_preview"),
                    ("hero_image_mobile", "hero_image_mobile_preview"),
                ),
                "description": "Previews refresh after the trip is saved.",
            },
        ),
        (
            "Tags & languages",
            {
                "fields": (
                    "category_tags",
                    "languages",
                )
            },
        ),
        (
            "Quick tools",
            {
                "fields": ("itinerary_manager_link", "content_shortcuts"),
                "classes": ("collapse",),
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

    @admin.display(description="Card image preview")
    def card_image_preview(self, obj):
        return _render_image_preview(getattr(obj, "card_image", None), "Card image")

    @admin.display(description="Hero image preview")
    def hero_image_preview(self, obj):
        return _render_image_preview(getattr(obj, "hero_image", None), "Hero image")

    @admin.display(description="Hero mobile preview")
    def hero_image_mobile_preview(self, obj):
        return _render_image_preview(
            getattr(obj, "hero_image_mobile", None), "Hero mobile image"
        )

    @admin.display(description="Itinerary days")
    def itinerary_manager_link(self, obj):
        if not obj or not obj.pk:
            return "Save this trip to manage itinerary days."
        url = f"{reverse('admin:web_tripitineraryday_changelist')}?trip__id__exact={obj.pk}"
        return format_html('<a class="button" href="{}">Manage itinerary days</a>', url)

    @admin.display(description="Highlights & gallery shortcuts")
    def content_shortcuts(self, obj):
        if not obj or not obj.pk:
            return "Save this trip to jump to highlights or gallery."
        return format_html(
            '<a class="button" href="#triphighlight_set-group">Highlights</a> '
            '<a class="button" href="#tripgalleryimage_set-group">Gallery</a>'
        )


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

    quick_action_targets = (
        (Booking.Status.RECEIVED, "Mark as new"),
        (Booking.Status.CONFIRMED, "Mark confirmed"),
        (Booking.Status.CANCELLED, "Mark cancelled"),
    )

    list_display = (
        "reference_code",
        "trip",
        "travel_date",
        "headcount_display",
        "grand_total",
        "status_badge",
        "status_updated_at",
        "days_to_travel",
        "quick_actions",
    )
    list_filter = (TravelDateWindowFilter, "status")
    search_fields = ("full_name", "email", "phone", "trip__title", "group_reference")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("trip", "trip_option")
    autocomplete_fields = ("trip",)
    actions_on_top = True
    actions_on_bottom = False

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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:booking_id>/status/<str:target>/",
                self.admin_site.admin_view(self.quick_status_view),
                name="web_booking_quick_status",
            )
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        if "status__exact" not in request.GET:
            query_params = request.GET.copy()
            query_params["status__exact"] = Booking.Status.RECEIVED
            return HttpResponseRedirect(f"{request.path}?{query_params.urlencode()}")

        extra_context = extra_context or {}
        extra_context["pinned_actions"] = True
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description="Travelers")
    def headcount_display(self, obj):
        parts = [
            f"{obj.adults} adult{'s' if obj.adults != 1 else ''}",
        ]
        if obj.children:
            parts.append(f"{obj.children} child{'ren' if obj.children != 1 else ''}")
        if obj.infants:
            parts.append(f"{obj.infants} infant{'s' if obj.infants != 1 else ''}")
        return ", ".join(parts)

    @admin.display(description="Days to travel")
    def days_to_travel(self, obj):
        if not obj.travel_date:
            return "—"

        today = timezone.localdate()
        delta_days = (obj.travel_date - today).days

        if delta_days == 0:
            label = "Today"
            css = "due-today"
        elif delta_days > 0:
            label = f"{delta_days} day{'s' if delta_days != 1 else ''}"
            css = "due-future"
        else:
            label = f"{abs(delta_days)} day{'s' if abs(delta_days) != 1 else ''} ago"
            css = "due-past"

        return format_html('<span class="days-chip {}">{}</span>', css, label)

    @admin.display(description="Status")
    def status_badge(self, obj):
        css = f"status-{obj.status}"
        return format_html('<span class="status-chip {}">{}</span>', css, obj.get_status_display())

    def _quick_action_signature(self, booking_id, status):
        signer = signing.Signer()
        return signer.sign(f"{booking_id}:{status}")

    def _quick_action_url(self, obj, target_status):
        base = reverse(
            "admin:web_booking_quick_status", args=[obj.pk, target_status]
        )
        signature = self._quick_action_signature(obj.pk, target_status)
        return f"{base}?sig={signature}"

    @admin.display(description="Quick actions")
    def quick_actions(self, obj):
        buttons = []
        for status, label in self.quick_action_targets:
            if obj.status == status:
                continue
            buttons.append(
                format_html(
                    '<a class="quick-action-btn" href="{}">{}</a>',
                    self._quick_action_url(obj, status),
                    label,
                )
            )
        if not buttons:
            return "—"
        return format_html(
            '<div class="quick-action-wrap">{}</div>',
            format_html_join("", "{}", ((button,) for button in buttons)),
        )

    def quick_status_view(self, request, booking_id, target):
        signature = request.GET.get("sig")
        if not signature:
            return HttpResponseBadRequest("Missing signature.")

        signer = signing.Signer()
        try:
            payload = signer.unsign(signature)
        except signing.BadSignature:
            return HttpResponseForbidden("Invalid signature.")

        if payload != f"{booking_id}:{target}":
            return HttpResponseForbidden("Invalid token.")

        if target not in dict(self.quick_action_targets):
            return HttpResponseBadRequest("Unsupported status.")

        booking = Booking.objects.filter(pk=booking_id).first()
        if not booking:
            return HttpResponseBadRequest("Booking not found.")

        if booking.status == target:
            messages.info(request, f"{booking} is already {booking.get_status_display().lower()}.")
        else:
            booking.status = target
            booking.save(update_fields=["status", "status_updated_at"])
            messages.success(
                request,
                f"{booking.reference_code} marked as {booking.get_status_display().lower()}.",
            )

        redirect_url = request.META.get("HTTP_REFERER") or reverse("admin:web_booking_changelist")
        return HttpResponseRedirect(redirect_url)

    def _mass_update_status(self, queryset, status):
        updated = 0
        for booking in queryset.exclude(status=status):
            booking.status = status
            booking.save(update_fields=["status", "status_updated_at"])
            updated += 1
        return updated

    @admin.action(description="Mark selected bookings as new")
    def mark_as_received(self, request, queryset):
        count = self._mass_update_status(queryset, Booking.Status.RECEIVED)
        if count:
            self.message_user(request, f"{count} booking(s) marked as new.")

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
        "status_badge",
        "threshold_amount",
        "discount_percent",
        "position",
        "eligible_trip_count",
        "eligibility_summary",
        "quick_actions",
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

    actions = ("activate_phases", "deactivate_phases")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(trip_count=Count("phase_trips"))

    @admin.display(description="Status")
    def status_badge(self, obj):
        css = f"status-{obj.status}"
        return format_html('<span class="status-chip {}">{}</span>', css, obj.get_status_display())

    def eligible_trip_count(self, obj):
        return getattr(obj, "trip_count", None) or obj.phase_trips.count()

    eligible_trip_count.short_description = "Eligible trips"
    eligible_trip_count.admin_order_field = "trip_count"

    @admin.display(description="Eligibility summary")
    def eligibility_summary(self, obj):
        return obj.eligible_trips_preview()

    @admin.display(description="Eligible trips preview")
    def eligible_trips_preview(self, obj):
        return obj.eligible_trips_preview()

    @admin.display(description="Quick actions")
    def quick_actions(self, obj):
        buttons = []
        if obj.status != RewardPhase.Status.ACTIVE:
            buttons.append(
                format_html(
                    '<a class="quick-action-btn" href="{}">Activate</a>',
                    self._status_action_url(obj.pk, "activate"),
                )
            )
        if obj.status != RewardPhase.Status.INACTIVE:
            buttons.append(
                format_html(
                    '<a class="quick-action-btn" href="{}">Deactivate</a>',
                    self._status_action_url(obj.pk, "deactivate"),
                )
            )
        if not buttons:
            return "—"
        return format_html(
            '<div class="quick-action-wrap">{}</div>',
            format_html_join("", "{}", ((button,) for button in buttons)),
        )

    def _status_action_url(self, phase_id, action):
        signer = signing.Signer()
        token = signer.sign(f"{phase_id}:{action}")
        return reverse("admin:web_rewardphase_quick_status", args=[phase_id, action]) + f"?sig={token}"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:phase_id>/<str:action>/",
                self.admin_site.admin_view(self.quick_status_view),
                name="web_rewardphase_quick_status",
            )
        ]
        return custom + urls

    def quick_status_view(self, request, phase_id, action):
        signature = request.GET.get("sig")
        if not signature:
            return HttpResponseBadRequest("Missing signature.")

        signer = signing.Signer()
        try:
            payload = signer.unsign(signature)
        except signing.BadSignature:
            return HttpResponseForbidden("Invalid signature.")

        if payload != f"{phase_id}:{action}":
            return HttpResponseForbidden("Invalid token.")

        if action not in {"activate", "deactivate"}:
            return HttpResponseBadRequest("Unsupported action.")

        desired_status = (
            RewardPhase.Status.ACTIVE if action == "activate" else RewardPhase.Status.INACTIVE
        )

        phase = RewardPhase.objects.filter(pk=phase_id).first()
        if not phase:
            messages.error(request, "Reward phase not found.")
        elif phase.status == desired_status:
            messages.info(request, f"{phase.name} is already {phase.get_status_display().lower()}.")
        else:
            phase.status = desired_status
            phase.save(update_fields=["status", "updated_at"])
            messages.success(
                request,
                f"{phase.name} marked as {phase.get_status_display().lower()}.",
            )

        redirect_url = request.META.get("HTTP_REFERER") or reverse("admin:web_rewardphase_changelist")
        return HttpResponseRedirect(redirect_url)

    @admin.action(description="Activate selected phases")
    def activate_phases(self, request, queryset):
        count = queryset.exclude(status=RewardPhase.Status.ACTIVE).update(
            status=RewardPhase.Status.ACTIVE
        )
        if count:
            messages.success(request, f"{count} reward phase(s) activated.")

    @admin.action(description="Deactivate selected phases")
    def deactivate_phases(self, request, queryset):
        count = queryset.exclude(status=RewardPhase.Status.INACTIVE).update(
            status=RewardPhase.Status.INACTIVE
        )
        if count:
            messages.success(request, f"{count} reward phase(s) deactivated.")


@admin.register(RewardPhaseTrip)
class RewardPhaseTripAdmin(admin.ModelAdmin):
    list_display = ("phase", "trip", "position")
    list_filter = ("phase", "trip__destination")
    search_fields = ("phase__name", "trip__title")
    ordering = ("phase__position", "position", "id")
    autocomplete_fields = ("phase", "trip")
    list_select_related = ("phase", "trip", "trip__destination")

    def has_module_permission(self, request):
        return False


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

    def has_module_permission(self, request):
        return False


User = get_user_model()


class StaffUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock_password_auth_field()

    def _lock_password_auth_field(self):
        field = self.fields.get("usable_password")
        if not field:
            return
        field.initial = "true"
        field.widget = forms.HiddenInput()
        field.help_text = ""
        if self.is_bound:
            data = self.data.copy()
            data[self.add_prefix("usable_password")] = "true"
            self.data = data


class StaffUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock_password_auth_field()

    def _lock_password_auth_field(self):
        field = self.fields.get("usable_password")
        if not field:
            return
        field.initial = "true"
        field.widget = forms.HiddenInput()
        field.help_text = ""
        if self.is_bound:
            data = self.data.copy()
            data[self.add_prefix("usable_password")] = "true"
            self.data = data


try:
    admin.site.unregister(User)
except NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = StaffUserCreationForm
    form = StaffUserChangeForm

    fieldsets = tuple(
        (
            name,
            {
                **opts,
                "fields": tuple(
                    field
                    for field in opts.get("fields", ())
                    if field != "usable_password"
                ),
            },
        )
        for name, opts in DjangoUserAdmin.fieldsets
    )

    add_fieldsets = tuple(
        (
            name,
            {
                **opts,
                "fields": tuple(
                    field
                    for field in opts.get("fields", ())
                    if field != "usable_password"
                ),
            },
        )
        for name, opts in DjangoUserAdmin.add_fieldsets
    )
