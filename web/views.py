from django.http import Http404
from django.contrib import messages
from django.views.generic import TemplateView

from .forms import BookingRequestForm

TRIP_DETAILS = {
    "pyramids-giza": {
        "slug": "pyramids-giza",
        "title": "Pyramids of Giza Experience",
        "summary": "Explore the last standing wonder of the ancient world",
        "description": "Explore the last standing wonder of the ancient world with our expert Egyptologist guides",
        "image": "img/hero-pyramids.jpg",
        "duration": "1 Day",
        "group_size": "2-15",
        "location": "Cairo",
        "price": "$120",
        "category": "Historical",
        "rating": "4.9/5",
        "highlights": [
            "Visit the Great Pyramid of Khufu",
            "Explore inside the pyramids",
            "See the Great Sphinx up close",
            "Visit the Solar Boat Museum",
            "Professional photography session",
            "Traditional Egyptian lunch included",
        ],
        "itinerary": [
            {"time": "08:00 AM", "activity": "Hotel pickup"},
            {"time": "09:00 AM", "activity": "Arrive at Giza Plateau"},
            {"time": "09:30 AM", "activity": "Tour the Great Pyramid"},
            {"time": "11:00 AM", "activity": "Visit the Sphinx"},
            {"time": "12:30 PM", "activity": "Lunch at local restaurant"},
            {"time": "02:00 PM", "activity": "Solar Boat Museum"},
            {"time": "04:00 PM", "activity": "Return to hotel"},
        ],
        "included": [
            "Hotel pickup and drop-off",
            "Professional Egyptologist guide",
            "Entrance fees",
            "Lunch",
            "Bottled water",
        ],
        "not_included": [
            "Gratuities",
            "Inside pyramid tickets (optional)",
            "Personal expenses",
        ],
        "booking_note": "Pricing shown is per person based on a minimum of two travelers.",
    },
    "nile-luxury-cruise": {
        "slug": "nile-luxury-cruise",
        "title": "Luxury Nile Cruise",
        "summary": "5-star cruise from Luxor to Aswan with ancient temple visits",
        "description": "5-star cruise from Luxor to Aswan with ancient temple visits and premium amenities",
        "image": "img/nile-cruise.jpg",
        "duration": "4 Days / 3 Nights",
        "group_size": "2-50",
        "location": "Luxor to Aswan",
        "price": "$890",
        "category": "Cruise",
        "rating": "5.0/5",
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
        "itinerary": [
            {"time": "Day 1", "activity": "Board in Luxor - Visit Karnak & Luxor Temples"},
            {"time": "Day 2", "activity": "Valley of the Kings - Hatshepsut Temple - Sail to Edfu"},
            {"time": "Day 3", "activity": "Edfu Temple - Kom Ombo Temple - Sail to Aswan"},
            {"time": "Day 4", "activity": "Philae Temple - Nubian Village - Disembark"},
        ],
        "included": [
            "3 nights accommodation",
            "All meals",
            "Guided tours",
            "Entrance fees",
            "Onboard entertainment",
        ],
        "not_included": ["Drinks", "Gratuities", "Optional excursions"],
        "booking_note": "Upgrade to suite cabins and private excursions available on request.",
    },
    "red-sea-diving": {
        "slug": "red-sea-diving",
        "title": "Red Sea Diving Adventure",
        "summary": "Discover vibrant coral reefs and marine life",
        "description": "Discover vibrant coral reefs and marine life in the world-famous Red Sea",
        "image": "img/red-sea.jpg",
        "duration": "3 Days / 2 Nights",
        "group_size": "2-12",
        "location": "Hurghada",
        "price": "$450",
        "category": "Adventure",
        "rating": "4.8/5",
        "highlights": [
            "6 guided dives included",
            "PADI certified instructors",
            "All diving equipment provided",
            "Visit pristine coral reefs",
            "Encounter diverse marine life",
            "Beachfront resort accommodation",
            "Airport transfers included",
        ],
        "itinerary": [
            {"time": "Day 1", "activity": "Arrival - Equipment briefing - 2 afternoon dives"},
            {"time": "Day 2", "activity": "Full day boat trip - 3 dives - Lunch on boat"},
            {"time": "Day 3", "activity": "Morning dive - Free time - Departure"},
        ],
        "included": [
            "2 nights accommodation",
            "6 guided dives",
            "All equipment",
            "Boat trips",
            "Airport transfers",
        ],
        "not_included": [
            "Meals except boat lunch",
            "Diving certification course",
            "Personal expenses",
        ],
        "booking_note": "Single occupancy upgrades and additional dive days available.",
    },
    "ancient-luxor": {
        "slug": "ancient-luxor",
        "title": "Ancient Luxor & Valley of Kings",
        "summary": "Journey through pharaonic tombs and magnificent temples",
        "description": "Journey through pharaonic tombs and magnificent temples in the world's greatest open-air museum",
        "image": "img/luxor-temple.jpg",
        "duration": "2 Days / 1 Night",
        "group_size": "2-20",
        "location": "Luxor",
        "price": "$280",
        "category": "Historical",
        "rating": "4.9/5",
        "highlights": [
            "Valley of the Kings exploration",
            "Hatshepsut Temple visit",
            "Karnak Temple complex",
            "Luxor Temple at night",
            "Hot air balloon ride (optional)",
            "Traditional felucca sailing",
            "Expert Egyptologist guide",
        ],
        "itinerary": [
            {"time": "Day 1 AM", "activity": "Valley of the Kings - Hatshepsut Temple - Colossi of Memnon"},
            {"time": "Day 1 PM", "activity": "Karnak Temple - Felucca sailing"},
            {"time": "Day 1 Night", "activity": "Luxor Temple illuminated tour"},
            {"time": "Day 2", "activity": "Optional hot air balloon - Free time - Departure"},
        ],
        "included": [
            "1 night hotel accommodation",
            "All entrance fees",
            "Expert guide",
            "Breakfast",
            "Felucca ride",
        ],
        "not_included": ["Lunch and dinner", "Hot air balloon ride", "Gratuities"],
        "booking_note": "Add-on experiences like hot air balloon rides can be arranged in advance.",
    },
}

TRIPS_LIST = [
    {
        "slug": trip["slug"],
        "title": trip["title"],
        "description": trip["summary"],
        "image": trip["image"],
        "duration": trip["duration"].split(" / ")[0] if " / " in trip["duration"] else trip["duration"],
        "group_size": trip["group_size"],
        "location": trip["location"],
        "price": trip["price"],
        "category": trip["category"],
    }
    for trip in TRIP_DETAILS.values()
]


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
        slug = self.kwargs.get("slug")
        trip = TRIP_DETAILS.get(slug)
        if not trip:
            raise Http404("Trip not found")
        return trip

    def get_form(self):
        return BookingRequestForm()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_trip()
        context["trip"] = trip
        context["form"] = kwargs.get("form", self.get_form())
        context["other_trips"] = [item for item in TRIPS_LIST if item["slug"] != trip["slug"]][:3]
        return context

    def post(self, request, *args, **kwargs):
        trip = self.get_trip()
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "Thanks for your request! A travel specialist will contact you shortly to confirm details.",
            )
            form = self.get_form()
        else:
            messages.error(request, "Please correct the errors below before submitting.")
        context = self.get_context_data(form=form, trip=trip)
        return self.render_to_response(context)
