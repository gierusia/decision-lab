"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, logout } from "../../lib/api";
import type { User, Workspace, WorkspaceRole } from "../../lib/types";

type AdminUserRow = {
  user: User;
  memberships: Array<{ workspace_id: string; workspace_name: string; role: WorkspaceRole }>;
};

export default function PeoplePage() {
  const [me, setMe] = useState<User | null>(null);
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [userId, setUserId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [role, setRole] = useState<"viewer" | "member">("viewer");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function reload() {
    const [people, rooms] = await Promise.all([
      api<AdminUserRow[]>("/admin/users"),
      api<Workspace[]>("/admin/workspaces"),
    ]);
    setRows(people);
    setWorkspaces(rooms);
    if (!userId && people[0]) setUserId(people[0].user.id);
    if (!workspaceId && rooms[0]) setWorkspaceId(rooms[0].id);
  }

  useEffect(() => {
    api<User>("/auth/me")
      .then((user) => {
        setMe(user);
        if (!user.is_admin) {
          setError("Только администратор платформы");
          return;
        }
        return reload();
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось загрузить людей");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onAssign(event: FormEvent) {
    event.preventDefault();
    if (!userId || !workspaceId) return;
    setPending(true);
    setError(null);
    try {
      await api(`/admin/users/${userId}/memberships`, {
        method: "PUT",
        body: JSON.stringify({ workspace_id: workspaceId, role }),
      });
      await reload();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось назначить");
    } finally {
      setPending(false);
    }
  }

  if (!me?.is_admin) {
    return <p className="content">{error ?? "Загрузка…"}</p>;
  }

  return (
    <div className="picker stack" style={{ maxWidth: 880 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h1 className="page-title">Люди</h1>
        <div className="row">
          <Link href="/workspaces">Workspaces</Link>
          <button type="button" className="ghost" onClick={() => logout()}>Выйти</button>
        </div>
      </div>

      <form onSubmit={onAssign} className="filter-panel">
        <select value={userId} onChange={(e) => setUserId(e.target.value)}>
          {rows.map((row) => (
            <option key={row.user.id} value={row.user.id}>
              {row.user.full_name || row.user.email}
            </option>
          ))}
        </select>
        <select value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)}>
          {workspaces.map((room) => (
            <option key={room.id} value={room.id}>
              {room.name}
            </option>
          ))}
        </select>
        <select value={role} onChange={(e) => setRole(e.target.value as "viewer" | "member")}>
          <option value="viewer">viewer</option>
          <option value="member">member</option>
        </select>
        <button type="submit" disabled={pending || workspaces.length === 0}>Назначить</button>
      </form>

      <ul className="list">
        {rows.map((row) => (
          <li key={row.user.id} className="list-card">
            <strong>{row.user.full_name || row.user.email}</strong>
            <div className="muted">{row.user.email}{row.user.is_admin ? " · admin" : ""}</div>
            {row.memberships.length === 0 && <p className="muted">не состоит ни в одном проекте</p>}
            <div className="badges">
              {row.memberships.map((item) => (
                <span key={item.workspace_id} className="badge">
                  {item.workspace_name}: {item.role}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ul>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
