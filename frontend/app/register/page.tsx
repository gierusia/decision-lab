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
    <main style={{ maxWidth: 420, margin: "10vh auto", padding: "0 1rem" }}>
      <h1>Регистрация</h1>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: "0.75rem" }}>
        <input
          type="email"
          required
          autoComplete="username"
          placeholder="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        <input
          placeholder="имя (необязательно)"
          autoComplete="name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        <input
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          placeholder="пароль, минимум 8 символов"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button type="submit" disabled={pending} style={{ padding: "0.6rem" }}>
          {pending ? "Создаём…" : "Создать аккаунт"}
        </button>
      </form>
      <p>
        Уже есть аккаунт? <Link href="/login">Вход</Link>
      </p>
    </main>
  );
}
