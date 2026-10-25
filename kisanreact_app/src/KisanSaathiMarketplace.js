import React, { useState, useEffect } from "react";
import "./Marketplace.css";
import logoImg from "./assets/images/img_3.jpg";
import { useNavigate } from "react-router-dom";


const API_BASE = "";

/* ==============================
   Auth Page
============================== */
function AuthPage({ onAuth, onClose }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/signup";
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok && data.token) {
        localStorage.setItem("token", data.token);
        onAuth();
      } else {
        setError(data.error || "We couldn't sign you in. Please try again.");
      }
    } catch (err) {
      console.error(err);
      setError("The marketplace couldn't be reached. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-overlay" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section className="auth-page" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <div className="auth-topline"><span className="market-brand-mark">K</span><button className="icon-button" type="button" onClick={onClose} aria-label="Close sign in">×</button></div>
        <span className="market-eyebrow">KISANSAATHI MARKETPLACE</span>
        <h2 id="auth-title">{isLogin ? "Welcome back." : "Join your local market."}</h2>
        <p className="auth-intro">{isLogin ? "Sign in to list your products and manage your farm listings." : "Create a free account to sell products and manage your listings."}</p>
      <form onSubmit={handleSubmit} className="auth-form">
        <label htmlFor="market-email">Email address</label>
        <input
          id="market-email"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <label htmlFor="market-password">Password</label>
        <input
          id="market-password"
          type="password"
          placeholder="At least 6 characters"
          minLength="6"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="market-error" role="alert">{error}</p>}
        <button type="submit" className="btn market-primary-button" disabled={busy}>
          {busy ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
        </button>
      </form>
        <p className="auth-switch">
          {isLogin ? "New to the marketplace?" : "Already have an account?"}{" "}
          <button type="button" onClick={() => { setIsLogin(!isLogin); setError(""); }}>
            {isLogin ? "Create an account" : "Sign in"}
          </button>
        </p>
      </section>
    </div>
  );
}

/* ==============================
   Product Card
============================== */
function ProductCard({ product, onView }) {
  return (
    <article className="card">
      <div className="card-img">
        {product.images && product.images.length > 0 ? (
          <img src={product.images[0]} alt="" loading="lazy" />
        ) : (
          <div className="placeholder"><span aria-hidden="true">✳</span><small>FARM FRESH</small></div>
        )}
        <span className="product-category">{product.category || "Farm goods"}</span>
      </div>
      <div className="card-body">
        <h3 className="title">{product.title}</h3>
        <p className="muted">Sold by <strong>{product.seller || "Local farmer"}</strong></p>
        <div className="card-footer">
          <strong className="price">{new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(product.price) || 0)}</strong>
          <button className="btn btn-sm" type="button" onClick={() => onView(product)} aria-label={`View ${product.title}`}>
            View details <span aria-hidden="true">↗</span>
          </button>
        </div>
      </div>
    </article>
  );
}

