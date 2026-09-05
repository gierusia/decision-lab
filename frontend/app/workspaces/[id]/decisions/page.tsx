"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "../../../../lib/api";
import type {
  Decision,
  DecisionStatus,
  Member,
  User,
  Workspace,
  WorkspaceRole,
} from "../../../../lib/types";

const STATUSES: Array<DecisionStatus | ""> = [
  "",
  "draft",
  "active",
  "needs_revision",
  "completed",
  "cancelled",
];

export default function DecisionsPage() {
  const params = useParams<{ id: string }>();
  const workspaceId = params.id;
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [decisions, setDecisions] = useState<Decision[] | null>(null);
  const [role, setRole] = useState<WorkspaceRole | null>(null);
  const [q, setQ] = useState("");
  const [tag, setTag] = useState("");
  const [status, setStatus] = useState<DecisionStatus | "">("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tagsText, setTagsText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const canEdit = role === "owner" || role === "member";

  function loadDecisions(nextQ = q, nextTag = tag, nextStatus = status) {
    const query = new URLSearchParams();
    if (nextQ.trim()) query.set("q", nextQ.trim());
    if (nextTag.trim()) query.set("tag", nextTag.trim());
    if (nextStatus) query.set("status", nextStatus);
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return api<Decision[]>(`/workspaces/${workspaceId}/decisions${suffix}`);
  }

  useEffect(() => {
    Promise.all([
      api<Workspace>(`/workspaces/${workspaceId}`),
      loadDecisions(),
      api<User>("/auth/me"),
      api<Member[]>(`/workspaces/${workspaceId}/members`),
    ])
      .then(([item, items, me, members]) => {
        setWorkspace(item);
        setDecisions(items);
        setRole(members.find((member) => member.user_id === me.id)?.role ?? null);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось загрузить решения");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  async function onFilter(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      setDecisions(await loadDecisions());
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось отфильтровать");
    }
  }

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!canEdit) return;
    setPending(true);
    setError(null);
    const tags = tagsText
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    try {
      const created = await api<Decision>(`/workspaces/${workspaceId}/decisions`, {
        method: "POST",
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim() || null,
          tags,
        }),
      });
      setDecisions((prev) => [created, ...(prev ?? [])]);
      setTitle("");
      setDescription("");
      setTagsText("");
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось создать решение");
    } finally {
      setPending(false);
    }
  }

  if (!workspace || !decisions) {
    return <p className="muted">{error ?? "Загрузка…"}</p>;
  }

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Решения</h1>
        <p className="muted">{decisions.length} в текущем фильтре</p>
      </div>

      <div className="split">
        <div className="stack">
          {decisions.length === 0 && <p className="muted">По фильтру ничего нет.</p>}
          <ul className="list">
            {decisions.map((decision) => (
              <li key={decision.id}>
                <Link className="decision-card" href={`/workspaces/${workspaceId}/decisions/${decision.id}`}>
                  <div className="decision-card-top">
                    <strong>{decision.title}</strong>
                    <span className="badge accent">{decision.status}</span>
                  </div>
                  {decision.description && <p className="muted clamp">{decision.description}</p>}
                  {decision.tags.length > 0 && (
                    <div className="badges">
                      {decision.tags.map((item) => (
                        <span key={item} className="badge">{item}</span>
                      ))}
                    </div>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <aside className="side-panel stack">
          <section className="panel-block stack">
            <h2>Фильтр</h2>
            <form onSubmit={onFilter} className="stack">
              <input placeholder="поиск" value={q} onChange={(e) => setQ(e.target.value)} />
              <input placeholder="тег" value={tag} onChange={(e) => setTag(e.target.value)} />
              <select value={status} onChange={(e) => setStatus(e.target.value as DecisionStatus | "")}>
                {STATUSES.map((item) => (
                  <option key={item || "all"} value={item}>
                    {item || "все статусы"}
                  </option>
                ))}
              </select>
              <button type="submit">Применить</button>
            </form>
          </section>

          {canEdit && (
            <section className="panel-block stack">
              <h2>Новое решение</h2>
              <form onSubmit={onCreate} className="stack">
                <input required minLength={1} placeholder="название" value={title} onChange={(e) => setTitle(e.target.value)} />
                <textarea placeholder="описание" value={description} onChange={(e) => setDescription(e.target.value)} />
                <input placeholder="теги через запятую" value={tagsText} onChange={(e) => setTagsText(e.target.value)} />
                <button type="submit" disabled={pending}>Создать</button>
              </form>
            </section>
          )}
        </aside>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
