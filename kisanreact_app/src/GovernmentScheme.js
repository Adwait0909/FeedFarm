// src/GovernmentScheme.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import schemeData from "./govern.json";
import "./govern.css";
import logoImg from "./assets/images/img_3.jpg"; // make sure this file exists

const GovernmentScheme = () => {
  const [lang, setLang] = useState("en");
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const t = schemeData[lang];

  // Filter schemes in a section based on search
  const filteredSchemes = (schemes) => {
    if (!search) return schemes;
    const s = search.toLowerCase();
    return schemes.filter(
      (sch) =>
        sch.title.toLowerCase().includes(s) ||
        (sch.info && sch.info.toLowerCase().includes(s))
    );
  };

  return (
    <div className="gov-page">
      {/* Navbar */}
      <header className="gov-navbar">
        {/* Left: Logo + Brand Name */}
        <div className="gov-logo">
          <img src={logoImg} alt="logo" className="gov-logo-img" />
          <span className="gov-brand">KisanSaathi</span>
        </div>

        {/* Center: Title */}
        <h2 className="gov-title">{t.title}</h2>

        {/* Right: Language + Back */}
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

      {/* Search Bar */}
      <div className="gov-search">
        <input
          type="text"
          placeholder={t.search_placeholder}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* All Sections */}
      <main className="gov-sections">
        {t.sections.map((sec, idx) => {
          const list = filteredSchemes(sec.schemes);
          return (
            <section className="gov-section" key={idx}>
              <h3 className="gov-section-title">{sec.name}</h3>
              {list.length === 0 ? (
                <p className="no-result">{t.no_schemes_found}</p>
              ) : (
                <div className="scheme-cards">
                  {list.map((sch, sidx) => (
                    <div className="scheme-card" key={sidx}>
                      <h4>{sch.title}</h4>
                      {sch.info && <p>{sch.info}</p>}
                      {sch.link && (
                        <a
                          href={sch.link}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {t.apply}
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          );
        })}
      </main>
    </div>
  );
};

export default GovernmentScheme;
