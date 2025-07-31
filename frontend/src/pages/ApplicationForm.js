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
            <form onSubmit={handleSubmit} className="space-y-6">

              <div>
                <Label htmlFor="name">Full Name *</Label>
                <Input id="name" name="name" type="text" value={formData.name} onChange={handleInputChange} required />
              </div>

              <div>
                <Label htmlFor="age">Age *</Label>
                <Input id="age" name="age" type="number" value={formData.age} onChange={handleInputChange} required />
              </div>

              <div>
                <Label htmlFor="email">Email *</Label>
                <Input id="email" name="email" type="email" value={formData.email} onChange={handleInputChange} required />
              </div>

              <div>
                <Label htmlFor="contact">Phone *</Label>
                <Input id="contact" name="contact" type="tel" value={formData.contact} onChange={handleInputChange} required />
              </div>

              <div>
                <Label htmlFor="instagram">Instagram</Label>
                <Input id="instagram" name="instagram" type="text" value={formData.instagram} onChange={handleInputChange} />
              </div>

              <div>
                <Label htmlFor="tiktok">TikTok</Label>
                <Input id="tiktok" name="tiktok" type="text" value={formData.tiktok} onChange={handleInputChange} />
              </div>

              <div>
                <Label htmlFor="twitter">X / Twitter</Label>
                <Input id="twitter" name="twitter" type="text" value={formData.twitter} onChange={handleInputChange} />
              </div>

              <div>
                <Label htmlFor="photos">Upload Photos (optional)</Label>
                <input type="file" accept="image/*" multiple onChange={handlePhotoUpload} />
              </div>

              {/* Upload progress bar (optional) */}
              {uploadProgress > 0 && (
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div className="bg-yellow-500 h-2 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
                </div>
              )}

              {/* Photo previews */}
              {formData.photos.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {formData.photos.map(photo => (
                    <div key={photo.id} className="relative">
                      <img src={photo.url} alt="preview" className="w-full h-20 object-cover rounded" />
                      <button type="button" onClick={() => removePhoto(photo.id)} className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-5 h-5 text-xs">×</button>
                    </div>
                  ))}
                </div>
              )}

              <Button type="submit" className="w-full bg-gradient-to-r from-yellow-400 to-yellow-600 hover:to-yellow-700 text-black py-3 rounded-xl text-lg font-semibold" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Application"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ApplicationForm;
