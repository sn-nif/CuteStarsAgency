import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../hooks/use-toast";
import {
  ArrowLeft, Crown, Upload, Loader2
} from "lucide-react";
import axios from "axios";
import PhoneInput from "react-phone-input-2";
import 'react-phone-input-2/lib/style.css';

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
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePhoneChange = (value) => {
    setFormData(prev => ({ ...prev, contact: value }));
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

    const { name, age, email, contact, photos } = formData;

    if (!name || !age || !email || !contact || photos.length === 0) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields and upload at least one photo.",
        variant: "destructive"
      });
      setIsSubmitting(false);
      return;
    }

    if (parseInt(age) < 18 || parseInt(age) > 35) {
      toast({
        title: "Age Requirement",
        description: "Applicants must be between 18–35 years old",
        variant: "destructive"
      });
      setIsSubmitting(false);
      return;
    }

    try {
      const applicationData = {
        ...formData,
        photos: formData.photos.map(photo => photo.file)
      };

      const form = new FormData();
      Object.entries(applicationData).forEach(([key, value]) => {
        if (key === "photos") {
          value.forEach(file => form.append("photos", file));
        } else {
          form.append(key, value);
        }
      });

      await axios.post(`${API}/apply`, form, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      setShowSuccessModal(true);
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
              <Input
                name="name"
                type="text"
                placeholder="Full Name *"
                value={formData.name}
                onChange={handleInputChange}
                className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 focus:border-yellow-500"
                required
              />
              <Input
                name="age"
                type="number"
                placeholder="Age (18–35) *"
                value={formData.age}
                onChange={handleInputChange}
                className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 focus:border-yellow-500"
                required
              />
              <Input
                name="email"
                type="email"
                placeholder="Email *"
                value={formData.email}
                onChange={handleInputChange}
                className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 focus:border-yellow-500"
                required
              />
              <div className="bg-gray-800/40 border border-gray-600 rounded-lg px-3 py-2">
                <PhoneInput
                  country={'us'}
                  value={formData.contact}
                  onChange={handlePhoneChange}
                  inputStyle={{
                    width: "100%",
                    backgroundColor: "transparent",
                    color: "white",
                    border: "none"
                  }}
                  buttonStyle={{
                    backgroundColor: "transparent",
                    border: "none"
                  }}
                  containerStyle={{ width: "100%" }}
                  placeholder="Phone Number *"
                  required
                />
              </div>

              <Input
                name="instagram"
                type="text"
                placeholder="Instagram (optional)"
                value={formData.instagram}
                onChange={handleInputChange}
                className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 focus:border-yellow-500"
              />
              <Input
                name="tiktok"
                type="text"
                placeholder="TikTok (optional)"
                value={formData.tiktok}
                onChange={handleInputChange}
                className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 focus:border-yellow-500"
              />
              <Input
                name="twitter"
                type="text"
                placeholder="X / Twitter (optional)"
                value={formData.twitter}
                onChange={handleInputChange}
                className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 focus:border-yellow-500"
              />

              {/* Upload */}
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
                  <p className="text-sm text-gray-300">Upload up to 5 photos *</p>
                  <p className="text-xs text-gray-500">Max size: 10MB each</p>
                </label>
              </div>

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

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
          <div className="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full text-center">
            <h2 className="text-xl font-semibold mb-2 text-yellow-600">Application Submitted</h2>
            <p className="text-gray-700 mb-4">You will hear from us soon.</p>
            <button
              onClick={() => setShowSuccessModal(false)}
              className="bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 px-4 rounded"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationForm;