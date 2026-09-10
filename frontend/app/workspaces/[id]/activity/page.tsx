"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "../../../../lib/api";
import type { ActivityEntry } from "../../../../lib/types";

export default function ActivityPage() {
  const params = useParams<{ id: string }>();
  const workspaceId = params.id;
  const [entries, setEntries] = useState<ActivityEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<ActivityEntry[]>(`/workspaces/${workspaceId}/activity`)
      .then(setEntries)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось загрузить ленту");
      });
  }, [workspaceId]);

  if (!entries) return <p className="muted">{error ?? "Загрузка…"}</p>;

  return (
    <div className="stack">
      <h1 className="page-title">Лента</h1>
      <p className="muted">Кто что сделал в этой комнате. Без правок текста, только создание, статусы и состав.</p>
      {entries.length === 0 && <p className="muted">Пока пусто.</p>}
      <ul className="list">
        {entries.map((entry) => (
          <li key={entry.id} className="list-card">
            <div>{entry.summary}</div>
            <div className="muted">
              {entry.actor_full_name || entry.actor_email} · {new Date(entry.created_at).toLocaleString()}
            </div>
          </li>
        ))}
      </ul>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
