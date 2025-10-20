# web/management/commands/seed_blog_top8_unusual_places.py

from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from web.models import (
    BlogCategory,
    BlogPost,
    BlogSection,
    BlogPostStatus,
)

POST_TITLE = "Top 8 Travel unusual places to see in Egypt"
CATEGORY_NAME = "Ancient Egypt"
PUBLISHED_AT = datetime(2025, 2, 15, 9, 0, 0)  # 09:00 local; adjust as you like

INTRO = (
    "Egypt, a nation of ancient civilization, thousands of years of customs, an ancient governing "
    "structure totally different from most of the world, famous for its pyramids, sculptures, culture, "
    "traditional facilities and numerous Hollywood movie appearances. If you’ve seen a movie dating back to "
    "ancient civilizations with a lost city, there’s a fair chance Egypt has something to do with the storyline. "
    "Here are the Top 8 unusual places to see in Egypt."
)

EXCERPT = (
    "Looking for Egypt’s lesser-known gems? From a sunken city and nilometers to desert art and mushroom-like "
    "rock formations, these are the Top 8 unusual places to see in Egypt."
)

SECTIONS = [
    {
        "heading": "1. The Lost City of Heracleion",
        "location": "Alexandria, Egypt",
        "body": (
            "After years of relentless exploration, a legend lost to time—a city submerged deep underwater—"
            "was discovered by Franck Goddio and his crew. Abu Qir Bay in Egypt’s coastal waters is where the "
            "city of myths was finally located. Among the finds were ~700 anchors, ~64 ships, and the remains "
            "of the massive Temple of Amun-Gereb, plus a trove of gold coins. Many sculptures are astonishingly "
            "well preserved after ~2,300 years. Urban planning visible from the ruins suggests one of the "
            "largest ports of its era."
        ),
    },
    {
        "heading": "2. The Ancient Instrument: Nilometer",
        "location": "Cairo, Egypt",
        "body": (
            "The nilometer was an ancient instrument Egyptians used to measure Nile water levels, helping "
            "predict floods and droughts. Three main forms existed: (1) a stilling well with a marked column, "
            "accessed by steps for priests to read levels; (2) stepped stairways descending to the river with "
            "height markings; and (3) a canal-fed cistern with level marks carved into its walls. These readings "
            "guided farmers, traders, and officials long before modern hydrology."
        ),
    },
    {
        "heading": "3. The Time-Keeping Temple of Abu Simbel",
        "location": "Abu Simbel, Nubia, Egypt",
        "body": (
            "Carved into a mountainside by order of Pharaoh Ramesses II, Abu Simbel is a masterpiece of "
            "ancient engineering. The temple’s inner sanctum is aligned so that on specific days the sun "
            "illuminates statues of Amun-Ra and Ramesses—while Ptah remains in shadow—marking important dates. "
            "In the 1960s the entire complex was relocated to save it from flooding, yet the solar phenomenon "
            "still works as designed. Completed around 1244 BCE, it remains one of Egypt’s most remarkable sites."
        ),
    },
    {
        "heading": "4. The Well-Preserved Hathor Temple",
        "location": "Dendera, Egypt",
        "body": (
            "Despite centuries of soot and sand, the Temple of Hathor at Dendera retains vivid colors and "
            "intricate reliefs after careful cleaning. The complex features multiple temples, including Hathor’s "
            "main temple, a birthing house at the front, and a temple of Isis to the rear. The famed ‘Dendera "
            "light bulb’ reliefs are found in the underground crypts (guide access required). Hathor—often linked "
            "with love, joy, and motherhood—was considered the companion of Horus."
        ),
    },
    {
        "heading": "5. The City of the Dead",
        "location": "El-Saf, Egypt",
        "body": (
            "A functioning cemetery with a sea of white conical domes and mausoleums, the City of the Dead "
            "is unusual and atmospheric. It offers a somber window into traditions that span centuries. "
            "Visitors should dress and behave respectfully—it is an active burial ground as well as a historic site."
        ),
    },
    {
        "heading": "6. Theban Necropolis & Colossi of Memnon",
        "location": "Luxor, Egypt",
        "body": (
            "The twin statues of the Colossi of Memnon—depicting Pharaoh Amenhotep III—have withstood ~3,400 years "
            "of sun, wind, and floods. Though their features are weathered, their scale still stuns. Ancient "
            "earthquakes caused fractures; later Roman-era repairs altered the originals. The wider Theban "
            "Necropolis brims with tombs, temples, and layers of history—catnip for photographers and history buffs."
        ),
    },
    {
        "heading": "7. The White Desert",
        "location": "Al Farafrah, Egypt",
        "body": (
            "An otherworldly landscape of chalk and limestone formations sculpted by wind and time, the White "
            "Desert looks like open-air abstract art. Iconic shapes like ‘the Mushroom’ and ‘the Chicken’ draw "
            "adventurers and photographers seeking silence, stars, and surreal geology."
        ),
    },
    {
        "heading": "8. Desert Breath",
        "location": "Qesm Hurghada, Egypt",
        "body": (
            "A monumental land art installation formed by synchronized conical mounds and depressions in the sand. "
            "Created to weather and fade, it has softened over the decades yet remains a striking counterpoint to "
            "Egypt’s ancient monuments—a contemplative, modern artwork set in the desert."
        ),
    },
]

