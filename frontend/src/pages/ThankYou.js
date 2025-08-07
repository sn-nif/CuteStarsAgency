import React from "react";
import { CheckCircle } from "lucide-react";

const ThankYou = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-black text-white p-6">
      <div className="bg-[#111] border border-gray-700 rounded-lg shadow-lg max-w-lg w-full p-8 text-center">
        <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
        <h1 className="text-3xl font-bold mb-4">Application Submitted</h1>
        <p className="mb-6 text-gray-300">
          Thank you for applying to <span className="text-gold-500">Cute Stars Agency</span>!
        </p>
        <p className="mb-6 text-gray-400">
          Please continue the onboarding process on Telegram by clicking the button below:
        </p>
        <a
          href="https://t.me/AiSiva_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-gold-500 hover:bg-gold-600 text-black font-semibold px-6 py-3 rounded-lg transition"
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
