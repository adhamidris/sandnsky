import json
from datetime import date, timedelta
from decimal import Decimal

from django.core import mail, signing
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    Booking,
    BookingExtra,
    BookingReward,
    BookingConfirmationEmailSettings,
    Destination,
    DestinationName,
    RewardPhase,
    RewardPhaseTrip,
    Trip,
    TripExtra,
)
from .views import CartCheckoutView, BOOKING_CART_REFERENCE_SALT
from .booking_cart import (
    add_entry,
    apply_reward_selection,
    build_cart_entry,
    get_cart,
    summarize_cart,
)
from .rewards import (
    RewardComputationError,
    build_entry_snapshot,
    calculate_entry_reward,
    calculate_unlock_progress,
    get_reward_phases,
    invalidate_reward_phase_cache,
    normalize_reward_selections,
)


class RewardTestSetupMixin:
    def setUp(self):
        super().setUp()
        invalidate_reward_phase_cache()
        self.destination = Destination.objects.create(
            name=DestinationName.ALEXANDRIA,
            tagline="Coastal gem",
            description="Waves and wonders",
            featured_position=2,
        )
        self.primary_trip = Trip.objects.create(
            title="Mediterranean Escape",
            destination=self.destination,
            teaser="Sail into the sunset",
            duration_days=4,
            group_size_max=10,
            base_price_per_person=Decimal("200.00"),
            tour_type_label="Guided Tour",
        )
        self.secondary_trip = Trip.objects.create(
            title="Historic Alexandria Walk",
            destination=self.destination,
            teaser="Step back in time",
            duration_days=1,
            group_size_max=20,
            base_price_per_person=Decimal("80.00"),
            tour_type_label="Day Trip",
        )
        self.reward_phase = RewardPhase.objects.create(
            name="Voyager Savings",
            position=1,
            threshold_amount=Decimal("500.00"),
            discount_percent=Decimal("50.00"),
            currency="USD",
            headline="Unlock 50% off select adventures",
        )
        RewardPhaseTrip.objects.create(
            phase=self.reward_phase,
            trip=self.primary_trip,
            position=1,
        )

    def tearDown(self):
        invalidate_reward_phase_cache()
        super().tearDown()


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

    def test_cart_checkout_uses_single_reference_for_multiple_bookings(self):
        travel_date_one = date.today() + timedelta(days=45)
        travel_date_two = date.today() + timedelta(days=60)

        entries = [
            {
                "trip_id": self.trip.pk,
                "travel_date": travel_date_one.isoformat(),
                "adults": 2,
                "children": 0,
                "infants": 0,
                "pricing": {
                    "base_total_cents": "30000",
                    "extras_total_cents": "0",
                    "grand_total_cents": "30000",
                },
                "extras": [],
                "message": "First adventure",
            },
            {
                "trip_id": self.trip.pk,
                "travel_date": travel_date_two.isoformat(),
                "adults": 2,
                "children": 1,
                "infants": 0,
                "pricing": {
                    "base_total_cents": "45000",
                    "extras_total_cents": "0",
                    "grand_total_cents": "45000",
                },
                "extras": [],
                "message": "Second adventure",
            },
        ]

        contact = {
            "name": "Alex Traveler",
            "email": "alex@example.com",
            "phone": "+20123456789",
            "notes": "Looking forward to the journeys.",
        }

        view = CartCheckoutView()
        cart = {
            "entries": entries,
            "contact": {},
            "rewards": {},
        }
        bookings = view._create_bookings(cart, contact)

        self.assertEqual(len(bookings), 2)

        group_references = {booking.group_reference for booking in bookings}
        self.assertEqual(len(group_references), 1)
        shared_reference = group_references.pop()
        self.assertTrue(shared_reference)

        reference_codes = {booking.reference_code for booking in bookings}
        self.assertEqual(reference_codes, {shared_reference})

        token = signing.dumps(
            {
                "bookings": [booking.pk for booking in bookings],
                "contact": contact,
            },
            salt=BOOKING_CART_REFERENCE_SALT,
        )

        response = self.client.get(f"{reverse('web:booking-success')}?ref={token}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, shared_reference)
        self.assertNotContains(response, "+1 more")


class RewardServiceTests(RewardTestSetupMixin, TestCase):

    def test_get_reward_phases_returns_active_phase_with_trip(self):
        phases = get_reward_phases(active_only=True, use_cache=False)
        self.assertEqual(len(phases), 1)
        phase = phases[0]
        self.assertTrue(phase.is_active)
        self.assertEqual(phase.trips[0].trip_id, self.primary_trip.id)
        self.assertEqual(phase.discount_percent, Decimal("50.00"))

    def test_calculate_unlock_progress_reports_remaining_amount(self):
        phases = get_reward_phases(active_only=True, use_cache=False)
        progress = calculate_unlock_progress(
            total_cents=int(Decimal("350.00") * 100),
            phases=phases,
        )
        self.assertEqual(progress.unlocked_phase_ids, ())
        self.assertEqual(progress.next_phase_id, self.reward_phase.id)
        self.assertEqual(progress.remaining_to_next_cents, 15000)

    def test_calculate_entry_reward_applies_discount(self):
        entry = {
            "id": "entry-1",
            "trip_id": self.primary_trip.id,
            "adults": 2,
            "children": 1,
            "pricing": {
                "currency": "USD",
                "base_price_cents": 20000,
                "base_total_cents": 60000,
                "extras_total_cents": 5000,
                "grand_total_cents": 65000,
            },
        }
        snapshot = build_entry_snapshot(entry)
        phase = get_reward_phases(active_only=True, use_cache=False)[0]
        calculation = calculate_entry_reward(snapshot=snapshot, phase=phase)

        self.assertEqual(calculation.discount_cents, 30000)
        self.assertEqual(calculation.updated_base_total_cents, 30000)
        self.assertEqual(calculation.updated_grand_total_cents, 35000)

    def test_calculate_entry_reward_validates_trip_membership(self):
        entry = {
            "id": "entry-2",
            "trip_id": self.secondary_trip.id,
            "adults": 2,
            "children": 0,
            "pricing": {
                "currency": "USD",
                "base_price_cents": 8000,
                "base_total_cents": 16000,
                "extras_total_cents": 0,
                "grand_total_cents": 16000,
            },
        }
        snapshot = build_entry_snapshot(entry)
        phase = get_reward_phases(active_only=True, use_cache=False)[0]
        with self.assertRaises(RewardComputationError):
            calculate_entry_reward(snapshot=snapshot, phase=phase)

    def test_normalize_reward_selections_filters_invalid_payloads(self):
        raw = [
            {"entry_id": "entry-1", "phase_id": self.reward_phase.id, "trip_id": self.primary_trip.id},
            {"entry_id": "", "phase_id": 99, "trip_id": 100},
            {"entry_id": "entry-2", "phase_id": None, "trip_id": "abc"},
        ]
        normalized = normalize_reward_selections(raw)
        self.assertEqual(len(normalized), 1)
        selection = normalized["entry-1"]
        self.assertEqual(selection.phase_id, self.reward_phase.id)
        self.assertEqual(selection.trip_id, self.primary_trip.id)


class CartRewardsApiTests(RewardTestSetupMixin, TestCase):
    def _add_entry_to_session(self, *, adults=3, children=0, infants=0):
        session = self.client.session
        entry = build_cart_entry(
            self.primary_trip,
            {
                "date": date.today() + timedelta(days=30),
                "adults": adults,
                "children": children,
                "infants": infants,
                "extras": [],
                "message": "",
            },
        )
        add_entry(session, entry)
        session.save()
        return entry

    def test_rewards_summary_endpoint_returns_phase_info(self):
        self._add_entry_to_session(adults=3)

        response = self.client.get(reverse("web:booking-cart-rewards"))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        summary = data["cart_summary"]
        phases = summary["rewards"]["phases"]
        self.assertTrue(phases)
        phase_payload = phases[0]
        self.assertTrue(phase_payload["unlocked"])
        self.assertEqual(phase_payload["id"], self.reward_phase.id)

    def test_rewards_apply_endpoint_updates_session_and_totals(self):
        entry = self._add_entry_to_session(adults=3)

        payload = {
            "entry_id": entry["id"],
            "phase_id": self.reward_phase.id,
            "trip_id": self.primary_trip.id,
        }
        response = self.client.post(
            reverse("web:booking-cart-rewards-apply"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        summary = data["cart_summary"]
        entry_summary = summary["entries"][0]
        self.assertEqual(entry_summary["discount_total_cents"], 30000)
        self.assertEqual(summary["discount_total_cents"], 30000)

        cart = get_cart(self.client.session)
        rewards_map = cart.get("rewards", {})
        self.assertIn(entry["id"], rewards_map)

    def test_rewards_remove_endpoint_clears_selection(self):
        entry = self._add_entry_to_session(adults=3)
        apply_payload = {
            "entry_id": entry["id"],
            "phase_id": self.reward_phase.id,
            "trip_id": self.primary_trip.id,
        }
        self.client.post(
            reverse("web:booking-cart-rewards-apply"),
            data=json.dumps(apply_payload),
            content_type="application/json",
        )

        remove_response = self.client.post(
            reverse("web:booking-cart-rewards-remove"),
            data=json.dumps({"entry_id": entry["id"]}),
            content_type="application/json",
        )
        self.assertEqual(remove_response.status_code, 200)

        summary = remove_response.json()["cart_summary"]
        entry_summary = summary["entries"][0]
        self.assertEqual(entry_summary["discount_total_cents"], 0)
        self.assertEqual(summary["discount_total_cents"], 0)

        cart = get_cart(self.client.session)
        rewards_map = cart.get("rewards", {})
        self.assertNotIn(entry["id"], rewards_map)


class CartRewardsCheckoutTests(RewardTestSetupMixin, TestCase):
    def _add_discounted_entry(self):
        session = self.client.session
        entry = build_cart_entry(
            self.primary_trip,
            {
                "date": date.today() + timedelta(days=10),
                "adults": 3,
                "children": 0,
                "infants": 0,
                "extras": [],
                "message": "",
            },
        )
        add_entry(session, entry)
        apply_reward_selection(
            session,
            entry_id=entry["id"],
            phase_id=self.reward_phase.id,
            trip_id=self.primary_trip.id,
        )
        session.save()
        return entry

    def test_checkout_persists_booking_reward_records(self):
        self._add_discounted_entry()
        cart = get_cart(self.client.session)
        contact = {
            "name": "Taylor Traveler",
            "email": "taylor@example.com",
            "phone": "+201001234567",
            "notes": "",
        }

        view = CartCheckoutView()
        bookings = view._create_bookings(cart, contact)

        self.assertEqual(len(bookings), 1)
        booking = bookings[0]
        booking.refresh_from_db()

        self.assertEqual(booking.base_subtotal, Decimal("300.00"))
        self.assertEqual(booking.extras_subtotal, Decimal("0.00"))
        self.assertEqual(booking.grand_total, Decimal("300.00"))

        rewards = BookingReward.objects.filter(booking=booking)
        self.assertEqual(rewards.count(), 1)
        reward_record = rewards.get()
        self.assertEqual(reward_record.discount_amount, Decimal("300.00"))
        self.assertEqual(reward_record.reward_phase_id, self.reward_phase.id)


class BookingConfirmationEmailTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            name=DestinationName.CAIRO,
            tagline="City of a Thousand Minarets",
            description="Historic capital with vibrant culture.",
            featured_position=5,
        )
        self.trip = Trip.objects.create(
            title="Nile Discovery Cruise",
            destination=self.destination,
            teaser="Sail the Nile and explore iconic temples.",
            duration_days=5,
            group_size_max=14,
            base_price_per_person=Decimal("450.00"),
            tour_type_label="Guided Journey",
        )
        self.booking_kwargs = {
            "trip": self.trip,
            "travel_date": date.today() + timedelta(days=40),
            "adults": 2,
            "children": 0,
            "infants": 0,
            "full_name": "Alex Voyager",
            "email": "alex@example.com",
            "phone": "+201201234567",
            "special_requests": "",
            "base_subtotal": Decimal("900.00"),
            "extras_subtotal": Decimal("0.00"),
            "grand_total": Decimal("900.00"),
        }

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_sent_when_status_transitions_to_confirmed(self):
        config = BookingConfirmationEmailSettings.get_solo()
        config.is_enabled = True
        config.from_email = "reservations@example.com"
        config.save()

        booking = Booking.objects.create(**self.booking_kwargs)
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status", "status_updated_at"])

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.from_email, "reservations@example.com")
        self.assertEqual(message.to, ["alex@example.com"])
        self.assertIn("confirmed", message.subject.lower())

        booking.save()
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_skipped_when_feature_disabled(self):
        config = BookingConfirmationEmailSettings.get_solo()
        config.is_enabled = False
        config.save()

        booking = Booking.objects.create(**self.booking_kwargs)
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status", "status_updated_at"])

        self.assertEqual(len(mail.outbox), 0)
