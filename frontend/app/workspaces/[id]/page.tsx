"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, logout } from "../../../lib/api";
import type { User, Workspace } from "../../../lib/types";

export default function WorkspaceHomePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const workspaceId = params.id;
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api<User>("/auth/me"), api<Workspace>(`/workspaces/${workspaceId}`)])
      .then(([me, item]) => {
        setUser(me);
        setWorkspace(item);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          return;
        }
        if (err instanceof ApiError && err.status === 403) {
          setError("Нет доступа к этому workspace");
          return;
        }
        if (err instanceof ApiError && err.status === 404) {
          setError("Workspace не найден");
          return;
        }
        setError(err instanceof ApiError ? err.detail : "Не удалось загрузить workspace");
      });
  }, [router, workspaceId]);

  if (error) {
    return (
      <main style={{ padding: "2rem" }}>
        <p>{error}</p>
        <Link href="/workspaces">К списку workspace</Link>
      </main>
    );
  }

  if (!workspace) {
    return <p style={{ padding: "2rem" }}>Загрузка…</p>;
  }

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", padding: "0 1rem" }}>
      <header style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
        <div>
          <p>
            <Link href="/workspaces">Все workspace</Link>
          </p>
          <h1>{workspace.name}</h1>
          <p>{user?.full_name || user?.email}</p>
        </div>
        <button type="button" onClick={() => logout()}>
          Выйти
        </button>
      </header>
      <nav style={{ display: "flex", gap: "1rem", margin: "1rem 0" }}>
        <Link href={`/workspaces/${workspaceId}/decisions`}>Решения</Link>
      </nav>
    </main>
  );
}
