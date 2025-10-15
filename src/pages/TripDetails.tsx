import { useParams, Link } from "react-router-dom";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import BookingForm from "@/components/BookingForm";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, MapPin, Users, Clock, Star, CheckCircle2, ArrowLeft } from "lucide-react";
import heroPyramids from "@/assets/hero-pyramids.jpg";
import nileCruise from "@/assets/nile-cruise.jpg";
import redSea from "@/assets/red-sea.jpg";
import luxorTemple from "@/assets/luxor-temple.jpg";

const tripData: Record<string, any> = {
  "pyramids-giza": {
    title: "Pyramids of Giza Experience",
    description: "Explore the last standing wonder of the ancient world with our expert Egyptologist guides",
    image: heroPyramids,
    duration: "1 Day",
    groupSize: "2-15",
    location: "Cairo",
    price: "$120",
    category: "Historical",
    highlights: [
      "Visit the Great Pyramid of Khufu",
      "Explore inside the pyramids",
      "See the Great Sphinx up close",
      "Visit the Solar Boat Museum",
      "Professional photography session",
      "Traditional Egyptian lunch included"
    ],
    itinerary: [
      { time: "08:00 AM", activity: "Hotel pickup" },
      { time: "09:00 AM", activity: "Arrive at Giza Plateau" },
      { time: "09:30 AM", activity: "Tour the Great Pyramid" },
      { time: "11:00 AM", activity: "Visit the Sphinx" },
      { time: "12:30 PM", activity: "Lunch at local restaurant" },
      { time: "02:00 PM", activity: "Solar Boat Museum" },
      { time: "04:00 PM", activity: "Return to hotel" }
    ],
    included: ["Hotel pickup and drop-off", "Professional Egyptologist guide", "Entrance fees", "Lunch", "Bottled water"],
    notIncluded: ["Gratuities", "Inside pyramid tickets (optional)", "Personal expenses"]
  },
  "nile-luxury-cruise": {
    title: "Luxury Nile Cruise",
    description: "5-star cruise from Luxor to Aswan with ancient temple visits and premium amenities",
    image: nileCruise,
    duration: "4 Days / 3 Nights",
    groupSize: "2-50",
    location: "Luxor to Aswan",
    price: "$890",
    category: "Cruise",
    highlights: [
      "5-star deluxe cruise ship",
      "All meals included",
      "Visit Karnak and Luxor Temples",
      "Explore Valley of the Kings",
      "Edfu and Kom Ombo temples",
      "Philae Temple in Aswan",
      "Traditional Nubian village visit",
      "Onboard entertainment"
    ],
    itinerary: [
      { time: "Day 1", activity: "Board in Luxor - Visit Karnak & Luxor Temples" },
      { time: "Day 2", activity: "Valley of the Kings - Hatshepsut Temple - Sail to Edfu" },
      { time: "Day 3", activity: "Edfu Temple - Kom Ombo Temple - Sail to Aswan" },
      { time: "Day 4", activity: "Philae Temple - Nubian Village - Disembark" }
    ],
    included: ["3 nights accommodation", "All meals", "Guided tours", "Entrance fees", "Onboard entertainment"],
    notIncluded: ["Drinks", "Gratuities", "Optional excursions"]
  },
  "red-sea-diving": {
    title: "Red Sea Diving Adventure",
    description: "Discover vibrant coral reefs and marine life in the world-famous Red Sea",
    image: redSea,
    duration: "3 Days / 2 Nights",
    groupSize: "2-12",
    location: "Hurghada",
    price: "$450",
    category: "Adventure",
    highlights: [
      "6 guided dives included",
      "PADI certified instructors",
      "All diving equipment provided",
      "Visit pristine coral reefs",
      "Encounter diverse marine life",
      "Beachfront resort accommodation",
      "Airport transfers included"
    ],
    itinerary: [
      { time: "Day 1", activity: "Arrival - Equipment briefing - 2 afternoon dives" },
      { time: "Day 2", activity: "Full day boat trip - 3 dives - Lunch on boat" },
      { time: "Day 3", activity: "Morning dive - Free time - Departure" }
    ],
    included: ["2 nights accommodation", "6 guided dives", "All equipment", "Boat trips", "Airport transfers"],
    notIncluded: ["Meals except boat lunch", "Diving certification course", "Personal expenses"]
  },
  "ancient-luxor": {
    title: "Ancient Luxor & Valley of Kings",
    description: "Journey through pharaonic tombs and magnificent temples in the world's greatest open-air museum",
    image: luxorTemple,
    duration: "2 Days / 1 Night",
    groupSize: "2-20",
    location: "Luxor",
    price: "$280",
    category: "Historical",
    highlights: [
      "Valley of the Kings exploration",
      "Hatshepsut Temple visit",
      "Karnak Temple complex",
      "Luxor Temple at night",
      "Hot air balloon ride (optional)",
      "Traditional felucca sailing",
      "Expert Egyptologist guide"
    ],
    itinerary: [
      { time: "Day 1 AM", activity: "Valley of the Kings - Hatshepsut Temple - Colossi of Memnon" },
      { time: "Day 1 PM", activity: "Karnak Temple - Felucca sailing" },
      { time: "Day 1 Night", activity: "Luxor Temple illuminated tour" },
      { time: "Day 2", activity: "Optional hot air balloon - Free time - Departure" }
    ],
    included: ["1 night hotel accommodation", "All entrance fees", "Expert guide", "Breakfast", "Felucca ride"],
    notIncluded: ["Lunch and dinner", "Hot air balloon ride", "Gratuities"]
  }
};

