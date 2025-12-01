from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class PageType(models.TextChoices):
    TRIP = "trip", "Trip"
    DESTINATION = "destination", "Destination"
    BLOG_POST = "blog_post", "Blog post"
    STATIC = "static", "Static page"


class SnippetPlacement(models.TextChoices):
    HEAD = "head", "Head"
    BODY = "body", "Body"


class SeoEntry(models.Model):
    page_type = models.CharField(max_length=50, choices=PageType.choices, db_index=True)

    # Optional links to concrete content
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seo_entries",
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Static pages use a page_code instead of content_object
    page_code = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Identifier for static pages (e.g., home, trips_list).",
    )

    slug = models.SlugField(max_length=200, blank=True)
    path = models.CharField(
        max_length=500,
        unique=True,
        help_text="Absolute path for the page (e.g., /trips/my-trip/).",
    )

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alt text for the main hero/primary image on the page.",
    )
    main_image = models.ImageField(
        upload_to="seo/images/",
        blank=True,
        null=True,
        help_text="Primary image override for this page.",
        max_length=255,
    )
    canonical_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Canonical URL. Leave blank to default to self.",
    )
    body_override = models.TextField(
        blank=True,
        help_text="Optional SEO-focused body copy override (English-only).",
    )
    is_indexable = models.BooleanField(
        default=True,
        help_text="Whether the page should be indexed (English-only).",
    )
    status_flags = models.JSONField(
        default=dict,
        blank=True,
        help_text="Lightweight flags (e.g., missing_meta, missing_alt).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["page_type", "path"]
        indexes = [
            models.Index(fields=["page_type", "path"]),
            models.Index(fields=["page_type", "page_code"]),
        ]

    def __str__(self):
        label = self.meta_title or self.slug or self.page_code or self.path
        return f"{self.get_page_type_display()} · {label}"


class SeoFaq(models.Model):
    entry = models.ForeignKey(
        SeoEntry,
        on_delete=models.CASCADE,
        related_name="faqs",
    )
    question = models.CharField(max_length=300)
    answer = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entry", "position", "id"]
        verbose_name = "SEO FAQ"
        verbose_name_plural = "SEO FAQs"

    def __str__(self):
        return self.question


class SeoSnippet(models.Model):
    entry = models.ForeignKey(
        SeoEntry,
        on_delete=models.CASCADE,
        related_name="snippets",
    )
    name = models.CharField(max_length=150)
    placement = models.CharField(
        max_length=10,
        choices=SnippetPlacement.choices,
        default=SnippetPlacement.HEAD,
    )
    value = models.TextField(
        help_text="Raw HTML/script for injection. Restrict to trusted admins.",
    )
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entry", "placement", "position", "id"]
        verbose_name = "SEO snippet"
        verbose_name_plural = "SEO snippets"

    def __str__(self):
        return f"{self.name} ({self.placement})"


class SeoRedirect(models.Model):
    entry = models.ForeignKey(
        SeoEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="redirects",
    )
    from_path = models.CharField(
        max_length=500,
        unique=True,
        help_text="Source path to redirect from (absolute, no domain).",
    )
    to_path = models.CharField(
        max_length=500,
        help_text="Destination path (absolute, no domain).",
    )
    is_permanent = models.BooleanField(
        default=True,
        help_text="True for 301, False for 302.",
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["from_path"]
        verbose_name = "SEO redirect"
        verbose_name_plural = "SEO redirects"

    def __str__(self):
        code = "301" if self.is_permanent else "302"
        return f"{self.from_path} → {self.to_path} ({code})"


# Static page codes used for non-model-backed pages
STATIC_PAGE_CODES = {
    "home": "/",
    "trips_list": "/trips/",
    "blog_list": "/blog/",
    "destinations_list": "/destinations/",
    "sahari": "/sahari/",
    "about": "/about/",
    "contact": "/contact/",
    "booking_terms": "/booking-terms/",
    "cancellation_policy": "/cancellation-policy/",
    "privacy_policy": "/privacy-policy/",
    "health_safety": "/health-safety/",
    "booking_cart_success": "/booking/cart/success/",
    "booking_success": "/booking/success/",
    "booking_status": "/booking/status/",
}
