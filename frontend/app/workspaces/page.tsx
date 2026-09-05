"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, logout } from "../../lib/api";
import type { User, Workspace } from "../../lib/types";

export default function WorkspacesPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[] | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    Promise.all([api<User>("/auth/me"), api<Workspace[]>("/workspaces")])
      .then(([me, items]) => {
        setUser(me);
        setWorkspaces(items);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          return;
        }
        setError(err instanceof ApiError ? err.detail : "Не удалось загрузить данные");
      });
  }, [router]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const created = await api<Workspace>("/workspaces/", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
      });
      setWorkspaces((prev) => [...(prev ?? []), created]);
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось создать workspace");
    } finally {
      setPending(false);
    }
  }

  if (!workspaces) {
    return <p style={{ padding: "2rem" }}>{error ?? "Загрузка…"}</p>;
  }

  return (
    <main style={{ maxWidth: 640, margin: "4rem auto", padding: "0 1rem" }}>
      <header style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
        <div>
          <h1>Workspaces</h1>
          <p>{user?.full_name || user?.email}</p>
        </div>
        <button type="button" onClick={() => logout()}>
          Выйти
        </button>
      </header>

      {workspaces.length === 0 && <p>Пока нет workspace — создайте первый.</p>}

      <ul style={{ padding: 0, listStyle: "none", display: "grid", gap: "0.5rem" }}>
        {workspaces.map((workspace) => (
          <li key={workspace.id}>
            <button
              type="button"
              onClick={() => router.push(`/workspaces/${workspace.id}`)}
              style={{ width: "100%", textAlign: "left", padding: "0.8rem" }}
            >
              {workspace.name}
            </button>
          </li>
        ))}
      </ul>

      <form onSubmit={onCreate} style={{ display: "grid", gap: "0.5rem", marginTop: "1.5rem" }}>
        <input
          required
          minLength={1}
          placeholder="Название нового workspace"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        <button type="submit" disabled={pending}>
          Создать
        </button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </main>
  );
}
