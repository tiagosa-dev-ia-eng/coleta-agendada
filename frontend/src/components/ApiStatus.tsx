"use client";

import { useEffect, useState } from "react";

import { API_URL } from "@/lib/api";

type State =
  | { kind: "checking" }
  | { kind: "ok"; service: string }
  | { kind: "degraded"; message: string };

export default function ApiStatus() {
  const [state, setState] = useState<State>({ kind: "checking" });

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/health`, { signal: controller.signal, cache: "no-store" })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<{ status: string; service: string }>;
      })
      .then((data) => setState({ kind: "ok", service: data.service }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const msg = err instanceof Error ? err.message : "sem resposta";
        setState({ kind: "degraded", message: msg });
      });
    return () => controller.abort();
  }, []);

  if (state.kind === "checking") {
    return <p className="text-sm text-zinc-500">Verificando status da API…</p>;
  }
  if (state.kind === "ok") {
    return (
      <p className="text-sm text-emerald-700">
        <span className="mr-2 inline-block size-2 rounded-full bg-emerald-500 align-middle" />
        API online ({state.service}) — {API_URL}
      </p>
    );
  }
  return (
    <p className="text-sm text-amber-700">
      <span className="mr-2 inline-block size-2 rounded-full bg-amber-500 align-middle" />
      API indisponível em {API_URL} ({state.message}). Suba o backend com{" "}
      <code className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-xs">make dev-backend</code>.
    </p>
  );
}
