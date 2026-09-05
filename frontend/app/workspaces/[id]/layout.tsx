"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import WorkspaceShell from "../../../components/WorkspaceShell";
import { api } from "../../../lib/api";
import type { Workspace } from "../../../lib/types";

export default function WorkspaceSectionLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ id: string }>();
  const [name, setName] = useState<string>("");

  useEffect(() => {
    api<Workspace>(`/workspaces/${params.id}`)
      .then((item) => setName(item.name))
      .catch(() => setName(""));
  }, [params.id]);

  return (
    <WorkspaceShell workspaceId={params.id} workspaceName={name}>
      {children}
    </WorkspaceShell>
  );
}
