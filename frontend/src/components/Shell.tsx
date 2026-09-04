"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { authedFetch, clearToken, ROLE_LABEL } from "@/lib/auth";
import { API_URL } from "@/lib/api";

type Me = {
  email: string;
  name?: string;
  role: { code: string; name: string } | null;
};

type VersionInfo = {
  name: string;
  version: string;
};

export default function Shell({ children, title }: { children: ReactNode; title?: string }) {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState<string>("1.1.12");

  useEffect(() => {
    authedFetch<Me>("/api/v1/auth/me")
      .then(setMe)
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "erro";
        if (msg.includes("Sessão expirada")) return;
        setError(msg);
      });

    // F-08: Indicador dinâmico de versão da aplicação
    fetch(`${API_URL}/api/v1/version`)
      .then(async (r) => {
        if (r.ok) return (await r.json()) as VersionInfo;
        const r2 = await fetch(`${API_URL}/version`);
        return (await r2.json()) as VersionInfo;
      })
      .then((data) => {
        if (data?.version) setVersion(data.version);
      })
      .catch(() => {});
  }, []);

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-zinc-50 p-6">
        <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>
      </main>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 text-zinc-900">
      <header className="sticky top-0 z-40 border-b border-zinc-200/80 bg-white/95 backdrop-blur-sm shadow-2xs">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div>
            <p className="text-base font-black tracking-tight text-emerald-700">Coleta Agendada</p>
            <p className="text-xs font-medium text-zinc-500">{title ?? (me?.role?.name ?? "…")}</p>
          </div>
          {me && (
            <div className="flex items-center gap-3 text-sm">
              <span className="hidden text-zinc-600 sm:block">
                {me.name || me.email} · <b className="text-zinc-900">{ROLE_LABEL[me.role?.code ?? ""] ?? me.role?.name}</b>
              </span>
              <button
                onClick={clearToken}
                className="rounded-xl border border-zinc-300 bg-zinc-50 px-3 py-1.5 text-xs font-semibold text-zinc-700 transition hover:bg-zinc-100 active:bg-zinc-200"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 space-y-4 px-4 py-6">{children}</main>
      <footer className="mt-auto border-t border-zinc-200/80 bg-white/60 py-4 text-xs text-zinc-500">
        <div className="mx-auto flex max-w-6xl flex-col sm:flex-row items-center justify-between gap-2 px-4">
          <p>Plataforma de Coleta Laboratorial Agendada</p>
          {/* F-08: Versão da aplicação */}
          <div className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1 font-mono text-[11px] text-zinc-600 shadow-2xs">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>v{version}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
