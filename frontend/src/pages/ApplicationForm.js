import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../hooks/use-toast";
import { 
  ArrowLeft, Crown, Upload, User, Mail, Phone, Calendar,
  Instagram, X, Loader2
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
    const validFiles = files.filter(file => file.type.startsWith('image/') && file.size <= 10 * 1024 * 1024);

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

  const uploadPhotos = async (photos) => {
    if (photos.length === 0) return [];
    const uploadPromises = photos.map(async (photo) => {
      const formData = new FormData();
      formData.append("photo", photo.file);
      try {
        const res = await axios.post(`${API}/upload/photo`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        });
        return res.data.url;
      } catch (err) {
        console.error("Upload failed:", err);
        throw new Error(`Failed to upload ${photo.name}`);
      }
    });
    return await Promise.all(uploadPromises);
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
        description: "Applicants must be between 18-35 years old",
        variant: "destructive"
      });
      setIsSubmitting(false);
      return;
    }

    try {
      const photoUrls = await uploadPhotos(formData.photos);
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
      console.error("Submission failed:", error);
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
              {/* All your existing input fields stay unchanged */}
              {/* No need to modify form UI — just backend hook is updated */}
              {/* ... form content as in your original code ... */}
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ApplicationForm;
