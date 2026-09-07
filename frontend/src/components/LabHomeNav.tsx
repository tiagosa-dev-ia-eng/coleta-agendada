"use client";

import { useState } from "react";
import { Button, Card } from "@/components/ui";
import WhatsAppContactsCard from "@/components/WhatsAppContactsCard";

export type LabView =
  | "home"
  | "dashboard"
  | "points"
  | "quotes"
  | "calendar"
  | "exams"
  | "resellers"
  | "audit"
  | "users";

export type LabRole = "admin" | "attendant";

interface LabHomeNavProps {
  currentRole: LabRole;
  onRoleChange: (role: LabRole) => void;
  onNavigate: (view: LabView) => void;
  counts: {
    requests: number;
    queue: number;
    points: number;
    exams: number;
    resellers: number;
    auditLogs: number;
    users: number;
  };
}

export default function LabHomeNav({
  currentRole,
  onRoleChange,
  onNavigate,
  counts,
}: LabHomeNavProps) {
  const [deniedModal, setDeniedModal] = useState<string | null>(null);

  const isAdmin = currentRole === "admin";

  // Módulos solicitados na demanda
  const modules = [
    {
      id: "dashboard" as LabView,
      title: "Dashboard",
      description: "Indicadores em tempo real, volume de coletas e agendamentos diários",
      icon: "📊",
      allowedRoles: ["admin", "attendant"],
      roleBadge: "Admin / Atendente",
      badgeColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
      accentBorder: "hover:border-emerald-500",
      accentBg: "hover:bg-emerald-50/40",
      metric: "KPIs e Gráficos",
      highlight: true,
    },
    {
      id: "points" as LabView,
      title: "Pontos de Coleta",
      description: "Unidades próprias e parceiras, janelas de horário e técnicos de enfermagem",
      icon: "📍",
      allowedRoles: ["admin"],
      roleBadge: "Apenas Admin",
      badgeColor: "bg-purple-100 text-purple-800 border-purple-200",
      accentBorder: "hover:border-purple-500",
      accentBg: "hover:bg-purple-50/40",
      metric: `${counts.points} cadastrados`,
      highlight: false,
    },
    {
      id: "quotes" as LabView,
      title: "Validação de Orçamentos",
      description: "Triagem humana de pedidos de exames, precificação e aprovação de pedidos",
      icon: "📋",
      allowedRoles: ["admin", "attendant"],
      roleBadge: "Admin / Atendente",
      badgeColor: "bg-blue-100 text-blue-800 border-blue-200",
      accentBorder: "hover:border-blue-500",
      accentBg: "hover:bg-blue-50/40",
      metric: `${counts.queue} na fila`,
      highlight: counts.queue > 0,
    },
    {
      id: "calendar" as LabView,
      title: "Calendário Integrado",
      description: "Visualização diária, semanal e WhatsApp das coletas agendadas",
      icon: "📅",
      allowedRoles: ["admin", "attendant"],
      roleBadge: "Admin / Atendente",
      badgeColor: "bg-blue-100 text-blue-800 border-blue-200",
      accentBorder: "hover:border-sky-500",
      accentBg: "hover:bg-sky-50/40",
      metric: "Agenda ao vivo",
      highlight: false,
    },
    {
      id: "exams" as LabView,
      title: "Exames e Tabela de Preços",
      description: "Cadastro de exames, valores do laboratório e ativação no catálogo",
      icon: "🧪",
      allowedRoles: ["admin", "attendant"],
      roleBadge: "Admin / Atendente",
      badgeColor: "bg-blue-100 text-blue-800 border-blue-200",
      accentBorder: "hover:border-indigo-500",
      accentBg: "hover:bg-indigo-50/40",
      metric: `${counts.exams} exames`,
      highlight: false,
    },
    {
      id: "resellers" as LabView,
      title: "Gestão de Revendedores",
      description: "Cadastro e ativação de parceiros comerciais e redes de distribuição",
      icon: "🤝",
      allowedRoles: ["admin"],
      roleBadge: "Apenas Admin",
      badgeColor: "bg-purple-100 text-purple-800 border-purple-200",
      accentBorder: "hover:border-purple-500",
      accentBg: "hover:bg-purple-50/40",
      metric: `${counts.resellers} parceiros`,
      highlight: false,
    },
    {
      id: "audit" as LabView,
      title: "Trilha de Auditoria",
      description: "Histórico completo de ações, conformidade LGPD e segurança operacional",
      icon: "🛡️",
      allowedRoles: ["admin"],
      roleBadge: "Apenas Admin",
      badgeColor: "bg-purple-100 text-purple-800 border-purple-200",
      accentBorder: "hover:border-zinc-500",
      accentBg: "hover:bg-zinc-50/80",
      metric: `${counts.auditLogs} eventos`,
      highlight: false,
    },
    {
      id: "users" as LabView,
      title: "Cadastro de Usuários",
      description: "Gestão de credenciais, administradores, atendentes e técnicos de coleta",
      icon: "👥",
      allowedRoles: ["admin"],
      roleBadge: "Apenas Admin",
      badgeColor: "bg-purple-100 text-purple-800 border-purple-200",
      accentBorder: "hover:border-purple-500",
      accentBg: "hover:bg-purple-50/40",
      metric: `${counts.users} contas ativas`,
      highlight: false,
    },
  ];

  const handleCardClick = (mod: typeof modules[0]) => {
    const isAllowed = mod.allowedRoles.includes(currentRole);
    if (!isAllowed) {
      setDeniedModal(mod.title);
      return;
    }
    onNavigate(mod.id);
  };

  return (
    <div className="space-y-6">
      {/* Banner de Boas-Vindas e Seletor de Perfil do Laboratório */}
      <div className="rounded-2xl border border-zinc-200/90 bg-gradient-to-r from-emerald-900 via-zinc-900 to-zinc-900 p-6 text-white shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="rounded-md bg-emerald-500/20 px-2 py-0.5 text-xs font-bold text-emerald-300 border border-emerald-500/30">
                Central de Operações
              </span>
              <span className="text-zinc-400 text-xs">Laboratório Central Diagnósticos</span>
            </div>
            <h1 className="mt-2 text-2xl sm:text-3xl font-black tracking-tight text-white">
              Painel Principal do Laboratório
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-zinc-300 max-w-2xl">
              Navegue pelos módulos operacionais e de gestão. O acesso aos formulários é controlado de acordo
              com o perfil ativo.
            </p>
          </div>

          {/* Simulador / Seletor de Perfil para Homologação */}
          <div className="rounded-xl border border-zinc-700/80 bg-zinc-800/80 p-3 backdrop-blur-sm shrink-0">
            <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">
              Simular Perfil no Laboratório:
            </p>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => onRoleChange("admin")}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition cursor-pointer ${
                  isAdmin
                    ? "bg-emerald-500 text-zinc-950 shadow-xs ring-2 ring-emerald-400/40"
                    : "bg-zinc-700/70 text-zinc-300 hover:bg-zinc-700"
                }`}
              >
                👑 Administrador (Total)
              </button>
              <button
                type="button"
                onClick={() => onRoleChange("attendant")}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition cursor-pointer ${
                  !isAdmin
                    ? "bg-blue-500 text-white shadow-xs ring-2 ring-blue-400/40"
                    : "bg-zinc-700/70 text-zinc-300 hover:bg-zinc-700"
                }`}
              >
                🎧 Atendente / Triagem
              </button>
            </div>
            <p className="mt-1.5 text-[10px] text-zinc-400">
              {isAdmin
                ? "Acesso completo aos 8 formulários e cadastros."
                : "Acesso a Dashboard, Orçamentos, Calendário e Catálogo."}
            </p>
          </div>
        </div>
      </div>

      {/* Grade de Botões Grandes de Navegação */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-black text-zinc-900 tracking-tight">
            Módulos & Formulários do Sistema
          </h2>
          <span className="text-xs text-zinc-500">
            {isAdmin ? "8 módulos disponíveis para você" : "4 módulos disponíveis para Atendente"}
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {modules.map((mod) => {
            const isAllowed = mod.allowedRoles.includes(currentRole);

            return (
              <div
                key={mod.id}
                onClick={() => handleCardClick(mod)}
                className={`group relative flex flex-col justify-between rounded-2xl border p-5 transition-all duration-200 cursor-pointer ${
                  isAllowed
                    ? `border-zinc-200/90 bg-white shadow-xs hover:shadow-md ${mod.accentBorder} ${mod.accentBg}`
                    : "border-dashed border-zinc-200 bg-zinc-50/80 opacity-60 hover:opacity-80"
                }`}
              >
                <div>
                  {/* Topo do Card */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 text-2xl shadow-2xs group-hover:scale-105 transition-transform">
                      {mod.icon}
                    </div>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${mod.badgeColor}`}
                    >
                      {mod.roleBadge}
                    </span>
                  </div>

                  {/* Título & Descrição */}
                  <h3 className="mt-4 text-base font-bold text-zinc-900 group-hover:text-emerald-700 transition-colors">
                    {mod.title}
                  </h3>
                  <p className="mt-1 text-xs text-zinc-500 leading-relaxed">
                    {mod.description}
                  </p>
                </div>

                {/* Rodapé do Card */}
                <div className="mt-5 flex items-center justify-between border-t border-zinc-100 pt-3 text-xs">
                  <span className="font-semibold text-zinc-700">{mod.metric}</span>
                  <div className="flex items-center gap-1 font-bold">
                    {isAllowed ? (
                      <span className="text-emerald-700 group-hover:translate-x-0.5 transition-transform inline-flex items-center gap-1">
                        Abrir <span aria-hidden="true">→</span>
                      </span>
                    ) : (
                      <span className="text-zinc-400 text-[11px] inline-flex items-center gap-1">
                        <span>🔒</span> Restrito
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Cartão de Canais Oficiais WhatsApp */}
      <WhatsAppContactsCard
        ownerKind="laboratory"
        title="Canais Oficiais de Atendimento WhatsApp (F-07)"
      />

      {/* Modal de Acesso Restrito ao Clicar em Módulo Bloqueado */}
      {deniedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl text-center space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-3xl">
              🔒
            </div>
            <div>
              <h3 className="text-base font-bold text-zinc-900">Acesso Restrito</h3>
              <p className="mt-1 text-xs text-zinc-600">
                O módulo <strong>{deniedModal}</strong> requer o perfil de <strong>Administrador / Gestor</strong>{" "}
                do laboratório.
              </p>
              <p className="mt-2 text-[11px] text-zinc-500 bg-zinc-50 rounded-xl p-2 border border-zinc-200">
                Dica de teste: utilize o alternador de perfil no banner acima para alternar para Administrador.
              </p>
            </div>
            <div className="flex gap-2 justify-center">
              <Button kind="ghost" onClick={() => setDeniedModal(null)}>
                Entendido
              </Button>
              <Button
                kind="primary"
                onClick={() => {
                  onRoleChange("admin");
                  setDeniedModal(null);
                }}
              >
                Alternar para Admin
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
