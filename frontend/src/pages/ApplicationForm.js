import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../hooks/use-toast";
import { 
  ArrowLeft, 
  Crown, 
  Upload, 
  User, 
  Mail, 
  Phone, 
  Calendar,
  Instagram,
  X,
  Loader2
} from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
  const [uploadProgress, setUploadProgress] = useState(0);

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
      // Validate file types and sizes
      const validFiles = files.filter(file => {
        const isValidType = file.type.startsWith('image/');
        const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB
        return isValidType && isValidSize;
      });

      if (validFiles.length !== files.length) {
        toast({
          title: "Invalid Files",
          description: "Some files were rejected. Only images under 10MB are allowed.",
          variant: "destructive"
        });
      }

      const newPhotos = validFiles.map(file => ({
        id: Date.now() + Math.random(),
        name: file.name,
        size: file.size,
        file: file,
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

  const uploadPhotos = async (photos) => {
    if (photos.length === 0) return [];
    
    const uploadPromises = photos.map(async (photo) => {
      const formData = new FormData();
      formData.append('photo', photo.file);
      
      try {
        const response = await axios.post(`${API}/upload/photo`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        });
        
        return response.data.url;
      } catch (error) {
        console.error('Photo upload failed:', error);
        throw new Error(`Failed to upload ${photo.name}`);
      }
    });

    return await Promise.all(uploadPromises);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setUploadProgress(0);

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

    try {
      // Upload photos first
      let photoUrls = [];
      if (formData.photos.length > 0) {
        photoUrls = await uploadPhotos(formData.photos);
      }

      // Submit application
      const applicationData = {
        name: formData.name,
        age: parseInt(formData.age),
        email: formData.email,
        contact: formData.contact,
        instagram: formData.instagram,
        tiktok: formData.tiktok,
        twitter: formData.twitter,
        photos: photoUrls
      };

      const response = await axios.post(`${API}/applications`, applicationData);

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
      
    } catch (error) {
      console.error('Application submission failed:', error);
      toast({
        title: "Submission Failed",
        description: error.response?.data?.message || "Please try again later",
        variant: "destructive"
      });
    }
    
    setIsSubmitting(false);
    setUploadProgress(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black text-white">
      {/* Header */}
      <header className="px-4 py-6 flex items-center">
        <Link to="/">
          <Button variant="ghost" size="sm" className="mr-3 text-white hover:text-yellow-400 hover:bg-gray-800">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div className="flex items-center gap-2">
          <Crown className="w-6 h-6 text-yellow-400 fill-current" />
          <h1 className="text-xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
            Luxury Application
          </h1>
        </div>
      </header>

      <div className="px-6 pb-8">
        <Card className="max-w-lg mx-auto shadow-2xl border-gray-700 bg-gradient-to-br from-gray-800/90 to-gray-900/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <CardTitle className="text-2xl bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
              Join Cute Stars Elite
            </CardTitle>
            <p className="text-gray-300 mt-2">Begin your luxury career journey</p>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="name" className="flex items-center gap-2 text-gray-200 mb-2">
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
                    className="border-gray-600 bg-gray-800/50 text-white placeholder-gray-400 focus:border-yellow-500 focus:ring-yellow-500/20"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="age" className="flex items-center gap-2 text-gray-200 mb-2">
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
                    className="border-gray-600 bg-gray-800/50 text-white placeholder-gray-400 focus:border-yellow-500 focus:ring-yellow-500/20"
                    required
                  />
                  <p className="text-xs text-gray-400 mt-1">Must be between 18-35 years old</p>
                </div>

                <div>
                  <Label htmlFor="email" className="flex items-center gap-2 text-gray-200 mb-2">
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
                    className="border-gray-600 bg-gray-800/50 text-white placeholder-gray-400 focus:border-yellow-500 focus:ring-yellow-500/20"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="contact" className="flex items-center gap-2 text-gray-200 mb-2">
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
                    className="border-gray-600 bg-gray-800/50 text-white placeholder-gray-400 focus:border-yellow-500 focus:ring-yellow-500/20"
                    required
                  />
                </div>
              </div>

              {/* Social Media */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-200">Social Media Profiles</h3>
                <p className="text-sm text-gray-400">Help us understand your online presence</p>
                
                <div>
                  <Label htmlFor="instagram" className="flex items-center gap-2 text-gray-200 mb-2">
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
                    className="border-gray-600 bg-gray-800/50 text-white placeholder-gray-400 focus:border-yellow-500 focus:ring-yellow-500/20"
                  />
                </div>

                <div>
                  <Label htmlFor="tiktok" className="flex items-center gap-2 text-gray-200 mb-2">
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
                    className="border-gray-600 bg-gray-800/50 text-white placeholder-gray-400 focus:border-yellow-500 focus:ring-yellow-500/20"
                  />
                </div>

                <div>
                  <Label htmlFor="twitter" className="flex items-center gap-2 text-gray-200 mb-2">
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
                    className="border-gray-600 bg-gray-800/50 text-white placeholder-gray-400 focus:border-yellow-500 focus:ring-yellow-500/20"
                  />
                </div>
              </div>

              {/* Photo Upload */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-200">Professional Photos</h3>
                <p className="text-sm text-gray-400">Upload up to 5 professional photos (optional but highly recommended)</p>
                
                <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-yellow-500 transition-colors bg-gray-800/30">
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handlePhotoUpload}
                    className="hidden"
                    id="photo-upload"
                  />
                  <label htmlFor="photo-upload" className="cursor-pointer">
                    <Upload className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                    <p className="text-gray-300">Click to upload photos</p>
                    <p className="text-xs text-gray-500">PNG, JPG up to 10MB each</p>
                  </label>
                </div>

                {/* Upload Progress */}
                {uploadProgress > 0 && uploadProgress < 100 && (
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-yellow-400 to-yellow-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                )}

                {/* Photo Preview */}
                {formData.photos.length > 0 && (
                  <div className="grid grid-cols-3 gap-2">
                    {formData.photos.map((photo) => (
                      <div key={photo.id} className="relative">
                        <img
                          src={photo.url}
                          alt={photo.name}
                          className="w-full h-20 object-cover rounded-lg border border-gray-600"
                        />
                        <button
                          type="button"
                          onClick={() => removePhoto(photo.id)}
                          className="absolute -top-2 -right-2 bg-red-600 hover:bg-red-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs transition-colors"
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
                className="w-full bg-gradient-to-r from-yellow-400 to-yellow-600 hover:from-yellow-500 hover:to-yellow-700 text-black py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 text-lg font-semibold disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting Application...
                  </>
                ) : (
                  "Submit Luxury Application"
                )}
              </Button>

              <p className="text-xs text-gray-500 text-center">
                By submitting, you agree to be contacted about exclusive opportunities with Cute Stars Agency
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ApplicationForm;