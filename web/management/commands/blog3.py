from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from web.models import BlogCategory, BlogPost, BlogPostStatus, BlogSection

POST_TITLE = "Top 8 Travel unusual places to see in Egypt"
POST_SUBTITLE = ""  # optional
POST_CATEGORY = "Ancient Egypt"
POST_STATUS = BlogPostStatus.PUBLISHED  # publish
# Feb 15, 2025 — keep tz-aware; assumes project TIME_ZONE is configured
PUBLISHED_AT = timezone.make_aware(timezone.datetime(2025, 2, 15, 9, 0, 0))

EXCERPT = (
    "From submerged ancient cities to modern land art in the desert, these eight unusual places "
    "reveal a different side of Egypt beyond the classic pyramid postcard."
)

INTRO = (
    "Egypt’s story stretches far beyond the famous pyramids and templ es. If you’re looking for "
    "sites that are a little unexpected—places where myth, ingenuity, and raw landscape meet—"
    "start with this curated list of eight unusual spots across the country."
)

SECTIONS = [
    {
        "heading": "The Lost City of Heracleion",
        "location": "Alexandria, Egypt",
        "body": (
            "Long considered a legend, Heracleion (near Abu Qir Bay) was rediscovered by archaeologist "
            "Franck Goddio and his team after years of underwater exploration. Among the finds: ~700 anchors, "
            "64 ships, gold coins, and the remains of the Temple of Amun-Gereb—remarkably preserved after ~2,300 years. "
            "The city’s layout hints at its role as a major ancient port."
        ),
    },
    {
        "heading": "The Ancient Instrument: Nilometer",
        "location": "Cairo, Egypt",
        "body": (
            "Nilometers measured the Nile’s water level to forecast floods and droughts—vital for agriculture and trade. "
            "Ancient Egyptians used three main types: a stilling well with a marked column, stairways descending to the "
            "river with level marks, and a canal-fed cistern with wall markings. These devices reflect sophisticated "
            "hydrology and planning dating back millennia."
        ),
    },
    {
        "heading": "Abu Simbel’s Time-Keeping Alignment",
        "location": "Abu Simbel, Nubia (from Aswan)",
        "body": (
            "Carved into the cliff under Ramesses II, Abu Simbel is famed for its solar alignment: twice yearly, sunlight "
            "pierces the temple to illuminate statues in the inner sanctum—traditionally Amun-Ra and Ramesses—while Ptah "
            "remains in shadow. The entire complex was relocated in the 1960s to escape Lake Nasser’s rising waters, "
            "yet the spectacle endures (original completion c. 1244 BCE)."
        ),
    },
    {
        "heading": "The Well-Preserved Temple of Hathor",
        "location": "Dendera (Dandarah), Egypt",
        "body": (
            "Despite centuries of soot and drifting sands, Dendera’s Hathor Temple retains vivid color and intricate "
            "reliefs after careful cleaning. The complex features multiple temples (including a birth house and a rear "
            "temple to Isis). The famed ‘Dendera Light’ relief resides in an underground crypt accessible with a guide."
        ),
    },
    {
        "heading": "The City of the Dead",
        "location": "Al-Saf / Cairo Necropolis, Egypt",
        "body": (
            "A living cemetery comprising tombs, mausolea, and distinctive white domes, the City of the Dead remains a "
            "place of active remembrance. Visitors should dress and behave respectfully—this is a community as much as "
            "a historical landscape."
        ),
    },
    {
        "heading": "Theban Necropolis & the Colossi of Memnon",
        "location": "Luxor, Egypt",
        "body": (
            "The twin statues of Amenhotep III have withstood ~3,400 years of floods, heat, and earthquakes. One once "
            "emitted a dawn ‘song’ after cracking—later Roman repairs altered the acoustics. The broader West Bank necropolis "
            "encapsulates Egypt’s mortuary grandeur and engineering."
        ),
    },
    {
        "heading": "The White Desert",
        "location": "Al-Farafra, Egypt",
        "body": (
            "An open-air gallery of wind-sculpted chalk formations—‘mushrooms,’ ‘monoliths,’ and surreal silhouettes. "
            "The White Desert offers otherworldly campscapes for travelers seeking raw geology over crowds."
        ),
    },
    {
        "heading": "Desert Breath",
        "location": "Qesm Hurghada, Egypt",
        "body": (
            "A monumental land-art installation formed by paired cones (excavated depressions and raised mounds) arranged "
            "in a spiral progression. Designed to erode slowly back into the landscape, it offers a striking modern counterpoint "
            "to Egypt’s ancient monuments."
        ),
    },
]

class Command(BaseCommand):
    help = "Seeds the blog post ‘Top 8 Travel unusual places to see in Egypt’ with category, excerpt, intro, and 8 sections. Safe to run multiple times."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding blog: Top 8 Travel unusual places to see in Egypt"))  # noqa: E501

        category, _ = BlogCategory.objects.get_or_create(name=POST_CATEGORY)
        # Save once to ensure slug generation (editable=False)
        category.save()

        post, created = BlogPost.objects.get_or_create(
            title=POST_TITLE,
            defaults={
                "subtitle": POST_SUBTITLE,
                "category": category,
                "excerpt": EXCERPT,
                "intro": INTRO,
                "status": POST_STATUS,
                "published_at": PUBLISHED_AT,
                "seo_title": POST_TITLE,
                "seo_description": "Eight unusual places in Egypt—from a sunken city to land art in the desert.",
                "read_time_minutes": 7,
            },
        )

        # If it already existed, ensure core fields are updated (idempotent)
        if not created:
            post.category = category
            post.subtitle = POST_SUBTITLE
            post.excerpt = EXCERPT
            post.intro = INTRO
            post.status = POST_STATUS
            post.published_at = PUBLISHED_AT
            post.seo_title = POST_TITLE
            post.seo_description = "Eight unusual places in Egypt—from a sunken city to land art in the desert."
            post.read_time_minutes = post.read_time_minutes or 7
            post.save()

        # (Re)build sections in order
        BlogSection.objects.filter(post=post).delete()
        for idx, sec in enumerate(SECTIONS, start=1):
            BlogSection.objects.create(
                post=post,
                position=idx,
                heading=sec["heading"],
                location_label=sec["location"],
                body=sec["body"],
            )

        self.stdout.write(self.style.SUCCESS(
            f"Post {'created' if created else 'updated'}: {post.title} (slug={post.slug})"
        ))
        self.stdout.write(self.style.MIGRATE_LABEL("Done."))
