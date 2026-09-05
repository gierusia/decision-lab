"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, logout } from "../../lib/api";
import type { User } from "../../lib/types";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [fullName, setFullName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    api<User>("/auth/me")
      .then((me) => {
        setUser(me);
        setFullName(me.full_name ?? "");
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        setError(err instanceof ApiError ? err.detail : "Не удалось загрузить профиль");
      });
  }, []);

  async function onSave(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setSaved(false);
    const body: Record<string, string> = { full_name: fullName };
    if (newPassword) {
      body.current_password = currentPassword;
      body.new_password = newPassword;
    }
    try {
      const updated = await api<User>("/auth/me", {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      setUser(updated);
      setFullName(updated.full_name ?? "");
      setCurrentPassword("");
      setNewPassword("");
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось сохранить");
    } finally {
      setPending(false);
    }
  }

  if (!user) return <p className="content">{error ?? "Загрузка…"}</p>;

  return (
    <div className="picker stack">
      <div className="brand">DECISION LAB</div>
      <h1 className="page-title">Профиль</h1>
      <p className="muted">{user.email}</p>
      <p>
        <Link href="/workspaces">К workspace</Link>
      </p>
      <form onSubmit={onSave} className="stack">
        <input placeholder="имя" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <input type="password" placeholder="текущий пароль (если меняешь)" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
        <input type="password" minLength={8} placeholder="новый пароль" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        <button type="submit" disabled={pending}>Сохранить</button>
      </form>
      {saved && <p className="muted">Сохранено.</p>}
      {error && <p className="error">{error}</p>}
      <button type="button" className="ghost" onClick={() => logout()}>Выйти</button>
    </div>
  );
}
