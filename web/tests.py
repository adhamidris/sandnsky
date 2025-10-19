from datetime import date, timedelta
from decimal import Decimal

from django.core import signing
from django.test import TestCase
from django.urls import reverse

from .models import (
    Booking,
    BookingExtra,
    Destination,
    DestinationName,
    Trip,
    TripExtra,
)


class BookingSubmissionTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            name=DestinationName.SIWA,
            tagline="Desert oasis",
            description="A serene escape",
            featured_position=1,
        )
        self.trip = Trip.objects.create(
            title="Oasis Adventure",
            destination=self.destination,
            teaser="Experience the desert magic",
            duration_days=3,
            group_size_max=12,
            base_price_per_person=Decimal("150.00"),
            tour_type_label="Small Group",
        )
        self.extra_camel = TripExtra.objects.create(
            trip=self.trip,
            name="Camel Safari",
            price=Decimal("75.00"),
            position=1,
        )
        self.extra_hot_air = TripExtra.objects.create(
            trip=self.trip,
            name="Hot Air Balloon",
            price=Decimal("120.00"),
            position=2,
        )

    def test_booking_form_submission_creates_booking_with_correct_totals(self):
        travel_date = date.today() + timedelta(days=30)
        url = reverse("web:trip-detail", args=[self.trip.slug])

        response = self.client.post(
            url,
            {
                "date": travel_date.isoformat(),
                "adults": "2",
                "children": "1",
                "infants": "0",
                "extras": [str(self.extra_camel.pk), str(self.extra_hot_air.pk)],
                "name": "Jordan Traveler",
                "email": "jordan@example.com",
                "phone": "+20123456789",
                "message": "Please arrange sunset viewing.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "booking_success.html")
        self.assertEqual(Booking.objects.count(), 1)

        booking = Booking.objects.get()
        self.assertEqual(booking.trip, self.trip)
        self.assertEqual(booking.travel_date, travel_date)
        self.assertEqual(booking.adults, 2)
        self.assertEqual(booking.children, 1)
        self.assertEqual(booking.infants, 0)
        self.assertEqual(booking.full_name, "Jordan Traveler")
        self.assertEqual(booking.email, "jordan@example.com")
        self.assertEqual(booking.phone, "+20123456789")
        self.assertEqual(booking.special_requests, "Please arrange sunset viewing.")

        expected_base = Decimal("150.00") * 3  # adults + children
        expected_extras = self.extra_camel.price + self.extra_hot_air.price
        expected_total = expected_base + expected_extras

        self.assertEqual(booking.base_subtotal, expected_base)
        self.assertEqual(booking.extras_subtotal, expected_extras)
        self.assertEqual(booking.grand_total, expected_total)

        extras = BookingExtra.objects.filter(booking=booking).order_by("extra__position")
        self.assertEqual(extras.count(), 2)
        self.assertEqual(extras[0].extra, self.extra_camel)
        self.assertEqual(extras[0].price_at_booking, self.extra_camel.price)
        self.assertEqual(extras[1].extra, self.extra_hot_air)
        self.assertEqual(extras[1].price_at_booking, self.extra_hot_air.price)

        self.assertContains(response, booking.reference_code)
        self.assertContains(response, "Thanks for choosing Sand &amp; Sky Tours")

    def test_success_page_requires_valid_token(self):
        url = reverse("web:booking-success")
        bad_response = self.client.get(url)
        self.assertEqual(bad_response.status_code, 404)

        booking = Booking.objects.create(
            trip=self.trip,
            travel_date=date.today(),
            adults=1,
            children=0,
            infants=0,
            full_name="Sam",
            email="sam@example.com",
            phone="123",
            special_requests="",
            base_subtotal=Decimal("150.00"),
            extras_subtotal=Decimal("0.00"),
            grand_total=Decimal("150.00"),
        )

        token = signing.dumps(booking.pk, salt="booking-success")
        response = self.client.get(f"{url}?ref={token}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, booking.reference_code)
