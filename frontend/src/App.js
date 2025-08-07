import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ApplicationForm from "./pages/ApplicationForm";
import ThankYou from "./pages/ThankYou";
import HomePage from "./pages/HomePage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/apply" element={<ApplicationForm />} />
        <Route path="/thank-you" element={<ThankYou />} />
      </Routes>
    </Router>
  );
}

export default App;
