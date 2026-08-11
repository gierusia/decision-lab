"use client";

import { useEffect, useState } from "react";

// В браузере запрос идёт на localhost, т.к. порт backend проброшен наружу
// через docker-compose (backend:8000 -> localhost:8000).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type HealthResponse = {
  status: string;
  service: string;
};

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: HealthResponse) => setHealth(data))
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Decision Lab — Этап 0</h1>
      <p>Проверка связки frontend ↔ backend:</p>
      {error && <p style={{ color: "crimson" }}>Ошибка: {error}</p>}
      {!error && !health && <p>Загрузка…</p>}
      {health && (
        <pre style={{ background: "#f4f4f4", padding: "1rem", borderRadius: 8 }}>
          {JSON.stringify(health, null, 2)}
        </pre>
      )}
    </main>
  );
}
