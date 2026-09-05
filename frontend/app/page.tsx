"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "../lib/api";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    api("/auth/me")
      .then(() => router.replace("/workspaces"))
      .catch(() => router.replace("/login"));
  }, [router]);

  return <p style={{ padding: "2rem" }}>Перенаправление…</p>;
}
