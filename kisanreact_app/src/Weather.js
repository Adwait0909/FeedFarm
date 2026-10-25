import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import FarmConditions from "./FarmConditions";
import "./wea.css";

const REQUEST_TIMEOUT_MS = 40000;

// Read a JSON body without throwing; a reply that is not JSON (for example an HTML error page) becomes {}.
async function readJson(response) {
  try {
    return await response.json();
  } catch (parseError) {
    return {};
  }
}

async function fetchWeather(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, { signal: controller.signal });
    return { response, data: await readJson(response) };
  } catch (networkError) {
    if (networkError && networkError.name === "AbortError") {
      throw new Error("The weather service took too long to answer. Please try again.");
    }
    throw new Error("Could not reach the server. Check your internet connection and try again.");
  } finally {
    clearTimeout(timer);
  }
}

function failureMessage(response, data) {
  if (data && data.error) return data.error;
  if (response.status === 404) return "City not found. Check the spelling and try again.";
  return `Weather is not available right now (error ${response.status}).`;
}

// Accept only a complete report so that an unexpected reply can never crash the page.
function isCompleteReport(data) {
  return Boolean(
    data && data.main && Array.isArray(data.weather) && data.weather[0] && data.wind &&
    Number.isFinite(Number(data.main.temp))
  );
}

function Weather() {
  const cityInput = useRef(null);
  const [city, setCity] = useState("");
  const [report, setReport] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [forecastNote, setForecastNote] = useState("");
  const navigate = useNavigate();

  async function findWeather(event) {
    event.preventDefault();
    const query = city.trim();
    if (!query) {
      setError("Enter a city or town to see the forecast.");
      cityInput.current?.focus();
      return;
    }

    setLoading(true);
    setError("");
    setReport(null);
    setForecast([]);
    setForecastNote("");
    try {
      const current = await fetchWeather(`/api/weather/current?city=${encodeURIComponent(query)}`);
      if (!current.response.ok) throw new Error(failureMessage(current.response, current.data));
      if (!isCompleteReport(current.data)) throw new Error("The weather service returned an unexpected answer. Please try again.");
      setReport(current.data);

      try {
        const next = await fetchWeather(`/api/weather/forecast?city=${encodeURIComponent(query)}`);
        if (next.response.ok && Array.isArray(next.data.list)) {
          const daily = new Map();
          next.data.list.forEach((item) => {
            const day = String(item.dt_txt).split(" ")[0];
            const saved = daily.get(day);
            if (!saved) {
              daily.set(day, {
                day,
                min: item.main.temp_min,
                max: item.main.temp_max,
                description: item.weather[0].description,
                farm: item.farm || null,
              });
            } else {
              saved.min = Math.min(saved.min, item.main.temp_min);
              saved.max = Math.max(saved.max, item.main.temp_max);
            }
          });
          setForecast(Array.from(daily.values()).slice(0, 5));
        } else {
          setForecastNote("The 5-day outlook is not available right now.");
        }
      } catch (forecastError) {
        console.error("Forecast request failed", forecastError);
        setForecastNote("The 5-day outlook is not available right now.");
      }
    } catch (requestError) {
      setError(requestError.message || "Weather is not available right now.");
    } finally {
      setLoading(false);
    }
  }

  function startVoiceSearch() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.onresult = (event) => setCity(event.results[0][0].transcript.trim().replace(/[.]$/, ""));
    recognition.onerror = () => setError("Could not hear the city name. Try typing it instead.");
    recognition.start();
  }

  function readReport() {
    if (!report || !("speechSynthesis" in window)) {
      setError("There is no forecast to read aloud yet.");
      return;
    }
    const spoken = new SpeechSynthesisUtterance(
      `${report.name}: ${Math.round(report.main.temp)} degrees Celsius, ${report.weather[0].description}. Humidity ${report.main.humidity} percent.`
    );
    spoken.lang = "en-IN";
    window.speechSynthesis.speak(spoken);
  }

  function clearReport() {
    setCity("");
    setReport(null);
    setForecast([]);
    setForecastNote("");
    setError("");
    cityInput.current?.focus();
  }

  return (
    <main className="weather-container">
      <span className="ks-eyebrow">LOCAL FARM PLANNING</span>
      <h1>Weather forecast</h1>
      <p>Check conditions for a city or town before planning your day in the field.</p>
      <form className="weather-search" onSubmit={findWeather}>
        <label className="weather-sr-only" htmlFor="weather-city">City or town</label>
        <input
          id="weather-city"
          type="text"
          placeholder="Enter city or town"
          value={city}
          onChange={(event) => setCity(event.target.value)}
          ref={cityInput}
        />
        <button type="submit" disabled={loading}>{loading ? "Checking…" : "Find weather"}</button>
        <button type="button" onClick={startVoiceSearch} aria-label="Search by voice">🎙️</button>
      </form>
      <div className="weather-tools">
        <button type="button" onClick={readReport}>Read forecast aloud</button>
        <button type="button" onClick={clearReport}>Clear</button>
      </div>
      {loading && <p className="loading-text" role="status">Loading weather data…</p>}
      {error && <p className="weather-error" role="alert">{error}</p>}
      {report && (
        <section className="weather-result" aria-live="polite">
          <div className="weather-current">
            <span className="weather-location">{report.name}{report.region ? `, ${report.region}` : ""}</span>
            <strong>{Math.round(report.main.temp)}°<small>C</small></strong>
            <span className="weather-condition">{report.weather[0].description}</span>
            <div className="weather-details">
              <span>Humidity <b>{report.main.humidity}%</b></span>
              <span>Wind <b>{report.wind.speed} m/s</b></span>
              <span>Feels like <b>{Math.round(report.main.feels_like)}°C</b></span>
            </div>
          </div>
          {report.farm && <FarmConditions farm={report.farm} days={forecast} />}
          {forecastNote && forecast.length === 0 && <p className="weather-note" role="status">{forecastNote}</p>}
          {forecast.length > 0 && (
            <div className="forecast">
              <h2>5-day outlook</h2>
              <ul>
                {forecast.map((day) => (
                  <li key={day.day}>
                    <strong>{new Date(`${day.day}T12:00:00`).toLocaleDateString("en-IN", { weekday: "short" })}</strong>
                    <span>{day.description}</span>
                    <span>{Math.round(day.min)}° / {Math.round(day.max)}°C</span>
                    {day.farm && (
                      <small className="forecast-extra">
                        Rain {day.farm.rain && Number.isFinite(day.farm.rain.chance_percent) ? `${Math.round(day.farm.rain.chance_percent)}%` : "–"}
                        {" · "}Wind {day.farm.wind && Number.isFinite(day.farm.wind.speed_max) ? `${day.farm.wind.speed_max} m/s ${day.farm.wind.direction || ""}` : "–"}
                        {" · "}ET₀ {Number.isFinite(day.farm.et0_mm) ? `${day.farm.et0_mm} mm` : "–"}
                      </small>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
      <button className="back-btn" type="button" onClick={() => navigate("/")}>← Back to KisanSaathi</button>
    </main>
  );
}

export default Weather;
