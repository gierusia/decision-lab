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
    <main style={{ maxWidth: 420, margin: "10vh auto", padding: "0 1rem" }}>
      <h1>Вход</h1>
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
          type="password"
          required
          minLength={8}
          autoComplete="current-password"
          placeholder="пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button type="submit" disabled={pending} style={{ padding: "0.6rem" }}>
          {pending ? "Входим…" : "Войти"}
        </button>
      </form>
      <p>
        Нет аккаунта? <Link href="/register">Регистрация</Link>
      </p>
    </main>
  );
}
