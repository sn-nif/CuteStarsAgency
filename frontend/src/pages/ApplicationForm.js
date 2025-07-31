import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../hooks/use-toast";
import {
  ArrowLeft, Crown, Upload, Loader2, X
} from "lucide-react";
import axios from "axios";

const API = "https://cutestars-backend.onrender.com";

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
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(file => file.type.startsWith("image/") && file.size <= 10 * 1024 * 1024);

    if (validFiles.length !== files.length) {
      toast({
        title: "Invalid Files",
        description: "Only image files under 10MB are allowed.",
        variant: "destructive"
      });
    }

    const newPhotos = validFiles.map(file => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      file,
      url: URL.createObjectURL(file)
    }));

    setFormData(prev => ({
      ...prev,
      photos: [...prev.photos, ...newPhotos].slice(0, 5)
    }));
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
    setUploadProgress(0);

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
        description: "Applicants must be between 18–35 years old",
        variant: "destructive"
      });
      setIsSubmitting(false);
      return;
    }

    try {
      const applicationData = { ...formData };
      await axios.post(`${API}/apply`, applicationData);

      toast({
        title: "Application Submitted!",
        description: "We'll contact you within 48 hours."
      });

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
      toast({
        title: "Submission Failed",
        description: error.response?.data?.message || "Something went wrong.",
        variant: "destructive"
      });
    }

    setIsSubmitting(false);
    setUploadProgress(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black text-white">
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

      <div className="px-6 pb-12">
        <Card className="max-w-lg mx-auto shadow-2xl border-gray-700 bg-gradient-to-br from-gray-800/90 to-gray-900/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <CardTitle className="text-2xl bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">
              Join Cute Stars Elite
            </CardTitle>
            <p className="text-gray-300 mt-2">Begin your luxury career journey</p>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">

              {[
                { id: "name", type: "text", placeholder: "Full Name *" },
                { id: "age", type: "number", placeholder: "Age (18–35) *" },
                { id: "email", type: "email", placeholder: "Email *" },
                { id: "contact", type: "tel", placeholder: "Phone Number *" },
                { id: "instagram", type: "text", placeholder: "Instagram" },
                { id: "tiktok", type: "text", placeholder: "TikTok" },
                { id: "twitter", type: "text", placeholder: "X / Twitter" }
              ].map(field => (
                <Input
                  key={field.id}
                  id={field.id}
                  name={field.id}
                  type={field.type}
                  placeholder={field.placeholder}
                  value={formData[field.id]}
                  onChange={handleInputChange}
                  required={field.placeholder.includes("*")}
                  className="w-full bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 focus:border-yellow-500 focus:ring-yellow-500/30"
                />
              ))}

              {/* Photo Upload Section */}
              <div className="bg-gray-800/40 border-2 border-dashed border-gray-600 hover:border-yellow-500 rounded-xl p-6 text-center transition-all">
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handlePhotoUpload}
                  className="hidden"
                  id="photo-upload"
                />
                <label htmlFor="photo-upload" className="cursor-pointer block">
                  <Upload className="w-8 h-8 mx-auto text-yellow-400 mb-2" />
                  <p className="text-sm text-gray-300">Upload up to 5 photos</p>
                  <p className="text-xs text-gray-500">Max size: 10MB each</p>
                </label>
              </div>

              {uploadProgress > 0 && (
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-yellow-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              )}

              {formData.photos.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {formData.photos.map(photo => (
                    <div key={photo.id} className="relative">
                      <img src={photo.url} alt={photo.name} className="w-full h-20 object-cover rounded-lg border border-gray-600" />
                      <button
                        type="button"
                        onClick={() => removePhoto(photo.id)}
                        className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-5 h-5 text-xs"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gradient-to-r from-yellow-400 to-yellow-600 hover:to-yellow-700 text-black py-3 rounded-xl text-lg font-semibold"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Application"
                )}
              </Button>

              <p className="text-xs text-gray-500 text-center">
                By submitting, you agree to be contacted by Cute Stars Agency
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ApplicationForm;