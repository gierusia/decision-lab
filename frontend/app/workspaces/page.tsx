"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
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
        if (err instanceof ApiError && err.status === 401) return;
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
    return <p className="content">{error ?? "Загрузка…"}</p>;
  }

  return (
    <div className="picker stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <div className="brand">DECISION LAB</div>
          <h1 className="page-title">Workspaces</h1>
          <p className="muted">{user?.full_name || user?.email}</p>
        </div>
        <div className="row">
          {user?.is_admin && <Link href="/people">Люди</Link>}
          <Link href="/profile">Профиль</Link>
          <button type="button" className="ghost" onClick={() => logout()}>
            Выйти
          </button>
        </div>
      </div>
      {workspaces.length === 0 && (
        <p className="muted">
          {user?.is_admin
            ? "Создайте первый workspace."
            : "Вас ещё не добавили ни в один проект. Когда владелец назначит комнату, она появится здесь."}
        </p>
      )}
      <ul className="list">
        {workspaces.map((workspace) => (
          <li key={workspace.id}>
            <button type="button" className="ghost" style={{ width: "100%", textAlign: "left" }} onClick={() => router.push(`/workspaces/${workspace.id}`)}>
              {workspace.name}
            </button>
          </li>
        ))}
      </ul>
      {user?.is_admin && (
      <form onSubmit={onCreate} className="stack">
        <input required minLength={1} placeholder="Название нового workspace" value={name} onChange={(e) => setName(e.target.value)} />
        <button type="submit" disabled={pending}>Создать</button>
      </form>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
