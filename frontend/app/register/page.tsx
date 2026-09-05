"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "../../lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          full_name: fullName.trim() || null,
        }),
      });
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      router.replace("/workspaces");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Не удалось зарегистрироваться");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card stack">
        <div className="brand">DECISION LAB</div>
        <h1 className="page-title">Регистрация</h1>
        <form onSubmit={onSubmit} className="stack">
          <input type="email" required autoComplete="username" placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="имя (необязательно)" autoComplete="name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <input type="password" required minLength={8} autoComplete="new-password" placeholder="пароль, минимум 8 символов" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={pending}>{pending ? "Создаём…" : "Создать аккаунт"}</button>
        </form>
        <p className="muted">
          Уже есть аккаунт? <Link href="/login">Вход</Link>
        </p>
      </div>
    </div>
  );
}
