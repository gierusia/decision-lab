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
  const [creating, setCreating] = useState(false);

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
      setCreating(false);
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
    <div className="stack">
      <h1 className="page-title">{summary.title}</h1>

      <div className="badges">
        <span className="badge accent">{summary.status}</span>
        <span className="badge">{summary.readiness}</span>
        {summary.is_stale && <span className="badge warn">stale</span>}
      </div>
      <p className="muted">автор: {summary.author.full_name ?? summary.author.id}</p>

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
          <button type="button" className="danger" disabled={pending} onClick={onDelete}>
            Удалить решение
          </button>
        </p>
      )}

      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>Эксперименты</h2>
        {canEdit && summary.status === "active" && (
          <button type="button" onClick={() => setCreating(true)}>
            Новый опыт
          </button>
        )}
      </div>
      {experiments.length === 0 && <p className="muted">Опытов пока нет.</p>}
      <ul className="list">
            {experiments.map((experiment) => {
              const own = experiment.created_by === userId;
              const canDelete = isOwner;
              const nexts = nextExperimentStatuses(experiment.status);
              const actualValue = actualDraft[experiment.id] ?? experiment.actual_value ?? "";
              return (
                <li key={experiment.id} className="decision-card">
                  <div className="decision-card-top">
                    <strong>{experiment.metric_name}</strong>
                    <span className="badge accent">{experiment.status}</span>
                  </div>
                  <p className="muted">
                    цель {experiment.target_value} · {experiment.metric_direction === "higher_is_better" ? "выше лучше" : "ниже лучше"} · допуск {experiment.partial_tolerance_percent}%
                  </p>
                  <div className="badges">
                    {experiment.verdict && <span className="badge">{experiment.verdict}</span>}
                    {experiment.is_frozen && <span className="badge warn">frozen</span>}
                    {experiment.feature_flag_key && <span className="badge">{experiment.feature_flag_key}</span>}
                  </div>
                  {canEdit && experiment.status === "running" && !experiment.is_frozen && (
                    <input
                      placeholder="actual"
                      value={actualValue}
                      onChange={(e) => setActualDraft((prev) => ({ ...prev, [experiment.id]: e.target.value }))}
                    />
                  )}
                  {experiment.status !== "running" && (
                    <p className="muted">факт: {experiment.actual_value ?? "—"}</p>
                  )}
                  <div className="row">
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
                    {isOwner && experiment.status === "completed" && (
                      <button
                        type="button"
                        className="ghost"
                        disabled={pending}
                        onClick={() => patchExperiment(experiment.id, { is_frozen: !experiment.is_frozen })}
                      >
                        {experiment.is_frozen ? "разморозить" : "заморозить"}
                      </button>
                    )}
                    {canDelete && (
                      <button type="button" className="danger" disabled={pending} onClick={() => onDeleteExperiment(experiment)}>
                        удалить
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>

      {creating && (
        <div className="modal-back" onClick={() => setCreating(false)}>
          <div className="auth-card stack" onClick={(event) => event.stopPropagation()}>
            <h2>Новый опыт</h2>
            <form onSubmit={onCreateExperiment} className="stack">
              <label className="field">
                <span className="muted">метрика</span>
                <input required placeholder="например conversion" value={metricName} onChange={(e) => setMetricName(e.target.value)} />
              </label>
              <label className="field">
                <span className="muted">направление</span>
                <select value={direction} onChange={(e) => setDirection(e.target.value as MetricDirection)}>
                  <option value="higher_is_better">выше — лучше</option>
                  <option value="lower_is_better">ниже — лучше</option>
                </select>
              </label>
              <label className="field">
                <span className="muted">цель (число)</span>
                <input required type="number" step="any" placeholder="100" value={targetValue} onChange={(e) => setTargetValue(e.target.value)} />
              </label>
              <label className="field">
                <span className="muted">допуск %</span>
                <input required type="number" min="0" max="100" step="any" placeholder="5" value={tolerance} onChange={(e) => setTolerance(e.target.value)} />
              </label>
              <div className="row">
                <button type="submit" disabled={pending}>Создать</button>
                <button type="button" className="ghost" onClick={() => setCreating(false)}>Отмена</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
