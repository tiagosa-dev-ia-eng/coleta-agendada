"use client";

import { useState } from "react";
import { API_URL } from "@/lib/api";
import { ROLE_HOME, RoleCode, setToken, setDemoRole } from "@/lib/auth";

export interface DemoProfile {
  id: "patient" | "laboratory" | "pharmacy" | "technician" | "reseller";
  tabId: "paciente" | "laboratorio" | "farmacia" | "tecnico" | "revendedor";
  label: string;
  role: RoleCode;
  email: string;
  badge: string;
  icon: string;
  description: string;
  keyFeatures: string[];
}

export const DEMO_PROFILES: DemoProfile[] = [
  {
    id: "patient",
    tabId: "paciente",
    label: "Paciente",
    role: "patient",
    email: "paciente@coleta.local",
    badge: "Solicitante",
    icon: "👤",
    description: "Acompanhamento de orçamentos, aprovação e status das coletas.",
    keyFeatures: ["Orçamentos emitidos", "Aprovação de solicitação", "Histórico de exames"],
  },
  {
    id: "laboratory",
    tabId: "laboratorio",
    label: "Laboratório Central",
    role: "laboratory",
    email: "lab@coleta.local",
    badge: "Gestão Central",
    icon: "🔬",
    description: "Gestão total de orçamentos, calendário multi-formato, exames e auditoria.",
    keyFeatures: ["Calendário Semana/Dia/WhatsApp", "CRUD de exames", "Pontos de Coleta & Auditoria"],
  },
  {
    id: "pharmacy",
    tabId: "farmacia",
    label: "Farmácia Parceira",
    role: "pharmacy",
    email: "farm-lab@demo.local",
    badge: "Ponto de Coleta",
    icon: "💊",
    description: "Atendimento do ponto de coleta, realização de exames e comissões.",
    keyFeatures: ["Agenda de coletas no ponto", "Check-in de paciente", "Canais WhatsApp oficiais"],
  },
  {
    id: "technician",
    tabId: "tecnico",
    label: "Técnico de Enfermagem",
    role: "technician",
    email: "tec@demo.local",
    badge: "Campo / Coleta",
    icon: "🩺",
    description: "Controle de turno de atendimento, rotas de campo e execução das coletas.",
    keyFeatures: ["Abertura/Fechamento de turno", "Atalhos GPS & WhatsApp", "Finalização de coleta"],
  },
  {
    id: "reseller",
    tabId: "revendedor",
    label: "Revendedor Parceiro",
    role: "reseller",
    email: "rev@demo.local",
    badge: "Expansão de Rede",
    icon: "🤝",
    description: "Gestão da rede credenciada de farmácias parceiras e técnicos.",
    keyFeatures: ["Rede credenciada", "Painel de comissões", "Extrato financeiro"],
  },
];

type LoginResp = { access: string; user: { role: { code: string } | null } };

