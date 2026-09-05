"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "../../../../lib/api";
import type { Member, Workspace } from "../../../../lib/types";

export default function MembersPage() {
  const params = useParams<{ id: string }>();
  const workspaceId = params.id;
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api<Workspace>(`/workspaces/${workspaceId}`),
      api<Member[]>(`/workspaces/${workspaceId}/members`),
    ])
      .then(([item, people]) => {
        setWorkspace(item);
        setMembers(people);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) return;
        setError(err instanceof ApiError ? `${err.status}: ${err.detail}` : "Не удалось загрузить участников");
      });
  }, [workspaceId]);

  if (!workspace) {
    return <p className="muted">{error ?? "Загрузка…"}</p>;
  }

  return (
    <div className="stack">
      <h1 className="page-title">Участники</h1>
      <p className="muted">Кто есть в проекте. Назначать роли может только администратор платформы.</p>
      <ul className="list">
        {members.map((member) => (
          <li key={member.id} className="list-card">
            {member.full_name || member.email}
            <div className="badges">
              <span className={member.role === "owner" ? "badge accent" : "badge"}>{member.role}</span>
            </div>
          </li>
        ))}
      </ul>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
