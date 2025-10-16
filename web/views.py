import copy

from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from .forms import BookingRequestForm

CURRENCY_SYMBOLS = {"USD": "$"}


def format_currency(amount, currency="USD"):
    symbol = CURRENCY_SYMBOLS.get(currency.upper(), "")
    if symbol:
        return f"{symbol}{amount:,.2f}"
    return f"{amount:,.2f} {currency.upper()}"


DEFAULT_LANGUAGES = [
    {"code": "EN", "label": "English"},
    {"code": "ES", "label": "Español"},
    {"code": "IT", "label": "Italian"},
    {"code": "RU", "label": "Russian"},
]

DEFAULT_EXTRAS = [
    {"id": "airport-transfer", "label": "Airport pickup & drop-off", "price": 15.0},
    {"id": "horse-riding", "label": "Horse riding experience", "price": 15.0},
]

DEFAULT_FAQS = [
    {
        "question": "Is this tour suitable for families?",
        "answer": "Absolutely. We regularly host families and can adjust pacing, meal preferences, and vehicle assignments to make the experience comfortable for travelers of all ages.",
    },
    {
        "question": "Can you accommodate dietary requirements?",
        "answer": "Yes. Let us know about dietary needs when you book and our team will confirm available meal options with our local partners before your trip.",
    },
    {
        "question": "Do I need to pay a deposit now?",
        "answer": "A small deposit secures your reservation. The balance is due closer to departure once final details are confirmed.",
    },
    {
        "question": "What should I pack?",
        "answer": "We recommend comfortable walking shoes, layered clothing, sun protection, and any medications you rely on daily. A detailed packing list is provided after booking.",
    },
    {
        "question": "Are entrance fees included?",
        "answer": "Yes, all scheduled entrance fees mentioned in the itinerary are included. Optional experiences can be arranged at additional cost.",
    },
    {
        "question": "How far in advance should I book?",
        "answer": "Peak seasons fill up quickly. We advise booking at least 4–6 weeks ahead to secure your preferred dates, especially for larger groups.",
    },
    {
        "question": "Can I customize this itinerary?",
        "answer": "Of course. Our travel specialists can tailor the route, pace, and accommodations to match your interests. Contact us to start personalizing your experience.",
    },
]