export default function Login({
  onNavigate,
}: {
  onNavigate?: (tab: "paciente" | "laboratorio" | "farmacia" | "tecnico" | "revendedor") => void;
}) {
  const [email, setEmail] = useState("lab@coleta.local");
  const [password, setPassword] = useState("SenhaForte123!");
  const [busy, setBusy] = useState(false);
  const [selectedDemo, setSelectedDemo] = useState<string>("laboratory");
  const [error, setError] = useState("");
  const [successNotice, setSuccessNotice] = useState("");

  // Transição rápida para validação de layout
  const handleDirectDemoAccess = (profile: DemoProfile) => {
    setBusy(true);
    setError("");
    setSuccessNotice(`Acessando layout de ${profile.label}…`);
    setSelectedDemo(profile.id);
    setEmail(profile.email);
    setPassword("SenhaForte123!");

    // Configura o papel simulado e o token correspondente
    setDemoRole(profile.role);
    setToken(`demo_preview_token_${profile.role}`);

    setTimeout(() => {
      if (onNavigate) {
        onNavigate(profile.tabId);
      } else if (typeof window !== "undefined") {
        if (window.location.hash !== undefined) {
          window.location.hash = profile.tabId;
        } else {
          window.location.assign(ROLE_HOME[profile.role] ?? `/${profile.tabId}`);
        }
      }
      setBusy(false);
    }, 200);
  };

  const handleFillCredentials = (profile: DemoProfile) => {
    setEmail(profile.email);
    setPassword("SenhaForte123!");
    setSelectedDemo(profile.id);
    setError("");
    setSuccessNotice(`Credenciais de ${profile.label} preenchidas.`);
  };

  async function doLogin(em: string, pw: string) {
    setBusy(true);
    setError("");
    setSuccessNotice("");

    // Identifica se é algum dos perfis demo conhecidos
    const matchedProfile = DEMO_PROFILES.find((p) => p.email.toLowerCase() === em.toLowerCase());

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: em, password: pw }),
      });

      if (!res.ok) {
        // Se a API externa não respondeu 200, mas é uma conta demo, permite validação sem bloqueio
        if (matchedProfile) {
          setDemoRole(matchedProfile.role);
          setToken(`demo_preview_token_${matchedProfile.role}`);
          if (onNavigate) {
            onNavigate(matchedProfile.tabId);
            return;
          }
          if (typeof window !== "undefined") {
            window.location.hash = matchedProfile.tabId;
            return;
          }
        }
        const data = (await res.json().catch(() => null)) as { error?: { message?: string } } | null;
        setError(data?.error?.message ?? "Falha no login. Verifique as credenciais.");
        return;
      }

      const data = (await res.json()) as LoginResp;
      setToken(data.access);
      const role = (data.user.role?.code ?? "patient") as keyof typeof ROLE_HOME;
      if (matchedProfile) {
        setDemoRole(matchedProfile.role);
      }

      if (onNavigate && matchedProfile) {
        onNavigate(matchedProfile.tabId);
      } else if (typeof window !== "undefined") {
        window.location.assign(ROLE_HOME[role] ?? "/paciente");
      }
    } catch {
      // Fallback gracioso para modo preview do AI Studio
      if (matchedProfile) {
        setDemoRole(matchedProfile.role);
        setToken(`demo_preview_token_${matchedProfile.role}`);
        if (onNavigate) {
          onNavigate(matchedProfile.tabId);
          return;
        }
        if (typeof window !== "undefined") {
          window.location.hash = matchedProfile.tabId;
          return;
        }
      }
      setError("Não foi possível conectar ao backend. Use os botões de demonstração abaixo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        {/* Cabeçalho */}
        <div className="text-center max-w-2xl mx-auto mb-8">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 font-extrabold text-white text-xl shadow-md mb-3">
            CA
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-zinc-900 tracking-tight">
            Coleta Agendada
          </h1>
          <p className="mt-2 text-sm sm:text-base text-zinc-600">
            Validação de layouts e fluxos operacionais por perfil de demonstração.
          </p>
        </div>

        {/* Seção 1: Perfis de Demonstração (Destaque Principal) */}
        <div className="mb-10 rounded-2xl border border-emerald-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-100 pb-4 mb-5">
            <div>
              <h2 className="text-lg font-bold text-zinc-900 flex items-center gap-2">
                <span className="text-xl">🚀</span> Entrar como Demo (1 Clique para Validar Layouts)
              </h2>
              <p className="text-xs sm:text-sm text-zinc-500">
                Selecione qualquer perfil abaixo para abrir instantaneamente o layout e testar todas as funcionalidades.
              </p>
            </div>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
              5 Perfis Disponíveis
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {DEMO_PROFILES.map((prof) => {
              const isSelected = selectedDemo === prof.id;
              return (
                <div
                  key={prof.id}
                  className={`flex flex-col justify-between rounded-xl border p-4 transition-all duration-150 ${
                    isSelected
                      ? "border-emerald-500 bg-emerald-50/40 shadow-xs"
                      : "border-zinc-200 hover:border-zinc-300 bg-white hover:bg-zinc-50/50"
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{prof.icon}</span>
                        <div>
                          <h3 className="text-sm font-bold text-zinc-900">{prof.label}</h3>
                          <span className="text-[11px] font-medium text-emerald-700 bg-emerald-100/70 px-1.5 py-0.5 rounded">
                            {prof.badge}
                          </span>
                        </div>
                      </div>
                    </div>

                    <p className="text-xs text-zinc-600 mt-2 mb-3 leading-relaxed">
                      {prof.description}
                    </p>

                    <div className="space-y-1 border-t border-zinc-100 pt-2.5 mb-3">
                      <div className="text-[11px] text-zinc-500 font-mono flex items-center gap-1 truncate">
                        <span className="text-zinc-400">Login:</span> {prof.email}
                      </div>
                      <div className="text-[11px] text-zinc-400 font-mono">
                        Senha: <span className="text-zinc-600">SenhaForte123!</span>
                      </div>
                    </div>

                    <ul className="mb-4 space-y-1">
                      {prof.keyFeatures.map((feat, idx) => (
                        <li key={idx} className="flex items-center gap-1.5 text-[11px] text-zinc-600">
                          <span className="h-1 w-1 rounded-full bg-emerald-500" />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="pt-2 flex flex-col gap-2">
                    <button
                      type="button"
                      onClick={() => handleDirectDemoAccess(prof)}
                      disabled={busy}
                      className="w-full inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs sm:text-sm font-bold text-white shadow-xs hover:bg-emerald-500 active:scale-[0.98] transition cursor-pointer disabled:opacity-50"
                    >
                      <span>Entrar como {prof.label}</span>
                      <span>→</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleFillCredentials(prof)}
                      className="w-full text-center text-[11px] font-medium text-zinc-500 hover:text-zinc-800 py-1"
                    >
                      Preencher no formulário
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Seção 2: Formulário Tradicional de Login */}
        <div className="mx-auto max-w-md rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-sm">
          <h2 className="text-base font-bold text-zinc-900 mb-1">Acesso Tradicional por E-mail</h2>
          <p className="text-xs text-zinc-500 mb-5">
            Insira suas credenciais ou use um dos perfis pré-preenchidos acima.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              doLogin(email, password);
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                E-mail do Usuário
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="usuario@dominio.com"
                className="w-full rounded-xl border border-zinc-300 px-3.5 py-2.5 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Senha de Acesso
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-zinc-300 px-3.5 py-2.5 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>

            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-medium text-rose-700">
                {error}
              </div>
            )}

            {successNotice && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs font-medium text-emerald-800 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
                {successNotice}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full inline-flex min-h-[46px] items-center justify-center rounded-xl bg-zinc-900 py-3 text-sm font-bold text-white shadow-xs hover:bg-zinc-800 active:scale-[0.98] transition cursor-pointer disabled:opacity-50"
            >
              {busy ? "Autenticando…" : "Entrar no Sistema"}
            </button>
          </form>
        </div>

        {/* Rodapé informativo */}
        <p className="mt-8 text-center text-xs text-zinc-400">
          Coleta Agendada • Ambiente de Demonstração e Homologação • Senha padrão para todos os perfis: <span className="font-mono text-zinc-600">SenhaForte123!</span>
        </p>
      </div>
    </main>
  );
}
