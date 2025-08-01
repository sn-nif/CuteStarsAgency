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
import "react-phone-input-2/lib/style.css";

const API = "https://cutestars-backend.onrender.com";

const countries = [
  "Afghanistan",
  "Albania",
  "Algeria",
  "Andorra",
  "Angola",
  "Antigua and Barbuda",
  "Argentina",
  "Armenia",
  "Australia",
  "Austria",
  "Azerbaijan",
  "Bahamas",
  "Bahrain",
  "Bangladesh",
  "Barbados",
  "Belarus",
  "Belgium",
  "Belize",
  "Benin",
  "Bhutan",
  "Bolivia",
  "Bosnia and Herzegovina",
  "Botswana",
  "Brazil",
  "Brunei",
  "Bulgaria",
  "Burkina Faso",
  "Burundi",
  "Cabo Verde",
  "Cambodia",
  "Cameroon",
  "Canada",
  "Central African Republic",
  "Chad",
  "Chile",
  "China",
  "Colombia",
  "Comoros",
  "Congo (Brazzaville)",
  "Congo (Kinshasa)",
  "Costa Rica",
  "Croatia",
  "Cuba",
  "Cyprus",
  "Czechia",
  "Denmark",
  "Djibouti",
  "Dominica",
  "Dominican Republic",
  "Ecuador",
  "Egypt",
  "El Salvador",
  "Equatorial Guinea",
  "Eritrea",
  "Estonia",
  "Eswatini",
  "Ethiopia",
  "Fiji",
  "Finland",
  "France",
  "Gabon",
  "Gambia",
  "Georgia",
  "Germany",
  "Ghana",
  "Greece",
  "Grenada",
  "Guatemala",
  "Guinea",
  "Guinea-Bissau",
  "Guyana",
  "Haiti",
  "Honduras",
  "Hungary",
  "Iceland",
  "India",
  "Indonesia",
  "Iran",
  "Iraq",
  "Ireland",
  "Israel",
  "Italy",
  "Ivory Coast",
  "Jamaica",
  "Japan",
  "Jordan",
  "Kazakhstan",
  "Kenya",
  "Kiribati",
  "Kuwait",
  "Kyrgyzstan",
  "Laos",
  "Latvia",
  "Lebanon",
  "Lesotho",
  "Liberia",
  "Libya",
  "Liechtenstein",
  "Lithuania",
  "Luxembourg",
  "Madagascar",
  "Malawi",
  "Malaysia",
  "Maldives",
  "Mali",
  "Malta",
  "Marshall Islands",
  "Mauritania",
  "Mauritius",
  "Mexico",
  "Micronesia",
  "Moldova",
  "Monaco",
  "Mongolia",
  "Montenegro",
  "Morocco",
  "Mozambique",
  "Myanmar",
  "Namibia",
  "Nauru",
  "Nepal",
  "Netherlands",
  "New Zealand",
  "Nicaragua",
  "Niger",
  "Nigeria",
  "North Korea",
  "North Macedonia",
  "Norway",
  "Oman",
  "Pakistan",
  "Palau",
  "Palestine",
  "Panama",
  "Papua New Guinea",
  "Paraguay",
  "Peru",
  "Philippines",
  "Poland",
  "Portugal",
  "Qatar",
  "Romania",
  "Russia",
  "Rwanda",
  "Saint Kitts and Nevis",
  "Saint Lucia",
  "Saint Vincent and the Grenadines",
  "Samoa",
  "San Marino",
  "Sao Tome and Principe",
  "Saudi Arabia",
  "Senegal",
  "Serbia",
  "Seychelles",
  "Sierra Leone",
  "Singapore",
  "Slovakia",
  "Slovenia",
  "Solomon Islands",
  "Somalia",
  "South Africa",
  "South Korea",
  "South Sudan",
  "Spain",
  "Sri Lanka",
  "Sudan",
  "Suriname",
  "Sweden",
  "Switzerland",
  "Syria",
  "Taiwan",
  "Tajikistan",
  "Tanzania",
  "Thailand",
  "Timor-Leste",
  "Togo",
  "Tonga",
  "Trinidad and Tobago",
  "Tunisia",
  "Turkey",
  "Turkmenistan",
  "Tuvalu",
  "Uganda",
  "Ukraine",
  "United Arab Emirates",
  "United Kingdom",
  "United States",
  "Uruguay",
  "Uzbekistan",
  "Vanuatu",
  "Vatican City",
  "Venezuela",
  "Vietnam",
  "Yemen",
  "Zambia",
  "Zimbabwe"
];

