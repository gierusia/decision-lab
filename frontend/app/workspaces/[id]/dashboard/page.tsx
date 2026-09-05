"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError, logout } from "../../../../lib/api";
import type { DashboardOut, DecisionStatus, Member, Workspace } from "../../../../lib/types";

const STATUSES: Array<DecisionStatus | ""> = [
  "",
  "draft",
  "active",
  "needs_revision",
  "completed",
  "cancelled",
];

function toIso(local: string, end = false): string | null {
  if (!local) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(local)) {
    return end ? `${local}T23:59:59.000Z` : `${local}T00:00:00.000Z`;
  }
  const date = new Date(local);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

export default function DashboardPage() {
  const params = useParams<{ id: string }>();
  const workspaceId = params.id;
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [data, setData] = useState<DashboardOut | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [status, setStatus] = useState<DecisionStatus | "">("");
  const [authorId, setAuthorId] = useState("");
  const [staleOnly, setStaleOnly] = useState(false);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const limit = 20;

  async function load(nextOffset = offset) {
    const query = new URLSearchParams();
    const from = toIso(dateFrom);
    const to = toIso(dateTo, true);
    if (from) query.set("date_from", from);
    if (to) query.set("date_to", to);
    if (status) query.set("status", status);
    if (authorId) query.set("author_id", authorId);
    if (staleOnly) query.set("stale_only", "true");
    query.set("limit", String(limit));
    query.set("offset", String(nextOffset));
    const body = await api<DashboardOut>(`/workspaces/${workspaceId}/dashboard?${query}`);
    setData(body);
    setOffset(nextOffset);
  }

  useEffect(() => {
    Promise.all([
      api<Workspace>(`/workspaces/${workspaceId}`),
      api<Member[]>(`/workspaces/${workspaceId}/members`),
    ])
      .then(([item, people]) => {
        setWorkspace(item);
        setMembers(people);
        return load(0);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось загрузить дашборд");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  async function onFilter(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await load(0);
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Фильтр не применился");
    }
  }

  if (!workspace || !data) {
    return <p style={{ padding: "2rem" }}>{error ?? "Загрузка…"}</p>;
  }

  const totals = data.totals;
  const pageEnd = Math.min(data.pagination.offset + data.pagination.limit, data.pagination.total);

  return (
    <div className="stack">
      <h1 className="page-title">Дашборд</h1>

      <div className="stat-grid">
        <div className="stat-card"><span className="muted">Решения</span><strong>{totals.decisions}</strong></div>
        <div className="stat-card"><span className="muted">Stale</span><strong>{totals.stale}</strong></div>
        <div className="stat-card"><span className="muted">Открытые опыты</span><strong>{totals.experiments_open}</strong></div>
        <div className="stat-card"><span className="muted">Закрытые опыты</span><strong>{totals.experiments_completed}</strong></div>
      </div>
      <p className="meta-line">
        статусы: draft {totals.by_status.draft} · active {totals.by_status.active} · revision {totals.by_status.needs_revision} · done {totals.by_status.completed} · cancel {totals.by_status.cancelled}
        {" · "}
        вердикты: {totals.verdicts.success}/{totals.verdicts.partial}/{totals.verdicts.failed}
      </p>

      <form onSubmit={onFilter} className="filter-panel">
        <label className="field">
          <span>с</span>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>
        <label className="field">
          <span>по</span>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>
        <select value={status} onChange={(e) => setStatus(e.target.value as DecisionStatus | "")}>
          {STATUSES.map((item) => (
            <option key={item || "all"} value={item}>
              {item || "все статусы"}
            </option>
          ))}
        </select>
        <select value={authorId} onChange={(e) => setAuthorId(e.target.value)}>
          <option value="">все авторы</option>
          {members.map((member) => (
            <option key={member.user_id} value={member.user_id}>
              {member.full_name || member.email}
            </option>
          ))}
        </select>
        <label className="check">
          <input type="checkbox" checked={staleOnly} onChange={(e) => setStaleOnly(e.target.checked)} />
          только stale
        </label>
        <button type="submit">Показать</button>
      </form>

      <ul className="list">
        {data.decisions.map((card) => (
          <li key={card.id}>
            <Link className="decision-card" href={`/workspaces/${workspaceId}/decisions/${card.id}`}>
              <div className="decision-card-top">
                <strong>{card.title}</strong>
                <span className="badge accent">{card.status}</span>
              </div>
              <div className="muted">{card.author.full_name ?? "без имени"}</div>
              <div className="badges">
                {card.readiness !== card.status && (
                  <span className="badge">{card.readiness.replaceAll("_", " ")}</span>
                )}
                {card.is_stale && <span className="badge warn">stale</span>}
                <span className="badge">
                  опыты {card.experiment_counts.planned}/{card.experiment_counts.running}/{card.experiment_counts.completed}
                </span>
              </div>
            </Link>
          </li>
        ))}
      </ul>

      {data.pagination.total > limit && (
        <p className="row">
          <span className="muted">
            {data.pagination.offset + 1}–{pageEnd} из {data.pagination.total}
          </span>
          <button type="button" className="ghost" disabled={offset === 0} onClick={() => load(Math.max(0, offset - limit)).catch((err) => setError(String(err)))}>
            назад
          </button>
          <button type="button" className="ghost" disabled={offset + limit >= data.pagination.total} onClick={() => load(offset + limit).catch((err) => setError(String(err)))}>
            вперёд
          </button>
        </p>
      )}
      {data.pagination.total === 0 && <p className="muted">По фильтру решений нет.</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
