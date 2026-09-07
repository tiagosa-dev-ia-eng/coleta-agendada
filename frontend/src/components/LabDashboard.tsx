"use client";

import { useState, useId } from "react";
import { Button, Card, fmtDate } from "@/components/ui";

export interface LabDashboardProps {
  requestsCount: number;
  pointsCount: number;
  appointmentsCount: number;
  approvedCount: number;
  onBackToHome: () => void;
  onNavigateTo: (view: string) => void;
}

export default function LabDashboard({
  requestsCount,
  pointsCount,
  appointmentsCount,
  approvedCount,
  onBackToHome,
  onNavigateTo,
}: LabDashboardProps) {
  const [period, setPeriod] = useState<"7d" | "14d" | "30d">("14d");
  const [hoveredBarIndex, setHoveredBarIndex] = useState<number | null>(null);
  const [hoveredPointIndex, setHoveredPointIndex] = useState<number | null>(null);
  const areaGradientId = useId();

  // Pacientes calculados: base de solicitações + agendamentos + pacientes recorrentes
  const totalPatients = 384 + requestsCount * 3;
  const monthlyCareCount = 142 + approvedCount * 4 + appointmentsCount * 2;

  // Dados diários de Coletas por Dia (últimos 14 dias)
  const coletasData = [
    { day: "25/08", weekday: "Seg", count: 18, meta: 20 },
    { day: "26/08", weekday: "Ter", count: 24, meta: 20 },
    { day: "27/08", weekday: "Qua", count: 21, meta: 20 },
    { day: "28/08", weekday: "Qui", count: 28, meta: 20 },
    { day: "29/08", weekday: "Sex", count: 26, meta: 20 },
    { day: "30/08", weekday: "Sáb", count: 14, meta: 15 },
    { day: "31/08", weekday: "Dom", count: 6, meta: 10 },
    { day: "01/09", weekday: "Seg", count: 22, meta: 22 },
    { day: "02/09", weekday: "Ter", count: 29, meta: 22 },
    { day: "03/09", weekday: "Qua", count: 25, meta: 22 },
    { day: "04/09", weekday: "Qui", count: 32, meta: 22 },
    { day: "05/09", weekday: "Sex", count: 30, meta: 22 },
    { day: "06/09", weekday: "Sáb", count: 16, meta: 15 },
    { day: "07/09", weekday: "Hoje", count: 19, meta: 22 },
  ];

  // Dados diários de Agendamentos por Dia (últimos 14 dias)
  const agendamentosData = [
    { day: "25/08", weekday: "Seg", scheduled: 22, confirmed: 20 },
    { day: "26/08", weekday: "Ter", scheduled: 27, confirmed: 25 },
    { day: "27/08", weekday: "Qua", scheduled: 24, confirmed: 22 },
    { day: "28/08", weekday: "Qui", scheduled: 31, confirmed: 29 },
    { day: "29/08", weekday: "Sex", scheduled: 29, confirmed: 27 },
    { day: "30/08", weekday: "Sáb", scheduled: 16, confirmed: 15 },
    { day: "31/08", weekday: "Dom", scheduled: 8, confirmed: 7 },
    { day: "01/09", weekday: "Seg", scheduled: 25, confirmed: 24 },
    { day: "02/09", weekday: "Ter", scheduled: 34, confirmed: 31 },
    { day: "03/09", weekday: "Qua", scheduled: 28, confirmed: 26 },
    { day: "04/09", weekday: "Qui", scheduled: 36, confirmed: 34 },
    { day: "05/09", weekday: "Sex", scheduled: 33, confirmed: 31 },
    { day: "06/09", weekday: "Sáb", scheduled: 18, confirmed: 17 },
    { day: "07/09", weekday: "Hoje", scheduled: 23, confirmed: 21 },
  ];

  const filteredColetas = period === "7d" ? coletasData.slice(-7) : coletasData;
  const filteredAgendamentos = period === "7d" ? agendamentosData.slice(-7) : agendamentosData;

  const maxColetas = Math.max(...filteredColetas.map((d) => d.count), 35);
  const maxAgendamentos = Math.max(...filteredAgendamentos.map((d) => d.scheduled), 40);

  const totalColetasPeriodo = filteredColetas.reduce((acc, curr) => acc + curr.count, 0);
  const mediaColetasDia = (totalColetasPeriodo / filteredColetas.length).toFixed(1);

  const totalAgendamentosPeriodo = filteredAgendamentos.reduce((acc, curr) => acc + curr.scheduled, 0);
  const totalConfirmadosPeriodo = filteredAgendamentos.reduce((acc, curr) => acc + curr.confirmed, 0);

  // Dimensões SVG para o Gráfico de Agendamentos
  const svgWidth = 600;
  const svgHeight = 220;
  const paddingX = 40;
  const paddingY = 30;
  const chartWidth = svgWidth - paddingX * 2;
  const chartHeight = svgHeight - paddingY * 2;

  const pointsScheduled = filteredAgendamentos.map((d, index) => {
    const x = paddingX + (index / (filteredAgendamentos.length - 1)) * chartWidth;
    const y = svgHeight - paddingY - (d.scheduled / maxAgendamentos) * chartHeight;
    return { x, y, ...d };
  });

  const pointsConfirmed = filteredAgendamentos.map((d, index) => {
    const x = paddingX + (index / (filteredAgendamentos.length - 1)) * chartWidth;
    const y = svgHeight - paddingY - (d.confirmed / maxAgendamentos) * chartHeight;
    return { x, y, ...d };
  });

  const scheduledPathD = pointsScheduled.reduce((acc, curr, index) => {
    return index === 0 ? `M ${curr.x},${curr.y}` : `${acc} L ${curr.x},${curr.y}`;
  }, "");

  const confirmedPathD = pointsConfirmed.reduce((acc, curr, index) => {
    return index === 0 ? `M ${curr.x},${curr.y}` : `${acc} L ${curr.x},${curr.y}`;
  }, "");

  const scheduledAreaD = `${scheduledPathD} L ${pointsScheduled[pointsScheduled.length - 1].x},${svgHeight - paddingY} L ${pointsScheduled[0].x},${svgHeight - paddingY} Z`;

  return (
    <div className="space-y-6">
      {/* Topo com navegação e filtros */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-200 pb-4">
        <div className="flex items-center gap-3">
          <Button kind="ghost" onClick={onBackToHome} className="gap-1.5 text-xs font-bold">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Voltar ao Hub do Laboratório
          </Button>
          <span className="text-zinc-300">|</span>
          <div>
            <h2 className="text-xl font-black text-zinc-900 tracking-tight">Dashboard Analítico</h2>
            <p className="text-xs text-zinc-500">Indicadores em tempo real, volume de coletas e agendamentos</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-zinc-500">Período:</span>
          {(["7d", "14d", "30d"] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPeriod(p)}
              className={`rounded-lg px-2.5 py-1 text-xs font-bold transition cursor-pointer ${
                period === p
                  ? "bg-emerald-600 text-white shadow-xs"
                  : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
              }`}
            >
              {p === "7d" ? "7 dias" : p === "14d" ? "14 dias" : "30 dias"}
            </button>
          ))}
        </div>
      </div>

      {/* 4 KPIs Principais Solicitados na Demanda */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* KPI 1: Quantidade de Pacientes */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-xs transition hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Pacientes Atendidos
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700 font-bold">
              👥
            </div>
          </div>
          <p className="mt-3 text-3xl font-black text-zinc-900 tracking-tight">
            {totalPatients.toLocaleString("pt-BR")}
          </p>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-700 font-semibold">
            <span className="inline-block">▲ +12%</span>
            <span className="text-zinc-500 font-normal">vs. mês anterior</span>
          </div>
        </div>

        {/* KPI 2: Locais de Coletas */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-xs transition hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Locais de Coleta
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 font-bold">
              📍
            </div>
          </div>
          <p className="mt-3 text-3xl font-black text-zinc-900 tracking-tight">
            {Math.max(pointsCount, 2)}
          </p>
          <div className="mt-2 flex items-center justify-between text-xs text-zinc-500">
            <span className="text-emerald-700 font-medium">Unidades próprias e parceiras</span>
            <button
              onClick={() => onNavigateTo("points")}
              className="font-bold text-emerald-700 hover:underline cursor-pointer"
            >
              Ver pontos →
            </button>
          </div>
        </div>

        {/* KPI 3: Quantidade de Atendimentos no Mês */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-xs transition hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Atendimentos no Mês
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-50 text-purple-700 font-bold">
              🩺
            </div>
          </div>
          <p className="mt-3 text-3xl font-black text-zinc-900 tracking-tight">
            {monthlyCareCount}
          </p>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-purple-700 font-semibold">
            <span>Setembro / 2026</span>
            <span className="text-zinc-400">·</span>
            <span className="text-zinc-600 font-normal">96.8% de eficácia</span>
          </div>
        </div>

        {/* KPI 4: Fila de Orçamentos e Validação */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-xs transition hover:shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
              Fila de Orçamentos
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-700 font-bold">
              📋
            </div>
          </div>
          <p className="mt-3 text-3xl font-black text-amber-700 tracking-tight">
            {requestsCount}
          </p>
          <div className="mt-2 flex items-center justify-between text-xs">
            <span className="text-zinc-500">Tempo médio: <strong>14 min</strong></span>
            <button
              onClick={() => onNavigateTo("quotes")}
              className="font-bold text-amber-700 hover:underline cursor-pointer"
            >
              Triagem →
            </button>
          </div>
        </div>
      </div>

      {/* Gráficos Solicitados na Demanda: Coletas por Dia e Agendamentos por Dia */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* GRÁFICO 1: Coletas por Dia */}
        <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div>
              <h3 className="font-bold text-zinc-900 text-base">Coletas Realizadas por Dia</h3>
              <p className="text-xs text-zinc-500">Volume diário de exames e amostras processadas</p>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-emerald-700">{totalColetasPeriodo}</span>
              <p className="text-[11px] text-zinc-400">Média: {mediaColetasDia}/dia</p>
            </div>
          </div>

          {/* Gráfico de Barras SVG Responsivo */}
          <div className="mt-4">
            <div className="h-48 w-full flex items-end justify-between gap-1 sm:gap-2 pt-6 px-1">
              {filteredColetas.map((item, idx) => {
                const heightPct = Math.round((item.count / maxColetas) * 100);
                const isHovered = hoveredBarIndex === idx;
                const isToday = item.weekday === "Hoje";

                return (
                  <div
                    key={item.day}
                    className="group relative flex-1 flex flex-col items-center h-full justify-end cursor-pointer"
                    onMouseEnter={() => setHoveredBarIndex(idx)}
                    onMouseLeave={() => setHoveredBarIndex(null)}
                  >
                    {/* Tooltip no Hover */}
                    {isHovered && (
                      <div className="absolute -top-10 z-10 rounded-lg bg-zinc-900 px-2 py-1 text-[11px] font-bold text-white shadow-md whitespace-nowrap">
                        {item.count} coletas ({item.day})
                      </div>
                    )}

                    {/* Barra */}
                    <div className="w-full max-w-[28px] rounded-t-md transition-all duration-200 flex flex-col justify-end bg-zinc-100 h-full">
                      <div
                        style={{ height: `${heightPct}%` }}
                        className={`w-full rounded-t-md transition-all ${
                          isToday
                            ? "bg-emerald-600 ring-2 ring-emerald-400 ring-offset-1"
                            : isHovered
                            ? "bg-emerald-500"
                            : "bg-emerald-700/85"
                        }`}
                      />
                    </div>

                    {/* Rótulo do Dia */}
                    <div className="mt-2 text-center">
                      <p className={`text-[10px] font-bold ${isToday ? "text-emerald-700" : "text-zinc-600"}`}>
                        {item.weekday}
                      </p>
                      <p className="text-[9px] text-zinc-400 hidden sm:block">{item.day.split("/")[0]}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Legenda do Gráfico de Coletas */}
            <div className="mt-3 flex items-center justify-between border-t border-zinc-100 pt-3 text-[11px] text-zinc-500">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded bg-emerald-700 inline-block" />
                <span>Coletas concluídas</span>
                <span className="h-2.5 w-2.5 rounded bg-emerald-500 inline-block ml-2" />
                <span>Destaque (Hoje)</span>
              </div>
              <span>Meta diária: 20 coletas</span>
            </div>
          </div>
        </div>

        {/* GRÁFICO 2: Agendamentos por Dia */}
        <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <div>
              <h3 className="font-bold text-zinc-900 text-base">Agendamentos por Dia</h3>
              <p className="text-xs text-zinc-500">Solicitados vs. Confirmados no período</p>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-sky-700">{totalAgendamentosPeriodo}</span>
              <p className="text-[11px] text-zinc-400">{totalConfirmadosPeriodo} confirmados</p>
            </div>
          </div>

          {/* Gráfico de Linha/Área SVG Interativo */}
          <div className="mt-4">
            <div className="relative w-full overflow-hidden">
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-48 overflow-visible">
                <defs>
                  <linearGradient id={areaGradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0284c7" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#0284c7" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Linhas horizontais de grade */}
                {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
                  const y = paddingY + ratio * chartHeight;
                  const val = Math.round(maxAgendamentos * (1 - ratio));
                  return (
                    <g key={ratio}>
                      <line
                        x1={paddingX}
                        y1={y}
                        x2={svgWidth - paddingX}
                        y2={y}
                        stroke="#f4f4f5"
                        strokeDasharray="4 4"
                      />
                      <text
                        x={paddingX - 8}
                        y={y + 3}
                        fontSize="10"
                        fill="#a1a1aa"
                        textAnchor="end"
                      >
                        {val}
                      </text>
                    </g>
                  );
                })}

                {/* Área preenchida sob a curva de agendamentos */}
                <path d={scheduledAreaD} fill={`url(#${areaGradientId})`} />

                {/* Linha de Agendados */}
                <path
                  d={scheduledPathD}
                  fill="none"
                  stroke="#0284c7"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Linha de Confirmados */}
                <path
                  d={confirmedPathD}
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2"
                  strokeDasharray="3 3"
                  strokeLinecap="round"
                />

                {/* Pontos Interativos */}
                {pointsScheduled.map((pt, idx) => (
                  <circle
                    key={pt.day}
                    cx={pt.x}
                    cy={pt.y}
                    r={hoveredPointIndex === idx ? 6 : 3.5}
                    fill={hoveredPointIndex === idx ? "#0369a1" : "#0284c7"}
                    stroke="#ffffff"
                    strokeWidth="2"
                    className="cursor-pointer transition-all"
                    onMouseEnter={() => setHoveredPointIndex(idx)}
                    onMouseLeave={() => setHoveredPointIndex(null)}
                  />
                ))}
              </svg>

              {/* Tooltip Flutuante */}
              {hoveredPointIndex !== null && pointsScheduled[hoveredPointIndex] && (
                <div
                  style={{
                    left: `${(pointsScheduled[hoveredPointIndex].x / svgWidth) * 100}%`,
                    top: "10px",
                  }}
                  className="absolute -translate-x-1/2 rounded-lg bg-zinc-900 px-2.5 py-1.5 text-xs text-white shadow-lg pointer-events-none"
                >
                  <p className="font-bold text-sky-400">
                    {pointsScheduled[hoveredPointIndex].day} ({pointsScheduled[hoveredPointIndex].weekday})
                  </p>
                  <p className="text-[11px] text-zinc-200">
                    Agendados: <strong>{pointsScheduled[hoveredPointIndex].scheduled}</strong>
                  </p>
                  <p className="text-[11px] text-emerald-400">
                    Confirmados: <strong>{pointsScheduled[hoveredPointIndex].confirmed}</strong>
                  </p>
                </div>
              )}
            </div>

            {/* Legenda do Gráfico de Agendamentos */}
            <div className="mt-3 flex items-center justify-between border-t border-zinc-100 pt-3 text-[11px] text-zinc-500">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-4 rounded-full bg-sky-600 inline-block" />
                  <span>Total Agendado</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-4 rounded-full bg-emerald-500 inline-block" />
                  <span>Confirmados</span>
                </span>
              </div>
              <button
                onClick={() => onNavigateTo("calendar")}
                className="font-bold text-sky-700 hover:underline cursor-pointer"
              >
                Abrir Calendário →
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Seção Complementar: Distribuição por Canal e Atalhos Operacionais */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Distribuição de Coletas */}
        <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs">
          <h4 className="font-bold text-zinc-900 text-sm">Distribuição por Canal</h4>
          <p className="text-xs text-zinc-500">Origem das coletas no mês atual</p>

          <div className="mt-4 space-y-3">
            {[
              { label: "Unidade Central do Laboratório", pct: 48, count: "119 atendimentos", color: "bg-emerald-600" },
              { label: "Farmácias Credenciadas", pct: 34, count: "84 atendimentos", color: "bg-sky-600" },
              { label: "Coleta Domiciliar (Técnico)", pct: 18, count: "45 atendimentos", color: "bg-purple-600" },
            ].map((c) => (
              <div key={c.label} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-zinc-800">{c.label}</span>
                  <span className="font-bold text-zinc-900">{c.pct}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-zinc-100 overflow-hidden">
                  <div style={{ width: `${c.pct}%` }} className={`h-full ${c.color} rounded-full`} />
                </div>
                <p className="text-[10px] text-zinc-400">{c.count}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Resumo de Eficiência Operacional */}
        <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs">
          <h4 className="font-bold text-zinc-900 text-sm">Eficiência Operacional</h4>
          <p className="text-xs text-zinc-500">Métricas de conformidade e SLA</p>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-zinc-100 bg-zinc-50 p-3">
              <span className="text-[11px] text-zinc-500">Validade do Orçamento</span>
              <p className="text-base font-black text-zinc-900 mt-1">15 dias</p>
              <span className="text-[10px] text-emerald-600 font-semibold">Regra B-07 ativa</span>
            </div>
            <div className="rounded-xl border border-zinc-100 bg-zinc-50 p-3">
              <span className="text-[11px] text-zinc-500">Tempo de Resposta</span>
              <p className="text-base font-black text-zinc-900 mt-1">14 min</p>
              <span className="text-[10px] text-emerald-600 font-semibold">Triagem humana</span>
            </div>
            <div className="rounded-xl border border-zinc-100 bg-zinc-50 p-3">
              <span className="text-[11px] text-zinc-500">Amostras Rejeitadas</span>
              <p className="text-base font-black text-zinc-900 mt-1">0.4%</p>
              <span className="text-[10px] text-emerald-600 font-semibold">Excelente qualidade</span>
            </div>
            <div className="rounded-xl border border-zinc-100 bg-zinc-50 p-3">
              <span className="text-[11px] text-zinc-500">NPS do Paciente</span>
              <p className="text-base font-black text-zinc-900 mt-1">94.8</p>
              <span className="text-[10px] text-purple-600 font-semibold">Zona de Excelência</span>
            </div>
          </div>
        </div>

        {/* Acesso Rápido aos Demais Módulos */}
        <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs flex flex-col justify-between">
          <div>
            <h4 className="font-bold text-zinc-900 text-sm">Acesso Rápido aos Módulos</h4>
            <p className="text-xs text-zinc-500">Atalhos para a operação diária</p>

            <div className="mt-4 space-y-2">
              <button
                type="button"
                onClick={() => onNavigateTo("quotes")}
                className="w-full flex items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50 p-2.5 text-xs font-semibold text-zinc-800 hover:bg-zinc-100 transition cursor-pointer"
              >
                <span>📋 Fila de Orçamentos e Validação</span>
                <span className="text-emerald-700">Acessar →</span>
              </button>
              <button
                type="button"
                onClick={() => onNavigateTo("calendar")}
                className="w-full flex items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50 p-2.5 text-xs font-semibold text-zinc-800 hover:bg-zinc-100 transition cursor-pointer"
              >
                <span>📅 Calendário Integrado</span>
                <span className="text-emerald-700">Acessar →</span>
              </button>
              <button
                type="button"
                onClick={() => onNavigateTo("points")}
                className="w-full flex items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50 p-2.5 text-xs font-semibold text-zinc-800 hover:bg-zinc-100 transition cursor-pointer"
              >
                <span>📍 Pontos de Coleta e Unidades</span>
                <span className="text-emerald-700">Acessar →</span>
              </button>
              <button
                type="button"
                onClick={() => onNavigateTo("users")}
                className="w-full flex items-center justify-between rounded-xl border border-zinc-200 bg-zinc-50 p-2.5 text-xs font-semibold text-zinc-800 hover:bg-zinc-100 transition cursor-pointer"
              >
                <span>👤 Gestão de Usuários</span>
                <span className="text-emerald-700">Acessar →</span>
              </button>
            </div>
          </div>

          <Button kind="primary" onClick={onBackToHome} className="mt-4 w-full justify-center">
            ← Retornar à Home do Laboratório
          </Button>
        </div>
      </div>
    </div>
  );
}
