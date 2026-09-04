"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";
import { ROLE_HOME, RoleCode, setToken, setDemoRole, clearToken, getToken } from "@/lib/auth";

export interface DemoProfile {
  id: "patient" | "laboratory" | "pharmacy" | "technician" | "reseller";
  tabId: "paciente" | "laboratorio" | "farmacia" | "tecnico" | "revendedor";
  label: string;
  role: RoleCode;
  email: string;
  category: "admin" | "field" | "client";
  badge: string;
  icon: string;
  description: string;
  keyFeatures: string[];
}

export const DEMO_PROFILES: DemoProfile[] = [
  {
    id: "laboratory",
    tabId: "laboratorio",
    label: "Laboratório Central",
    role: "laboratory",
    email: "lab@coleta.local",
    category: "admin",
    badge: "Gestão Central",
    icon: "🔬",
    description: "Gestão total de orçamentos, calendário multi-formato, exames, pontos e auditoria.",
    keyFeatures: ["Calendário Semana/Dia/WhatsApp", "CRUD de exames", "Pontos de Coleta & Auditoria"],
  },
  {
    id: "pharmacy",
    tabId: "farmacia",
    label: "Farmácia Parceira",
    role: "pharmacy",
    email: "farm-lab@demo.local",
    category: "field",
    badge: "Ponto de Coleta",
    icon: "💊",
    description: "Atendimento do ponto de coleta, realização de exames e canais WhatsApp.",
    keyFeatures: ["Agenda de coletas no ponto", "Check-in de paciente", "Canais WhatsApp oficiais"],
  },
  {
    id: "technician",
    tabId: "tecnico",
    label: "Técnico de Enfermagem",
    role: "technician",
    email: "tec@demo.local",
    category: "field",
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
    category: "admin",
    badge: "Expansão de Rede",
    icon: "🤝",
    description: "Gestão da rede credenciada de farmácias parceiras e técnicos.",
    keyFeatures: ["Rede credenciada", "Painel de comissões", "Extrato financeiro"],
  },
  {
    id: "patient",
    tabId: "paciente",
    label: "Paciente",
    role: "patient",
    email: "paciente@coleta.local",
    category: "client",
    badge: "Solicitante",
    icon: "👤",
    description: "Acompanhamento de orçamentos, aprovação e status das coletas.",
    keyFeatures: ["Orçamentos emitidos", "Aprovação de solicitação", "Histórico de exames"],
  },
];

type LoginResp = { access: string; user: { role: { code: string } | null } };

