from django.db import migrations


PACKAGE_TRIP_CATEGORY_SLUG = "package-trip"
PACKAGE_TRIP_CATEGORY_NAME = "Package Trip"
PACKAGE_DESTINATION_EQUIVALENCE_GROUPS = [
    frozenset({"White & Black Desert", "Bahareya Oasis"}),
    frozenset({"Cairo", "Giza"}),
]


def _unique_preserve_order(values):
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _count_package_destinations(names):
    remaining = {name for name in names if name}
    count = 0
    for group in PACKAGE_DESTINATION_EQUIVALENCE_GROUPS:
        if remaining & group:
            count += 1
            remaining -= group
    count += len(remaining)
    return count


def create_package_trip_category(apps, schema_editor):
    TripCategory = apps.get_model("web", "TripCategory")
    Trip = apps.get_model("web", "Trip")
    Destination = apps.get_model("web", "Destination")

    category, _ = TripCategory.objects.get_or_create(
        slug=PACKAGE_TRIP_CATEGORY_SLUG,
        defaults={"name": PACKAGE_TRIP_CATEGORY_NAME},
    )

    if category.name != PACKAGE_TRIP_CATEGORY_NAME:
        category.name = PACKAGE_TRIP_CATEGORY_NAME
        category.save(update_fields=["name"])

    through = Trip.category_tags.through
    trip_field = next(
        field for field in through._meta.get_fields() if getattr(field, "related_model", None) is Trip
    )
    category_field = next(
        field for field in through._meta.get_fields() if getattr(field, "related_model", None) is TripCategory
    )
    trip_fk_id_name = f"{trip_field.name}_id"
    category_fk_id_name = f"{category_field.name}_id"

    dest_lookup = dict(Destination.objects.values_list("id", "name"))

    def get_trip_destination_names(trip):
        names = []
        primary = dest_lookup.get(trip.destination_id)
        if primary:
            names.append(primary)
        additional_names = trip.additional_destinations.values_list("name", flat=True)
        names.extend(additional_names)
        return _unique_preserve_order(names)

    package_trip_ids = []
    for trip in Trip.objects.all().iterator():
        names = get_trip_destination_names(trip)
        if _count_package_destinations(names) > 2:
            package_trip_ids.append(trip.id)

    if package_trip_ids:
        filter_kwargs = {
            category_fk_id_name: category.id,
            f"{trip_fk_id_name}__in": package_trip_ids,
        }
        existing_ids = set(
            through.objects.filter(**filter_kwargs).values_list(trip_fk_id_name, flat=True)
        )
        to_add = [
            through(**{trip_fk_id_name: trip_id, category_fk_id_name: category.id})
            for trip_id in package_trip_ids
            if trip_id not in existing_ids
        ]
        if to_add:
            through.objects.bulk_create(to_add)

    cleanup_filter = {category_fk_id_name: category.id}
    if package_trip_ids:
        through.objects.filter(**cleanup_filter).exclude(
            **{f"{trip_fk_id_name}__in": package_trip_ids}
        ).delete()
    else:
        through.objects.filter(**cleanup_filter).delete()


def remove_package_trip_category(apps, schema_editor):
    TripCategory = apps.get_model("web", "TripCategory")
    TripCategory.objects.filter(slug=PACKAGE_TRIP_CATEGORY_SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0036_remove_review_rating_remove_review_title"),
    ]

    operations = [
        migrations.RunPython(
            create_package_trip_category, remove_package_trip_category
        ),
    ]
