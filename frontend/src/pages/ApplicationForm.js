import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { 
  ArrowLeft, Crown, Upload, User, Mail, Phone, Calendar,
  Instagram, X, Loader2
} from "lucide-react";
import axios from "axios";

const API = "https://cutestars-backend.onrender.com";

const ApplicationForm = () => {
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
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const handleChange = (e) => {
    const { name, value, files } = e.target;
    if (name === "photos") {
      setFormData({ ...formData, photos: Array.from(files) });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const form = new FormData();
      for (const key in formData) {
        if (key === "photos") {
          formData.photos.forEach(photo => {
            form.append("photos", photo);
          });
        } else {
          form.append(key, formData[key]);
        }
      }

      const response = await axios.post(`${API}/apply`, form, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      if (response.status === 200) {
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
      }
    } catch (error) {
      alert("Submission failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-center text-gold-600 text-2xl font-bold">
            Apply Now
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              name="name"
              placeholder="Name"
              value={formData.name}
              onChange={handleChange}
              className="placeholder:text-yellow-500"
              required
            />
            <Input
              name="age"
              placeholder="Age"
              value={formData.age}
              onChange={handleChange}
              className="placeholder:text-yellow-500"
              required
            />
            <Input
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              className="placeholder:text-yellow-500"
              required
            />
            <Input
              name="contact"
              placeholder="Phone Number"
              value={formData.contact}
              onChange={handleChange}
              className="placeholder:text-yellow-500"
              required
            />
            <Input
              name="instagram"
              placeholder="Instagram Username"
              value={formData.instagram}
              onChange={handleChange}
              className="placeholder:text-yellow-500"
            />
            <Input
              name="tiktok"
              placeholder="TikTok Username"
              value={formData.tiktok}
              onChange={handleChange}
              className="placeholder:text-yellow-500"
            />
            <Input
              name="twitter"
              placeholder="Twitter Username"
              value={formData.twitter}
              onChange={handleChange}
              className="placeholder:text-yellow-500"
            />

            <div>
              <label className="block mb-2 text-yellow-500 font-medium">Upload Photos</label>
              <input
                type="file"
                name="photos"
                accept="image/*"
                multiple
                onChange={handleChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-yellow-500 file:text-white hover:file:bg-yellow-600"
                required
              />
            </div>

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-yellow-500 hover:bg-yellow-600 text-white"
            >
              {isSubmitting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                "Submit Application"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

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