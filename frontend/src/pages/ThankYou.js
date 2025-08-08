import React, { useEffect, useState } from "react";
import { CheckCircle } from "lucide-react";

const ThankYou = () => {
  const [botUrl, setBotUrl] = useState("#");

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch("/api/settings", { credentials: "include" });
        if (!res.ok) throw new Error("Failed to load settings");
        const s = await res.json();
        if (s.webhook_enabled) {
          setBotUrl(s.bot_main_url || "https://t.me/AiSiva_bot");
        } else {
          setBotUrl(s.bot_alt_url || "https://t.me/AlternateBot");
        }
      } catch (err) {
        console.error("Settings fetch failed:", err);
        setBotUrl("https://t.me/AiSiva_bot"); // fallback
      }
    };
    fetchSettings();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white p-6">
      <div className="bg-[#111] border border-gray-700 rounded-lg shadow-lg max-w-lg w-full p-8 text-center">
        <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
        <h1 className="text-3xl font-bold mb-4">Application Submitted</h1>
        <p className="mb-6 text-gray-300">
          Thank you for applying to <span className="text-yellow-400">Cute Stars Agency</span>!
        </p>
        <p className="mb-6 text-gray-400">
          Please continue the onboarding process on Telegram by clicking the button below:
        </p>
        <a
          href={botUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-gradient-to-r from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600 text-black font-semibold px-6 py-3 rounded-lg shadow-lg transition"
        >
          Open Telegram Bot
        </a>
        <p className="mt-4 text-xs text-gray-500">
          You’ll receive further instructions and complete your setup there.
        </p>
      </div>
    </div>
  );
};

export default ThankYou;