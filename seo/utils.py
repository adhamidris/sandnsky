from django.contrib.contenttypes.models import ContentType

from .models import PageType, SeoEntry, STATIC_PAGE_CODES


STATIC_META = {
    "home": ("Home", True),
    "trips_list": ("Trips", True),
    "blog_list": ("Blog", True),
    "destinations_list": ("Destinations", True),
    "sahari": ("Sahari", True),
    "about": ("About", True),
    "contact": ("Contact", True),
    "booking_terms": ("Booking Terms", True),
    "cancellation_policy": ("Cancellation Policy", True),
    "privacy_policy": ("Privacy Policy", True),
    "health_safety": ("Health & Safety", True),
    "booking_cart_success": ("Booking Cart Success", False),
    "booking_success": ("Booking Success", False),
    "booking_status": ("Booking Status", False),
}


def ensure_seo_entries():
    """
    Create missing SeoEntry rows for trips, destinations, blog posts, and static pages.
    English-only; safe to call multiple times.
    """
    from web.models import Trip, Destination, BlogPost  # imported lazily

    # Static pages
    for code, path in STATIC_PAGE_CODES.items():
        title, indexable = STATIC_META.get(code, (code.title(), True))
        SeoEntry.objects.get_or_create(
            page_type=PageType.STATIC,
            page_code=code,
            defaults={
                "path": path,
                "meta_title": title,
                "meta_description": "",
                "is_indexable": indexable,
            },
        )

    # Trips
    trip_ct = ContentType.objects.get_for_model(Trip)
    for trip in Trip.objects.all():
        slug = (trip.slug or "").strip()
        path = f"/trips/{slug}/" if slug else ""
        SeoEntry.objects.get_or_create(
            page_type=PageType.TRIP,
            content_type=trip_ct,
            object_id=trip.pk,
            defaults={
                "slug": slug,
                "path": path,
                "meta_title": trip.title or slug or "Trip",
                "meta_description": trip.teaser or "",
            },
        )

    # Destinations (all classifications)
    dest_ct = ContentType.objects.get_for_model(Destination)
    for destination in Destination.objects.all():
        slug = (destination.slug or "").strip()
        path = f"/destinations/{slug}/page/" if slug else ""
        SeoEntry.objects.get_or_create(
            page_type=PageType.DESTINATION,
            content_type=dest_ct,
            object_id=destination.pk,
            defaults={
                "slug": slug,
                "path": path,
                "meta_title": destination.name or slug or "Destination",
                "meta_description": destination.tagline or destination.description or "",
            },
        )

    # Blog posts
    blog_ct = ContentType.objects.get_for_model(BlogPost)
    for post in BlogPost.objects.all():
        slug = (post.slug or "").strip()
        path = f"/blog/{slug}/" if slug else ""
        SeoEntry.objects.get_or_create(
            page_type=PageType.BLOG_POST,
            content_type=blog_ct,
            object_id=post.pk,
            defaults={
                "slug": slug,
                "path": path,
                "meta_title": post.seo_title or post.title or slug or "Blog post",
                "meta_description": post.seo_description or post.excerpt or post.intro or "",
            },
        )
