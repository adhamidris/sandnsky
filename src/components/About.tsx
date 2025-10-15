import { Award, Heart, Shield, Users } from "lucide-react";

const features = [
  {
    icon: Award,
    title: "Expert Guides",
    description: "Licensed Egyptologists and local experts bring history to life",
  },
  {
    icon: Shield,
    title: "Safe & Secure",
    description: "Your safety is our priority with comprehensive travel insurance",
  },
  {
    icon: Heart,
    title: "Personalized Service",
    description: "Tailored itineraries designed around your interests and pace",
  },
  {
    icon: Users,
    title: "Small Groups",
    description: "Intimate group sizes ensure a more personal experience",
  },
];

const About = () => {
  return (
    <section id="about" className="py-24 px-4 sm:px-6 lg:px-8 bg-secondary/30">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="font-serif text-4xl sm:text-5xl font-bold text-foreground mb-4">
            Why Choose Nile Dreams
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            We're passionate about creating extraordinary experiences in Egypt
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div 
              key={feature.title} 
              className="text-center animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary to-accent mb-4">
                <feature.icon className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-serif text-xl font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default About;
