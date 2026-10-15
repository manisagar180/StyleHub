import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import CheckoutForm from "./CheckoutForm";
import {
  Search,
  ShoppingBag,
  Heart,
  UserRound,
  ArrowRight,
  Menu,
  X,
  Plus,
  Minus,
  Trash2,
  LogOut,
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8000/api";
const stripePromise = loadStripe(
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
);
const TOKEN_KEY = "stylehub_token";
const CATEGORIES = ["Clothing", "Footwear", "Accessories", "Outerwear"];

const departments = [
  {
    name: "Men",
    subtitle: "Everyday essentials, elevated.",
    image:
      "https://images.unsplash.com/photo-1516257984-b1b4d707412e?auto=format&fit=crop&w=900&q=85",
  },
  {
    name: "Women",
    subtitle: "Made for your own kind of style.",
    image:
      "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=85",
  },
  {
    name: "Kids",
    subtitle: "Little looks, big personalities.",
    image:
      "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?auto=format&fit=crop&w=900&q=85",
  },
];

const formatPrice = (price) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(price || 0));

function getErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || "Invalid input").join(", ");
  }

  if (!error.response) {
    return error.message || "Cannot connect to the backend. Check that FastAPI is running.";
  }

  return fallback;
}

function ProductImage({ src, alt, loading = "lazy" }) {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
  }, [src]);

  if (!src || failed) {
    return (
      <div
        className="product-image-placeholder"
        role="img"
        aria-label={`${alt} image unavailable`}
      >
        <ShoppingBag size={28} />
        <span>Image unavailable</span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      loading={loading}
      onError={() => setFailed(true)}
    />
  );
}

