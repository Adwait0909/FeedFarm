// Plain helper functions for the farm-weather panel (no React, unit-tested in farmWeather.test.js).

export const CROP_STAGES = [
  { id: "reference", label: "Reference crop (short green grass)", kc: 1.0 },
  { id: "initial", label: "Just planted / establishing", kc: 0.4 },
  { id: "development", label: "Growing fast", kc: 0.75 },
  { id: "mid", label: "Flowering / fruiting (peak need)", kc: 1.15 },
  { id: "late", label: "Ripening / close to harvest", kc: 0.7 },
];

export const isNumber = (value) => typeof value === "number" && Number.isFinite(value);

export function formatNumber(value, digits = 1) {
  return isNumber(value) ? String(Number(value.toFixed(digits))) : "–";
}

// FAO-style classes for reference evapotranspiration (mm per day).
export function et0Level(mm) {
  if (!isNumber(mm)) return null;
  if (mm < 2) return { label: "Low", tone: "low" };
  if (mm < 4) return { label: "Moderate", tone: "moderate" };
  if (mm < 6) return { label: "High", tone: "high" };
  return { label: "Very high", tone: "very-high" };
}

// Crop water use = reference evapotranspiration x crop coefficient (Kc).
export function cropNeedMm(et0, kc) {
  return isNumber(et0) ? et0 * kc : null;
}

// Showers under about 2 mm mostly evaporate; larger rain is counted at 80 % as "effective".
export function effectiveRainMm(rainMm) {
  return isNumber(rainMm) && rainMm >= 2 ? rainMm * 0.8 : 0;
}

export function humidityInsight(morning, afternoon) {
  if (!isNumber(morning) || !isNumber(afternoon)) return "";
  if (afternoon < 40) return `Dry afternoon air (${afternoon}%): plants and soil lose water quickly. Water early in the morning.`;
  if (afternoon >= 75) return `Humid air (${afternoon}% in the afternoon): water evaporates slowly, but fungal disease risk is higher. Avoid watering late in the day.`;
  if (morning - afternoon >= 25) return `The air dries out a lot from morning (${morning}%) to afternoon (${afternoon}%), so evaporation peaks after midday.`;
  return "Humidity stays fairly steady through the day.";
}

export function windInsight(speedMs) {
  if (!isNumber(speedMs)) return "";
  if (speedMs >= 8) return "Strong wind: spray and sprinkler water will drift. Avoid spraying today.";
  if (speedMs >= 5) return "Breezy: prefer drip irrigation, or spray when the wind drops.";
  return "Light wind: fine for spraying and sprinklers.";
}

// days: [{ et0, rainMm, chance }] for today and the following days.
export function irrigationAdvice(days, kc) {
  const today = days && days[0];
  if (!today || !isNumber(today.et0)) {
    return { headline: "Evapotranspiration data is not available for this place right now, so no irrigation estimate can be given.", details: [] };
  }
  const need = cropNeedMm(today.et0, kc);
  const effective = effectiveRainMm(today.rainMm);
  const net = Math.max(0, need - effective);
  const chance = isNumber(today.chance) ? today.chance : null;
  const details = [];

  let headline;
  if ((chance !== null && chance >= 70 && effective > 0) || effective >= need * 0.9) {
    headline = "Rain should cover today's water need. Hold off irrigating and check again tomorrow.";
  } else if (chance !== null && chance >= 40) {
    headline = `Rain is possible (${chance}% chance). If you can, wait; otherwise irrigate about ${formatNumber(net)} mm.`;
  } else {
    headline = `Dry day: the crop may use about ${formatNumber(need)} mm. Irrigate to replace roughly ${formatNumber(net)} mm.`;
  }
  if (net > 0) {
    details.push(`${formatNumber(net)} mm of water = ${formatNumber(net)} litres per square metre = about ${Math.round(net * 10000).toLocaleString("en-IN")} litres per hectare.`);
  }

  const next = days.slice(0, 3).filter((day) => isNumber(day.et0));
  if (next.length > 1) {
    const needTotal = next.reduce((sum, day) => sum + cropNeedMm(day.et0, kc), 0);
    const rainTotal = next.reduce((sum, day) => sum + effectiveRainMm(day.rainMm), 0);
    details.push(`Next ${next.length} days: crop use about ${formatNumber(needTotal)} mm, useful rain about ${formatNumber(rainTotal)} mm, so about ${formatNumber(Math.max(0, needTotal - rainTotal))} mm still to supply.`);
  }
  return { headline, details };
}
