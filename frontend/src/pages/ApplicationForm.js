import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Textarea } from "../components/ui/textarea";
import { useToast } from "../hooks/use-toast";
import { 
  ArrowLeft, 
  Star, 
  Upload, 
  User, 
  Mail, 
  Phone, 
  Calendar,
  Instagram,
  X
} from "lucide-react";
import { mockApplications } from "../utils/mock";

const ApplicationForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    email: "",
    contact: "",
    instagram: "",
    tiktok: "",
    twitter: "",
    photos: []
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      // Mock file handling - in real app would upload to server
      const newPhotos = files.map(file => ({
        id: Date.now() + Math.random(),
        name: file.name,
        size: file.size,
        url: URL.createObjectURL(file)
      }));
      
      setFormData(prev => ({
        ...prev,
        photos: [...prev.photos, ...newPhotos].slice(0, 5) // Max 5 photos
      }));
    }
  };

  const removePhoto = (photoId) => {
    setFormData(prev => ({
      ...prev,
      photos: prev.photos.filter(photo => photo.id !== photoId)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Basic validation
    if (!formData.name || !formData.age || !formData.email || !formData.contact) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields",
        variant: "destructive"
      });
      setIsSubmitting(false);
      return;
    }

    if (parseInt(formData.age) < 18 || parseInt(formData.age) > 35) {
      toast({
        title: "Age Requirement",
        description: "Applicants must be between 18-35 years old",
        variant: "destructive"
      });
      setIsSubmitting(false);
      return;
    }

    // Mock submission
    setTimeout(() => {
      mockApplications.push({
        id: Date.now(),
        ...formData,
        submittedAt: new Date().toISOString(),
        status: "pending"
      });

      toast({
        title: "Application Submitted Successfully!",
        description: "We'll review your application and contact you within 48 hours",
      });

      // Reset form
      setFormData({
        name: "",
        age: "",
        email: "",
        contact: "",
        instagram: "",
        tiktok: "",
        twitter: "",
        photos: []
      });
      
      setIsSubmitting(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-purple-50">
      {/* Header */}
      <header className="px-4 py-6 flex items-center">
        <Link to="/">
          <Button variant="ghost" size="sm" className="mr-3">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div className="flex items-center gap-2">
          <Star className="w-6 h-6 text-rose-500 fill-current" />
          <h1 className="text-xl font-bold text-gray-900">Application Form</h1>
        </div>
      </header>

      <div className="px-6 pb-8">
        <Card className="max-w-lg mx-auto shadow-lg border-0 bg-white/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <CardTitle className="text-2xl text-gray-900">Join Cute Stars</CardTitle>
            <p className="text-gray-600 mt-2">Tell us about yourself and start your journey</p>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="name" className="flex items-center gap-2 text-gray-700 mb-2">
                    <User className="w-4 h-4" />
                    Full Name *
                  </Label>
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Enter your full name"
                    className="border-gray-200 focus:border-rose-500"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="age" className="flex items-center gap-2 text-gray-700 mb-2">
                    <Calendar className="w-4 h-4" />
                    Age *
                  </Label>
                  <Input
                    id="age"
                    name="age"
                    type="number"
                    min="18"
                    max="35"
                    value={formData.age}
                    onChange={handleInputChange}
                    placeholder="18"
                    className="border-gray-200 focus:border-rose-500"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">Must be between 18-35 years old</p>
                </div>

                <div>
                  <Label htmlFor="email" className="flex items-center gap-2 text-gray-700 mb-2">
                    <Mail className="w-4 h-4" />
                    Email Address *
                  </Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="your.email@example.com"
                    className="border-gray-200 focus:border-rose-500"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="contact" className="flex items-center gap-2 text-gray-700 mb-2">
                    <Phone className="w-4 h-4" />
                    Phone Number *
                  </Label>
                  <Input
                    id="contact"
                    name="contact"
                    type="tel"
                    value={formData.contact}
                    onChange={handleInputChange}
                    placeholder="+1 (555) 123-4567"
                    className="border-gray-200 focus:border-rose-500"
                    required
                  />
                </div>
              </div>

              {/* Social Media */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">Social Media Profiles</h3>
                <p className="text-sm text-gray-600">Help us understand your online presence</p>
                
                <div>
                  <Label htmlFor="instagram" className="flex items-center gap-2 text-gray-700 mb-2">
                    <Instagram className="w-4 h-4" />
                    Instagram
                  </Label>
                  <Input
                    id="instagram"
                    name="instagram"
                    type="text"
                    value={formData.instagram}
                    onChange={handleInputChange}
                    placeholder="@yourusername"
                    className="border-gray-200 focus:border-rose-500"
                  />
                </div>

                <div>
                  <Label htmlFor="tiktok" className="flex items-center gap-2 text-gray-700 mb-2">
                    <span className="w-4 h-4 text-sm font-bold">TT</span>
                    TikTok
                  </Label>
                  <Input
                    id="tiktok"
                    name="tiktok"
                    type="text"
                    value={formData.tiktok}
                    onChange={handleInputChange}
                    placeholder="@yourusername"
                    className="border-gray-200 focus:border-rose-500"
                  />
                </div>

                <div>
                  <Label htmlFor="twitter" className="flex items-center gap-2 text-gray-700 mb-2">
                    <X className="w-4 h-4" />
                    X (Twitter)
                  </Label>
                  <Input
                    id="twitter"
                    name="twitter"
                    type="text"
                    value={formData.twitter}
                    onChange={handleInputChange}
                    placeholder="@yourusername"
                    className="border-gray-200 focus:border-rose-500"
                  />
                </div>
              </div>

              {/* Photo Upload */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">Photos</h3>
                <p className="text-sm text-gray-600">Upload up to 5 professional photos (optional but recommended)</p>
                
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-rose-400 transition-colors">
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handlePhotoUpload}
                    className="hidden"
                    id="photo-upload"
                  />
                  <label htmlFor="photo-upload" className="cursor-pointer">
                    <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-600">Click to upload photos</p>
                    <p className="text-xs text-gray-500">PNG, JPG up to 10MB each</p>
                  </label>
                </div>

                {/* Photo Preview */}
                {formData.photos.length > 0 && (
                  <div className="grid grid-cols-3 gap-2">
                    {formData.photos.map((photo) => (
                      <div key={photo.id} className="relative">
                        <img
                          src={photo.url}
                          alt={photo.name}
                          className="w-full h-20 object-cover rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={() => removePhoto(photo.id)}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-rose-600 hover:bg-rose-700 text-white py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 text-lg"
              >
                {isSubmitting ? "Submitting Application..." : "Submit Application"}
              </Button>

              <p className="text-xs text-gray-500 text-center">
                By submitting, you agree to be contacted about opportunities with Cute Stars Agency
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ApplicationForm;