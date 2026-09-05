"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError, logout } from "../../../../lib/api";
import type { Decision, DecisionStatus, Workspace } from "../../../../lib/types";

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
  const [q, setQ] = useState("");
  const [tag, setTag] = useState("");
  const [status, setStatus] = useState<DecisionStatus | "">("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tagsText, setTagsText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

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
    ])
      .then(([item, items]) => {
        setWorkspace(item);
        setDecisions(items);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          return;
        }
        setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось загрузить решения");
      });
    // first load only
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
    return <p style={{ padding: "2rem" }}>{error ?? "Загрузка…"}</p>;
  }

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", padding: "0 1rem" }}>
      <p>
        <Link href="/workspaces">Все workspace</Link>
        {" · "}
        <Link href={`/workspaces/${workspaceId}`}>{workspace.name}</Link>
      </p>
      <header style={{ display: "flex", justifyContent: "space-between" }}>
        <h1>Решения</h1>
        <button type="button" onClick={() => logout()}>
          Выйти
        </button>
      </header>

      <form onSubmit={onFilter} style={{ display: "grid", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <input
          placeholder="поиск по названию и описанию"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        <input
          placeholder="тег"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value as DecisionStatus | "")} style={{ padding: "0.6rem" }}>
          {STATUSES.map((item) => (
            <option key={item || "all"} value={item}>
              {item || "все статусы"}
            </option>
          ))}
        </select>
        <button type="submit">Фильтровать</button>
      </form>

      {decisions.length === 0 && <p>Решений пока нет.</p>}
      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "0.5rem" }}>
        {decisions.map((decision) => (
          <li key={decision.id} style={{ border: "1px solid #ddd", padding: "0.8rem" }}>
            <strong>{decision.title}</strong>
            <div>
              {decision.status}
              {decision.tags.length ? ` · ${decision.tags.join(", ")}` : ""}
            </div>
          </li>
        ))}
      </ul>

      <h2>Новое решение</h2>
      <form onSubmit={onCreate} style={{ display: "grid", gap: "0.5rem" }}>
        <input
          required
          minLength={1}
          placeholder="название"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{ padding: "0.6rem" }}
        />
        <textarea
          placeholder="описание (необязательно)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{ padding: "0.6rem", minHeight: 80 }}
        />
        <input
          placeholder="теги через запятую"
          value={tagsText}
          onChange={(e) => setTagsText(e.target.value)}
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
