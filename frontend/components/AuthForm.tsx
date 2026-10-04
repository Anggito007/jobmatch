"use client";

import { useState } from "react";
import { login, register, setToken } from "@/lib/api";

interface Props {
  onAuth: (email: string) => void;
}

export default function AuthForm({ onAuth }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const fn = mode === "login" ? login : register;
      const res = await fn(email, password);
      setToken(res.token);
      onAuth(res.email);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Gagal.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-box">
      <div className="auth-tabs">
        <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
          Masuk
        </button>
        <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
          Daftar
        </button>
      </div>
      <div className="form-row">
        <div className="field">
          <label htmlFor="auth-email">Email</label>
          <input
            id="auth-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="kamu@email.com"
          />
        </div>
        <div className="field">
          <label htmlFor="auth-pass">Password (min. 6 karakter)</label>
          <input
            id="auth-pass"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••"
          />
        </div>
      </div>
      <div className="form-row">
        <button className="btn" onClick={submit} disabled={busy || !email || !password}>
          {busy ? "Memproses…" : mode === "login" ? "Masuk" : "Daftar"}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
