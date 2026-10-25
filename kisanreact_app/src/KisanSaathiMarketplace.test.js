import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import KisanSaathiMarketplace from "./KisanSaathiMarketplace";

jest.mock("react-router-dom", () => ({
  useNavigate: () => jest.fn(),
}), { virtual: true });

const demoProduct = {
  id: 7,
  title: "Wai Turmeric Powder",
  category: "Crops",
  price: 240,
  seller: "Meera's farm",
  description: "Stone-ground turmeric from the latest harvest.",
  images: [],
  createdAt: 10,
};

beforeEach(() => {
  localStorage.clear();
  global.fetch = jest.fn().mockImplementation((url) => {
    if (String(url).includes("/api/products")) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve([demoProduct]) });
    }
    if (String(url).includes("/api/auth/signup")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ token: "header.eyJpZCI6MX0.signature" }),
      });
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({ error: "Unexpected request" }) });
  });
});

afterEach(() => {
  jest.clearAllMocks();
});

test("visitors can browse listings and see seller details without an account", async () => {
  render(<KisanSaathiMarketplace loggedIn={false} onAuth={jest.fn()} onLogout={jest.fn()} />);

  expect(await screen.findByRole("heading", { name: "Wai Turmeric Powder" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /view wai turmeric powder/i }));
  expect(screen.getByRole("dialog")).toHaveTextContent("Meera's farm");
  expect(screen.getByText(/contact the seller directly/i)).toBeInTheDocument();
});

test("farmers can create an account from the sell tab", async () => {
  render(<KisanSaathiMarketplace />);

  fireEvent.click(screen.getByRole("button", { name: "Sell" }));
  fireEvent.click(screen.getByRole("button", { name: "Create an account" }));
  fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "grower@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secure-pass-123" } });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));

  await waitFor(() => expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument());
  expect(localStorage.getItem("token")).toBe("header.eyJpZCI6MX0.signature");
});
