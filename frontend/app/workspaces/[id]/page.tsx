"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "../../../lib/api";
import type { DashboardOut, User, Workspace } from "../../../lib/types";

export default function WorkspaceHomePage() {
  const params = useParams<{ id: string }>();
  const workspaceId = params.id;
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [dash, setDash] = useState<DashboardOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api<User>("/auth/me"),
      api<Workspace>(`/workspaces/${workspaceId}`),
      api<DashboardOut>(`/workspaces/${workspaceId}/dashboard?limit=5&offset=0`),
    ])
      .then(([me, item, board]) => {
        setUser(me);
        setWorkspace(item);
        setDash(board);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        if (err instanceof ApiError && err.status === 403) {
          setError("Нет доступа к этому workspace");
          return;
        }
        setError(err instanceof ApiError ? err.detail : "Не удалось загрузить workspace");
      });
  }, [workspaceId]);

  if (error) return <p className="error">{error}</p>;
  if (!workspace) return <p className="muted">Загрузка…</p>;

  const totals = dash?.totals;

  return (
    <div className="stack">
      <div>
        <p className="muted">workspace</p>
        <h1 className="page-title">{workspace.name}</h1>
        <p className="muted">{user?.full_name || user?.email}</p>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span className="muted">Решения</span>
          <strong>{totals?.decisions ?? "—"}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Stale</span>
          <strong>{totals?.stale ?? "—"}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Открытые опыты</span>
          <strong>{totals?.experiments_open ?? "—"}</strong>
        </div>
        <div className="stat-card">
          <span className="muted">Завершённые опыты</span>
          <strong>{totals?.experiments_completed ?? "—"}</strong>
        </div>
      </div>

      <div className="action-grid">
        <Link className="action-card" href={`/workspaces/${workspaceId}/decisions`}>
          <h2>Решения</h2>
          <p className="muted">Список, фильтры и создание. Сюда же ведёт карточка с дашборда.</p>
        </Link>
        <Link className="action-card" href={`/workspaces/${workspaceId}/dashboard`}>
          <h2>Дашборд</h2>
          <p className="muted">Агрегаты по статусам, stale и лента решений.</p>
        </Link>
        <Link className="action-card" href={`/workspaces/${workspaceId}/members`}>
          <h2>Команда</h2>
          <p className="muted">Роли, инвайт и порог устаревания.</p>
        </Link>
      </div>

      {dash && dash.decisions.length > 0 && (
        <div className="stack">
          <h2>Недавние решения</h2>
          <ul className="list">
            {dash.decisions.map((card) => (
              <li key={card.id}>
                <Link className="decision-card" href={`/workspaces/${workspaceId}/decisions/${card.id}`}>
                  <div className="decision-card-top">
                    <strong>{card.title}</strong>
                    <span className="badge accent">{card.status}</span>
                  </div>
                  <div className="badges">
                    {card.readiness !== card.status && <span className="badge">{card.readiness.replaceAll("_", " ")}</span>}
                    {card.is_stale && <span className="badge warn">stale</span>}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
