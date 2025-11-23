from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from seo.middleware import SeoRedirectMiddleware
from seo.models import PageType, SeoEntry, SeoRedirect
from seo.resolver import build_seo_context, resolve_seo_entry
from web.models import Destination, Trip


class SeoResolverTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(name="Siwa")
        self.trip = Trip.objects.create(
            title="Desert Escape",
            destination=self.destination,
            teaser="Explore the dunes.",
            duration_days=3,
            group_size_max=6,
            base_price_per_person=1000,
            tour_type_label="Adventure",
        )

    def test_fallback_trip_returns_path_and_flags(self):
        resolved = resolve_seo_entry(page_type=PageType.TRIP, obj=self.trip)
        self.assertTrue(resolved.status_flags.get("fallback"))
        self.assertIn("/trips/", resolved.path)
        self.assertEqual(resolved.meta_title, "Desert Escape")
        self.assertEqual(resolved.meta_description, "Explore the dunes.")

    def test_build_seo_context_uses_entry(self):
        entry = SeoEntry.objects.create(
            page_type=PageType.TRIP,
            content_object=self.trip,
            slug=self.trip.slug,
            path=f"/trips/{self.trip.slug}/",
            meta_title="Custom Title",
            meta_description="Custom description.",
            alt_text="Custom alt",
            canonical_url="/canonical-path/",
        )
        context = build_seo_context(page_type=PageType.TRIP, obj=self.trip, path=entry.path, og_image_url="img.jpg")
        seo = context["seo"]
        self.assertEqual(seo.meta_title, "Custom Title")
        self.assertEqual(seo.canonical_url, "/canonical-path/")
        self.assertEqual(context["seo_og_image"], "img.jpg")


class SeoRedirectMiddlewareTests(TestCase):
    def setUp(self):
        self.middleware = SeoRedirectMiddleware(lambda request: HttpResponse("ok"))
        SeoRedirect.objects.create(from_path="/old/", to_path="/new/", is_permanent=True)

    def test_permanent_redirect_preserves_query(self):
        factory = RequestFactory()
        request = factory.get("/old/?a=1")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/new/?a=1")
