"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { authedFetch, clearToken, ROLE_LABEL } from "@/lib/auth";

type Me = {
  email: string;
  name?: string;
  role: { code: string; name: string } | null;
};

export default function Shell({ children, title }: { children: ReactNode; title?: string }) {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    authedFetch<Me>("/api/v1/auth/me")
      .then(setMe)
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "erro";
        if (msg.includes("Sessão expirada")) return;
        setError(msg);
      });
  }, []);

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-zinc-50 p-6">
        <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>
      </main>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div>
            <p className="text-sm font-bold text-emerald-700">Coleta Agendada</p>
            <p className="text-xs text-zinc-500">{title ?? (me?.role?.name ?? "…")}</p>
          </div>
          {me && (
            <div className="flex items-center gap-3 text-sm">
              <span className="hidden text-zinc-600 sm:block">
                {me.name || me.email} · <b>{ROLE_LABEL[me.role?.code ?? ""] ?? me.role?.name}</b>
              </span>
              <button onClick={clearToken} className="rounded border border-zinc-300 px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-100">
                Sair
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 space-y-4 px-4 py-6">{children}</main>
      <footer className="py-4 text-center text-xs text-zinc-400">Homologação interna · Coleta Agendada</footer>
    </div>
  );
}
