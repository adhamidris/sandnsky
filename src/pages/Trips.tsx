import { Link } from "react-router-dom";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, MapPin, Users } from "lucide-react";
import heroPyramids from "@/assets/hero-pyramids.jpg";
import nileCruise from "@/assets/nile-cruise.jpg";
import redSea from "@/assets/red-sea.jpg";
import luxorTemple from "@/assets/luxor-temple.jpg";

const trips = [
  {
    id: "pyramids-giza",
    title: "Pyramids of Giza Experience",
    description: "Explore the last standing wonder of the ancient world",
    image: heroPyramids,
    duration: "1 Day",
    groupSize: "2-15",
    location: "Cairo",
    price: "$120",
    category: "Historical"
  },
  {
    id: "nile-luxury-cruise",
    title: "Luxury Nile Cruise",
    description: "5-star cruise from Luxor to Aswan with ancient temple visits",
    image: nileCruise,
    duration: "4 Days",
    groupSize: "2-50",
    location: "Luxor to Aswan",
    price: "$890",
    category: "Cruise"
  },
  {
    id: "red-sea-diving",
    title: "Red Sea Diving Adventure",
    description: "Discover vibrant coral reefs and marine life",
    image: redSea,
    duration: "3 Days",
    groupSize: "2-12",
    location: "Hurghada",
    price: "$450",
    category: "Adventure"
  },
  {
    id: "ancient-luxor",
    title: "Ancient Luxor & Valley of Kings",
    description: "Journey through pharaonic tombs and magnificent temples",
    image: luxorTemple,
    duration: "2 Days",
    groupSize: "2-20",
    location: "Luxor",
    price: "$280",
    category: "Historical"
  }
];

const Trips = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="pt-20">
        {/* Header */}
        <section className="py-16 px-4">
          <div className="max-w-7xl mx-auto text-center">
            <h1 className="font-serif text-4xl md:text-5xl text-foreground mb-4 animate-fade-in">
              Our Tours & Experiences
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Carefully curated journeys to unveil the wonders of Egypt
            </p>
          </div>
        </section>

        {/* Trips Grid */}
        <section className="pb-20 px-4">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-2 lg:grid-cols-2 gap-8">
              {trips.map((trip, index) => (
                <Card key={trip.id} className="overflow-hidden hover-scale animate-fade-in border-border" style={{ animationDelay: `${index * 100}ms` }}>
                  <div className="relative h-64 overflow-hidden">
                    <img 
                      src={trip.image} 
                      alt={trip.title}
                      className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
                    />
                    <Badge className="absolute top-4 right-4 bg-primary text-primary-foreground">
                      {trip.category}
                    </Badge>
                  </div>
                  <CardHeader>
                    <CardTitle className="font-serif text-2xl">{trip.title}</CardTitle>
                    <CardDescription className="text-base">{trip.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>{trip.duration}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        <span>{trip.groupSize} people</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4" />
                        <span>{trip.location}</span>
                      </div>
                    </div>
                    <div className="mt-4">
                      <p className="text-2xl font-serif text-primary">
                        {trip.price}
                        <span className="text-sm text-muted-foreground font-sans"> / person</span>
                      </p>
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Link to={`/trips/${trip.id}`} className="w-full">
                      <Button className="w-full">View Details</Button>
                    </Link>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Trips;
