// src/App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from "react-router-dom";
import Home from "./Home";
import Weather from "./Weather";
import CropCalendar from "./CropCalendar";
import AboutUs from "./About_us";
import ContactUs from "./Contact_us";
import KisanSaathiMarketplace from "./KisanSaathiMarketplace";
import AuthPage from "./AuthPage";
import GovernmentScheme from "./GovernmentScheme";
import ModernFarming from "./ModernFarming";

function KisaathPageLinks() {
  const { pathname } = useLocation();
  if (pathname === "/") return null;

  return (
    <div className="ks-app-switch">
      <Link to="/">← KisanSaathi home</Link>
      <a href="/">Cow QR portal <span aria-hidden="true">↗</span></a>
    </div>
  );
}

function App() {
  return (
    <Router basename="/kisaath">
      <KisaathPageLinks />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/weather" element={<Weather />} />
        <Route path="/crop-calendar" element={<CropCalendar />} />
        <Route path="/about" element={<AboutUs />} />
        <Route path="/contact" element={<ContactUs />} />
        <Route path="/marketplace" element={<KisanSaathiMarketplace />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/government" element={<GovernmentScheme />} />
        <Route path="/modern-farming" element={<ModernFarming />} />
        <Route path="*" element={<Home />} />
      </Routes>
    </Router>
  );
}

export default App;
