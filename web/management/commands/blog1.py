from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from web.models import BlogCategory, BlogPost, BlogPostStatus, BlogSection

POST_CATEGORY = "Ancient Egypt"
POST_TITLE = "Why You Should Plan an Egypt Trip in 2025"
POST_SUBTITLE = ""
PUBLISHED_AT = timezone.make_aware(timezone.datetime(2025, 2, 15, 9, 0, 0))

EXCERPT = (
    "Temples, tombs, Nile cruises, Red Sea reefs, delicious food, and world-class museums—"
    "here are compelling reasons to make 2025 the year you finally visit Egypt."
)

INTRO = (
    "Dreaming of pyramids, golden masks, and sailing the Nile? If Egypt is on your bucket list, "
    "2025 is a fantastic time to go. From value for money and short flight times from Europe to "
    "history, beaches, and museums, here are nine reasons to start planning."
)

SECTIONS = [
    {
        "heading": "1) Egypt Welcomes Visitors",
        "location_label": "Nationwide",
        "body": (
            "Egypt’s tourism infrastructure is open and operating, with major archaeological sites and museums—"
            "from the Pyramids and Sphinx to Abu Simbel, Karnak, the Valley of the Kings, and more—receiving visitors. "
            "Beach hubs like Hurghada, Sharm El Sheikh, and Marsa Alam continue to host sun-seekers year-round."
        ),
    },
    {
        "heading": "2) Great Value for Money",
        "location_label": "Countrywide",
        "body": (
            "Egypt remains an excellent value destination across accommodation, dining, guides, transport, and activities. "
            "Package tours can bundle hotels, transport, entrances, and Egyptologist guides for a price that often undercuts "
            "DIY planning—especially in shoulder seasons."
        ),
    },
    {
        "heading": "3) Fascinating History Everywhere",
        "location_label": "Cairo • Luxor • Aswan • Alexandria",
        "body": (
            "From Old Kingdom pyramids to New Kingdom temples and Greco-Roman legacies, Egypt’s timeline stretches millennia. "
            "Guided visits unlock deeper context around iconic names—Tutankhamun, Ramesses, Hatshepsut, Cleopatra—"
            "and the discoveries that still emerge today."
        ),
    },
    {
        "heading": "4) A Nile Cruise You’ll Never Forget",
        "location_label": "Luxor ↔ Aswan",
        "body": (
            "Sail past palm groves and desert escarpments while visiting riverside temples. Nile cruises suit a range of budgets, "
            "typically including full board and guided excursions—an easy, scenic way to connect Luxor, Esna, Edfu, Kom Ombo, and Aswan."
        ),
    },
    {
        "heading": "5) Red Sea Beaches & Diving",
        "location_label": "Hurghada • Sharm El Sheikh • Dahab",
        "body": (
            "Egypt is also a beach destination. Expect warm water, healthy reefs, snorkeling, glass-bottom boats, "
            "and renowned dive sites like Dahab’s Blue Hole. New and experienced divers alike will find excellent training and guiding."
        ),
    },
    {
        "heading": "6) Museums That Wow",
        "location_label": "Cairo • Luxor • Aswan",
        "body": (
            "The Egyptian Museum in Cairo hosts a vast trove of antiquities, while the Luxor Museum focuses on high-quality, "
            "beautifully presented pieces. In Aswan, the Nubian Museum adds rich regional context. A knowledgeable guide "
            "can help you prioritize highlights among thousands of artifacts."
        ),
    },
    {
        "heading": "7) Mind-Blowing Temples",
        "location_label": "Nationwide",
        "body": (
            "Karnak’s forest of columns, Luxor Temple’s regal avenue, the terraced perfection of Hatshepsut’s temple, "
            "the twin cliff-cut sanctuaries at Abu Simbel, Medinet Habu’s reliefs, Kom Ombo’s dual sanctuaries, "
            "and Edfu’s preservation—each brings ancient Egypt vividly to life."
        ),
    },
    {
        "heading": "8) Delicious Egyptian Food",
        "location_label": "Countrywide",
        "body": (
            "Expect vegetable-forward plates alongside chicken, duck, and seafood: koshari, ta’meya and ful medames, "
            "kebabs and kofta, and the beloved dessert om ali. Along the coast, fresh fish and Red Sea specialties shine."
        ),
    },
    {
        "heading": "9) The Long-Anticipated Grand Egyptian Museum (GEM)",
        "location_label": "Giza Plateau",
        "body": (
            "The new museum project near the Pyramids has been one of the most anticipated cultural openings in the world. "
            "Keep an eye on official updates as you plan—paired with Giza’s monuments, it will anchor many Cairo itineraries."
        ),
    },
]

class Command(BaseCommand):
    help = "Seeds the blog post ‘Why You Should Plan an Egypt Trip in 2025’ under ‘Ancient Egypt’ with structured sections. Idempotent."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding blog: Why You Should Plan an Egypt Trip in 2025"))

        category, _ = BlogCategory.objects.get_or_create(name=POST_CATEGORY)
        # Ensure slug generation
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
                "seo_description": "Nine compelling reasons to plan your Egypt trip in 2025—from Nile cruises to Red Sea beaches.",
                "read_time_minutes": 8,
            },
        )

        if not created:
            post.category = category
            post.subtitle = POST_SUBTITLE
            post.excerpt = EXCERPT
            post.intro = INTRO
            post.status = BlogPostStatus.PUBLISHED
            post.published_at = PUBLISHED_AT
            post.seo_title = POST_TITLE
            post.seo_description = "Nine compelling reasons to plan your Egypt trip in 2025—from Nile cruises to Red Sea beaches."
            if not post.read_time_minutes:
                post.read_time_minutes = 8
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
