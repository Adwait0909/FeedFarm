// src/CropCalendar.js
import React, { useState } from "react";
import cropsData from "./crops";          
import translationsData from "./translation"; 
import "./crop_sty.css";                     
import logoImg from "./assets/images/img_3.jpg";
import { useNavigate } from "react-router-dom"; 

const CropCalendar = () => {

      const navigate = useNavigate(); 

  const [currentLang, setCurrentLang] = useState("en");
  const [search, setSearch] = useState("");
  const [region, setRegion] = useState("All");
  const [season, setSeason] = useState("All");

  const months_en = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const months_mr = ["जाने","फेब्रु","मार्च","एप्रि","मे","जून","जुलै","ऑग","सप्टें","ऑक्टो","नोव्हें","डिसें"];
  const months = currentLang === "en" ? months_en : months_mr;


  const applyTranslations = (key) => {
    return translationsData[currentLang]?.[key] || key;
  };


  const filteredCrops = cropsData.filter(crop => {
    const cropName = currentLang === "en" ? crop.name_en.toLowerCase() : crop.name_mr.toLowerCase();
    const matchesSearch = cropName.includes(search.toLowerCase());
    const matchesRegion = region === "All" || crop.region === region;
    const matchesSeason = season === "All" || crop.season === season;
    return matchesSearch && matchesRegion && matchesSeason;
  });

  const handleLangChange = (e) => {
    setCurrentLang(e.target.value);
  };

  return (
    <div className="crop-calendar">
      <header>
        <div className="brand">
          <div>
            <img src={logoImg} alt="KisanSaathi Logo" className="logo" />
          </div>
          <div>
            <h1>{applyTranslations("title")}</h1>
            <p className="lead">{applyTranslations("subtitle")}</p>
          </div>
        </div>

        <div className="controls">
          <div className="select">
            <label htmlFor="region">{applyTranslations("region")}</label>
            <select id="region" value={region} onChange={(e) => setRegion(e.target.value)}>
              <option value="All">{applyTranslations("allRegions")}</option>
              <option value="Marathwada">Marathwada</option>
              <option value="Vidarbha">Vidarbha</option>
              <option value="Konkan">Konkan</option>
              <option value="Western Maharashtra">Western Maharashtra</option>
            </select>
          </div>

          <div className="select">
            <label htmlFor="season">{applyTranslations("season")}</label>
            <select id="season" value={season} onChange={(e) => setSeason(e.target.value)}>
              <option value="All">{applyTranslations("allSeasons")}</option>
              <option value="Kharif">Kharif</option>
              <option value="Rabi">Rabi</option>
              <option value="Zaid">Zaid</option>
            </select>
          </div>

          <div className="select">
            <label htmlFor="language">{applyTranslations("language")}</label>
            <select id="language" value={currentLang} onChange={handleLangChange}>
              <option value="en">English</option>
              <option value="mr">मराठी</option>
            </select>
          </div>
        </div>
      </header>

      <button onClick={() => navigate("/")} className="back-btn">
        {applyTranslations("back")}
      </button>

      <div className="search-bar">
        <input
          type="text"
          id="search"
          placeholder={applyTranslations("searchPlaceholder")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="legend">
        <div className="legend-item">
          <div className="legend-color legend-sowing"></div>
          <span>{applyTranslations("sowing")}</span>
        </div>
        <div className="legend-item">
          <div className="legend-color legend-growing"></div>
          <span>{applyTranslations("growing")}</span>
        </div>
        <div className="legend-item">
          <div className="legend-color legend-harvesting"></div>
          <span>{applyTranslations("harvesting")}</span>
        </div>
      </div>

      <main>
        <div id="crop-list" className="cards">
          {filteredCrops.map((crop, idx) => {
            const cropName = currentLang === "en" ? crop.name_en : crop.name_mr;
            return (
              <div className="crop-card" key={idx}>
                <h3 className="crop-name">{cropName}</h3>
                <div className="calendar months">
                  {months.map((m, i) => (
                    <span className="month-label" key={i}>{m}</span>
                  ))}
                </div>
                <div className="calendar">
                  {Array.from({ length: 12 }, (_, i) => {
                    const month = i + 1;
                    let cls = "";
                    if (crop.sowing.includes(month)) cls = "sowing";
                    else if (crop.growing.includes(month)) cls = "growing";
                    else if (crop.harvesting.includes(month)) cls = "harvesting";
                    return <span className={cls} key={i}>{month}</span>;
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </main>

      <footer>
        <p>&copy; KisanSaathi</p>
      </footer>
    </div>
  );
};

export default CropCalendar;
