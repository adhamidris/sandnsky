import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";
import heroImage from "@/assets/hero-pyramids.jpg";

const Hero = () => {
  return (
    <section className="relative h-screen flex items-center justify-center overflow-hidden">
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-black/20 to-black/60" />
      </div>
      
      <div className="relative z-10 text-center px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto animate-fade-in">
        <h1 className="font-serif text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6">
          Discover the Magic of Egypt
        </h1>
        <p className="text-xl sm:text-2xl text-white/90 mb-8 max-w-2xl mx-auto">
          Embark on an unforgettable journey through ancient wonders and timeless beauty
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" className="text-lg px-8">
            Explore Tours
          </Button>
          <Button size="lg" variant="outline" className="text-lg px-8 bg-white/10 backdrop-blur-sm border-white text-white hover:bg-white hover:text-foreground">
            Learn More
          </Button>
        </div>
      </div>

      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <ChevronDown className="w-8 h-8 text-white" />
      </div>
    </section>
  );
};

export default Hero;