/* ==============================
   Sell Form
============================== */
function SellForm({ onAdd, texts }) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Crops");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");
  const [seller, setSeller] = useState("");
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  function clearForm() {
    setTitle("");
    setCategory("Crops");
    setPrice("");
    setDescription("");
    setSeller("");
    setImages([]);
  }

  async function handleFiles(e) {
    const files = Array.from(e.target.files).slice(0, 3);
    setUploading(true);
    const uploadedImages = [];

    for (let file of files) {
      const formData = new FormData();
      formData.append("image", file);

      try {
        const res = await fetch(`${API_BASE}/upload`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
          body: formData,
        });
        const data = await res.json();
        if (!res.ok || !data.filePath) throw new Error(data.error || "Image upload failed");
        uploadedImages.push(data.filePath);
      } catch (err) {
        console.error("Upload error:", err);
        setError(err.message || "Error uploading image");
      }
    }

    setImages(uploadedImages);
    setUploading(false);
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (!title.trim() || !price || Number(price) <= 0 || !seller.trim()) {
      setError("Add a product name, a price greater than zero, and your seller name.");
      return;
    }
    if (images.length === 0) {
      setError("Add at least one product photo before posting.");
      return;
    }

    const product = {
      title,
      category,
      price: Number(price),
      description,
      images,
      seller,
      createdAt: Date.now(),
    };

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/products`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(product),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to post product");
      onAdd();
      clearForm();
    } catch (err) {
      console.error(err);
      setError(err.message || "Error posting product");
    }
  }

  return (
    <form className="sell-form" onSubmit={submit}>
      <h2>{texts.sellFormTitle}</h2>
      <p className="form-intro">Give local buyers the details they need to find your listing.</p>
      <label htmlFor="listing-title">{texts.productTitle}</label>
      <input id="listing-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g., Fresh turmeric, 10 kg" required />

      <label htmlFor="listing-category">{texts.category}</label>
      <select id="listing-category" value={category} onChange={(e) => setCategory(e.target.value)}>
        <option>Crops</option>
        <option>Fertilizers</option>
        <option>Pesticides</option>
        <option>Machines</option>
        <option>Others</option>
      </select>

      <label htmlFor="listing-price">{texts.price}</label>
      <input id="listing-price" type="number" min="1" step="1" value={price} onChange={(e) => setPrice(e.target.value)} required />

      <label htmlFor="listing-description">{texts.description}</label>
      <textarea id="listing-description" value={description} onChange={(e) => setDescription(e.target.value)} rows="4" placeholder="Quality, quantity, pickup details…" />

      <label htmlFor="listing-seller">{texts.seller}</label>
      <input id="listing-seller" value={seller} onChange={(e) => setSeller(e.target.value)} placeholder="e.g., Ram Kumar - 98765XXXXX" required />

      <label htmlFor="listing-images">{texts.images}</label>
      <input id="listing-images" type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={handleFiles} />
      <small className="field-hint">Use clear JPG, PNG or WebP photos, up to 3 images.</small>
      {uploading && <div className="upload-status" role="status">Uploading photos…</div>}

      <div className="preview-row">
        {images.map((src, i) => <img className="preview" key={i} src={src} alt={`preview-${i}`} />)}
      </div>
      {error && <p className="market-error" role="alert">{error}</p>}

      <div className="form-actions">
        <button type="submit" className="btn market-primary-button" disabled={uploading}>{texts.postListing}</button>
      </div>
    </form>
  );
}

/* ==============================
   Main Marketplace Component
============================== */
function Marketplace({ loggedIn, onAuth, onLogout }) {
  const [products, setProducts] = useState([]);
  const [tab, setTab] = useState("buy");
  const [query, setQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [selected, setSelected] = useState(null);
  const [lang, setLang] = useState("en");
  const [showAuth, setShowAuth] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);

   const navigate = useNavigate();

  const translations = {
    en: {
      title: "KisanSaathi Marketplace",
      tagline: "Buy & sell agricultural products locally",
      buy: "Buy",
      sell: "Sell",
      dashboard: "Dashboard",
      back: "⬅ Back to Home",
      sellFormTitle: "Sell a Product",
      productTitle: "Product Title",
      category: "Category",
      price: "Price (₹)",
      description: "Description",
      seller: "Seller Name / Contact",
      images: "Images (up to 3)",
      postListing: "Post Listing",
    },
    mr: {
      title: "किसानसाथी बाजारपेठ",
      tagline: "शेती उत्पादने खरेदी व विक्री करा",
      buy: "खरेदी",
      sell: "विक्री",
      dashboard: "डॅशबोर्ड",
      back: "⬅ मुख्यपृष्ठावर परत जा",
      sellFormTitle: "उत्पादन विक्री करा",
      productTitle: "उत्पादनाचे नाव",
      category: "श्रेणी",
      price: "किंमत (₹)",
      description: "वर्णन",
      seller: "विक्रेत्याचे नाव / संपर्क",
      images: "छायाचित्रे (३ पर्यंत)",
      postListing: "जाहिरात पोस्ट करा",
    },
  };
  const texts = translations[lang];

  async function loadProducts() {
    try {
      setLoadError("");
      const res = await fetch(`${API_BASE}/api/products`);
      const data = await res.json();
      if (!res.ok || !Array.isArray(data)) throw new Error(data.error || "Could not load listings.");
      const productsWithImages = data.map((p) => ({
        ...p,
        images: Array.isArray(p.images) ? p.images : []
      }));
      setProducts(productsWithImages.sort((a, b) => b.createdAt - a.createdAt));
    } catch (err) {
      console.error("fetch products error", err);
      setLoadError(err.message || "Could not load listings.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProducts();
    const refresh = window.setInterval(loadProducts, 30000);
    return () => window.clearInterval(refresh);
  }, []);

  function filtered() {
    return products.filter((p) =>
      (p.title + " " + (p.description || "") + " " + (p.seller || "")).toLowerCase().includes(query.toLowerCase()) &&
      (categoryFilter === "All" || p.category === categoryFilter)
    );
  }

  async function deleteProduct(id) {
    if (!window.confirm("Remove this listing from the marketplace?")) return;
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_BASE}/api/products/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not remove this listing.");
      setProducts((prev) => prev.filter((x) => x.id !== id));
    } catch (err) {
      console.error(err);
      setLoadError(err.message || "Could not remove this listing.");
    }
  }
  const visibleProducts = filtered();
  const myProducts = products.filter((product) => {
    try {
      const payload = localStorage.getItem("token")?.split(".")[1] || "";
      const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
      const userId = JSON.parse(atob(normalized + "=".repeat((4 - normalized.length % 4) % 4))).id;
      return String(product.ownerId) === String(userId);
    } catch {
      return false;
    }
  });

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="brand">
         <img src={logoImg} alt="" className="brand-img" />
          <div className="brand-text">
            <h1>{texts.title}</h1>
            <div className="muted-small">{texts.tagline}</div>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-sm" onClick={() => setLang(lang === "en" ? "mr" : "en")}>
            {lang === "en" ? "मराठी" : "English"}
          </button>
          <button className="account-button" type="button" onClick={() => {
            if (loggedIn) { onLogout(); setTab("buy"); }
            else setShowAuth(true);
          }}>
            <span className="account-avatar" aria-hidden="true">{loggedIn ? "✓" : "↗"}</span>
            {loggedIn ? "Sign out" : "Sign in"}
          </button>
          <button className="home-link" type="button" onClick={() => navigate("/")}>← Farm tools</button>
        </div>
      </header>

      <div className="marketplace-main">
        <section className="market-hero">
          <div className="market-hero-copy">
            <span className="market-eyebrow"><i /> LOCAL FARM TRADE</span>
            <h2>Good things grow<br />closer to home.</h2>
            <p>Find farm essentials and fresh produce from growers in your community.</p>
          </div>
          <div className="market-hero-note"><span aria-hidden="true">✳</span><strong>Grown here.<br />Shared nearby.</strong></div>
        </section>

        <nav className="top-tabs" aria-label="Marketplace sections">
          {[[ "buy", texts.buy ], [ "sell", texts.sell ], [ "dashboard", texts.dashboard ]].map(([key, label]) => (
            <button key={key} type="button" className={`tab ${tab === key ? "active" : ""}`} onClick={() => {
              if (key !== "buy" && !loggedIn) { setShowAuth(true); return; }
              setTab(key);
            }}>
              {label}{key === "dashboard" && loggedIn && myProducts.length > 0 && <span className="tab-count">{myProducts.length}</span>}
            </button>
          ))}
        </nav>

      {tab === "buy" && (
        <section className="page buy-page">
          <div className="market-section-heading">
            <div><span className="market-eyebrow">THE COMMUNITY SHELF</span><h2>Find your next farm favourite</h2></div>
            <span className="listing-count">{products.length} {products.length === 1 ? "listing" : "listings"}</span>
          </div>
          <div className="controls">
            <label className="search-field"><span aria-hidden="true">⌕</span><input aria-label="Search products" placeholder="Search produce, tools and more" value={query} onChange={(e) => setQuery(e.target.value)} /></label>
            <select aria-label="Filter by category" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
              <option>All</option>
              <option>Crops</option>
              <option>Fertilizers</option>
              <option>Pesticides</option>
              <option>Machines</option>
              <option>Others</option>
            </select>
          </div>
          {loadError && <div className="market-message market-error" role="alert">{loadError}<button type="button" onClick={loadProducts}>Try again</button></div>}
          {loading ? <div className="market-message">Loading local listings…</div> : visibleProducts.length ? <div className="cards-grid">
            {visibleProducts.map((p) => (
              <ProductCard key={p.id} product={p} onView={setSelected} />
            ))}
          </div> : !loadError && <div className="market-empty"><span aria-hidden="true">✳</span><h3>{query || categoryFilter !== "All" ? "No matching listings yet" : "The shelf is ready for its first listing."}</h3><p>{query || categoryFilter !== "All" ? "Try a different search or category." : "Browse freely, or sign in to share something from your farm."}</p>{!query && categoryFilter === "All" && <button className="btn market-primary-button" type="button" onClick={() => loggedIn ? setTab("sell") : setShowAuth(true)}>List a product <span aria-hidden="true">↗</span></button>}</div>}
        </section>
      )}

      {tab === "sell" && <section className="page sell-page"><SellForm onAdd={() => { loadProducts(); setTab("buy"); }} texts={texts} /></section>}

      {tab === "dashboard" && (
        <section className="page dashboard-page">
          <div className="market-section-heading"><div><span className="market-eyebrow">YOUR FARM STALL</span><h2>Manage your listings</h2></div></div>
          {loadError && <div className="market-message market-error" role="alert">{loadError}</div>}
          {myProducts.length ? <div className="cards-grid">
            {myProducts.map((p) => (
              <div key={p.id} className="dashboard-card">
                <ProductCard product={p} onView={setSelected} />
                <button className="remove-listing" type="button" onClick={() => deleteProduct(p.id)}>
                  Remove listing
                </button>
              </div>
            ))}
          </div> : <div className="market-empty"><span aria-hidden="true">↗</span><h3>No listings to manage yet</h3><p>When you post a product, it will be available here.</p><button className="btn market-primary-button" type="button" onClick={() => setTab("sell")}>Create a listing</button></div>}
        </section>
      )}

      {selected && (
        <div className="modal" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}>
          <section className="modal-content" role="dialog" aria-modal="true" aria-labelledby="listing-title">
            <button className="icon-button modal-close" type="button" onClick={() => setSelected(null)} aria-label="Close listing details">×</button>
            <div className="modal-left">{selected.images?.length ? <img src={selected.images[0]} alt="" /> : <div className="no-image"><span>✳</span> FARM FRESH</div>}</div>
            <div className="modal-right">
              <span className="market-eyebrow">{selected.category || "Farm goods"}</span>
              <h2 id="listing-title">{selected.title}</h2>
              <h3>{new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(selected.price) || 0)}</h3>
              <p>{selected.description || "Ask the seller for more details about this listing."}</p>
              <div className="seller-panel"><small>LISTED BY</small><strong>{selected.seller || "Local farmer"}</strong><span>Contact the seller directly to arrange pickup and payment.</span></div>
              <div className="modal-actions"><button className="btn market-primary-button" type="button" onClick={() => setSelected(null)}>Got it</button></div>
            </div>
          </section>
        </div>
      )}
      </div>
      {showAuth && <AuthPage onAuth={() => { onAuth(); setShowAuth(false); }} onClose={() => setShowAuth(false)} />}
    </div>
  );
}

/* ==============================
   Protected Wrapper
============================== */
export default function App() {
  const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem("token"));

  return <Marketplace
    loggedIn={loggedIn}
    onAuth={() => setLoggedIn(true)}
    onLogout={() => { localStorage.removeItem("token"); setLoggedIn(false); }}
  />;
}
