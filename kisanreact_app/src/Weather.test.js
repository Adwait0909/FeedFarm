import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Weather from "./Weather";

jest.mock("react-router-dom", () => ({ useNavigate: () => jest.fn() }), { virtual: true });

const report = {
  name: "Baramati", region: "Maharashtra, India",
  main: { temp: 29.4, humidity: 61, feels_like: 31.2 },
  weather: [{ main: "Clouds", description: "partly cloudy" }], wind: { speed: 3 },
};
const forecast = {
  list: [0, 1, 2, 3, 4].map((i) => ({
    dt_txt: `2026-10-${14 + i} 12:00:00`, main: { temp_min: 20, temp_max: 31 }, weather: [{ main: "Clear", description: "clear sky" }],
  })),
};
const reply = (status, body) => Promise.resolve({ ok: status < 400, status, json: () => (body === undefined ? Promise.reject(new Error("not json")) : Promise.resolve(body)) });

function renderPage() {
  render(<Weather />);
}
function search(text) {
  fireEvent.change(screen.getByPlaceholderText(/enter city or town/i), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: /find weather/i }));
}

afterEach(() => { delete global.fetch; });

test("shows the weather and the 5-day outlook for a town", async () => {
  global.fetch = jest.fn((url) => (url.includes("/current") ? reply(200, report) : reply(200, forecast)));
  renderPage();
  search("Baramati");
  expect(await screen.findByText(/Baramati, Maharashtra, India/)).toBeInTheDocument();
  expect(screen.getByText(/partly cloudy/)).toBeInTheDocument();
  expect(await screen.findByText(/5-day outlook/)).toBeInTheDocument();
  expect(global.fetch.mock.calls[0][0]).toBe("/api/weather/current?city=Baramati");
});

test("shows a clear message when the city is not found", async () => {
  global.fetch = jest.fn(() => reply(404, { error: "City not found. Check the spelling and try again." }));
  renderPage();
  search("Nowhere");
  expect(await screen.findByRole("alert")).toHaveTextContent(/City not found/);
});

test("shows a message when the server answers with a page that is not JSON", async () => {
  global.fetch = jest.fn(() => reply(502, undefined));
  renderPage();
  search("Pune");
  expect(await screen.findByRole("alert")).toHaveTextContent(/not available right now \(error 502\)/);
});

test("does not crash when the answer is incomplete", async () => {
  global.fetch = jest.fn(() => reply(200, { name: "Pune" }));
  renderPage();
  search("Pune");
  expect(await screen.findByRole("alert")).toHaveTextContent(/unexpected answer/);
  expect(screen.getByRole("heading", { name: /weather forecast/i })).toBeInTheDocument();   // page still rendered
});

test("keeps the current weather and says so when only the forecast fails", async () => {
  global.fetch = jest.fn((url) => (url.includes("/current") ? reply(200, report) : reply(502, { error: "x" })));
  renderPage();
  search("Pune");
  expect(await screen.findByText(/Baramati, Maharashtra, India/)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText(/5-day outlook is not available/)).toBeInTheDocument());
});

test("explains a network failure instead of staying blank", async () => {
  global.fetch = jest.fn(() => Promise.reject(new TypeError("Failed to fetch")));
  renderPage();
  search("Pune");
  expect(await screen.findByRole("alert")).toHaveTextContent(/Could not reach the server/);
  expect(screen.getByRole("button", { name: /find weather/i })).not.toBeDisabled();
});

test("asks for a place when the box is empty", () => {
  global.fetch = jest.fn();
  renderPage();
  fireEvent.click(screen.getByRole("button", { name: /find weather/i }));
  expect(screen.getByRole("alert")).toHaveTextContent(/Enter a city or town/);
  expect(global.fetch).not.toHaveBeenCalled();
});

const farmReport = {
  ...report,
  farm: {
    now: { wind_speed: 3, wind_gust: 7, wind_degrees: 315, wind_direction: "NW", rain_mm: 0.2, humidity: 61 },
    today: {
      rain: { chance_percent: 10, amount_mm: 0 },
      wind: { speed_max: 5, gust_max: 9, degrees: 315, direction: "NW" },
      humidity: { morning: 81, afternoon: 40 },
      et0_mm: 5.4,
    },
  },
};
const farmForecast = {
  list: [0, 1, 2, 3, 4].map((i) => ({
    dt_txt: `2026-10-${14 + i} 12:00:00`, main: { temp_min: 20, temp_max: 31 }, weather: [{ main: "Clear", description: "clear sky" }],
    pop: 0.2, farm: { rain: { chance_percent: 20 + i * 10, amount_mm: i }, wind: { speed_max: 5, direction: "S" }, et0_mm: 5 - i * 0.5 },
  })),
};

test("shows wind, rain, humidity and evapotranspiration details with an irrigation guide", async () => {
  global.fetch = jest.fn((url) => (url.includes("/current") ? reply(200, farmReport) : reply(200, farmForecast)));
  renderPage();
  search("Pune");
  expect(await screen.findByText(/Farm conditions today/)).toBeInTheDocument();
  expect(screen.getByText(/From the NW \(315°\)/)).toBeInTheDocument();
  expect(screen.getByText(/Gusts now:/).textContent).toMatch(/7 m\/s/);
  expect(screen.getByLabelText("Rain")).toHaveTextContent("10%");
  expect(screen.getByLabelText("Humidity")).toHaveTextContent(/Morning \(6–10 am\): 81%/);
  expect(screen.getByLabelText("Humidity")).toHaveTextContent(/Afternoon \(1–5 pm\): 40%/);
  expect(screen.getByLabelText("Evapotranspiration")).toHaveTextContent(/5\.4\s*mm\/day/);
  expect(screen.getByText(/High water loss/)).toBeInTheDocument();
  expect(screen.getByRole("status", { name: "" , hidden: true })).toBeDefined();
  expect(await screen.findByText(/5-day outlook/)).toBeInTheDocument();
  expect(screen.getAllByText(/ET₀ \d/).length).toBeGreaterThanOrEqual(5);
});

test("changing the crop stage changes the irrigation estimate", async () => {
  global.fetch = jest.fn((url) => (url.includes("/current") ? reply(200, farmReport) : reply(200, farmForecast)));
  renderPage();
  search("Pune");
  await screen.findByText(/Farm conditions today/);
  expect(screen.getByText(/Dry day: the crop may use about 5.4 mm/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Crop stage"), { target: { value: "initial" } });
  expect(screen.getByText(/the crop may use about 2.2 mm/)).toBeInTheDocument();
});

test("an answer without farm details still shows the normal weather and no farm panel", async () => {
  global.fetch = jest.fn((url) => (url.includes("/current") ? reply(200, report) : reply(200, forecast)));
  renderPage();
  search("Pune");
  expect(await screen.findByText(/partly cloudy/)).toBeInTheDocument();
  expect(screen.queryByText(/Farm conditions today/)).not.toBeInTheDocument();
});