TRIP_DETAILS = {
    "pyramids-giza": {
        "slug": "pyramids-giza",
        "title": "Pyramids of Giza Experience",
        "category": "Historical",
        "hero_image": "img/hero-pyramids.jpg",
        "card_image": "img/hero-pyramids.jpg",
        "summary": "Explore the last standing wonder of the ancient world with expert Egyptologist guides.",
        "lead": "Spend a full day immersed in Egypt's most iconic UNESCO World Heritage Site with priority access and insider storytelling.",
        "overview_paragraphs": [
            "Your private guide will walk you through the Pyramids of Giza complex from multiple vantage points, sharing lesser-known stories about the pharaohs who commissioned these monuments.",
            "Enjoy time to explore the plateau, snap photos from panoramic viewpoints, and savor a traditional Egyptian lunch before returning to your hotel.",
        ],
        "tour_length": "1 Day",
        "tour_type": "Daily Tour — Historical Wonders",
        "group_size": 15,
        "base_price": 120.0,
        "currency": "USD",
        "primary_destination": "Cairo",
        "destinations": ["Cairo", "Giza"],
        "highlights": [
            "Visit the Great Pyramid of Khufu",
            "Explore inside the pyramids",
            "See the Great Sphinx up close",
            "Visit the Solar Boat Museum",
            "Professional photography session",
            "Traditional Egyptian lunch included",
        ],
        "itinerary_days": [
            {
                "title": "Day 1",
                "summary": "Giza Plateau & Sphinx",
                "activities": [
                    {"time": "08:00", "title": "Hotel pickup", "description": "Meet your Egyptologist guide and travel in air-conditioned comfort to the Giza Plateau."},
                    {"time": "09:00", "title": "Great Pyramid tour", "description": "Stand at the base of the Great Pyramid of Khufu and hear the stories behind its construction."},
                    {"time": "10:30", "title": "Inside pyramid visit", "description": "Descend into one of the pyramids (optional upgrade) for an unforgettable look inside."},
                    {"time": "12:00", "title": "Traditional lunch", "description": "Enjoy an authentic Egyptian meal overlooking the pyramids."},
                    {"time": "13:30", "title": "Solar Boat Museum", "description": "Discover the reconstructed solar barque and learn why it mattered to the ancient Egyptians."},
                    {"time": "15:00", "title": "Sphinx viewpoint", "description": "Capture close-up photos of the Great Sphinx and hear legends that surround it."},
                    {"time": "16:00", "title": "Return transfer", "description": "Head back to your hotel with rest stops and shopping opportunities on request."},
                ],
            }
        ],
        "included": [
            "Hotel pickup and drop-off",
            "Professional Egyptologist guide",
            "Entrance fees",
            "Lunch",
            "Bottled water",
        ],
        "excluded": [
            "Gratuities",
            "Inside pyramid tickets (optional)",
            "Personal expenses",
        ],
        "booking_note": "Pricing shown is per person based on a minimum of two travelers.",
        "extras": copy.deepcopy(DEFAULT_EXTRAS),
        "languages": copy.deepcopy(DEFAULT_LANGUAGES),
        "faqs": copy.deepcopy(DEFAULT_FAQS),
        "reviews": [],
    },
    "nile-luxury-cruise": {
        "slug": "nile-luxury-cruise",
        "title": "Luxury Nile Cruise",
        "category": "Cruise",
        "hero_image": "img/nile-cruise.jpg",
        "card_image": "img/nile-cruise.jpg",
        "summary": "Sail from Luxor to Aswan aboard a 5-star vessel with curated temple visits and onboard indulgence.",
        "lead": "A four-day journey that blends iconic temples, sunset sailing, and attentive hospitality across the Nile.",
        "overview_paragraphs": [
            "Board a deluxe floating hotel featuring spacious cabins, sundeck pool, and nightly entertainment.",
            "Daily guided tours unlock Egypt's most celebrated temples while you travel effortlessly between Luxor and Aswan.",
        ],
        "tour_length": "4 Days / 3 Nights",
        "tour_type": "Daily Sailing — Cultural Discovery",
        "group_size": 50,
        "base_price": 890.0,
        "currency": "USD",
        "primary_destination": "Luxor",
        "destinations": ["Luxor", "Edfu", "Kom Ombo", "Aswan"],
        "highlights": [
            "5-star deluxe cruise ship",
            "All meals included",
            "Visit Karnak and Luxor Temples",
            "Explore Valley of the Kings",
            "Edfu and Kom Ombo temples",
            "Philae Temple in Aswan",
            "Traditional Nubian village visit",
            "Onboard entertainment",
        ],
        "itinerary_days": [
            {
                "title": "Day 1",
                "summary": "Luxor Embarkation",
                "activities": [
                    {"time": "14:00", "title": "Board in Luxor", "description": "Settle into your cabin and meet your cruise director."},
                    {"time": "16:00", "title": "Karnak & Luxor Temples", "description": "Guided visit through the vast Karnak complex followed by Luxor Temple at sunset."},
                    {"time": "20:00", "title": "Welcome dinner", "description": "Enjoy a multi-course meal onboard with live music."},
                ],
            },
            {
                "title": "Day 2",
                "summary": "Valley of the Kings",
                "activities": [
                    {"time": "07:30", "title": "Valley of the Kings", "description": "Tour three royal tombs, including the resting place of Tutankhamun (optional upgrade)."},
                    {"time": "10:30", "title": "Hatshepsut Temple", "description": "Marvel at the terraced mortuary temple and its dramatic cliff backdrop."},
                    {"time": "13:00", "title": "Sail to Edfu", "description": "Lunch onboard as the cruise begins its southbound journey."},
                ],
            },
            {
                "title": "Day 3",
                "summary": "Edfu & Kom Ombo",
                "activities": [
                    {"time": "08:00", "title": "Edfu Temple", "description": "Horse-drawn carriage ride to the best-preserved temple in Egypt."},
                    {"time": "13:00", "title": "Kom Ombo Temple", "description": "Twin temple dedicated to Sobek and Horus with Nile crocodile museum."},
                    {"time": "19:00", "title": "Galabeya night", "description": "Egyptian dinner party with music and traditional dress."},
                ],
            },
            {
                "title": "Day 4",
                "summary": "Aswan Finale",
                "activities": [
                    {"time": "08:30", "title": "Philae Temple", "description": "Boat ride to the island sanctuary of Isis."},
                    {"time": "11:30", "title": "Nubian Village", "description": "Optional motorboat excursion to meet Nubian artisans."},
                    {"time": "12:30", "title": "Disembarkation", "description": "Check-out with assistance to onward transfers or flights."},
                ],
            },
        ],
        "included": [
            "3 nights accommodation",
            "All meals",
            "Guided tours",
            "Entrance fees",
            "Onboard entertainment",
        ],
        "excluded": ["Drinks", "Gratuities", "Optional excursions"],
        "booking_note": "Upgrade to suite cabins and private excursions available on request.",
        "extras": copy.deepcopy(DEFAULT_EXTRAS),
        "languages": copy.deepcopy(DEFAULT_LANGUAGES),
        "faqs": copy.deepcopy(DEFAULT_FAQS),
        "reviews": [],
    },
    "red-sea-diving": {
        "slug": "red-sea-diving",
        "title": "Red Sea Diving Adventure",
        "category": "Adventure",
        "hero_image": "img/red-sea.jpg",
        "card_image": "img/red-sea.jpg",
        "summary": "Discover vibrant coral reefs and marine life with a PADI-certified dive team in Hurghada.",
        "lead": "Ideal for certified divers seeking warm waters, technicolor reefs, and relaxed resort downtime between dives.",
        "overview_paragraphs": [
            "This three-day program balances guided boat dives with time to enjoy beachfront amenities and seaside dining.",
            "Equipment, transportation, and experienced dive masters are included so you can focus on the underwater spectacle.",
        ],
        "tour_length": "3 Days / 2 Nights",
        "tour_type": "Adventure Break — Red Sea Diving",
        "group_size": 12,
        "base_price": 450.0,
        "currency": "USD",
        "primary_destination": "Hurghada",
        "destinations": ["Hurghada", "Red Sea"],
        "highlights": [
            "6 guided dives included",
            "PADI certified instructors",
            "All diving equipment provided",
            "Visit pristine coral reefs",
            "Encounter diverse marine life",
            "Beachfront resort accommodation",
            "Airport transfers included",
        ],
        "itinerary_days": [
            {
                "title": "Day 1",
                "summary": "Check-in & Warm-up Dives",
                "activities": [
                    {"time": "Morning", "title": "Arrival & briefing", "description": "Transfer from airport to resort, gear sizing, and safety orientation."},
                    {"time": "Afternoon", "title": "Two reef dives", "description": "Gentle drift dives to reacquaint yourself with Red Sea conditions."},
                    {"time": "Evening", "title": "Sunset at the marina", "description": "Relax with a seaside dinner or optional night dive."},
                ],
            },
            {
                "title": "Day 2",
                "summary": "Full-Day Boat Safari",
                "activities": [
                    {"time": "Morning", "title": "Three dive sites", "description": "Explore pinnacles and coral gardens rich with macro life."},
                    {"time": "Midday", "title": "Lunch onboard", "description": "Freshly prepared meal between dives with time to sunbathe."},
                    {"time": "Late afternoon", "title": "Debrief & photo sharing", "description": "Compare sightings with your dive master over refreshments."},
                ],
            },
            {
                "title": "Day 3",
                "summary": "Leisure & Departure",
                "activities": [
                    {"time": "Morning", "title": "Optional dawn dive", "description": "Add-on dive to catch the reef waking up (subject to conditions)."},
                    {"time": "Late morning", "title": "Resort downtime", "description": "Poolside relaxation or spa treatment before checkout."},
                    {"time": "Afternoon", "title": "Transfer to airport", "description": "Private vehicle transfer to Hurghada airport or onward hotel."},
                ],
            },
        ],
        "included": [
            "2 nights accommodation",
            "6 guided dives",
            "All equipment",
            "Boat trips",
            "Airport transfers",
        ],
        "excluded": [
            "Meals except boat lunch",
            "Diving certification course",
            "Personal expenses",
        ],
        "booking_note": "Single occupancy upgrades and additional dive days available.",
        "extras": copy.deepcopy(DEFAULT_EXTRAS),
        "languages": copy.deepcopy(DEFAULT_LANGUAGES),
        "faqs": copy.deepcopy(DEFAULT_FAQS),
        "reviews": [],
    },
    "ancient-luxor": {
        "slug": "ancient-luxor",
        "title": "Ancient Luxor & Valley of Kings",
        "category": "Historical",
        "hero_image": "img/luxor-temple.jpg",
        "card_image": "img/luxor-temple.jpg",
        "summary": "Two immersive days exploring Luxor's temples, tombs, and Nile sunsets with an expert guide.",
        "lead": "A flexible overnighter that showcases the best of Luxor on both the East and West Banks of the Nile.",
        "overview_paragraphs": [
            "Trace the footsteps of pharaohs as you uncover painted tombs, sprawling temple complexes, and hidden courtyards.",
            "Evening felucca cruises and optional sunrise balloon rides add extra magic to this classic itinerary.",
        ],
        "tour_length": "2 Days / 1 Night",
        "tour_type": "Daily Tour — Discovery Safari",
        "group_size": 20,
        "base_price": 280.0,
        "currency": "USD",
        "primary_destination": "Luxor",
        "destinations": ["Luxor", "West Bank"],
        "highlights": [
            "Valley of the Kings exploration",
            "Hatshepsut Temple visit",
            "Karnak Temple complex",
            "Luxor Temple at night",
            "Hot air balloon ride (optional)",
            "Traditional felucca sailing",
            "Expert Egyptologist guide",
        ],
        "itinerary_days": [
            {
                "title": "Day 1",
                "summary": "West Bank Treasures",
                "activities": [
                    {"time": "Morning", "title": "Valley of the Kings", "description": "Discover intricately painted tombs with stories that span millennia."},
                    {"time": "Late morning", "title": "Temple of Hatshepsut", "description": "Admire the queen's mortuary temple carved into the cliffs."},
                    {"time": "Afternoon", "title": "Felucca sail", "description": "Glide along the Nile at sunset with mint tea and local snacks."},
                    {"time": "Evening", "title": "Luxor Temple", "description": "Experience the illuminated temple after dark with fewer crowds."},
                ],
            },
            {
                "title": "Day 2",
                "summary": "Sunrise & East Bank Icons",
                "activities": [
                    {"time": "Pre-dawn", "title": "Optional balloon flight", "description": "Drift above the West Bank as the sun rises over the Nile."},
                    {"time": "Morning", "title": "Karnak Temple", "description": "Walk through grand hypostyle halls and sacred lakes."},
                    {"time": "Afternoon", "title": "Shopping & departure", "description": "Visit a local artisan workshop before returning to your hotel or airport."},
                ],
            },
        ],
        "included": [
            "1 night hotel accommodation",
            "All entrance fees",
            "Expert guide",
            "Breakfast",
            "Felucca ride",
        ],
        "excluded": ["Lunch and dinner", "Hot air balloon ride", "Gratuities"],
        "booking_note": "Add-on experiences like hot air balloon rides can be arranged in advance.",
        "extras": copy.deepcopy(DEFAULT_EXTRAS),
        "languages": copy.deepcopy(DEFAULT_LANGUAGES),
        "faqs": copy.deepcopy(DEFAULT_FAQS),
        "reviews": [],
    },
}


