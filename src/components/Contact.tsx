import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Mail, Phone, MapPin } from "lucide-react";

const Contact = () => {
  return (
    <section id="contact" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
          <div className="animate-slide-in">
            <h2 className="font-serif text-4xl sm:text-5xl font-bold text-foreground mb-6">
              Start Your Journey
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Ready to explore Egypt? Get in touch with our travel experts and we'll help create your perfect adventure.
            </p>

            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Mail className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Email Us</h3>
                  <p className="text-muted-foreground">info@niledreams.com</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Phone className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Call Us</h3>
                  <p className="text-muted-foreground">+20 123 456 7890</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <MapPin className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Visit Us</h3>
                  <p className="text-muted-foreground">Cairo, Egypt</p>
                </div>
              </div>
            </div>
          </div>

          <div className="animate-fade-in">
            <form className="space-y-6">
              <div>
                <Input 
                  type="text" 
                  placeholder="Your Name" 
                  className="w-full"
                />
              </div>
              <div>
                <Input 
                  type="email" 
                  placeholder="Your Email" 
                  className="w-full"
                />
              </div>
              <div>
                <Textarea 
                  placeholder="Tell us about your dream Egypt trip..."
                  className="w-full min-h-[150px]"
                />
              </div>
              <Button className="w-full" size="lg">
                Send Message
              </Button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Contact;