FOOTER_NOTE = (
    "Travel tips: Some sites undergo upgrades—check access and timing. If you have medical conditions, keep your "
    "prescriptions handy. Expect dry heat much of the year; wear suitable clothing and carry plenty of water."
)


def _estimate_read_time_minutes(*texts, wpm=200):
    total_words = 0
    for t in texts:
        if not t:
            continue
        total_words += len(t.split())
    minutes = max(1, round(total_words / wpm))
    return minutes


class Command(BaseCommand):
    help = "Seeds the blog post and card for 'Top 8 Travel unusual places to see in Egypt' (images left blank)."

    @transaction.atomic
    def handle(self, *args, **options):
        # Category
        category, _ = BlogCategory.objects.get_or_create(
            name=CATEGORY_NAME,
            defaults={"description": "Stories and insights from Ancient Egypt."},
        )

        # Publish date (timezone-aware in the current timezone)
        aware_published_at = timezone.make_aware(PUBLISHED_AT, timezone.get_current_timezone())

        # Post (idempotent by title)
        post, created = BlogPost.objects.get_or_create(
            title=POST_TITLE,
            defaults={
                "subtitle": "Ancient Egypt — February 15, 2025",
                "category": category,
                "excerpt": EXCERPT,
                "intro": INTRO,
                "status": BlogPostStatus.PUBLISHED,
                "published_at": aware_published_at,
                "seo_title": "Top 8 Unusual Places to See in Egypt",
                "seo_description": "From a sunken city and nilometers to desert land art—discover Egypt’s 8 most unusual places.",
            },
        )

        # If it already existed, update core fields (but keep images blank as requested)
        if not created:
            post.category = category
            post.subtitle = "Ancient Egypt — February 15, 2025"
            post.excerpt = EXCERPT
            post.intro = INTRO
            post.status = BlogPostStatus.PUBLISHED
            post.published_at = aware_published_at
            post.seo_title = "Top 8 Unusual Places to See in Egypt"
            post.seo_description = "From a sunken city and nilometers to desert land art—discover Egypt’s 8 most unusual places."
            # Leave hero_image and card_image untouched/blank per request
            post.save()

        # Compute read time from intro + sections + footer
        read_time = _estimate_read_time_minutes(
            post.intro,
            *(s["body"] for s in SECTIONS),
            FOOTER_NOTE,
        )
        if post.read_time_minutes != read_time:
            post.read_time_minutes = read_time
            post.save(update_fields=["read_time_minutes"])

        # Sections: replace for clean ordering/idempotency
        post.sections.all().delete()

        for idx, sec in enumerate(SECTIONS, start=1):
            BlogSection.objects.create(
                post=post,
                position=idx,
                heading=sec["heading"],
                location_label=sec["location"],
                body=sec["body"],
                # section_image left blank intentionally
            )

        # Optional closing/tips section (not numbered)
        BlogSection.objects.create(
            post=post,
            position=len(SECTIONS) + 1,
            heading="Before You Go",
            location_label="Egypt — Practical Tips",
            body=FOOTER_NOTE,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded blog post '{post.title}' (published_at={post.published_at:%Y-%m-%d %H:%M}, "
            f"read_time≈{post.read_time_minutes} min). Images left blank as requested."
        ))
