"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      router.replace("/workspaces");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Не удалось войти");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card stack">
        <div className="brand">DECISION LAB</div>
        <h1 className="page-title">Вход</h1>
        <form onSubmit={onSubmit} className="stack">
          <input type="email" required autoComplete="username" placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" required minLength={8} autoComplete="current-password" placeholder="пароль" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={pending}>{pending ? "Входим…" : "Войти"}</button>
        </form>
        <p className="muted">
          Нет аккаунта? <Link href="/register">Регистрация</Link>
        </p>
      </div>
    </div>
  );
}
