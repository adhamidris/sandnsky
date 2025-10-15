import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";

const Navigation = () => {
  const location = useLocation();
  const isHomePage = location.pathname === "/";

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/">
              <h1 className="text-2xl font-serif font-semibold text-primary">Nile Dreams</h1>
            </Link>
          </div>
          
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/" className="text-foreground hover:text-primary transition-colors">
              Home
            </Link>
            <Link to="/trips" className="text-foreground hover:text-primary transition-colors">
              Our Trips
            </Link>
            {isHomePage && (
              <>
                <a href="#about" className="text-foreground hover:text-primary transition-colors">
                  About
                </a>
                <a href="#contact" className="text-foreground hover:text-primary transition-colors">
                  Contact
                </a>
              </>
            )}
          </div>

          <Link to="/trips">
            <Button variant="default">Book Now</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
