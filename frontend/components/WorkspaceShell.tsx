"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api, logout } from "../lib/api";
import { Icon } from "./Icon";
import type { User } from "../lib/types";

export default function WorkspaceShell({
  workspaceId,
  workspaceName,
  children,
}: {
  workspaceId: string;
  workspaceName?: string;
  children: React.ReactNode;
}) {
  const path = usePathname();
  const [admin, setAdmin] = useState(false);
  const items = [
    { href: `/workspaces/${workspaceId}`, label: "Обзор", icon: "home", exact: true },
    { href: `/workspaces/${workspaceId}/decisions`, label: "Решения", icon: "list" },
    { href: `/workspaces/${workspaceId}/dashboard`, label: "Дашборд", icon: "chart" },
    { href: `/workspaces/${workspaceId}/members`, label: "Участники", icon: "users" },
  ];

  useEffect(() => {
    api<User>("/auth/me")
      .then((me) => setAdmin(Boolean(me.is_admin)))
      .catch(() => setAdmin(false));
  }, []);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div>
          <div className="brand">DECISION LAB</div>
          {workspaceName && <div className="ws-name">{workspaceName}</div>}
        </div>
        <nav className="nav">
          {items.map((item) => {
            const active = item.exact ? path === item.href : path.startsWith(item.href);
            return (
              <Link key={item.href} href={item.href} className={active ? "active" : undefined}>
                <Icon name={item.icon} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          {admin && (
            <Link href="/people">
              <Icon name="users" />
              <span>Люди</span>
            </Link>
          )}
          <Link href="/profile">
            <Icon name="user" />
            <span>Профиль</span>
          </Link>
          <Link href="/workspaces">
            <Icon name="grid" />
            <span>Все workspace</span>
          </Link>
          <button type="button" className="side-btn" onClick={() => logout()}>
            Выйти
          </button>
        </div>
      </aside>
      <section className="content">{children}</section>
    </div>
  );
}