def build_trip_list_item(trip):
    return {
        "slug": trip["slug"],
        "title": trip["title"],
        "description": trip["summary"],
        "image": trip["card_image"],
        "duration": trip["tour_length"].split(" / ")[0] if " / " in trip["tour_length"] else trip["tour_length"],
        "group_size": f"Up to {trip['group_size']} guests",
        "location": trip["primary_destination"],
        "price": format_currency(trip["base_price"], trip["currency"]),
        "category": trip["category"],
    }


TRIPS_LIST = [build_trip_list_item(trip) for trip in TRIP_DETAILS.values()]


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            hero={
                "title": "Discover the Magic of Egypt",
                "subtitle": "Embark on an unforgettable journey through ancient wonders and timeless beauty",
                "image": "img/hero-pyramids.jpg",
                "primary_cta": {"label": "Explore Tours", "href": "/trips"},
                "secondary_cta": {"label": "Learn More", "href": "#about"},
            },
            destinations_section={
                "title": "Featured Destinations",
                "subtitle": "Explore the most captivating experiences Egypt has to offer",
                "items": [
                    {
                        "title": "Nile River Cruise",
                        "description": "Sail through history on a luxury cruise, visiting ancient temples and monuments along the legendary Nile.",
                        "image": "img/nile-cruise.jpg",
                        "cta": {"label": "View Details", "href": "/trips"},
                    },
                    {
                        "title": "Red Sea Paradise",
                        "description": "Dive into crystal-clear waters and explore vibrant coral reefs in one of the world's premier diving destinations.",
                        "image": "img/red-sea.jpg",
                        "cta": {"label": "View Details", "href": "/trips"},
                    },
                    {
                        "title": "Ancient Temples",
                        "description": "Walk in the footsteps of pharaohs at Luxor and Karnak, marveling at architectural wonders that have stood for millennia.",
                        "image": "img/luxor-temple.jpg",
                        "cta": {"label": "View Details", "href": "/trips"},
                    },
                ],
            },
            about_section={
                "title": "Why Choose Nile Dreams",
                "subtitle": "We're passionate about creating extraordinary experiences in Egypt",
                "features": [
                    {
                        "badge": "EG",
                        "title": "Expert Guides",
                        "description": "Licensed Egyptologists and local experts bring history to life.",
                    },
                    {
                        "badge": "SS",
                        "title": "Safe & Secure",
                        "description": "Your safety is our priority with comprehensive travel support.",
                    },
                    {
                        "badge": "PS",
                        "title": "Personalized Service",
                        "description": "Tailored itineraries designed around your interests and pace.",
                    },
                    {
                        "badge": "SG",
                        "title": "Small Groups",
                        "description": "Intimate group sizes ensure a more personal experience.",
                    },
                ],
            },
            contact_section={
                "title": "Start Your Journey",
                "subtitle": "Ready to explore Egypt? Get in touch with our travel experts and we'll help create your perfect adventure.",
                "channels": [
                    {
                        "badge": "@",
                        "title": "Email Us",
                        "value": "info@niledreams.com",
                    },
                    {
                        "badge": "+",
                        "title": "Call Us",
                        "value": "+20 123 456 7890",
                    },
                    {
                        "badge": "LV",
                        "title": "Visit Us",
                        "value": "Cairo, Egypt",
                    },
                ],
                "form": {"action": "#"},
            },
        )

        return context


