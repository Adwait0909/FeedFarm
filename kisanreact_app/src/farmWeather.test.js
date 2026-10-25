import {
  CROP_STAGES, cropNeedMm, effectiveRainMm, et0Level, formatNumber, humidityInsight, irrigationAdvice, windInsight,
} from "./farmWeather";

test("evapotranspiration classes follow the usual mm/day bands", () => {
  expect(et0Level(1.2).label).toBe("Low");
  expect(et0Level(3.9).label).toBe("Moderate");
  expect(et0Level(5.5).label).toBe("High");
  expect(et0Level(7.1).label).toBe("Very high");
  expect(et0Level(null)).toBeNull();
});

test("crop water use is ET0 times the crop factor, and only real showers count as rain", () => {
  expect(cropNeedMm(5, 0.4)).toBeCloseTo(2);
  expect(cropNeedMm(null, 1)).toBeNull();
  expect(effectiveRainMm(1.5)).toBe(0);
  expect(effectiveRainMm(10)).toBeCloseTo(8);
  expect(effectiveRainMm(undefined)).toBe(0);
});

test("humidity advice compares morning with afternoon", () => {
  expect(humidityInsight(80, 35)).toMatch(/Dry afternoon air \(35%\)/);
  expect(humidityInsight(85, 78)).toMatch(/Humid air/);
  expect(humidityInsight(90, 60)).toMatch(/dries out a lot/);
  expect(humidityInsight(70, 60)).toMatch(/fairly steady/);
  expect(humidityInsight(null, 50)).toBe("");
});

test("wind advice has calm, breezy and strong levels", () => {
  expect(windInsight(2)).toMatch(/Light wind/);
  expect(windInsight(6)).toMatch(/Breezy/);
  expect(windInsight(9)).toMatch(/Strong wind/);
  expect(windInsight(undefined)).toBe("");
});

test("dry day: irrigate the crop's water use", () => {
  const advice = irrigationAdvice([{ et0: 6, rainMm: 0, chance: 10 }], 1);
  expect(advice.headline).toMatch(/Dry day: the crop may use about 6 mm. Irrigate to replace roughly 6 mm/);
  expect(advice.details[0]).toMatch(/60,000 litres per hectare/);
});

test("crop stage scales the estimate", () => {
  const young = CROP_STAGES.find((stage) => stage.id === "initial").kc;
  expect(irrigationAdvice([{ et0: 5, rainMm: 0, chance: 0 }], young).headline).toMatch(/about 2 mm/);
});

test("heavy likely rain means hold off; possible rain means wait if you can", () => {
  expect(irrigationAdvice([{ et0: 4, rainMm: 12, chance: 85 }], 1).headline).toMatch(/Hold off irrigating/);
  expect(irrigationAdvice([{ et0: 4, rainMm: 1, chance: 55 }], 1).headline).toMatch(/Rain is possible \(55% chance\)/);
});

test("three-day summary adds up need and useful rain", () => {
  const advice = irrigationAdvice([{ et0: 5, rainMm: 0, chance: 0 }, { et0: 5, rainMm: 10, chance: 70 }, { et0: 4, rainMm: 0, chance: 10 }], 1);
  expect(advice.details.join(" ")).toMatch(/Next 3 days: crop use about 14 mm, useful rain about 8 mm, so about 6 mm still to supply/);
});

test("missing evapotranspiration gives an honest message instead of a number", () => {
  expect(irrigationAdvice([{ et0: null, rainMm: 0, chance: 0 }], 1).headline).toMatch(/not available/);
  expect(irrigationAdvice([], 1).details).toEqual([]);
  expect(formatNumber(null)).toBe("–");
  expect(formatNumber(2.3456, 1)).toBe("2.3");
});