function App() {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [department, setDepartment] = useState("All");
  const [wishlist, setWishlist] = useState([]);

  const [token, setToken] = useState(
    () => localStorage.getItem(TOKEN_KEY) || ""
  );

  const [cart, setCart] = useState({
    items: [],
    total_items: 0,
    total_price: 0,
  });

  const [loading, setLoading] = useState(true);
  const [cartLoading, setCartLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkoutSecret, setCheckoutSecret] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [orders, setOrders] = useState([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [showOrders, setShowOrders] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [notice, setNotice] = useState("");
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const authHeaders = useMemo(
    () => (token ? { Authorization: `Bearer ${token}` } : {}),
    [token]
  );

  async function loadProducts() {
    setLoading(true);

    try {
      const { data } = await axios.get(`${API}/products/`);

      const rows = Array.isArray(data)
        ? data
        : data.products || data.items || data.results || [];

      const mapped = rows.map((product) => ({
        ...product,
        price: Number(product.price ?? product.unit_price ?? 0),
        category:
          typeof product.category === "object"
            ? product.category?.name || "Uncategorized"
            : product.category || "Uncategorized",
        department: product.department || "Men",
        image_url:
          product.image_url || product.image || product.photo || "",
      }));

      setProducts(mapped);

      if (!mapped.length) {
        setNotice("The backend returned no active products.");
      }
    } catch (error) {
      // Never display demo products when the real API fails.
      setProducts([]);
      setNotice(
        getErrorMessage(error, "Could not load products from the backend.")
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadCart(currentToken = token) {
    if (!currentToken) {
      setCart({ items: [], total_items: 0, total_price: 0 });
      return;
    }

    setCartLoading(true);

    try {
      const { data } = await axios.get(`${API}/cart/`, {
        headers: { Authorization: `Bearer ${currentToken}` },
      });

      const items = Array.isArray(data) ? data : data.items || [];

      const totalItems =
        data.total_items ??
        items.reduce((sum, item) => sum + Number(item.quantity || 0), 0);

      const totalPrice =
        data.total_price ??
        items.reduce((sum, item) => sum + Number(item.subtotal || 0), 0);

      setCart({
        items,
        total_items: Number(totalItems),
        total_price: Number(totalPrice),
      });
    } catch (error) {
      setNotice(getErrorMessage(error, "Could not load your shopping bag."));
    } finally {
      setCartLoading(false);
    }
  }

  async function loadOrders() {
    if (!token) {
      setNotice("Please sign in to view your orders.");
      return;
    }

    setOrdersLoading(true);

    try {
      const { data } = await axios.get(`${API}/orders/`, {
        headers: authHeaders,
      });
      setOrders(Array.isArray(data) ? data : []);
      setShowOrders(true);
    } catch (error) {
      setNotice(getErrorMessage(error, "Could not load order history."));
    } finally {
      setOrdersLoading(false);
    }
  }

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    loadCart(token);
  }, [token]);

  const visibleProducts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return products.filter((product) => {
      const matchesDepartment =
        department === "All" || product.department === department;

      const matchesCategory =
        category === "All" || product.category === category;

      const matchesSearch =
        !query ||
        `${product.name || ""} ${product.category || ""} ${
          product.department || ""
        } ${product.description || ""}`
          .toLowerCase()
          .includes(query);

      return matchesDepartment && matchesCategory && matchesSearch;
    });
  }, [products, department, category, search]);

  function chooseDepartment(name) {
    setDepartment(name);
    setCategory("All");
    setMenuOpen(false);

    document.getElementById("collection")?.scrollIntoView({
      behavior: "smooth",
    });
  }

  async function submitAuth(event) {
    event.preventDefault();
    setBusy(true);
    setNotice("");

    try {
      let response;

      if (authMode === "register") {
        await axios.post(`${API}/auth/register`, {
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password,
        });

        setNotice("Account created. Please sign in.");
        setAuthMode("login");
        setForm((previous) => ({
          ...previous,
          password: "",
        }));
        return;
      }

      // OAuth2PasswordRequestForm expects form-encoded credentials.
      const body = new URLSearchParams();
      body.set("username", form.email.trim());
      body.set("password", form.password);

      response = await axios.post(`${API}/auth/login`, body, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      const accessToken = response.data.access_token;

      if (!accessToken) {
        setNotice("Login response did not contain an access token.");
        return;
      }

      localStorage.setItem(TOKEN_KEY, accessToken);
      setToken(accessToken);
      setAuthOpen(false);
      setForm({ name: "", email: "", password: "" });
      setNotice("Welcome to StyleHub!");
    } catch (error) {
      setNotice(
        getErrorMessage(error, "Authentication failed. Check your details.")
      );
    } finally {
      setBusy(false);
    }
  }

  async function addToCart(product) {
    if (!Number.isInteger(Number(product.id)) || Number(product.id) <= 0) {
      setNotice("This product does not have a valid backend product ID.");
      return;
    }

    if (!token) {
      setAuthMode("login");
      setAuthOpen(true);
      setNotice("Sign in to add products to your shopping bag.");
      return;
    }

    try {
      await axios.post(
        `${API}/cart/items/`,
        { product_id: Number(product.id), quantity: 1 },
        { headers: authHeaders }
      );

      await loadCart();
      setNotice(`${product.name} added to your bag.`);
    } catch (error) {
      setNotice(getErrorMessage(error, "Could not add this product."));
    }
  }

  async function updateCartItem(item, quantity) {
    if (quantity < 1) {
      await removeCartItem(item);
      return;
    }

    try {
      await axios.patch(
        `${API}/cart/items/${item.id}`,
        { quantity },
        { headers: authHeaders }
      );

      await loadCart();
    } catch (error) {
      setNotice(getErrorMessage(error, "Could not update the quantity."));
    }
  }

  async function removeCartItem(item) {
    try {
      await axios.delete(`${API}/cart/items/${item.id}`, {
        headers: authHeaders,
      });

      await loadCart();
      setNotice("Item removed from your bag.");
    } catch (error) {
      setNotice(getErrorMessage(error, "Could not remove this item."));
    }
  }

  function signOut() {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setCart({ items: [], total_items: 0, total_price: 0 });
    setOrders([]);
    setShowOrders(false);
    setCheckoutSecret("");
    setCartOpen(false);
    setNotice("You have signed out.");
  }

  async function startCheckout() {
    if (!token) {
      setCartOpen(false);
      setAuthMode("login");
      setAuthOpen(true);
      setNotice("Please sign in before checkout.");
      return;
    }

    if (!cart.items.length) {
      setNotice("Your shopping bag is empty.");
      return;
    }

    if (checkoutLoading || checkoutSecret) return;

    const publishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;
    if (!publishableKey || publishableKey.startsWith("pk_test_REPLACE")) {
      setNotice(
        "Add your Stripe test publishable key to frontend/.env and restart Vite."
      );
      return;
    }

    setCheckoutLoading(true);
    setNotice("");

    try {
      const { data } = await axios.post(
        `${API}/orders/`,
        {},
        { headers: authHeaders }
      );

      if (!data.client_secret) {
        throw new Error("The backend did not return a Stripe client secret.");
      }

      setCheckoutSecret(data.client_secret);
      setNotice(
        `Order #${data.order_id} created. Complete your test payment below.`
      );
    } catch (error) {
      setNotice(
        getErrorMessage(error, error.message || "Could not start checkout.")
      );
    } finally {
      setCheckoutLoading(false);
    }
  }

  async function handlePaymentSuccess() {
    setCheckoutSecret("");
    setNotice(
      "Stripe reports the payment succeeded. Refresh order history to verify the backend order status."
    );
    await loadOrders();
    await loadCart();
  }

  return (
    <div className="stylehub">
      <div className="announcement">
        YOUR STYLE, YOUR STORY <span>✦</span> EVERYDAY FASHION, REIMAGINED
      </div>

      <header className="site-header">
        <button
          className="mobile-menu icon-button"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
        >
          {menuOpen ? <X /> : <Menu />}
        </button>

        <a href="#home" className="logo">
          style<span>hub</span><i>.</i>
        </a>

        <nav className={menuOpen ? "navigation navigation-open" : "navigation"}>
          <a href="#home" onClick={() => setMenuOpen(false)}>Home</a>
          <a href="#departments" onClick={() => setMenuOpen(false)}>Shop by category</a>
          <a href="#collection" onClick={() => setMenuOpen(false)}>Collection</a>
        </nav>

        <div className="header-tools">
          <label className="search-field">
            <Search size={18} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Find your style"
            />
          </label>

          <button
            className="icon-button account-button"
            aria-label="Account"
            onClick={() => {
              setAuthMode("login");
              setAuthOpen(true);
            }}
          >
            <UserRound />
          </button>

          {token && (
            <button
              className="icon-button"
              aria-label="Sign out"
              title="Sign out"
              onClick={signOut}
            >
              <LogOut />
            </button>
          )}

          <button
            className="icon-button bag-button"
            aria-label="Shopping bag"
            onClick={() => {
              setCartOpen(true);
              loadCart();
            }}
          >
            <ShoppingBag />
            <span className="bag-count">{cart.total_items}</span>
          </button>
        </div>
      </header>

      {notice && (
        <div className="notice" role="status">
          <span>{notice}</span>
          <button
            onClick={() => setNotice("")}
            aria-label="Dismiss notification"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <main id="home">
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">
              <span className="eyebrow-line" /> THE NEW SEASON EDIT
            </span>
            <h1>Wear what<br />makes you <em>you.</em></h1>
            <p>
              Discover everyday essentials and statement pieces for every side
              of your story.
            </p>
            <a className="button-dark" href="#departments">
              Explore the collection <ArrowRight size={17} />
            </a>
            <div className="hero-footnote">Personal style starts here.</div>
          </div>

          <div className="hero-visual">
            <img
              src="https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1400&q=90"
              alt="StyleHub fashion collection"
            />
            <div className="hero-stamp">
              <span>THE STYLE EDIT</span>
              <strong>Made for<br /><em>every you.</em></strong>
              <span>EST. STYLEHUB</span>
            </div>
          </div>

          <span className="hero-vertical">FASHION FOR EVERY DAY — STYLEHUB</span>
        </section>

        <section className="trust-strip">
          <div><span>01</span><strong>Everyday essentials</strong></div>
          <div><span>02</span><strong>Styles for everyone</strong></div>
          <div><span>03</span><strong>Easy online shopping</strong></div>
        </section>

        <section className="department-section" id="departments">
          <div className="section-title">
            <div>
              <span className="eyebrow">MADE FOR EVERY YOU</span>
              <h2>Shop by <em>category.</em></h2>
            </div>
            <p>Different days. Different moods.<br />Find the style that feels like you.</p>
          </div>

          <div className="department-grid">
            {departments.map((item, index) => (
              <button
                className="department-card"
                key={item.name}
                onClick={() => chooseDepartment(item.name)}
              >
                <img
                  src={item.image}
                  alt={`${item.name} fashion`}
                  loading="lazy"
                />
                <span className="department-number">0{index + 1} / 03</span>
                <span className="department-overlay">
                  <span className="department-kicker">EXPLORE THE EDIT</span>
                  <strong>{item.name}</strong>
                  <span className="department-subtitle">{item.subtitle}</span>
                  <span className="department-link">
                    Shop {item.name} <ArrowRight size={17} />
                  </span>
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="collection-section" id="collection">
          <div className="section-title">
            <div>
              <span className="eyebrow">THE STYLEHUB SELECTION</span>
              <h2>Good things, <em>well chosen.</em></h2>
            </div>
            <span className="items-count">{visibleProducts.length} pieces</span>
          </div>

          <div className="filter-row">
            <div className="department-filters">
              {["All", "Men", "Women", "Kids"].map((name) => (
                <button
                  key={name}
                  className={
                    department === name ? "filter-pill selected" : "filter-pill"
                  }
                  onClick={() => chooseDepartment(name)}
                >
                  {name}
                </button>
              ))}
            </div>

            <div className="category-filters">
              {["All", ...CATEGORIES].map((name) => (
                <button
                  key={name}
                  className={
                    category === name
                      ? "category-filter selected"
                      : "category-filter"
                  }
                  onClick={() => setCategory(name)}
                >
                  {name}
                </button>
              ))}
            </div>
          </div>

          <div className="product-grid">
            {loading && (
              <p className="loading-state">Loading products from StyleHub…</p>
            )}

            {!loading &&
              visibleProducts.map((product, index) => (
                <article className="product-card" key={product.id}>
                  <div className="product-image">
                    <ProductImage
                      src={product.image_url}
                      alt={product.name || "Product"}
                    />

                    <span className="product-label">
                      {index % 2 ? "NEW SEASON" : "STYLE PICK"}
                    </span>

                    <button
                      className={
                        wishlist.includes(product.id)
                          ? "wishlist-button wishlisted"
                          : "wishlist-button"
                      }
                      aria-label="Toggle wishlist"
                      onClick={() =>
                        setWishlist((old) =>
                          old.includes(product.id)
                            ? old.filter((id) => id !== product.id)
                            : [...old, product.id]
                        )
                      }
                    >
                      <Heart
                        size={18}
                        fill={
                          wishlist.includes(product.id) ? "currentColor" : "none"
                        }
                      />
                    </button>

                    <button
                      className="add-button"
                      onClick={() => addToCart(product)}
                    >
                      <Plus size={16} /> Add to bag
                    </button>
                  </div>

                  <div className="product-details">
                    <div>
                      <span className="product-category">
                        {product.department} · {product.category}
                      </span>
                      <h3>{product.name}</h3>
                    </div>
                    <strong>{formatPrice(product.price)}</strong>
                  </div>
                </article>
              ))}

            {!loading && !visibleProducts.length && (
              <div className="empty-results">
                {products.length
                  ? "No products match your current search or filters."
                  : "No products are available from the backend. Check the API connection."}
              </div>
            )}
          </div>
        </section>

        <section className="editorial-banner">
          <div>
            <span className="eyebrow">A LITTLE STYLE GOES A LONG WAY</span>
            <h2>Everyday looks.<br /><em>Extraordinary you.</em></h2>
          </div>
          <a href="#collection" className="button-light">
            Find your favourites <ArrowRight size={17} />
          </a>
        </section>
      </main>

      <footer className="site-footer">
        <a href="#home" className="logo">style<span>hub</span><i>.</i></a>
        <p>Fashion for every side of you.</p>
        <span>© {new Date().getFullYear()} StyleHub</span>
      </footer>

      {authOpen && (
        <div className="modal-shade" onClick={() => setAuthOpen(false)}>
          <form
            className="auth-card"
            onSubmit={submitAuth}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              className="auth-close"
              type="button"
              onClick={() => setAuthOpen(false)}
              aria-label="Close"
            >
              <X />
            </button>

            <span className="eyebrow">WELCOME TO STYLEHUB</span>
            <h2>
              {authMode === "register"
                ? "Join the style club."
                : "Good to see you."}
            </h2>

            {authMode === "register" && (
              <input
                required
                minLength={2}
                placeholder="Full name"
                value={form.name}
                onChange={(event) =>
                  setForm({ ...form, name: event.target.value })
                }
              />
            )}

            <input
              type="email"
              required
              placeholder="Email address"
              value={form.email}
              onChange={(event) =>
                setForm({ ...form, email: event.target.value })
              }
            />

            <input
              type="password"
              required
              minLength={8}
              placeholder="Password (8+ characters)"
              value={form.password}
              onChange={(event) =>
                setForm({ ...form, password: event.target.value })
              }
            />

            <button className="button-dark auth-submit" disabled={busy}>
              {busy
                ? "Please wait…"
                : authMode === "register"
                  ? "Create account"
                  : "Sign in"}
              <ArrowRight size={17} />
            </button>

            <p className="auth-switch">
              {authMode === "login" ? "New here?" : "Already a member?"}
              <button
                type="button"
                onClick={() => {
                  setAuthMode(authMode === "login" ? "register" : "login");
                  setNotice("");
                }}
              >
                {authMode === "login" ? "Create an account" : "Sign in"}
              </button>
            </p>
          </form>
        </div>
      )}

      {cartOpen && (
        <div
          className="modal-shade cart-shade"
          onClick={() => setCartOpen(false)}
        >
          <section
            className="cart-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Your shopping bag"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="cart-heading">
              <div>
                <span className="eyebrow">YOUR SELECTION</span>
                <h2>{checkoutSecret ? "Secure checkout" : "Your shopping bag"}</h2>
                <button
                  type="button"
                  className="button-dark order-history-toggle"
                  onClick={loadOrders}
                  disabled={ordersLoading}
                >
                  {ordersLoading ? "Loading orders…" : "View order history"}
                </button>
              </div>
              <button
                className="icon-button"
                onClick={() => setCartOpen(false)}
                aria-label="Close bag"
              >
                <X />
              </button>
            </div>

            {showOrders && (
              <section className="order-history">
                <div className="order-history-title">
                  <h3>My orders</h3>
                  <button type="button" onClick={() => setShowOrders(false)}>
                    Hide
                  </button>
                </div>

                {ordersLoading ? (
                  <p>Loading orders…</p>
                ) : orders.length === 0 ? (
                  <p>No orders found.</p>
                ) : (
                  orders.map((order) => (
                    <article key={order.id} className="order-history-item">
                      <div className="order-history-line">
                        <strong>Order #{order.id}</strong>
                        <span className={`order-status status-${String(order.status || "").toLowerCase()}`}>
                          {order.status}
                        </span>
                      </div>
                      <p>Total: {formatPrice(order.total_amount)}</p>
                      <ul>
                        {(order.items || []).map((item) => (
                          <li key={item.id}>
                            {item.product_name} × {item.quantity}
                          </li>
                        ))}
                      </ul>
                    </article>
                  ))
                )}
              </section>
            )}

            {checkoutSecret ? (
              <div className="stripe-checkout-section">
                <p>Complete your payment using Stripe's secure test payment form.</p>
                <Elements
                  stripe={stripePromise}
                  options={{ clientSecret: checkoutSecret }}
                >
                  <CheckoutForm
                    onSuccess={handlePaymentSuccess}
                    onCancel={() => {
                      setCheckoutSecret("");
                      setNotice(
                        "Checkout closed. Check order history for any pending order."
                      );
                    }}
                  />
                </Elements>
                <button
                  type="button"
                  className="stripe-cancel-button"
                  onClick={() => setCheckoutSecret("")}
                  disabled={checkoutLoading}
                >
                  Back to shopping bag
                </button>
              </div>
            ) : cartLoading ? (
              <p>Loading your bag…</p>
            ) : !token ? (
              <div className="cart-empty">
                <ShoppingBag size={34} />
                <p>Sign in to view your shopping bag.</p>
                <button
                  className="button-dark"
                  onClick={() => {
                    setCartOpen(false);
                    setAuthMode("login");
                    setAuthOpen(true);
                  }}
                >
                  Sign in <ArrowRight size={17} />
                </button>
              </div>
            ) : cart.items.length === 0 ? (
              <div className="cart-empty">
                <ShoppingBag size={34} />
                <p>Your bag is waiting for something special.</p>
                <button
                  className="button-dark"
                  onClick={() => setCartOpen(false)}
                >
                  Continue shopping <ArrowRight size={17} />
                </button>
              </div>
            ) : (
              <>
                <div className="cart-items">
                  {cart.items.map((item) => {
                    const product = item.product || {};

                    return (
                      <article className="cart-item" key={item.id}>
                        <ProductImage
                          src={product.image_url}
                          alt={product.name || "Product"}
                        />

                        <div className="cart-item-info">
                          <span>{product.category}</span>
                          <h3>
                            {product.name || `Product ${item.product_id}`}
                          </h3>
                          <strong>{formatPrice(item.subtotal)}</strong>

                          <div className="quantity-controls">
                            <button
                              aria-label="Decrease quantity"
                              onClick={() =>
                                updateCartItem(item, item.quantity - 1)
                              }
                            >
                              <Minus size={14} />
                            </button>

                            <span>{item.quantity}</span>

                            <button
                              aria-label="Increase quantity"
                              onClick={() =>
                                updateCartItem(item, item.quantity + 1)
                              }
                            >
                              <Plus size={14} />
                            </button>

                            <button
                              aria-label="Remove item"
                              className="remove-cart-item"
                              onClick={() => removeCartItem(item)}
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>

                <div className="cart-summary">
                  <div>
                    <span>Subtotal</span>
                    <strong>{formatPrice(cart.total_price)}</strong>
                  </div>

                  <p>Shipping and final totals are confirmed during checkout.</p>

                  <button
                    className="button-dark checkout-button"
                    onClick={startCheckout}
                    disabled={checkoutLoading}
                  >
                    {checkoutLoading ? "Preparing checkout…" : "Checkout"}
                    <ArrowRight size={17} />
                  </button>
                </div>
              </>
            )}
          </section>
        </div>
      )}

      <footer className="mobile-footer-note">
        STYLEHUB — YOUR STYLE, YOUR STORY
      </footer>
    </div>
  );
}

export default App;
