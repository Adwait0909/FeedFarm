import React, { useState } from "react";
import {
  CROP_STAGES, et0Level, formatNumber, humidityInsight, irrigationAdvice, isNumber, windInsight,
} from "./farmWeather";

// Wind, rain, humidity and evapotranspiration for today, plus an irrigation estimate.
// `farm` comes from /api/weather/current, `days` from the 5-day forecast (each day may carry `farm`).
function FarmConditions({ farm, days }) {
  const [stageId, setStageId] = useState(CROP_STAGES[0].id);
  const stage = CROP_STAGES.find((item) => item.id === stageId) || CROP_STAGES[0];
  const now = farm.now || {};
  const today = farm.today || {};
  const wind = today.wind || {};
  const rain = today.rain || {};
  const humidity = today.humidity || {};
  const level = et0Level(today.et0_mm);

  const outlook = [{ et0: today.et0_mm, rainMm: rain.amount_mm, chance: rain.chance_percent }].concat(
    (days || []).slice(1).map((day) => ({
      et0: day.farm && day.farm.et0_mm,
      rainMm: day.farm && day.farm.rain && day.farm.rain.amount_mm,
      chance: day.farm && day.farm.rain && day.farm.rain.chance_percent,
    }))
  );
  const advice = irrigationAdvice(outlook, stage.kc);
  const windSpeed = isNumber(now.wind_speed) ? now.wind_speed : wind.speed_max;

  return (
    <section className="farm-conditions" aria-labelledby="farm-conditions-title">
      <h2 id="farm-conditions-title">Farm conditions today</h2>
      <div className="farm-grid">
        <article className="farm-card" aria-label="Wind">
          <h3>Wind</h3>
          <p className="farm-big">
            {isNumber(now.wind_degrees) && (
              <span className="wind-arrow" aria-hidden="true" style={{ transform: `rotate(${(now.wind_degrees + 180) % 360}deg)` }}>↑</span>
            )}
            {formatNumber(now.wind_speed)} <small>m/s</small>
          </p>
          <p>{now.wind_direction ? `From the ${now.wind_direction} (${Math.round(now.wind_degrees)}°)` : "Direction not available"}</p>
          <p>Gusts now: <b>{formatNumber(now.wind_gust)} m/s</b></p>
          <p>Today's strongest: <b>{formatNumber(wind.speed_max)} m/s</b>{wind.direction ? `, mostly from the ${wind.direction}` : ""}</p>
          <p className="farm-tip">{windInsight(windSpeed)}</p>
        </article>

        <article className="farm-card" aria-label="Rain">
          <h3>Rain</h3>
          <p className="farm-big">{isNumber(rain.chance_percent) ? `${Math.round(rain.chance_percent)}%` : "–"} <small>chance</small></p>
          <p>Expected today: <b>{formatNumber(rain.amount_mm)} mm</b></p>
          <p>Falling now: <b>{formatNumber(now.rain_mm)} mm</b></p>
        </article>

        <article className="farm-card" aria-label="Humidity">
          <h3>Humidity</h3>
          <p className="farm-big">{formatNumber(now.humidity, 0)}<small>% now</small></p>
          <p>Morning (6–10 am): <b>{formatNumber(humidity.morning, 0)}%</b></p>
          <p>Afternoon (1–5 pm): <b>{formatNumber(humidity.afternoon, 0)}%</b></p>
          <p className="farm-tip">{humidityInsight(humidity.morning, humidity.afternoon)}</p>
        </article>

        <article className="farm-card" aria-label="Evapotranspiration">
          <h3>Evapotranspiration (ET₀)</h3>
          <p className="farm-big">{formatNumber(today.et0_mm)} <small>mm/day</small></p>
          <p>{level ? <span className={`et-level et-${level.tone}`}>{level.label} water loss</span> : "Not available"}</p>
          <p>Crop use at this stage: <b>{isNumber(today.et0_mm) ? `${formatNumber(today.et0_mm * stage.kc)} mm/day` : "–"}</b></p>
        </article>
      </div>

      <div className="irrigation-box">
        <h3>Irrigation guide</h3>
        <label htmlFor="crop-stage">Crop stage</label>
        <select id="crop-stage" value={stageId} onChange={(event) => setStageId(event.target.value)}>
          {CROP_STAGES.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
        <p className="irrigation-headline" role="status">{advice.headline}</p>
        {advice.details.map((line) => <p key={line} className="irrigation-detail">{line}</p>)}
        <p className="farm-note">
          ET₀ is the water a short green crop loses through soil evaporation and plant leaves, from the FAO-56 Penman–Monteith model.
          Crop use = ET₀ × a crop factor ({stage.kc} for this stage). Actual need also depends on your crop, soil and recent irrigation.
        </p>
      </div>
    </section>
  );
}

export default FarmConditions;
