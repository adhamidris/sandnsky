const Footer = () => {
    return (
      <footer className="bg-foreground text-background py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
            <div>
              <h3 className="font-serif text-2xl font-semibold mb-4">Nile Dreams</h3>
              <p className="text-background/80">
                Creating unforgettable journeys through the wonders of Egypt since 2010.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Quick Links</h4>
              <ul className="space-y-2 text-background/80">
                <li><a href="#destinations" className="hover:text-background transition-colors">Destinations</a></li>
                <li><a href="#about" className="hover:text-background transition-colors">About Us</a></li>
                <li><a href="#contact" className="hover:text-background transition-colors">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Follow Us</h4>
              <p className="text-background/80 mb-2">Stay connected for travel inspiration</p>
              <div className="flex gap-4">
                <a href="#" className="text-background/80 hover:text-background transition-colors">Facebook</a>
                <a href="#" className="text-background/80 hover:text-background transition-colors">Instagram</a>
                <a href="#" className="text-background/80 hover:text-background transition-colors">Twitter</a>
              </div>
            </div>
          </div>
          
          <div className="border-t border-background/20 pt-8 text-center text-background/60">
            <p>&copy; 2024 Nile Dreams Travel. All rights reserved.</p>
          </div>
        </div>
      </footer>
    );
  };
  
  export default Footer;
  