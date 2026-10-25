// src/About_us.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import logoImg from "./assets/images/img_3.jpg";
import "./About_us.css";
import groupPhoto from "./assets/images/img_3.jpg";


function AboutUs() {
  const navigate = useNavigate();
  const [lang, setLang] = useState("en");

  // Simple translation object
  const t = {
    title: "KisanSaathi",
    nav_home: "Home",
    nav_about: "About Us",
    nav_contact: "Contact Us",
  };

  return (
<>
    <header>
      <div className="navbar">
        {/* Left: Logo & Title */}
        <div className="logo-section">
          <img src={logoImg} alt="KisanSaathi Logo" className="logo" />
          <h2>{t.title}</h2>
        </div>

        {/* Center: Navigation Links */}
        <nav>
          <ul>
            <li onClick={() => navigate("/")} style={{ cursor: "pointer" }}>{t.nav_home}</li>
            <li onClick={() => navigate("/about")} style={{ cursor: "pointer" }}>{t.nav_about}</li>
            <li onClick={() => navigate("/contact")} style={{ cursor: "pointer" }}>{t.nav_contact}</li>
          </ul>
        </nav>

        {/* Right: Language Dropdown & Logout */}
        <div className="nav-actions">
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            <option value="en">English</option>
            <option value="mr">मराठी</option>
          </select>
         
        </div>
      </div>
    </header>

<div className="end-msg">
  <h1>About Us</h1>
<img src={groupPhoto} alt="KisanSaathi project team" className="group-photo" />
  <h2>
    This is a mini project made by Adwait, Aryan, Dharni and Aditya with the
    focus of helping out the farmers through various methods used in this
    project. <br />
    We are TE IT Students and look forward to building many more websites like
    these! <br />
    We created this project to contribute towards solving real-life challenges
    faced by farmers, using technology as a bridge. <br />
    Thank you for visiting our site, and see you again!
  </h2>
</div>




</>
  );
}

export default AboutUs;
