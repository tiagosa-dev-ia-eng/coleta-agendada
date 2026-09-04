/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { CalendarView } from "@/components/CalendarView";
import { Button, Card, Empty, Notice, StatusBadge, fmtDate, money } from "@/components/ui";
import { authedFetch } from "@/lib/auth";

type Appt = {
  id: number;
  code: string;
  status: string;
  scheduled_at: string;
  patient?: { name?: string; phone?: string; email?: string };
  location?: string;
  technician_name?: string | null;
};

type Commission = {
  id: number;
  request_protocol: string;
  amount: string;
  status: string;
};

export default function Farmacia() {
  const [appts, setAppts] = useState<Appt[]>([]);
  const [comms, setComms] = useState<Commission[]>([]);
  const [err, setErr] = useState("");
  const [activeTab, setActiveTab] = useState<"calendar" | "list">("calendar");

  const load = useCallback(async () => {
    try {
      const [a, c] = await Promise.all([
        authedFetch<Appt[]>("/api/v1/appointments"),
        authedFetch<Commission[]>("/api/v1/commissions"),
      ]);
      setAppts(a);
      setComms(c);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "erro");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const totalCommissions = comms.reduce((acc, c) => acc + parseFloat(c.amount || "0"), 0);

  return (
    <Shell title="Painel da Farmácia / Ponto de Coleta">
      {err && <Notice kind="err">{err}</Notice>}

      {/* Métricas do Ponto da Farmácia */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-zinc-200 bg-white p-4 text-center shadow-xs">
          <p className="text-2xl font-bold text-zinc-800">{appts.length}</p>
          <p className="text-xs text-zinc-500">Coletas Agendadas</p>
        </div>
        <div className="rounded-2xl border border-zinc-200 bg-white p-4 text-center shadow-xs">
          <p className="text-2xl font-bold text-emerald-600">
            {appts.filter((a) => a.status === "COMPLETED").length}
          </p>
          <p className="text-xs text-zinc-500">Coletas Concluídas</p>
        </div>
        <div className="col-span-2 sm:col-span-1 rounded-2xl border border-zinc-200 bg-white p-4 text-center shadow-xs">
          <p className="text-2xl font-bold text-indigo-600">{money(totalCommissions)}</p>
          <p className="text-xs text-zinc-500">Total de Comissões</p>
        </div>
      </div>

      {/* Agenda e Calendário com Alternância Visual */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h2 className="text-base font-bold text-zinc-900">
            📅 Agenda de Atendimento no Estabelecimento
          </h2>
          <div className="flex items-center gap-2">
            <div className="flex rounded-xl bg-zinc-100 p-1 text-xs font-medium">
              <button
                onClick={() => setActiveTab("calendar")}
                className={`rounded-lg px-3 py-1.5 transition-all ${
                  activeTab === "calendar"
                    ? "bg-white text-zinc-900 font-bold shadow-xs"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
              >
                Visão Calendário
              </button>
              <button
                onClick={() => setActiveTab("list")}
                className={`rounded-lg px-3 py-1.5 transition-all ${
                  activeTab === "list"
                    ? "bg-white text-zinc-900 font-bold shadow-xs"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
              >
                Visão Lista
              </button>
            </div>
            <Button kind="ghost" onClick={() => void load()}>Atualizar</Button>
          </div>
        </div>

        {activeTab === "calendar" ? (
          <CalendarView
            appointments={appts.map((a) => ({
              id: a.id,
              code: a.code,
              status: a.status,
              scheduled_at: a.scheduled_at,
              patient_name: a.patient?.name ?? a.patient?.email,
              patient_phone: a.patient?.phone,
              location: a.location,
              technician_name: a.technician_name,
            }))}
          />
        ) : (
          <Card title="Lista sequencial de agendamentos">
            {appts.length === 0 && <Empty text="Nenhuma coleta agendada para este ponto." />}
            <div className="space-y-2">
              {appts.map((a) => (
                <div
                  key={a.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-200 bg-white p-3.5 text-sm shadow-2xs hover:border-zinc-300 transition-all"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <b className="font-mono text-zinc-900">{a.code}</b>
                      <StatusBadge status={a.status} />
                    </div>
                    <p className="text-xs text-zinc-600">
                      👤 {a.patient?.name || "Paciente anônimo"} {a.patient?.phone ? `(${a.patient.phone})` : ""}
                    </p>
                  </div>
                  <div className="text-right text-xs">
                    <span className="font-medium text-emerald-700 block">{fmtDate(a.scheduled_at)}</span>
                    <span className="text-zinc-500">
                      {a.technician_name ? `🩺 Técnico: ${a.technician_name}` : "Aguardando técnico"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Comissões da Farmácia */}
      <Card title="Extrato de Comissões por Acolhimento e Suporte">
        {comms.length === 0 && <Empty text="Nenhuma comissão creditada ainda." />}
        <div className="divide-y divide-zinc-100">
          {comms.map((c) => (
            <div key={c.id} className="flex items-center justify-between py-2.5 text-xs sm:text-sm">
              <div className="space-y-0.5">
                <span className="font-semibold text-zinc-800">Protocolo: {c.request_protocol}</span>
                <p className="text-[11px] text-zinc-400">Comissão por uso do espaço e acolhimento</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-bold text-emerald-600 text-sm sm:text-base">{money(c.amount)}</span>
                <span className="rounded-lg bg-zinc-100 px-2.5 py-1 text-[11px] font-semibold text-zinc-700">
                  {c.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </Shell>
  );
}
