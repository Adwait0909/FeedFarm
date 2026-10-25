import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./modernFarming.css";

// Images
import logoImg from "./img_3.jpg";
import heroImg from "./modern_farming_hero.jpg";
import droneImg from "./drone.jfif";
import hydroImg from "./hydroponics.jpg";
import aiImg from "./ai_crop.png";
import sensorImg from "./sensor.jfif";
import irrigationImg from "./drip.jpg";

const ModernFarming = () => {
  const navigate = useNavigate();
  const [lang, setLang] = useState("en");

  // Translations for entire page
  const translations = {
    en: {
      title: "Modern Farming",
      back: "Back",
      heroHeading: "Empowering Agriculture with Innovation",
      heroText:
        "Discover how modern technology is transforming farming into a smart and sustainable system.",
      exploreBtn: "Explore Techniques",
      introTitle: "What is Modern Farming?",
      introText:
        "Modern farming combines advanced technologies like IoT, Artificial Intelligence, drones, and sensors to improve crop yield, reduce effort, and use resources efficiently. It enables farmers to make data-driven decisions for better productivity and sustainability.",
      techniquesTitle: "Modern Farming Techniques",
      techniques: [
        {
          name: "Drones in Agriculture",
          desc: "Used for crop monitoring, spraying, and data collection with high efficiency.",
        },
        {
          name: "Hydroponics",
          desc: "Grows plants without soil using nutrient-rich water, saving space and resources.",
        },
        {
          name: "AI-Based Crop Prediction",
          desc: "Analyzes soil, weather, and crop data to predict yields and detect diseases early.",
        },
        {
          name: "Smart Sensors",
          desc: "Monitor soil moisture, temperature, and nutrient levels in real-time.",
        },
        {
          name: "Drip Irrigation",
          desc: "Delivers water directly to plant roots, reducing waste and improving water efficiency.",
        },
      ],
      compareTitle: "Traditional vs Modern Farming",
      table: {
        aspect: "Aspect",
        trad: "Traditional Farming",
        modern: "Modern Farming",
        data: [
          ["Method", "Manual labor and traditional tools", "Automated machines and smart devices"],
          ["Productivity", "Depends on manpower and weather", "Data-driven and optimized for high yield"],
          ["Water Usage", "High water wastage", "Efficient systems like drip irrigation"],
          ["Monitoring", "Visual and experience-based", "Real-time data via sensors and AI"],
          ["Environmental Impact", "Higher due to overuse of resources", "Promotes sustainability and eco-balance"],
        ],
      },
      benefitsTitle: "Benefits of Modern Farming",
      benefits: [
        "🌱 Higher Crop Productivity",
        "💧 Efficient Water Usage",
        "🤖 Reduced Labor Effort",
        "🌿 Sustainable Practices",
        "📈 Increased Profitability",
      ],
      footerTitle: "Ready to Modernize Your Farm?",
      footerText:
        "Explore tools, guides, and expert advice on KisanSaathi to bring innovation to your fields.",
      footerBtn: "Explore More",
    },
    mr: {
      title: "आधुनिक शेती",
      back: "मागे",
      heroHeading: "नवीन तंत्रज्ञानाने शेतीला बळकट करा",
      heroText:
        "आधुनिक तंत्रज्ञान कसे शेतीला स्मार्ट आणि शाश्वत प्रणालीमध्ये रूपांतरित करते ते जाणून घ्या.",
      exploreBtn: "तंत्रज्ञान जाणून घ्या",
      introTitle: "आधुनिक शेती म्हणजे काय?",
      introText:
        "आधुनिक शेतीमध्ये IoT, कृत्रिम बुद्धिमत्ता, ड्रोन आणि सेन्सर सारखी प्रगत तंत्रज्ञान वापरून पिकांचे उत्पादन वाढवले जाते, मेहनत कमी होते आणि संसाधनांचा योग्य वापर होतो. हे शेतकऱ्यांना माहितीवर आधारित निर्णय घेण्यास मदत करते.",
      techniquesTitle: "आधुनिक शेतीची तंत्रे",
      techniques: [
        {
          name: "शेतीतील ड्रोन वापर",
          desc: "पिकांची तपासणी, फवारणी आणि डेटा गोळा करण्यासाठी कार्यक्षमतेने वापरले जाते.",
        },
        {
          name: "हायड्रोपोनिक्स",
          desc: "मातीशिवाय पोषक द्रवांमध्ये झाडे वाढवण्याची पद्धत, जागा आणि संसाधने वाचवते.",
        },
        {
          name: "AI आधारित पिकांचा अंदाज",
          desc: "माती, हवामान आणि पिकांचा डेटा विश्लेषित करून उत्पन्नाचा अंदाज लावते आणि रोग लवकर ओळखते.",
        },
        {
          name: "स्मार्ट सेन्सर",
          desc: "मातीतील आर्द्रता, तापमान आणि पोषकतत्त्वांचे रिअल-टाइम निरीक्षण करतात.",
        },
        {
          name: "ड्रिप सिंचन",
          desc: "पाण्याचा अपव्यय कमी करून पाणी थेट मुळांपर्यंत पोहोचवते.",
        },
      ],
      compareTitle: "पारंपरिक वि. आधुनिक शेती",
      table: {
        aspect: "घटक",
        trad: "पारंपरिक शेती",
        modern: "आधुनिक शेती",
        data: [
          ["पद्धत", "हातमजुरी आणि पारंपरिक साधने", "स्वयंचलित यंत्रे आणि स्मार्ट उपकरणे"],
          ["उत्पादन", "मनुष्यबळ आणि हवामानावर अवलंबून", "डेटा-आधारित आणि अधिक उत्पादनक्षम"],
          ["पाण्याचा वापर", "जास्त पाणी वाया जाते", "ड्रिप सिंचनासारख्या कार्यक्षम प्रणाली"],
          ["निगराणी", "दृश्य आणि अनुभवावर आधारित", "सेन्सर आणि AI द्वारे रिअल-टाइम डेटा"],
          ["पर्यावरणीय परिणाम", "संसाधनांचा अधिक वापर", "शाश्वतता आणि पर्यावरण संतुलन प्रोत्साहन देते"],
        ],
      },
      benefitsTitle: "आधुनिक शेतीचे फायदे",
      benefits: [
        "🌱 अधिक पिक उत्पादन",
        "💧 कार्यक्षम पाण्याचा वापर",
        "🤖 कमी मेहनत",
        "🌿 शाश्वत पद्धती",
        "📈 अधिक नफा",
      ],
      footerTitle: "तुमची शेती आधुनिक बनवायची तयारी आहे का?",
      footerText:
        "किसान साथीवर तंत्रज्ञान, मार्गदर्शक आणि तज्ज्ञ सल्ल्याबद्दल जाणून घ्या आणि तुमच्या शेतात नवोपक्रम घडवा.",
      footerBtn: "अधिक जाणून घ्या",
    },
  };

  const t = translations[lang];

  return (
    <>
      {/* Navbar */}
      <header className="gov-navbar">
        <div className="gov-logo">
          <img src={logoImg} alt="logo" className="gov-logo-img" />
          <span className="gov-brand">KisanSaathi</span>
        </div>

        <h2 className="gov-title">{t.title}</h2>

        <div className="gov-controls">
          <select
            className="gov-lang"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
          >
            <option value="en">English</option>
            <option value="mr">मराठी</option>
          </select>
          <button className="gov-back-btn" onClick={() => navigate("/")}>
            ← {t.back}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="modern-farming-container">
        {/* Hero Section */}
        <section className="hero-section">
          <img src={heroImg} alt="Modern Farming" className="hero-img" />
          <div className="hero-content">
            <h1>{t.heroHeading}</h1>
            <p>{t.heroText}</p>
            <a href="#techniques" className="explore-btn">
              {t.exploreBtn}
            </a>
          </div>
        </section>

        {/* Introduction */}
        <section className="intro-section">
          <h2>{t.introTitle}</h2>
          <p>{t.introText}</p>
        </section>

        {/* Techniques */}
        <section id="techniques" className="techniques-section">
          <h2>{t.techniquesTitle}</h2>
          <div className="techniques-grid">
            {t.techniques.map((tech, index) => (
              <div className="tech-card" key={index}>
                <img
                  src={[droneImg, hydroImg, aiImg, sensorImg, irrigationImg][index]}
                  alt={tech.name}
                />
                <h3>{tech.name}</h3>
                <p>{tech.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Comparison Table */}
        <section className="comparison-section">
          <h2>{t.compareTitle}</h2>
          <table className="comparison-table">
            <thead>
              <tr>
                <th>{t.table.aspect}</th>
                <th>{t.table.trad}</th>
                <th>{t.table.modern}</th>
              </tr>
            </thead>
            <tbody>
              {t.table.data.map((row, index) => (
                <tr key={index}>
                  <td>{row[0]}</td>
                  <td>{row[1]}</td>
                  <td>{row[2]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Benefits */}
        <section className="benefits-section">
          <h2>{t.benefitsTitle}</h2>
          <div className="benefits-grid">
            {t.benefits.map((b, i) => (
              <div className="benefit-card" key={i}>
                {b}
              </div>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="modern-footer">
          <h3>{t.footerTitle}</h3>
          <p>{t.footerText}</p>
        </footer>
      </div>
    </>
  );
};

export default ModernFarming;
