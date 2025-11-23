from django.db import migrations


STATIC_PAGES = [
    ("home", "/", "Home", True),
    ("trips_list", "/trips/", "Trips", True),
    ("blog_list", "/blog/", "Blog", True),
    ("destinations_list", "/destinations/", "Destinations", True),
    ("sahari", "/sahari/", "Sahari", True),
    ("about", "/about/", "About", True),
    ("contact", "/contact/", "Contact", True),
    ("booking_terms", "/booking-terms/", "Booking Terms", True),
    ("cancellation_policy", "/cancellation-policy/", "Cancellation Policy", True),
    ("privacy_policy", "/privacy-policy/", "Privacy Policy", True),
    ("health_safety", "/health-safety/", "Health & Safety", True),
    ("booking_cart_success", "/booking/cart/success/", "Booking Cart Success", False),
    ("booking_success", "/booking/success/", "Booking Success", False),
    ("booking_status", "/booking/status/", "Booking Status", False),
]


def _create_entry(SeoEntry, *, path, defaults):
    if not path:
        return None
    obj, created = SeoEntry.objects.get_or_create(path=path, defaults=defaults)
    if not created:
        dirty = False
        for field, value in defaults.items():
            if not getattr(obj, field):
                setattr(obj, field, value)
                dirty = True
        if dirty:
            obj.save(update_fields=list(defaults.keys()))
    return obj


def seed_static_pages(apps, SeoEntry):
    for code, path, title, is_indexable in STATIC_PAGES:
        _create_entry(
            SeoEntry,
            path=path,
            defaults={
                "page_type": "static",
                "page_code": code,
                "meta_title": title,
                "meta_description": "",
                "is_indexable": is_indexable,
            },
        )


def seed_trips(apps, SeoEntry, ContentType):
    Trip = apps.get_model("web", "Trip")
    if not Trip.objects.exists():
        return
    trip_ct = ContentType.objects.get_for_model(Trip)
    for trip in Trip.objects.all():
        slug = (trip.slug or "").strip()
        path = f"/trips/{slug}/" if slug else ""
        meta_title = (trip.title or "").strip() or slug or "Trip"
        meta_description = (trip.teaser or "").strip()
        _create_entry(
            SeoEntry,
            path=path,
            defaults={
                "page_type": "trip",
                "content_type": trip_ct,
                "object_id": trip.pk,
                "slug": slug,
                "meta_title": meta_title,
                "meta_description": meta_description,
            },
        )


def seed_destinations(apps, SeoEntry, ContentType):
    Destination = apps.get_model("web", "Destination")
    if not Destination.objects.exists():
        return
    destination_ct = ContentType.objects.get_for_model(Destination)
    destinations = Destination.objects.all()
    # Only destinations that have a dedicated page in the current code (classification = "sahari")
    destinations = destinations.filter(classification="sahari")
    for destination in destinations:
        slug = (destination.slug or "").strip()
        path = f"/destinations/{slug}/page/" if slug else ""
        meta_title = (destination.name or "").strip() or slug or "Destination"
        meta_description = (destination.tagline or destination.description or "").strip()
        _create_entry(
            SeoEntry,
            path=path,
            defaults={
                "page_type": "destination",
                "content_type": destination_ct,
                "object_id": destination.pk,
                "slug": slug,
                "meta_title": meta_title,
                "meta_description": meta_description,
            },
        )


def seed_blog_posts(apps, SeoEntry, ContentType):
    BlogPost = apps.get_model("web", "BlogPost")
    if not BlogPost.objects.exists():
        return
    blog_ct = ContentType.objects.get_for_model(BlogPost)
    for post in BlogPost.objects.all():
        slug = (post.slug or "").strip()
        path = f"/blog/{slug}/" if slug else ""
        meta_title = (post.seo_title or post.title or "").strip() or slug or "Blog post"
        meta_description = (post.seo_description or post.excerpt or post.intro or "").strip()
        _create_entry(
            SeoEntry,
            path=path,
            defaults={
                "page_type": "blog_post",
                "content_type": blog_ct,
                "object_id": post.pk,
                "slug": slug,
                "meta_title": meta_title,
                "meta_description": meta_description,
            },
        )


def forwards_func(apps, schema_editor):
    SeoEntry = apps.get_model("seo", "SeoEntry")
    ContentType = apps.get_model("contenttypes", "ContentType")

    seed_static_pages(apps, SeoEntry)
    seed_trips(apps, SeoEntry, ContentType)
    seed_destinations(apps, SeoEntry, ContentType)
    seed_blog_posts(apps, SeoEntry, ContentType)


def reverse_func(apps, schema_editor):
    SeoEntry = apps.get_model("seo", "SeoEntry")
    SeoEntry.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0001_initial"),
        ("web", "0041_alter_bookingconfirmationemailsettings_body_text_template"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
