"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, logout } from "../../../../../lib/api";
import { canCloseDecision, nextStatuses } from "../../../../../lib/decisionTransitions";
import { nextExperimentStatuses } from "../../../../../lib/experimentTransitions";
import type {
  DecisionStatus,
  DecisionSummary,
  Experiment,
  Member,
  MetricDirection,
  User,
  WorkspaceRole,
} from "../../../../../lib/types";

export default function DecisionHeaderPage() {
  const params = useParams<{ id: string; decisionId: string }>();
  const router = useRouter();
  const workspaceId = params.id;
  const decisionId = params.decisionId;

  const [summary, setSummary] = useState<DecisionSummary | null>(null);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [userId, setUserId] = useState<string | null>(null);
  const [role, setRole] = useState<WorkspaceRole | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tagsText, setTagsText] = useState("");
  const [metricName, setMetricName] = useState("");
  const [direction, setDirection] = useState<MetricDirection>("higher_is_better");
  const [targetValue, setTargetValue] = useState("");
  const [tolerance, setTolerance] = useState("5");
  const [actualDraft, setActualDraft] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const canEdit = role === "owner" || role === "member";
  const isOwner = role === "owner";
  const closed = summary?.status === "completed" || summary?.status === "cancelled";

  useEffect(() => {
    Promise.all([
      api<DecisionSummary>(`/workspaces/${workspaceId}/decisions/${decisionId}/summary`),
      api<Experiment[]>(`/workspaces/${workspaceId}/decisions/${decisionId}/experiments`),
      api<User>("/auth/me"),
      api<Member[]>(`/workspaces/${workspaceId}/members`),
    ])
      .then(([item, items, me, members]) => {
        setSummary(item);
        setExperiments(items);
        setUserId(me.id);
        setTitle(item.title);
        setDescription(item.description ?? "");
        setTagsText(item.tags.join(", "));
        const mine = members.find((member) => member.user_id === me.id);
        setRole(mine?.role ?? null);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось загрузить решение");
      });
  }, [workspaceId, decisionId]);

  async function reloadAll() {
    const [item, items] = await Promise.all([
      api<DecisionSummary>(`/workspaces/${workspaceId}/decisions/${decisionId}/summary`),
      api<Experiment[]>(`/workspaces/${workspaceId}/decisions/${decisionId}/experiments`),
    ]);
    setSummary(item);
    setExperiments(items);
    setTitle(item.title);
    setDescription(item.description ?? "");
    setTagsText(item.tags.join(", "));
  }

  async function onSave(event: FormEvent) {
    event.preventDefault();
    if (!canEdit || closed) return;
    setPending(true);
    setError(null);
    try {
      await api(`/workspaces/${workspaceId}/decisions/${decisionId}`, {
        method: "PATCH",
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim() || null,
          tags: tagsText
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean),
        }),
      });
      await reloadAll();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось сохранить");
    } finally {
      setPending(false);
    }
  }

  async function onStatus(target: DecisionStatus) {
    if (!summary || !canEdit) return;
    if (!canCloseDecision(target, summary.readiness, role)) return;
    setPending(true);
    setError(null);
    try {
      await api(`/workspaces/${workspaceId}/decisions/${decisionId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: target }),
      });
      await reloadAll();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось сменить статус");
    } finally {
      setPending(false);
    }
  }

  async function onDelete() {
    if (!isOwner) return;
    if (!window.confirm("Удалить решение и его эксперименты?")) return;
    setPending(true);
    setError(null);
    try {
      await api(`/workspaces/${workspaceId}/decisions/${decisionId}`, { method: "DELETE" });
      router.replace(`/workspaces/${workspaceId}/decisions`);
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось удалить");
      setPending(false);
    }
  }

  const expBase = `/workspaces/${workspaceId}/decisions/${decisionId}/experiments`;

  async function onCreateExperiment(event: FormEvent) {
    event.preventDefault();
    if (!canEdit || summary?.status !== "active") return;
    setPending(true);
    setError(null);
    try {
      await api(expBase, {
        method: "POST",
        body: JSON.stringify({
          metric_name: metricName.trim(),
          metric_direction: direction,
          target_value: targetValue,
          partial_tolerance_percent: tolerance,
        }),
      });
      setMetricName("");
      setTargetValue("");
      setTolerance("5");
      await reloadAll();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось создать опыт");
    } finally {
      setPending(false);
    }
  }

  async function patchExperiment(id: string, body: Record<string, unknown>) {
    setPending(true);
    setError(null);
    try {
      await api(`${expBase}/${id}`, { method: "PATCH", body: JSON.stringify(body) });
      await reloadAll();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось обновить опыт");
    } finally {
      setPending(false);
    }
  }

  async function onDeleteExperiment(experiment: Experiment) {
    const own = experiment.created_by === userId;
    if (!isOwner && !own) return;
    if (!window.confirm("Удалить эксперимент?")) return;
    setPending(true);
    setError(null);
    try {
      await api(`${expBase}/${experiment.id}`, { method: "DELETE" });
      await reloadAll();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось удалить опыт");
    } finally {
      setPending(false);
    }
  }

  if (!summary) {
    return <p style={{ padding: "2rem" }}>{error ?? "Загрузка…"}</p>;
  }

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", padding: "0 1rem" }}>
      <p>
        <Link href={`/workspaces/${workspaceId}/decisions`}>К списку решений</Link>
      </p>
      <header style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
        <h1>{summary.title}</h1>
        <button type="button" onClick={() => logout()}>
          Выйти
        </button>
      </header>

      <p>
        статус: {summary.status}
        {" · "}
        readiness: {summary.readiness}
        {summary.is_stale ? " · stale" : ""}
      </p>
      <p>автор: {summary.author.full_name ?? summary.author.id}</p>

      {canEdit && !closed && (
        <form onSubmit={onSave} style={{ display: "grid", gap: "0.5rem", margin: "1rem 0" }}>
          <input required value={title} onChange={(e) => setTitle(e.target.value)} style={{ padding: "0.6rem" }} />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{ padding: "0.6rem", minHeight: 80 }}
          />
          <input
            value={tagsText}
            onChange={(e) => setTagsText(e.target.value)}
            placeholder="теги через запятую"
            style={{ padding: "0.6rem" }}
          />
          <button type="submit" disabled={pending}>
            Сохранить
          </button>
        </form>
      )}

      {(!canEdit || closed) && (
        <div>
          <p>{summary.description}</p>
          <p>{summary.tags.join(", ")}</p>
        </div>
      )}

      {canEdit && nextStatuses(summary.status).length > 0 && (
        <p style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {nextStatuses(summary.status).map((target) => {
            const blocked = !canCloseDecision(target, summary.readiness, role);
            return (
              <button
                key={target}
                type="button"
                disabled={pending || blocked}
                title={blocked ? "Сначала закройте или удалите открытые эксперименты" : undefined}
                onClick={() => onStatus(target)}
              >
                → {target}
              </button>
            );
          })}
        </p>
      )}

      {isOwner && !closed && (
        <p>
          <button type="button" disabled={pending} onClick={onDelete}>
            Удалить решение
          </button>
        </p>
      )}

      <h2>Эксперименты</h2>
      {experiments.length === 0 && <p>Опытов пока нет.</p>}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["metric", "dir", "target", "actual", "tol%", "status", "verdict", "flag", "frozen", ""].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: "0.3rem" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {experiments.map((experiment) => {
              const own = experiment.created_by === userId;
              const canDelete = isOwner || own;
              const nexts = nextExperimentStatuses(experiment.status);
              const actualValue = actualDraft[experiment.id] ?? experiment.actual_value ?? "";
              return (
                <tr key={experiment.id}>
                  <td style={{ padding: "0.3rem" }}>{experiment.metric_name}</td>
                  <td style={{ padding: "0.3rem" }}>{experiment.metric_direction === "higher_is_better" ? "↑" : "↓"}</td>
                  <td style={{ padding: "0.3rem" }}>{experiment.target_value}</td>
                  <td style={{ padding: "0.3rem" }}>
                    {canEdit && experiment.status === "running" && !experiment.is_frozen ? (
                      <input
                        value={actualValue}
                        onChange={(e) =>
                          setActualDraft((prev) => ({ ...prev, [experiment.id]: e.target.value }))
                        }
                        style={{ width: 80 }}
                      />
                    ) : (
                      experiment.actual_value ?? "—"
                    )}
                  </td>
                  <td style={{ padding: "0.3rem" }}>{experiment.partial_tolerance_percent}</td>
                  <td style={{ padding: "0.3rem" }}>{experiment.status}</td>
                  <td style={{ padding: "0.3rem" }}>{experiment.verdict ?? "—"}</td>
                  <td style={{ padding: "0.3rem" }}>{experiment.feature_flag_key ?? "—"}</td>
                  <td style={{ padding: "0.3rem" }}>
                    {experiment.is_frozen ? "yes" : "no"}
                    {isOwner && experiment.status === "completed" && (
                      <button
                        type="button"
                        disabled={pending}
                        onClick={() => patchExperiment(experiment.id, { is_frozen: !experiment.is_frozen })}
                      >
                        {experiment.is_frozen ? "снять" : "заморозить"}
                      </button>
                    )}
                  </td>
                  <td style={{ padding: "0.3rem" }}>
                    {canEdit &&
                      nexts.map((target) => {
                        const needsActual = target === "completed";
                        const actual = actualDraft[experiment.id] ?? experiment.actual_value;
                        const missing = needsActual && (actual === undefined || actual === null || actual === "");
                        return (
                          <button
                            key={target}
                            type="button"
                            disabled={pending || experiment.is_frozen || missing || summary.status !== "active"}
                            onClick={() => {
                              const body: Record<string, unknown> = { status: target };
                              if (needsActual) body.actual_value = actual;
                              patchExperiment(experiment.id, body);
                            }}
                          >
                            → {target}
                          </button>
                        );
                      })}
                    {canDelete && (
                      <button type="button" disabled={pending} onClick={() => onDeleteExperiment(experiment)}>
                        удалить
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {canEdit && summary.status === "active" && (
        <form onSubmit={onCreateExperiment} style={{ display: "grid", gap: "0.5rem", marginTop: "1rem" }}>
          <h3>Новый опыт</h3>
          <input
            required
            placeholder="метрика"
            value={metricName}
            onChange={(e) => setMetricName(e.target.value)}
            style={{ padding: "0.6rem" }}
          />
          <select value={direction} onChange={(e) => setDirection(e.target.value as MetricDirection)}>
            <option value="higher_is_better">выше — лучше</option>
            <option value="lower_is_better">ниже — лучше</option>
          </select>
          <input
            required
            placeholder="цель"
            value={targetValue}
            onChange={(e) => setTargetValue(e.target.value)}
            style={{ padding: "0.6rem" }}
          />
          <input
            required
            placeholder="допуск %"
            value={tolerance}
            onChange={(e) => setTolerance(e.target.value)}
            style={{ padding: "0.6rem" }}
          />
          <button type="submit" disabled={pending}>
            Добавить опыт
          </button>
        </form>
      )}

      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </main>
  );
}