export default function Login({
  onNavigate,
}: {
  onNavigate?: (tab: "paciente" | "laboratorio" | "farmacia" | "tecnico" | "revendedor") => void;
}) {
  const [activeMode, setActiveMode] = useState<"demo" | "form">("demo");
  const [demoCategory, setDemoCategory] = useState<"all" | "admin" | "field" | "client">("all");
  const [email, setEmail] = useState("lab@coleta.local");
  const [password, setPassword] = useState("SenhaForte123!");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [busy, setBusy] = useState(false);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("laboratory");
  const [error, setError] = useState("");
  const [successNotice, setSuccessNotice] = useState("");
  const [existingToken, setExistingToken] = useState<string | null>(null);

  useEffect(() => {
    setExistingToken(getToken());
  }, []);

  const selectedProfile =
    DEMO_PROFILES.find((p) => p.id === selectedProfileId) ?? DEMO_PROFILES[0];

  // Acesso Direto com 1 clique (para validação rápida de layout)
  const handleDirectDemoAccess = (profile: DemoProfile) => {
    setBusy(true);
    setError("");
    setSuccessNotice(`Entrando no layout de ${profile.label}…`);
    setSelectedProfileId(profile.id);
    setEmail(profile.email);
    setPassword("SenhaForte123!");

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
    }, 180);
  };

  // Preencher dados na aba de formulário manual
  const handleSelectProfileForForm = (profile: DemoProfile) => {
    setSelectedProfileId(profile.id);
    setEmail(profile.email);
    setPassword("SenhaForte123!");
    setError("");
    setSuccessNotice(`Credenciais de ${profile.label} carregadas no formulário.`);
  };

  const handleClearForm = () => {
    setEmail("");
    setPassword("");
    setError("");
    setSuccessNotice("Formulário limpo.");
  };

  const handleLogoutExisting = () => {
    clearToken();
    setExistingToken(null);
    setSuccessNotice("Sessão anterior encerrada com sucesso.");
  };

  async function doLogin(em: string, pw: string) {
    setBusy(true);
    setError("");
    setSuccessNotice("");

    const matchedProfile = DEMO_PROFILES.find(
      (p) => p.email.toLowerCase() === em.trim().toLowerCase()
    );

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: em.trim(), password: pw }),
      });

      if (!res.ok) {
        // Se a chamada de rede falhou ou backend não está rodando no preview, mas é demo válida
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
        setError(data?.error?.message ?? "Falha na autenticação. Verifique e-mail e senha.");
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
      // Fallback para modo mock do AI Studio
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
      setError("Não foi possível conectar à API de autenticação. Use os perfis de demonstração abaixo.");
    } finally {
      setBusy(false);
    }
  }

  const filteredProfiles = DEMO_PROFILES.filter((p) => {
    if (demoCategory === "all") return true;
    return p.category === demoCategory;
  });

  return (
    <main className="min-h-screen bg-zinc-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        {/* Banner de Sessão Ativa (com botão de Logout rápido) */}
        {existingToken && (
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 text-xs text-emerald-900 shadow-2xs">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
              <span>
                Você possui uma sessão ativa no navegador. Deseja retornar ao painel ou encerrar?
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  if (onNavigate) onNavigate("laboratorio");
                  else if (typeof window !== "undefined") window.location.hash = "laboratorio";
                }}
                className="rounded-xl bg-emerald-700 px-3 py-1.5 font-bold text-white hover:bg-emerald-600 transition cursor-pointer"
              >
                Voltar ao Painel →
              </button>
              <button
                type="button"
                onClick={handleLogoutExisting}
                className="rounded-xl border border-rose-200 bg-white px-3 py-1.5 font-bold text-rose-700 hover:bg-rose-50 transition cursor-pointer flex items-center gap-1"
              >
                <svg className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                <span>Fazer Logout</span>
              </button>
            </div>
          </div>
        )}

        {/* Cabeçalho */}
        <div className="text-center max-w-2xl mx-auto mb-8">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 font-extrabold text-white text-xl shadow-md mb-2">
            CA
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-zinc-900 tracking-tight">
            Coleta Agendada
          </h1>
          <p className="mt-1 text-sm sm:text-base text-zinc-600">
            Acesso ao sistema e validação de layouts por perfil operacional.
          </p>

          {/* Abas de Navegação Principal do Login */}
          <div className="mt-5 inline-flex p-1 rounded-2xl bg-zinc-200/80 border border-zinc-300/60 shadow-inner">
            <button
              type="button"
              onClick={() => setActiveMode("demo")}
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs sm:text-sm font-bold transition-all cursor-pointer ${
                activeMode === "demo"
                  ? "bg-white text-zinc-900 shadow-xs"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              <span>🚀</span>
              <span>Perfis Demo (1 Clique)</span>
              <span className="rounded-full bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 font-semibold">
                5 Perfis
              </span>
            </button>
            <button
              type="button"
              onClick={() => setActiveMode("form")}
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs sm:text-sm font-bold transition-all cursor-pointer ${
                activeMode === "form"
                  ? "bg-white text-zinc-900 shadow-xs"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              <span>🔐</span>
              <span>Formulário Tradicional</span>
            </button>
          </div>
        </div>

        {/* MODO 1: PERFIS DEMO (VALIDAÇÃO RÁPIDA DE LAYOUT) */}
        {activeMode === "demo" && (
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 shadow-xs">
            {/* Filtros de Categorias para Navegação Rápida */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 pb-4 mb-5">
              <div>
                <h2 className="text-base sm:text-lg font-bold text-zinc-900 flex items-center gap-2">
                  <span>Escolha o Perfil para Validar o Layout</span>
                </h2>
                <p className="text-xs text-zinc-500">
                  Clique no botão verde do perfil desejado para acessar o painel imediatamente.
                </p>
              </div>

              {/* Filtros de Navegação */}
              <div className="flex flex-wrap items-center gap-1.5">
                {[
                  { id: "all", label: "Todos (5)" },
                  { id: "admin", label: "Laboratório & Revenda" },
                  { id: "field", label: "Farmácia & Técnico" },
                  { id: "client", label: "Paciente" },
                ].map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setDemoCategory(cat.id as any)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition cursor-pointer ${
                      demoCategory === cat.id
                        ? "bg-emerald-600 text-white shadow-xs"
                        : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Grid de Cartões Demo */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredProfiles.map((prof) => (
                <div
                  key={prof.id}
                  className="flex flex-col justify-between rounded-xl border border-zinc-200 bg-white p-4 hover:border-emerald-300 hover:shadow-xs transition-all duration-150"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2.5">
                        <span className="text-2xl p-1.5 rounded-xl bg-zinc-100">{prof.icon}</span>
                        <div>
                          <h3 className="text-sm font-bold text-zinc-900 leading-tight">
                            {prof.label}
                          </h3>
                          <span className="inline-block text-[10px] font-semibold text-emerald-800 bg-emerald-100/80 px-1.5 py-0.5 rounded mt-0.5">
                            {prof.badge}
                          </span>
                        </div>
                      </div>
                    </div>

                    <p className="text-xs text-zinc-600 mt-2 mb-3 leading-relaxed">
                      {prof.description}
                    </p>

                    <div className="rounded-lg bg-zinc-50 border border-zinc-100 p-2 text-[11px] font-mono text-zinc-600 mb-3 space-y-0.5">
                      <div className="truncate">
                        <span className="text-zinc-400 font-sans">E-mail:</span> {prof.email}
                      </div>
                      <div>
                        <span className="text-zinc-400 font-sans">Senha:</span> SenhaForte123!
                      </div>
                    </div>

                    <ul className="mb-4 space-y-1">
                      {prof.keyFeatures.map((feat, idx) => (
                        <li key={idx} className="flex items-center gap-1.5 text-[11px] text-zinc-600">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
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
                      onClick={() => {
                        handleSelectProfileForForm(prof);
                        setActiveMode("form");
                      }}
                      className="w-full text-center text-[11px] font-medium text-zinc-500 hover:text-emerald-700 py-1 transition"
                    >
                      Editar credenciais no formulário →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* MODO 2: FORMULÁRIO TRADICIONAL COM NAVEGAÇÃO APERFEIÇOADA */}
        {activeMode === "form" && (
          <div className="mx-auto max-w-xl rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-xs">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-4 mb-5">
              <div>
                <h2 className="text-base font-bold text-zinc-900">Formulário de Acesso Manual</h2>
                <p className="text-xs text-zinc-500">
                  Preencha os campos ou clique em um dos atalhos rápidos abaixo.
                </p>
              </div>
              <button
                type="button"
                onClick={handleClearForm}
                className="text-xs font-semibold text-zinc-500 hover:text-rose-600 transition"
              >
                Limpar Campos
              </button>
            </div>

            {/* Chips de Seleção Rápida de Perfil (Navegação Instantânea) */}
            <div className="mb-5">
              <label className="block text-[11px] font-bold text-zinc-500 uppercase tracking-wider mb-2">
                Atalhos Rápidos de Preenchimento:
              </label>
              <div className="flex flex-wrap gap-1.5">
                {DEMO_PROFILES.map((p) => {
                  const isCurrent = email === p.email;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => handleSelectProfileForForm(p)}
                      className={`inline-flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold transition cursor-pointer ${
                        isCurrent
                          ? "border border-emerald-400 bg-emerald-50 text-emerald-800 ring-2 ring-emerald-500/20"
                          : "border border-zinc-200 bg-zinc-50 text-zinc-700 hover:bg-zinc-100"
                      }`}
                    >
                      <span>{p.icon}</span>
                      <span>{p.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Formulário Principal */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                doLogin(email, password);
              }}
              className="space-y-4"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label htmlFor="login-email" className="text-xs font-bold text-zinc-700">
                    E-mail de Acesso
                  </label>
                  {selectedProfile && (
                    <span className="text-[11px] text-emerald-700 font-medium">
                      Perfil: <strong>{selectedProfile.label}</strong>
                    </span>
                  )}
                </div>
                <div className="relative">
                  <input
                    id="login-email"
                    type="email"
                    required
                    autoFocus
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="usuario@coletaagendada.com.br"
                    className="w-full rounded-xl border border-zinc-300 px-3.5 py-2.5 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                  />
                  {email && (
                    <button
                      type="button"
                      onClick={() => setEmail("")}
                      className="absolute right-3 top-2.5 text-zinc-400 hover:text-zinc-600 text-xs"
                      title="Limpar e-mail"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label htmlFor="login-password" className="text-xs font-bold text-zinc-700">
                    Senha
                  </label>
                  <span className="text-[11px] text-zinc-400">Padrão demo: SenhaForte123!</span>
                </div>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-zinc-300 px-3.5 py-2.5 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-xs font-medium text-zinc-500 hover:text-zinc-800"
                    title={showPassword ? "Ocultar senha" : "Ver senha"}
                  >
                    {showPassword ? "Ocultar" : "Mostrar"}
                  </button>
                </div>
              </div>

              {/* Opções de Navegação e Lembrança */}
              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center gap-2 text-xs text-zinc-600 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Lembrar credenciais</span>
                </label>

                <button
                  type="button"
                  onClick={() => {
                    if (selectedProfile) handleDirectDemoAccess(selectedProfile);
                  }}
                  className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 transition"
                >
                  Entrar direto com 1 clique →
                </button>
              </div>

              {/* Mensagens de Erro ou Sucesso */}
              {error && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-medium text-rose-700 flex items-center justify-between">
                  <span>{error}</span>
                  <button type="button" onClick={() => setError("")} className="text-rose-500 hover:text-rose-800">
                    ✕
                  </button>
                </div>
              )}

              {successNotice && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs font-medium text-emerald-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
                    <span>{successNotice}</span>
                  </div>
                  <button type="button" onClick={() => setSuccessNotice("")} className="text-emerald-600 hover:text-emerald-900">
                    ✕
                  </button>
                </div>
              )}

              {/* Ações do Formulário */}
              <div className="space-y-2 pt-2">
                <button
                  type="submit"
                  disabled={busy}
                  className="w-full inline-flex min-h-[46px] items-center justify-center gap-2 rounded-xl bg-zinc-900 py-3 text-sm font-bold text-white shadow-xs hover:bg-zinc-800 active:scale-[0.98] transition cursor-pointer disabled:opacity-50"
                >
                  {busy ? (
                    <>
                      <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                      <span>Autenticando…</span>
                    </>
                  ) : (
                    <span>Entrar no Sistema</span>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setActiveMode("demo")}
                  className="w-full text-center text-xs text-zinc-500 hover:text-zinc-800 py-2"
                >
                  ← Voltar para lista de perfis demo
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Rodapé informativo */}
        <p className="mt-8 text-center text-xs text-zinc-400">
          Coleta Agendada • Ambiente de Demonstração e Homologação • Senha padrão para todos os perfis: <span className="font-mono text-zinc-600">SenhaForte123!</span>
        </p>
      </div>
    </main>
  );
}
