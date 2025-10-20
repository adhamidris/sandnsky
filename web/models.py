from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify



# -----------------------------
# Core reference tables
# -----------------------------

class DestinationName(models.TextChoices):
    SIWA = "Siwa", "Siwa"
    FAYOUM = "Fayoum", "Fayoum"
    WHITE_BLACK = "White & Black Desert", "White & Black Desert"
    FARAFRA = "Farafra", "Farafra"
    DAKHLA = "Dakhla", "Dakhla"
    KHARGA = "Kharga", "Kharga"
    BAHAREYA = "Bahareya Oasis", "Bahareya Oasis"


ALLOWED_DESTINATIONS = [choice.value for choice in DestinationName]


class Destination(models.Model):
    name = models.CharField(
        max_length=200,
        choices=DestinationName.choices,
        unique=True,
    )
    slug = models.SlugField(max_length=200, unique=True, db_index=True, editable=False)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    card_image = models.ImageField(upload_to="destinations/", blank=True)
    hero_image = models.ImageField(upload_to="destinations/hero/", blank=True)
    hero_subtitle = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    featured_position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                name="destination_name_allowed",
                check=Q(name__in=ALLOWED_DESTINATIONS),
            )
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        base_url = reverse("web:trips")
        return f"{base_url}?destination={self.slug}"

    @property
    def cta_label(self):
        return "View Trips"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)


class DestinationGalleryImage(models.Model):
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ImageField(upload_to="destinations/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Destination gallery image"
        verbose_name_plural = "Destination gallery images"

    def __str__(self) -> str:
        base = self.caption or self.image.name
        return f"{self.destination.name} · {base}"


class TripCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Language(models.Model):
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=10)  # e.g., en, es, it, ru

    class Meta:
        ordering = ["name"]
        unique_together = (("name", "code"),)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


# -----------------------------
# Blog
# -----------------------------


class BlogCategory(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, editable=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)


class BlogPostStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    PUBLISHED = "published", "Published"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=250, blank=True)
    slug = models.SlugField(max_length=200, unique=True, editable=False)

    category = models.ForeignKey(
        BlogCategory, on_delete=models.PROTECT, related_name="posts"
    )

    hero_image = models.ImageField(upload_to="blog/hero/", blank=True)
    card_image = models.ImageField(upload_to="blog/cards/", blank=True)

    excerpt = models.TextField(blank=True)
    intro = models.TextField(blank=True)

    status = models.CharField(
        max_length=15,
        choices=BlogPostStatus.choices,
        default=BlogPostStatus.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(blank=True, null=True)

    read_time_minutes = models.PositiveSmallIntegerField(blank=True, null=True)

    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("web:blog-detail", args=[self.slug])

    @property
    def is_published(self) -> bool:
        if self.status != BlogPostStatus.PUBLISHED:
            return False
        if self.published_at is None:
            return False
        return self.published_at <= timezone.now()


class BlogSection(models.Model):
    post = models.ForeignKey(
        BlogPost, on_delete=models.CASCADE, related_name="sections"
    )
    position = models.PositiveSmallIntegerField(default=0)
    heading = models.CharField(max_length=200)
    location_label = models.CharField(max_length=150, blank=True)
    body = models.TextField()
    section_image = models.ImageField(upload_to="blog/sections/", blank=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        base = self.heading or "Section"
        return f"{self.post.title} · {base}"

# -----------------------------
# Site configuration
# -----------------------------


class SiteConfiguration(models.Model):
    hero_title = models.CharField(max_length=200, default="Discover the Magic of Egypt")
    hero_subtitle = models.TextField(
        blank=True,
        default="Embark on an unforgettable journey through ancient wonders and timeless beauty",
    )
    hero_primary_cta_label = models.CharField(max_length=100, default="Explore Tours")
    hero_primary_cta_href = models.CharField(max_length=255, default="/trips")
    hero_secondary_cta_label = models.CharField(max_length=100, default="Learn More")
    hero_secondary_cta_href = models.CharField(max_length=255, default="#about")
    hero_image = models.ImageField(upload_to="site/hero/", blank=True)
    trips_hero_image = models.ImageField(upload_to="site/trips_hero/", blank=True)

    class Meta:
        verbose_name = "Site configuration"
        verbose_name_plural = "Site configuration"

    def __str__(self) -> str:
        return "Site configuration"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# -----------------------------
# Trips
# -----------------------------

class Trip(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True, editable=False)

    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="trips"
    )

    additional_destinations = models.ManyToManyField(
        Destination, blank=True, related_name="additional_trips"
    )

    teaser = models.TextField(help_text="Short blurb shown on listing cards.")
    card_image = models.ImageField(upload_to="trips/cards/", blank=True)
    hero_image = models.ImageField(upload_to="trips/hero/", blank=True)

    duration_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    group_size_max = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    base_price_per_person = models.DecimalField(max_digits=10, decimal_places=2)

    # Simple display label exactly as seen in UI (e.g., "Daily Tour — Discovery Safari")
    tour_type_label = models.CharField(max_length=200)

    category_tags = models.ManyToManyField(
        TripCategory, blank=True, related_name="trips"
    )
    languages = models.ManyToManyField(
        Language, blank=True, related_name="trips"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["destination"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)


def _generate_unique_slug(instance, value, slug_field_name="slug"):
    base_slug = slugify(value) or "item"
    slug = base_slug
    ModelClass = instance.__class__
    unique_lookup = {slug_field_name: slug}
    counter = 2

    while (
        ModelClass.objects.filter(**unique_lookup)
        .exclude(pk=instance.pk)
        .exists()
    ):
        slug = f"{base_slug}-{counter}"
        unique_lookup[slug_field_name] = slug
        counter += 1

    return slug


# -----------------------------
# Trip content (highlights, about, itinerary, inclusions/exclusions, FAQs, extras, relations)
# -----------------------------

class TripHighlight(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="highlights")
    text = models.CharField(max_length=300)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"Highlight #{self.position} · {self.trip.title}"


class TripAbout(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="about")
    body = models.TextField()

    def __str__(self) -> str:
        return f"About · {self.trip.title}"


class TripItineraryDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="itinerary_days")
    day_number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ["day_number"]
        unique_together = (("trip", "day_number"),)

    def __str__(self) -> str:
        return f"{self.trip.title} · Day {self.day_number}: {self.title}"


class TripItineraryStep(models.Model):
    day = models.ForeignKey(TripItineraryDay, on_delete=models.CASCADE, related_name="steps")
    time_label = models.CharField(max_length=50, blank=True)  # e.g., "08:00"
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"Day {self.day.day_number} · {self.title}"


class TripInclusion(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="inclusions")
    text = models.CharField(max_length=300)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"Inclusion #{self.position} · {self.trip.title}"


class TripExclusion(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="exclusions")
    text = models.CharField(max_length=300)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"Exclusion #{self.position} · {self.trip.title}"


class TripFAQ(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=300)
    answer = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"FAQ #{self.position} · {self.trip.title}"


class TripExtra(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="extras")
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"{self.name} · {self.trip.title}"


class TripRelation(models.Model):
    """
    Manual curation for "You may also like" / related trips.
    """
    from_trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="related_to"
    )
    to_trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="related_from"
    )
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        unique_together = (("from_trip", "to_trip"),)

    def __str__(self) -> str:
        return f"{self.from_trip.title} → {self.to_trip.title}"


# -----------------------------
# Booking (detail page form → submission)
# -----------------------------

class Booking(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name="bookings")
    travel_date = models.DateField()

    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)
    infants = models.PositiveSmallIntegerField(default=0)

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=40)

    special_requests = models.TextField(blank=True)

    # Snapshots at the time of booking
    base_subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    extras_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trip", "travel_date"]),
        ]

    def __str__(self) -> str:
        return f"Booking #{self.pk} · {self.trip.title} · {self.travel_date}"

    @property
    def reference_code(self) -> str:
        if self.pk is None:
            return "PENDING"
        timestamp = self.created_at or timezone.now()
        return f"SKY{timestamp:%y%m%d}-{self.pk:06d}"


class BookingExtra(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="booking_extras")
    extra = models.ForeignKey(TripExtra, on_delete=models.PROTECT, related_name="booked_in")
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = (("booking", "extra"),)

    def __str__(self) -> str:
        return f"{self.extra.name} for booking #{self.booking_id}"


# -----------------------------
# Reviews (empty state supported; future-proof for star ratings)
# -----------------------------

class Review(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    author_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.rating}★ by {self.author_name} · {self.trip.title}"
