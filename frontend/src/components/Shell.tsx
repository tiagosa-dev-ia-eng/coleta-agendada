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
    const handleLogoutEvent = () => setMe(null);
    window.addEventListener("ca:logout", handleLogoutEvent);

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

    return () => {
      window.removeEventListener("ca:logout", handleLogoutEvent);
    };
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
      <header className="sticky top-0 z-40 border-b border-zinc-200/90 bg-white/95 backdrop-blur-md shadow-xs">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          {/* Logo + Título do Sistema e Subtítulo da Página */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-600 font-bold text-white shadow-xs text-sm">
              CA
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-extrabold tracking-tight text-zinc-900 text-sm sm:text-base">
                  Coleta Agendada
                </span>
                {title && (
                  <span className="inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 truncate">
                    {title}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Dados do Usuário Ativo e Botão de Logout */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {me && (
              <div className="hidden md:flex items-center gap-2.5 text-right pl-3 border-l border-zinc-200">
                <div className="text-xs">
                  <p className="font-bold text-zinc-900 truncate max-w-[180px]">
                    {me.name || me.email}
                  </p>
                  <p className="text-[11px] font-medium text-zinc-500">
                    {ROLE_LABEL[me.role?.code ?? ""] ?? me.role?.name}
                  </p>
                </div>
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold ring-2 ring-emerald-500/20">
                  {(me.name || me.email || "U").slice(0, 2).toUpperCase()}
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={clearToken}
              aria-label="Sair da conta e voltar ao login"
              title="Sair da conta e voltar ao login"
              className="inline-flex min-h-[36px] items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50/90 px-3 py-1.5 text-xs font-bold text-rose-700 transition hover:bg-rose-100 active:scale-[0.98] cursor-pointer shadow-2xs"
            >
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              <span>Sair</span>
            </button>
          </div>
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
