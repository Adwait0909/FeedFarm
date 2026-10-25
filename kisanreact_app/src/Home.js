import React, { useState } from "react";
import { Link } from "react-router-dom";
import "./home.css";

import heroImage from "./modern_farming_hero.jpg";
import cropImage from "./assets/images/crop.webp";
import weatherImage from "./assets/images/weather.jpg";
import schemesImage from "./assets/images/gov.jpg";
import marketImage from "./assets/images/mk.jpg";
import farmingImage from "./assets/images/Mod_far.png";

const copy = {
  en: {
    eyebrow: "A better-connected farm day",
    title: "Good farming starts with a clearer next step.",
    intro: "Plan the season, check local weather, find support and connect with nearby buyers — with your cow records close at hand.",
    plan: "Plan your crops",
    explore: "Explore farm tools",
    link: "Cow QR home",
    features: "A connected toolkit",
    featureTitle: "Practical tools for the work ahead.",
    featureIntro: "Move between planning, information and the people who help your farm thrive.",
    bridgeTitle: "Caring for your herd, too.",
    bridgeIntro: "Open the Cow QR passport to register animals, scan tags, and keep health records together.",
    openPortal: "Open Cow QR home",
    scan: "Scan a cow QR",
    footer: "KisanSaathi · Farm tools, together",
  },
  mr: {
    eyebrow: "शेतीसाठी अधिक जोडलेली साधने",
    title: "शेतीची पुढची पायरी आता अधिक स्पष्ट.",
    intro: "हंगामाचे नियोजन करा, हवामान तपासा, योजनांची माहिती मिळवा आणि जवळच्या खरेदीदारांशी जोडा.",
    plan: "पीक नियोजन करा",
    explore: "सर्व साधने पहा",
    link: "गाय QR मुख्यपृष्ठ",
    features: "एकत्रित शेती साधने",
    featureTitle: "पुढील कामासाठी उपयुक्त साधने.",
    featureIntro: "नियोजन, माहिती आणि शेतीला मदत करणाऱ्या सेवांमध्ये सहज जा.",
    bridgeTitle: "आपल्या जनावरांची काळजीही.",
    bridgeIntro: "गायींची नोंदणी, QR स्कॅन आणि आरोग्य नोंदींसाठी Cow QR पासपोर्ट उघडा.",
    openPortal: "Cow QR मुख्यपृष्ठ उघडा",
    scan: "गायीचा QR स्कॅन करा",
    footer: "KisanSaathi · शेतीची साधने, एकत्र",
  },
};

const tools = [
  {
    title: "Crop calendar",
    subtitle: "Plan by season",
    description: "Browse crop guidance and keep important growing stages in view.",
    to: "/crop-calendar",
    image: cropImage,
    tone: "sage",
    mark: "01",
  },
  {
    title: "Weather",
    subtitle: "Check conditions",
    description: "See current conditions and forecasts to plan your farm work.",
    to: "/weather",
    image: weatherImage,
    tone: "blue",
    mark: "02",
  },
  {
    title: "Government schemes",
    subtitle: "Find support",
    description: "Explore government programs and services for farmers.",
    to: "/government",
    image: schemesImage,
    tone: "gold",
    mark: "03",
  },
  {
    title: "Farm marketplace",
    subtitle: "Buy and sell",
    description: "Browse listings or share products with the local farming community.",
    to: "/marketplace",
    image: marketImage,
    tone: "clay",
    mark: "04",
  },
  {
    title: "Modern farming",
    subtitle: "Explore new methods",
    description: "Discover practical approaches, equipment and farm technologies.",
    to: "/modern-farming",
    image: farmingImage,
    tone: "leaf",
    mark: "05",
  },
];

function Home() {
  const [lang, setLang] = useState("en");
  const t = copy[lang];

  return (
    <main className="ks-home">
      <header className="ks-nav">
        <Link className="ks-brand" to="/">
          <span className="ks-brand-mark" aria-hidden="true">K</span>
          <span><strong>KisanSaathi</strong><small>Farm tools, together</small></span>
        </Link>
        <nav className="ks-nav-links" aria-label="Main navigation">
          <a href="#tools">{t.features}</a>
          <a href="/animal-health/">Animal Health AI</a>
          <Link to="/about">About</Link>
          <Link to="/contact">Contact</Link>
        </nav>
        <div className="ks-nav-actions">
          <select aria-label="Language" value={lang} onChange={(event) => setLang(event.target.value)}>
            <option value="en">English</option>
            <option value="mr">मराठी</option>
          </select>
          <a className="ks-nav-cow" href="/">{t.link}<span aria-hidden="true">↗</span></a>
        </div>
      </header>

      <section className="ks-hero">
        <div className="ks-hero-copy">
          <span className="ks-eyebrow"><i />{t.eyebrow}</span>
          <h1>{t.title}</h1>
          <p>{t.intro}</p>
          <div className="ks-hero-actions">
            <Link className="ks-button ks-button-dark" to="/crop-calendar">{t.plan}<span aria-hidden="true">↗</span></Link>
            <a className="ks-button ks-button-quiet" href="#tools">{t.explore}</a>
          </div>
          <div className="ks-hero-note"><span className="ks-note-mark">✳</span><span>Crop planning <b>·</b> Weather <b>·</b> Market <b>·</b> Animal care</span></div>
        </div>
        <div className="ks-hero-image" style={{ backgroundImage: `url("${heroImage}")` }}>
          <div className="ks-image-overlay" />
          <div className="ks-image-tag"><span>FIELD NOTES</span><strong>Small decisions.<br />Stronger seasons.</strong></div>
        </div>
      </section>

      <section className="ks-tools" id="tools">
        <div className="ks-section-heading">
          <div><span className="ks-eyebrow">{t.features}</span><h2>{t.featureTitle}</h2></div>
          <p>{t.featureIntro}</p>
        </div>
        <div className="ks-tool-grid">
          {tools.map((tool) => (
            <Link className={`ks-tool-card ks-${tool.tone}`} to={tool.to} key={tool.to}>
              <div className="ks-tool-image" style={{ backgroundImage: `url("${tool.image}")` }}>
                <span className="ks-tool-number">{tool.mark}</span>
              </div>
              <div className="ks-tool-content">
                <span className="ks-tool-subtitle">{tool.subtitle}</span>
                <h3>{tool.title}</h3>
                <p>{tool.description}</p>
                <span className="ks-tool-open">Explore tool <b aria-hidden="true">↗</b></span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="ks-cow-bridge">
        <div className="ks-cow-copy">
          <span className="ks-eyebrow">COW QR DIGITAL PASSPORT</span>
          <h2>{t.bridgeTitle}</h2>
          <p>{t.bridgeIntro}</p>
          <div className="ks-bridge-actions">
            <a className="ks-button ks-button-dark" href="/">{t.openPortal}<span aria-hidden="true">↗</span></a>
            <a className="ks-text-link" href="/animal-health/">Animal Health AI<span aria-hidden="true">↗</span></a>
            <a className="ks-text-link" href="/scan">{t.scan}<span aria-hidden="true">↗</span></a>
          </div>
        </div>
        <div className="ks-cow-art" role="img" aria-label="Cow QR passport tools">
          <span className="ks-cow-stamp">CARE<br />&amp; TRACE</span>
        </div>
      </section>

      <footer className="ks-footer"><span>{t.footer}</span><a href="/">Cow QR portal <span aria-hidden="true">↗</span></a></footer>
    </main>
  );
}

export default Home;