const TripDetails = () => {
  const { id } = useParams();
  const trip = id ? tripData[id] : null;

  if (!trip) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="pt-32 pb-20 px-4 text-center">
          <h1 className="text-4xl font-serif mb-4">Trip Not Found</h1>
          <Link to="/trips">
            <Button>View All Trips</Button>
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="pt-20">
        {/* Hero Image */}
        <div className="relative h-[60vh] overflow-hidden">
          <img 
            src={trip.image} 
            alt={trip.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/40 flex items-end">
            <div className="max-w-7xl mx-auto px-4 pb-12 w-full">
              <Link to="/trips" className="inline-flex items-center gap-2 text-white mb-4 hover:underline">
                <ArrowLeft className="w-4 h-4" />
                Back to all trips
              </Link>
              <Badge className="bg-primary text-primary-foreground mb-4">{trip.category}</Badge>
              <h1 className="font-serif text-4xl md:text-5xl text-white mb-4 animate-fade-in">
                {trip.title}
              </h1>
              <p className="text-xl text-white/90 max-w-3xl">
                {trip.description}
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 py-16">
          <div className="grid lg:grid-cols-3 gap-12">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-12">
              {/* Quick Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center p-4 bg-muted rounded-lg">
                  <Calendar className="w-6 h-6 mx-auto mb-2 text-primary" />
                  <p className="text-sm text-muted-foreground">Duration</p>
                  <p className="font-semibold">{trip.duration}</p>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <Users className="w-6 h-6 mx-auto mb-2 text-primary" />
                  <p className="text-sm text-muted-foreground">Group Size</p>
                  <p className="font-semibold">{trip.groupSize}</p>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <MapPin className="w-6 h-6 mx-auto mb-2 text-primary" />
                  <p className="text-sm text-muted-foreground">Location</p>
                  <p className="font-semibold">{trip.location}</p>
                </div>
                <div className="text-center p-4 bg-muted rounded-lg">
                  <Star className="w-6 h-6 mx-auto mb-2 text-primary" />
                  <p className="text-sm text-muted-foreground">Rating</p>
                  <p className="font-semibold">4.9/5</p>
                </div>
              </div>

              {/* Highlights */}
              <div>
                <h2 className="font-serif text-3xl mb-6">Tour Highlights</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {trip.highlights.map((highlight: string, index: number) => (
                    <div key={index} className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-muted-foreground">{highlight}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Itinerary */}
              <div>
                <h2 className="font-serif text-3xl mb-6">Itinerary</h2>
                <div className="space-y-4">
                  {trip.itinerary.map((item: any, index: number) => (
                    <div key={index} className="flex gap-4 p-4 bg-muted rounded-lg">
                      <Clock className="w-5 h-5 text-primary mt-1 flex-shrink-0" />
                      <div>
                        <p className="font-semibold mb-1">{item.time}</p>
                        <p className="text-muted-foreground">{item.activity}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Included/Not Included */}
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h3 className="font-serif text-xl mb-4">What's Included</h3>
                  <ul className="space-y-2">
                    {trip.included.map((item: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-muted-foreground">
                        <CheckCircle2 className="w-4 h-4 text-primary mt-1 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="font-serif text-xl mb-4">Not Included</h3>
                  <ul className="space-y-2">
                    {trip.notIncluded.map((item: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-muted-foreground">
                        <span className="w-4 h-4 text-muted-foreground mt-1 flex-shrink-0">×</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Booking Sidebar */}
            <div className="lg:col-span-1">
              <div className="sticky top-24">
                <div className="bg-muted p-6 rounded-lg">
                  <div className="mb-6">
                    <p className="text-3xl font-serif text-primary">
                      {trip.price}
                      <span className="text-sm text-muted-foreground font-sans"> / person</span>
                    </p>
                  </div>
                  <BookingForm tripTitle={trip.title} tripPrice={trip.price} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default TripDetails;