const ApplicationForm = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    email: "",
    contact: "",
    country: "",
    instagram: "",
    tiktok: "",
    telegram: "",
    photos: [],
    ip: "",
    geoCountry: "",
    geoCity: "",
    geoRegion: ""
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  useEffect(() => {
  const fetchGeoInfo = async () => {
    try {
      const res = await fetch("https://ipapi.co/json/");
      const data = await res.json();
      setFormData(prev => ({
        ...prev,
        ip: data.ip || "",
        geoCountry: data.country_name || "",
        geoCity: data.city || "",
        geoRegion: data.region || ""
      }));
    } catch (err) {
      console.error("Failed to fetch geo info", err);
    }
  };
  fetchGeoInfo();
}, []);
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
      setErrorMessage("Only image files under 10MB are allowed.");
      setShowErrorModal(true);
      return;
    }
    const newPhotos = validFiles.map(file => ({
      id: Date.now() + Math.random(),
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

    const { name, age, email, contact, photos, country } = formData;

    if (!name || !age || !email || !contact || !country || photos.length === 0) {
      setErrorMessage("Please fill in all required fields and upload at least one photo.");
      setShowErrorModal(true);
      setIsSubmitting(false);
      return;
    }

    if (parseInt(age) < 18) {
      setErrorMessage("Applicants must be at least 18 years old.");
      setShowErrorModal(true);
      setIsSubmitting(false);
      return;
    }

    try {
      const form = new FormData();
      for (let key in formData) {
        if (key === "photos") {
          formData.photos.forEach(p => form.append("photos", p.file));
        } else {
          form.append(key, formData[key]);
        }
      }
      await axios.post(`${API}/apply`, form, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setShowSuccessModal(true);
      setFormData({
        name: "",
        age: "",
        email: "",
        contact: "",
        country: "",
        instagram: "",
        tiktok: "",
        telegram: "",
        photos: [],
        ip: "",
        geoCountry: "",
        geoCity: "",
        geoRegion: ""
      });
    } catch (error) {
      setErrorMessage(error.response?.data?.message || "Server error.");
      setShowErrorModal(true);
    }

    setIsSubmitting(false);
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
              <Input name="name" placeholder="Full Name *" value={formData.name} onChange={handleInputChange} required className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600" />

              <select
                name="age"
                value={formData.age}
                onChange={handleInputChange}
                required
                className="w-full bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 rounded-lg py-2 px-3"
              >
                <option value="">Select your age *</option>
                {Array.from({ length: 52 }, (_, i) => 18 + i).map((age) => (
                  <option key={age} value={age}>{age}</option>
                ))}
              </select>

              <Input name="email" type="email" placeholder="Email *" value={formData.email} onChange={handleInputChange} required className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600" />

              <div className="bg-gray-800/40 border border-gray-600 rounded-lg px-3 py-2">
                <PhoneInput
                  country={'us'}
                  value={formData.contact}
                  onChange={handlePhoneChange}
                  inputStyle={{ backgroundColor: 'transparent', color: 'white', border: 'none' }}
                  buttonStyle={{ backgroundColor: 'transparent', border: 'none' }}
                  containerStyle={{ width: "100%" }}
                  placeholder="Phone Number *"
                  required
                />
              </div>

              <select
                name="country"
                value={formData.country}
                onChange={handleInputChange}
                required
                className="w-full bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600 rounded-lg py-2 px-3"
              >
                <option value="">Select your nationality *</option>
                {countries.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <Input name="instagram" placeholder="Instagram (optional)" value={formData.instagram} onChange={handleInputChange} className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600" />
              <Input name="tiktok" placeholder="TikTok (optional)" value={formData.tiktok} onChange={handleInputChange} className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600" />
              <Input name="telegram" placeholder="Telegram (optional)" value={formData.telegram} onChange={handleInputChange} className="bg-gray-800/40 text-white placeholder-yellow-400 border border-gray-600" />

              <div className="bg-gray-800/40 border-2 border-dashed border-gray-600 hover:border-yellow-500 rounded-xl p-6 text-center">
                <input type="file" accept="image/*" multiple onChange={handlePhotoUpload} className="hidden" id="photo-upload" />
                <label htmlFor="photo-upload" className="cursor-pointer block text-yellow-400">
                  <Upload className="w-8 h-8 mx-auto mb-2" />
                  <p>Upload up to 5 photos *</p>
                  <p className="text-xs text-gray-500">Max size: 10MB each</p>
                </label>
              </div>

              {formData.photos.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {formData.photos.map(photo => (
                    <div key={photo.id} className="relative">
                      <img src={photo.url} alt="Uploaded" className="w-full object-cover rounded-lg border border-gray-600" />
                      <button type="button" onClick={() => removePhoto(photo.id)} className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-5 h-5 text-xs">×</button>
                    </div>
                  ))}
                </div>
              )}

              <Button type="submit" disabled={isSubmitting} className="w-full bg-gradient-to-r from-yellow-400 to-yellow-600 hover:to-yellow-700 text-black py-3 rounded-xl text-lg font-semibold">
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Application"
                )}
              </Button>
              <p className="text-xs text-gray-500 text-center">By submitting, you agree to be contacted by Cute Stars Agency</p>
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
            <button onClick={() => setShowSuccessModal(false)} className="bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 px-4 rounded">Close</button>
          </div>
        </div>
      )}

      {/* Error Modal */}
      {showErrorModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
          <div className="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full text-center">
            <h2 className="text-xl font-semibold mb-2 text-red-600">Submission Error</h2>
            <p className="text-gray-700 mb-4">{errorMessage}</p>
            <button onClick={() => setShowErrorModal(false)} className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded">Close</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationForm;

