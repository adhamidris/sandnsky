import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import nileCruise from "@/assets/nile-cruise.jpg";
import redSea from "@/assets/red-sea.jpg";
import luxorTemple from "@/assets/luxor-temple.jpg";
import heroPyramids from "@/assets/hero-pyramids.jpg";

const destinations = [
  {
    title: "Nile River Cruise",
    description: "Sail through history on a luxury cruise, visiting ancient temples and monuments along the legendary Nile.",
    image: nileCruise,
  },
  {
    title: "Red Sea Paradise",
    description: "Dive into crystal-clear waters and explore vibrant coral reefs in one of the world's premier diving destinations.",
    image: redSea,
  },
  {
    title: "Ancient Temples",
    description: "Walk in the footsteps of pharaohs at Luxor and Karnak, marveling at architectural wonders that have stood for millennia.",
    image: luxorTemple,
  },
];

const Destinations = () => {
  return (
    <section id="destinations" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="font-serif text-4xl sm:text-5xl font-bold text-foreground mb-4">
            Featured Destinations
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Explore the most captivating experiences Egypt has to offer
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {destinations.map((destination, index) => (
            <Card 
              key={destination.title} 
              className="group overflow-hidden border-0 shadow-medium hover:shadow-xl transition-all duration-300 animate-fade-in"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              <div className="relative h-64 overflow-hidden">
                <img
                  src={destination.image}
                  alt={destination.title}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              </div>
              <CardContent className="p-6">
                <h3 className="font-serif text-2xl font-semibold text-foreground mb-3">
                  {destination.title}
                </h3>
                <p className="text-muted-foreground mb-4">
                  {destination.description}
                </p>
                <Button variant="link" className="p-0 h-auto text-primary hover:text-accent">
                  View Details →
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Destinations;
