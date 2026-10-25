
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import logoImg from "./assets/images/img_3.jpg";
import "./About_us.css";

function ContactUs() {
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

	<div>
		<h1>Contact Us</h1>
		<h2>🌾 We’re Here to Help Farmers Grow Better!<br/>

At KisanSaathi, we believe that every farmer deserves the right support, guidance, and technology to achieve sustainable growth. Whether you have a question, feedback, or a suggestion — we’d love to hear from you!
<br/><br/>
📞 Get in Touch
Email: support@kisansaathi.com
Phone: +91 98765 43210
Address: Department of Information & Technology,
Datta Meghe College of Engineering Navi Mumbai, India
<br/><br/>
🌱 Follow Us
Stay connected with us for updates on farming techniques, government schemes, and agricultural innovations:
<br/>
🌐 www.kisansaathi.com<br/>
📘 Facebook: @KisanSaathi<br/>
🐦 Twitter: @Kisan_Saathi<br/>
📸 Instagram: @kisan.saathi
<br/><br/>
🤝 Join Our Mission<br/>
Be a part of our growing community and help revolutionize Indian agriculture through smart farming and digital empowerment.
</h2>
	</div>	
</>
  );
}

export default ContactUs;