class TripListView(TemplateView):
    template_name = "trips.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trips"] = TRIPS_LIST
        return context


class TripDetailView(TemplateView):
    template_name = "trip_detail.html"

    def get_trip(self):
        if not hasattr(self, "_trip"):
            slug = self.kwargs.get("slug")
            trip = TRIP_DETAILS.get(slug)
            if not trip:
                raise Http404("Trip not found")
            self._trip = trip
        return self._trip

    def get_form(self, data=None):
        trip = self.get_trip()
        extra_choices = [(extra["id"], extra["label"]) for extra in trip["extras"]]
        return BookingRequestForm(data=data, extra_choices=extra_choices)

    def _pricing_context(self, trip, form):
        currency = trip["currency"]
        base_price = trip["base_price"]

        def extract_int(field_name, fallback):
            value = form[field_name].value()
            try:
                return max(int(value), 0)
            except (TypeError, ValueError):
                return fallback

        adults = max(extract_int("adults", form.fields["adults"].initial), 1)
        children = extract_int("children", form.fields["children"].initial)
        infants = extract_int("infants", form.fields["infants"].initial)

        traveler_count = max(adults + children, 1)
        base_total = base_price * traveler_count

        selected_extras = set(form["extras"].value() or [])
        extras_with_state = []
        extras_total = 0.0
        for extra in trip["extras"]:
            selected = extra["id"] in selected_extras
            if selected:
                extras_total += extra["price"]
            extras_with_state.append(
                {
                    **extra,
                    "selected": selected,
                    "price_display": format_currency(extra["price"], currency),
                }
            )

        total = base_total + extras_total

        return {
            "currency": currency,
            "currency_symbol": CURRENCY_SYMBOLS.get(currency, ""),
            "base_price": base_price,
            "base_price_display": format_currency(base_price, currency),
            "traveler_count": traveler_count,
            "adults": adults,
            "children": children,
            "infants": infants,
            "base_total": base_total,
            "base_total_display": format_currency(base_total, currency),
            "extras_total": extras_total,
            "extras_total_display": format_currency(extras_total, currency),
            "total": total,
            "total_display": format_currency(total, currency),
            "extras": extras_with_state,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or self.get_form()
        trip = copy.deepcopy(self.get_trip())

        pricing = self._pricing_context(trip, form)
        trip["price_display"] = pricing["base_price_display"]
        trip["group_size_label"] = f"Up to {trip['group_size']} guests"
        trip["language_chips"] = trip["languages"]
        trip["locations_display"] = " • ".join(trip["destinations"])
        trip["extras"] = pricing["extras"]
        trip["breadcrumbs"] = [
            {"label": "Home", "url": reverse("web:home")},
            {"label": trip["primary_destination"], "url": "#"},
            {"label": trip["title"], "url": ""},
        ]
        trip["anchor_nav"] = [
            {"label": "Overview", "target": "overview"},
            {"label": "Highlights", "target": "highlights"},
            {"label": "Itinerary", "target": "itinerary"},
            {"label": "What's Included", "target": "included"},
            {"label": "FAQs", "target": "faqs"},
            {"label": "Reviews", "target": "reviews"},
        ]
        trip["key_facts"] = [
            {"icon": "⏱", "label": trip["tour_length"], "sr": "Duration"},
            {"icon": "🧭", "label": trip["tour_type"], "sr": "Tour type"},
            {"icon": "👥", "label": trip["group_size_label"], "sr": "Group size"},
            {
                "icon": "🗣",
                "label": " • ".join(language["label"] for language in trip["languages"]),
                "sr": "Languages",
            },
        ]
        trip["has_reviews"] = bool(trip["reviews"])
        trip["review_summary"] = (
            "New — be the first to review" if not trip["reviews"] else "Excellent (4.8) • 12 reviews"
        )
        trip["contact_actions"] = [
            {
                "label": "WhatsApp",
                "href": "https://wa.me/201234567890",
                "icon": "whatsapp",
                "aria": "Chat with us on WhatsApp",
            },
            {"label": "Call", "href": "tel:+201234567890", "icon": "phone", "aria": "Call Nile Dreams"},
            {
                "label": "Email",
                "href": "mailto:info@niledreams.com",
                "icon": "mail",
                "aria": "Email Nile Dreams",
            },
        ]

        context.update(
            trip=trip,
            form=form,
            pricing={k: v for k, v in pricing.items() if k != "extras"},
            other_trips=[item for item in TRIPS_LIST if item["slug"] != trip["slug"]][:3],
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "Thanks for your request! A travel specialist will contact you shortly to confirm details.",
            )
            form = self.get_form()
        else:
            messages.error(request, "Please correct the errors below before submitting.")
        return self.render_to_response(self.get_context_data(form=form))
