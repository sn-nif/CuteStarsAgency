import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { 
  Star, 
  Globe, 
  Users, 
  Smartphone, 
  DollarSign, 
  Shield, 
  Clock,
  ArrowRight,
  CheckCircle,
  Crown
} from "lucide-react";

const HomePage = () => {
  const features = [
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Safe & Professional",
      description: "Work in a secure, supportive environment with full management backing"
    },
    {
      icon: <Smartphone className="w-6 h-6" />,
      title: "100% Remote",
      description: "Work from anywhere using just your phone - complete flexibility"
    },
    {
      icon: <DollarSign className="w-6 h-6" />,
      title: "High Earnings",
      description: "Competitive compensation through live interactive streaming"
    },
    {
      icon: <Clock className="w-6 h-6" />,
      title: "Flexible Schedule",
      description: "Set your own hours and work when it suits your lifestyle"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Dedicated Support",
      description: "International management team provides training and guidance"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Global Platform",
      description: "Connect with audiences worldwide on a major streaming platform"
    }
  ];

  const benefits = [
    "No experience required - just confidence and energy",
    "Complete onboarding and training provided",
    "Professional growth opportunities",
    "Flexible part-time or full-time options",
    "Safe and regulated working environment"
  ];

  const testimonialImages = [
    "https://images.unsplash.com/photo-1653035778893-b46df4793052?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHxwcm9mZXNzaW9uYWwlMjBtb2RlbCUyMHdvbWFufGVufDB8fHx8MTc1Mzk0MzcwNXww&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1706824261799-55343861e08e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwyfHxwcm9mZXNzaW9uYWwlMjBtb2RlbCUyMHdvbWFufGVufDB8fHx8MTc1Mzk0MzcwNXww&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1588802658751-1a3d0dca0f61?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzV8MHwxfHNlYXJjaHwxfHxlbGVnYW50JTIwZmVtYWxlJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzUzOTQzNzEyfDA&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1631695117568-c56a4e039ac4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzV8MHwxfHNlYXJjaHwyfHxlbGVnYW50JTIwZmVtYWxlJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzUzOTQzNzEyfDA&ixlib=rb-4.1.0&q=85"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black text-white">
    <a
      href="https://cutestars-backend.onrender.com/login"
      target="_blank"
      rel="noopener noreferrer"
      className="fixed top-4 right-4 z-50 bg-yellow-400 text-black font-semibold py-2 px-4 rounded-md shadow-lg hover:bg-yellow-500 transition-all duration-300"
    >
      Admin Login
    </a>
      {/* Header */}
      <header className="px-4 py-6 text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Crown className="w-8 h-8 text-yellow-400 fill-current" />
          <h1 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
            Cute Stars
          </h1>
        </div>
        <Badge variant="secondary" className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-black hover:from-yellow-500 hover:to-yellow-700 font-semibold">
          Premier International Talent Agency
        </Badge>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-8 text-center relative">
        <div className="absolute inset-0 bg-gradient-to-r from-yellow-400/10 to-transparent rounded-3xl"></div>
        <div className="max-w-md mx-auto relative z-10">
          <h2 className="text-3xl font-bold mb-4 leading-tight">
            Launch Your 
            <span className="bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent"> Luxury Career</span> Today
          </h2>
          <p className="text-lg text-gray-300 mb-6 leading-relaxed">
            Join elite women aged 18-35 earning premium income from home through exclusive live streaming platforms
          </p>
          <div className="flex flex-col gap-3">
            <Link to="/apply">
              <Button className="w-full bg-gradient-to-r from-yellow-400 to-yellow-600 hover:from-yellow-500 hover:to-yellow-700 text-black py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 font-semibold">
                Start Your Application
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <p className="text-sm text-gray-400">Exclusive opportunity • Premium positions • Hiring globally</p>
          </div>
        </div>
      </section>

      {/* Success Stories */}
      <section className="px-6 py-8">
        <h3 className="text-2xl font-bold text-center mb-8 bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
          Our Success Stories
        </h3>
        <div className="grid grid-cols-2 gap-4 max-w-lg mx-auto mb-6">
          {testimonialImages.map((image, index) => (
            <div key={index} className="relative group">
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent rounded-lg z-10"></div>
              <img
                src={image}
                alt={`Success story ${index + 1}`}
                className="w-full h-32 object-cover rounded-lg filter brightness-90 group-hover:brightness-100 transition-all duration-300"
                loading="lazy"
              />
              <div className="absolute bottom-2 left-2 z-20">
                <div className="flex items-center gap-1">
                  {Array.from({length: 5}).map((_, i) => (
                    <Star key={i} className="w-3 h-3 text-yellow-400 fill-current" />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="text-center text-gray-300 text-sm">
          "The support and flexibility have transformed my life" - Our talents
        </p>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-8">
        <h3 className="text-2xl font-bold text-center mb-8 bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
          Luxury Benefits
        </h3>
        <div className="grid grid-cols-1 gap-4 max-w-lg mx-auto">
          {features.map((feature, index) => (
            <Card key={index} className="border-gray-700 bg-gradient-to-r from-gray-800/50 to-gray-900/50 backdrop-blur-sm hover:from-gray-700/50 hover:to-gray-800/50 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 p-2 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-lg text-black">
                    {feature.icon}
                  </div>
                  <div>
                    <h4 className="font-semibold text-white mb-1">{feature.title}</h4>
                    <p className="text-sm text-gray-300 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Benefits Section */}
      <section className="px-6 py-8 bg-gradient-to-r from-gray-800/30 to-gray-900/30 backdrop-blur-sm">
        <div className="max-w-lg mx-auto">
          <h3 className="text-2xl font-bold text-center mb-8 bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
            Why Choose Cute Stars?
          </h3>
          <div className="space-y-4">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                <p className="text-gray-200">{benefit}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-12 text-center">
        <div className="max-w-md mx-auto">
          <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
            Ready for Luxury?
          </h3>
          <p className="text-gray-300 mb-8">
            Join hundreds of successful women who have built premium careers with flexible online opportunities
          </p>
          <Link to="/apply">
            <Button className="w-full bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 hover:from-yellow-500 hover:via-yellow-600 hover:to-yellow-700 text-black py-4 rounded-xl shadow-xl hover:shadow-2xl transition-all duration-300 text-lg font-bold">
              Apply Now - Exclusive Access
            </Button>
          </Link>
          <p className="text-xs text-gray-500 mt-4">
            Premium opportunity • Ages 18-35 • International luxury positions
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 text-center text-gray-500 text-sm border-t border-gray-800">
        <p>© 2025 Cute Stars Agency. Luxury talent management worldwide.</p>
      </footer>
    </div>
  );
};

export default HomePage;