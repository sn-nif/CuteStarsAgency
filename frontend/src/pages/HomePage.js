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
  CheckCircle
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-purple-50">
      {/* Header */}
      <header className="px-4 py-6 text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Star className="w-8 h-8 text-rose-500 fill-current" />
          <h1 className="text-2xl font-bold text-gray-900">Cute Stars</h1>
        </div>
        <Badge variant="secondary" className="bg-rose-100 text-rose-700 hover:bg-rose-200">
          Premier International Talent Agency
        </Badge>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-8 text-center">
        <div className="max-w-md mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-4 leading-tight">
            Launch Your 
            <span className="text-rose-600"> Digital Career</span> Today
          </h2>
          <p className="text-lg text-gray-600 mb-6 leading-relaxed">
            Join confident women aged 18-35 earning from home through live streaming on a global platform
          </p>
          <div className="flex flex-col gap-3">
            <Link to="/apply">
              <Button className="w-full bg-rose-600 hover:bg-rose-700 text-white py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300">
                Start Your Application
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <p className="text-sm text-gray-500">No experience needed • Hiring globally</p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="px-6 py-8">
        <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">What We Offer</h3>
        <div className="grid grid-cols-1 gap-4 max-w-lg mx-auto">
          {features.map((feature, index) => (
            <Card key={index} className="border-0 shadow-md hover:shadow-lg transition-shadow duration-300 bg-white/80 backdrop-blur-sm">
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 p-2 bg-rose-100 rounded-lg text-rose-600">
                    {feature.icon}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">{feature.title}</h4>
                    <p className="text-sm text-gray-600 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Benefits Section */}
      <section className="px-6 py-8 bg-white/60 backdrop-blur-sm">
        <div className="max-w-lg mx-auto">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">Why Choose Cute Stars?</h3>
          <div className="space-y-4">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                <p className="text-gray-700">{benefit}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-12 text-center">
        <div className="max-w-md mx-auto">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Ready to Get Started?</h3>
          <p className="text-gray-600 mb-8">
            Join hundreds of successful women who have transformed their lives with flexible online careers
          </p>
          <Link to="/apply">
            <Button className="w-full bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-700 hover:to-pink-700 text-white py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 text-lg">
              Apply Now - It's Free!
            </Button>
          </Link>
          <p className="text-xs text-gray-500 mt-4">
            Professional opportunity • Ages 18-35 • International positions available
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 text-center text-gray-500 text-sm">
        <p>© 2025 Cute Stars Agency. Professional talent management worldwide.</p>
      </footer>
    </div>
  );
};

export default HomePage;