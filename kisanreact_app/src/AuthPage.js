import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = "";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/signup";

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",
      });

      const data = await res.json();

      if (res.ok && data.token) {
        localStorage.setItem("token", data.token);
        navigate("/marketplace"); // Navigate to Marketplace after login/signup
      } else {
        alert(data.error || "Error");
      }
    } catch (err) {
      console.error(err);
      alert("Something went wrong");
    }
  }

  // Inline styles
  const styles = {
    container: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      height: "100vh",
      background: "#f5f5dc",
      fontFamily: "Arial, sans-serif",
    },
    formContainer: {
      display: "flex",
      flexDirection: "column",
      width: "350px",
      padding: "30px 25px",
      background: "#fff",
      borderRadius: "12px",
      boxShadow: "0 8px 25px rgba(0,0,0,0.15)",
    },
    heading: {
      marginBottom: "20px",
      color: "#2e7d32",
      textAlign: "center",
    },
    input: {
      marginBottom: "15px",
      padding: "10px 12px",
      fontSize: "16px",
      border: "1px solid #ccc",
      borderRadius: "6px",
    },
    button: {
      padding: "10px",
      fontSize: "16px",
      background: "#2e7d32",
      color: "#fff",
      border: "none",
      borderRadius: "6px",
      cursor: "pointer",
      transition: "background 0.2s",
    },
    toggle: {
      marginTop: "15px",
      textAlign: "center",
      fontSize: "14px",
      color: "#654321",
      cursor: "pointer",
    },
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.heading}>{isLogin ? "Login" : "Sign Up"}</h2>
      <form style={styles.formContainer} onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={styles.input}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
          required
        />
        <button
          type="submit"
          style={styles.button}
          onMouseOver={(e) => (e.target.style.background = "#27642a")}
          onMouseOut={(e) => (e.target.style.background = "#2e7d32")}
        >
          {isLogin ? "Login" : "Sign Up"}
        </button>
      </form>
      <p style={styles.toggle} onClick={() => setIsLogin(!isLogin)}>
        {isLogin ? "Need an account? Sign Up" : "Have an account? Login"}
      </p>
    </div>
  );
}
