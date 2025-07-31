import React from "react";
import ReactDOM from "react-dom/client";
import 'react-phone-input-2/lib/style.css'; // ✅ Add this line
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);