from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from web.models import BlogCategory, BlogPost, BlogPostStatus, BlogSection

POST_CATEGORY = "Beauty beaches"
POST_TITLE = "Why you should travel to Hurghada Egypt"
POST_SUBTITLE = ""
PUBLISHED_AT = timezone.make_aware(timezone.datetime(2025, 2, 15, 9, 0, 0))

EXCERPT = (
    "Warm weather, short flight times from Europe, excellent value, and world-class Red Sea reefs—"
    "here’s why Hurghada, Egypt should be on your next-holiday shortlist."
)

INTRO = (
    "Should I travel to Egypt? Where should I go next? If you’re weighing your holiday options, "
    "Hurghada on Egypt’s Red Sea offers sun-sure weather, easy access from Europe, great prices, "
    "resort comfort, and plenty to do—from scuba diving to desert safaris."
)

SECTIONS = [
    {
        "heading": "1) Weather in Hurghada, Egypt",
        "location_label": "Hurghada, Red Sea",
        "body": (
            "If sunshine is non-negotiable, Hurghada delivers. Days are typically warm year-round; "
            "winter evenings can be breezy and a bit cool, but daytime temperatures often sit around 20–25°C. "
            "Rain is rare, so if you want a high chance of blue skies, Hurghada is a strong bet."
        ),
    },
    {
        "heading": "2) Location",
        "location_label": "Close to Europe",
        "body": (
            "From much of Northern Europe and the UK, flights to Hurghada are roughly five hours—"
            "far shorter than long-haul alternatives to Asia (~12 hours). For a 1-week break, "
            "less time in the air means more time by the sea."
        ),
    },
    {
        "heading": "3) Price level",
        "location_label": "Great value",
        "body": (
            "Egypt is excellent value for travelers using foreign currencies. While local prices can shift, "
            "visitors generally find food, activities, and transport competitively priced—ideal if you want "
            "a quality beach holiday without a luxury-price sting."
        ),
    },
    {
        "heading": "4) History",
        "location_label": "Day trips from the Red Sea",
        "body": (
            "Pyramids, the Sphinx, the Egyptian Museum, the Valley of the Kings, Karnak and Luxor Temples, Abu Simbel—"
            "Egypt’s icons are within reach via organized day trips or short itineraries from Hurghada. "
            "Blend beach time with ancient wonders."
        ),
    },
    {
        "heading": "5) Hotel resorts",
        "location_label": "Hurghada • El Gouna • Sahl Hasheesh • Makadi Bay",
        "body": (
            "The Red Sea Riviera is lined with resorts spanning family-friendly all-inclusive stays to chic boutique escapes. "
            "Expect pools, private beaches, gyms, spas, aqua parks, and varied dining—an easy, self-contained holiday setup."
        ),
    },
    {
        "heading": "6) Scuba diving & other activities",
        "location_label": "Red Sea",
        "body": (
            "Hurghada is a gateway to some of the world’s most beloved dive sites: coral gardens, vibrant reefs, "
            "and abundant marine life. Not a diver? Try snorkeling, glass-bottom boats, desert safaris, the Grand Aquarium, "
            "Hurghada Sand City, Mini Egypt Park, horseback riding, and more."
        ),
    },
    {
        "heading": "7) People",
        "location_label": "Local hospitality",
        "body": (
            "Behind every vendor is a person—Egyptians are famously warm and family-oriented. "
            "In Hurghada, expect smiles, help with kids, and a welcoming attitude across hotels, shops, and tours."
        ),
    },
    {
        "heading": "8) Relaxation",
        "location_label": "Holiday mode: ON",
        "body": (
            "Everyone needs a proper switch-off now and then. With the sea, the sun, and simple logistics, "
            "Hurghada makes it easy to relax—whether you’re a couple, family, or solo traveler."
        ),
    },
    {
        "heading": "Safety note",
        "location_label": "Practical info",
        "body": (
            "Egypt consistently features in ‘safe to visit’ roundups, and major destinations—from Cairo and Luxor to "
            "Sharm El Sheikh, Hurghada, and Marsa Alam—are well-trodden by tourists. As with any trip, stay updated on "
            "official travel advisories, keep prescriptions on hand, dress for a dry, sunny climate, and hydrate well."
        ),
    },
]

class Command(BaseCommand):
    help = "Seeds the blog post ‘Why you should travel to Hurghada Egypt’ under the ‘Beauty beaches’ category with sections. Idempotent."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding blog: Why you should travel to Hurghada Egypt"))

        category, _ = BlogCategory.objects.get_or_create(name=POST_CATEGORY)
        # Ensure slug generation via model.save()
        category.save()

        post, created = BlogPost.objects.get_or_create(
            title=POST_TITLE,
            defaults={
                "subtitle": POST_SUBTITLE,
                "category": category,
                "excerpt": EXCERPT,
                "intro": INTRO,
                "status": BlogPostStatus.PUBLISHED,
                "published_at": PUBLISHED_AT,
                "seo_title": POST_TITLE,
                "seo_description": "Warm weather, short flights, great value, and Red Sea adventures—why Hurghada belongs on your list.",
                "read_time_minutes": 6,
            },
        )

        if not created:
            # Keep it idempotent but ensure fields reflect latest copy
            post.category = category
            post.subtitle = POST_SUBTITLE
            post.excerpt = EXCERPT
            post.intro = INTRO
            post.status = BlogPostStatus.PUBLISHED
            post.published_at = PUBLISHED_AT
            post.seo_title = POST_TITLE
            post.seo_description = "Warm weather, short flights, great value, and Red Sea adventures—why Hurghada belongs on your list."
            if not post.read_time_minutes:
                post.read_time_minutes = 6
            post.save()

        # Rebuild sections deterministically
        BlogSection.objects.filter(post=post).delete()
        for idx, sec in enumerate(SECTIONS, start=1):
            BlogSection.objects.create(
                post=post,
                position=idx,
                heading=sec["heading"],
                location_label=sec.get("location_label", ""),
                body=sec["body"],
            )

        self.stdout.write(self.style.SUCCESS(
            f"Post {'created' if created else 'updated'}: {post.title} (slug={post.slug})"
        ))
        self.stdout.write(self.style.MIGRATE_LABEL("Done."))
