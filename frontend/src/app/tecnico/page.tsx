/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { CalendarView } from "@/components/CalendarView";
import {
  Button,
  Card,
  ConfirmModal,
  Empty,
  Notice,
  StatusBadge,
  fmtDate,
  money,
  weekdayLabel,
} from "@/components/ui";
import { authedFetch } from "@/lib/auth";

type Appt = {
  id: number;
  code: string;
  status: string;
  scheduled_at: string;
  patient?: { name?: string; phone?: string };
  location?: string;
  completed_at?: string | null;
  pharmacy_name?: string | null;
};

type Commission = {
  id: number;
  request_protocol: string;
  amount: string;
  status: string;
};

type OpeningWindow = {
  id: number;
  weekday: number;
  open_time: string;
  close_time: string;
};

type CollectionPoint = {
  id: number;
  kind: "pharmacy" | "laboratory";
  kind_display: string;
  name: string;
  pharmacy_name?: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  is_open: boolean;
  status: string;
  windows: OpeningWindow[];
};

export default function Tecnico() {
  const [appts, setAppts] = useState<Appt[]>([]);
  const [comms, setComms] = useState<Commission[]>([]);
  const [points, setPoints] = useState<CollectionPoint[]>([]);
  const [notice, setNotice] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [confirmAppt, setConfirmAppt] = useState<Appt | null>(null);
  const [confirmClosePoint, setConfirmClosePoint] = useState<CollectionPoint | null>(null);
  const [operating, setOperating] = useState(false);
  const [activeAgendaTab, setActiveAgendaTab] = useState<"cards" | "calendar">("cards");

  const load = useCallback(async () => {
    try {
      const [a, c, p] = await Promise.all([
        authedFetch<Appt[]>("/api/v1/appointments"),
        authedFetch<Commission[]>("/api/v1/commissions"),
        authedFetch<CollectionPoint[]>("/api/v1/collection-points").catch(() => [] as CollectionPoint[]),
      ]);
      setAppts(a);
      setComms(c);
      setPoints(p);
    } catch (e) {
      setNotice({ kind: "err", text: e instanceof Error ? e.message : "Erro ao carregar dados." });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function act(a: Appt, action: "check-in" | "complete") {
    try {
      setOperating(true);
      await authedFetch("/api/v1/appointments/" + a.id + "/" + action, {
        method: "POST",
        body: "{}",
      });
      setNotice({
        kind: "ok",
        text: action === "check-in" ? `Check-in da coleta ${a.code} registrado.` : `Coleta ${a.code} concluída com sucesso.`,
      });
      setConfirmAppt(null);
      await load();
    } catch (e) {
      setNotice({ kind: "err", text: "Erro: " + (e instanceof Error ? e.message : "falha na ação") });
    } finally {
      setOperating(false);
    }
  }

  async function togglePoint(point: CollectionPoint, shouldOpen: boolean) {
    try {
      setOperating(true);
      const action = shouldOpen ? "open" : "close";
      await authedFetch(`/api/v1/collection-points/${point.id}/${action}`, {
        method: "POST",
        body: "{}",
      });
      setNotice({
        kind: "ok",
        text: shouldOpen
          ? `Ponto "${point.name}" aberto para atendimento!`
          : `Ponto "${point.name}" encerrado com sucesso.`,
      });
      setConfirmClosePoint(null);
      await load();
    } catch (e) {
      setNotice({
        kind: "err",
        text: "Erro ao alterar estado do ponto: " + (e instanceof Error ? e.message : "falha"),
      });
    } finally {
      setOperating(false);
    }
  }

  return (
    <Shell title="Painel do Técnico de Coleta">
      {notice && (
        <div className="mb-4">
          <Notice kind={notice.kind}>{notice.text}</Notice>
        </div>
      )}

      {/* D-03 / F-02: Gestão do Ponto de Coleta pelo Técnico Designado */}
      {points.length > 0 && (
        <div className="space-y-3 mb-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500">
            Ponto de Coleta Designado (D-03)
          </h2>
          {points.map((p) => (
            <Card
              key={p.id}
              className={`border-2 transition-colors ${
                p.is_open ? "border-emerald-500/50 bg-emerald-50/20" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-bold text-zinc-900">{p.name}</h3>
                    <StatusBadge status={p.is_open ? "OPEN" : "CLOSED"} />
                    <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 font-medium">
                      {p.kind_display}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-600">
                    📍 {p.address}, {p.city} - {p.state} {p.zip_code ? `· CEP ${p.zip_code}` : ""}
                  </p>
                  {p.windows && p.windows.length > 0 && (
                    <div className="text-xs text-zinc-500 flex flex-wrap gap-x-3 gap-y-1 pt-1">
                      <span className="font-medium text-zinc-700">Horários de funcionamento:</span>
                      {p.windows.map((w) => (
                        <span key={w.id}>
                          {weekdayLabel(w.weekday)}: {w.open_time.slice(0, 5)} - {w.close_time.slice(0, 5)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex sm:self-center w-full sm:w-auto">
                  {p.is_open ? (
                    <Button
                      kind="danger"
                      disabled={operating}
                      className="w-full sm:w-auto text-base py-3 px-5"
                      onClick={() => setConfirmClosePoint(p)}
                    >
                      🔴 Encerrar Turno / Fechar Ponto
                    </Button>
                  ) : (
                    <Button
                      kind="primary"
                      disabled={operating}
                      className="w-full sm:w-auto text-base py-3 px-6 bg-emerald-600 hover:bg-emerald-500"
                      onClick={() => togglePoint(p, true)}
                    >
                      🟢 Iniciar Turno / Abrir Ponto
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Agenda de Coletas e Calendário Multi-formato */}
      <div className="mb-6 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <h2 className="text-base font-bold text-zinc-900">
            Minha agenda de coletas (Turno e Escala)
          </h2>
          <div className="flex items-center rounded-xl bg-zinc-100 p-1 text-xs font-medium self-start sm:self-auto">
            <button
              onClick={() => setActiveAgendaTab("cards")}
              className={`rounded-lg px-3 py-1.5 transition-all ${
                activeAgendaTab === "cards"
                  ? "bg-white text-zinc-900 font-bold shadow-xs"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              Cards de Campo
            </button>
            <button
              onClick={() => setActiveAgendaTab("calendar")}
              className={`rounded-lg px-3 py-1.5 transition-all ${
                activeAgendaTab === "calendar"
                  ? "bg-white text-zinc-900 font-bold shadow-xs"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              📅 Calendário / WhatsApp
            </button>
          </div>
        </div>

        {activeAgendaTab === "calendar" ? (
          <CalendarView
            appointments={appts.map((a) => ({
              id: a.id,
              code: a.code,
              status: a.status,
              scheduled_at: a.scheduled_at,
              patient_name: a.patient?.name ?? "Paciente",
              patient_phone: a.patient?.phone,
              location: a.location,
              pharmacy_name: a.pharmacy_name,
            }))}
          />
        ) : (
          <Card title="Cards de Coletas e Ações de Campo">
        {appts.length === 0 && <Empty text="Nenhuma coleta atribuída para você no momento." />}
        <div className="space-y-3">
          {appts.map((a) => {
            const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
              a.location || "Local da coleta"
            )}`;
            const patientPhone = a.patient?.phone?.replace(/\D/g, "") ?? "";
            const waUrl = patientPhone
              ? `https://wa.me/55${patientPhone}?text=${encodeURIComponent(
                  `Olá ${a.patient?.name ?? ""}, sou o técnico responsável pela sua coleta agendada (${a.code}).`
                )}`
              : null;

            return (
              <div
                key={a.id}
                className="rounded-xl border border-zinc-200 bg-white p-4 transition-all hover:border-zinc-300 shadow-sm"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-bold text-zinc-900">{a.code}</span>
                      <StatusBadge status={a.status} />
                    </div>
                    <div className="mt-1 text-sm font-semibold text-zinc-700">
                      👤 {a.patient?.name || "Paciente não informado"}
                    </div>
                    <div className="mt-0.5 text-xs text-zinc-500">
                      📅 {fmtDate(a.scheduled_at)} · 📍 {a.location || "Endereço a confirmar"}
                    </div>
                  </div>

                  {/* Ações Rápidas de Campo */}
                  <div className="flex flex-wrap items-center gap-2 pt-2 sm:pt-0">
                    {a.location && (
                      <a
                        href={mapsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-xl border border-zinc-300 bg-zinc-50 px-3.5 py-2 text-xs sm:text-sm font-semibold text-zinc-700 hover:bg-zinc-100 active:bg-zinc-200"
                      >
                        🗺️ Ver Rota
                      </a>
                    )}

                    {waUrl && (
                      <a
                        href={waUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50 px-3.5 py-2 text-xs sm:text-sm font-semibold text-emerald-800 hover:bg-emerald-100 active:bg-emerald-200"
                      >
                        💬 WhatsApp
                      </a>
                    )}

                    {a.status === "SCHEDULED" && (
                      <Button
                        kind="ghost"
                        disabled={operating}
                        onClick={() => act(a, "check-in")}
                        className="text-xs sm:text-sm"
                      >
                        📍 Fazer Check-in
                      </Button>
                    )}

                    {(a.status === "IN_PROGRESS" || a.status === "SCHEDULED") && (
                      <Button
                        kind="primary"
                        disabled={operating}
                        onClick={() => setConfirmAppt(a)}
                        className="text-xs sm:text-sm"
                      >
                        ✓ Concluir Coleta
                      </Button>
                    )}

                    {a.status === "COMPLETED" && (
                      <span className="inline-flex min-h-[44px] items-center rounded-xl bg-emerald-50 px-3 py-1.5 text-xs sm:text-sm font-semibold text-emerald-700 border border-emerald-200">
                        ✓ Coleta Realizada
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
        )}
      </div>

      {/* Comissões */}
      <Card title="Minhas comissões operacionais">
        {comms.length === 0 && <Empty text="Nenhuma comissão registrada até o momento." />}
        <div className="divide-y divide-zinc-100">
          {comms.map((c) => (
            <div key={c.id} className="flex items-center justify-between py-2.5 text-sm">
              <span className="font-medium text-zinc-700">Protocolo: {c.request_protocol}</span>
              <div className="flex items-center gap-3">
                <span className="font-bold text-zinc-900">{money(c.amount)}</span>
                <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">{c.status}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Modal de Confirmação para Concluir Coleta */}
      <ConfirmModal
        isOpen={Boolean(confirmAppt)}
        title="Confirmar Conclusão de Coleta"
        description={`Deseja confirmar a realização da coleta ${confirmAppt?.code}? Certifique-se de que todas as amostras foram devidamente identificadas e armazenadas.`}
        confirmText="Confirmar Coleta"
        cancelText="Voltar"
        onConfirm={() => {
          if (confirmAppt) void act(confirmAppt, "complete");
        }}
        onCancel={() => setConfirmAppt(null)}
      />

      {/* Modal de Confirmação para Fechar Ponto */}
      <ConfirmModal
        isOpen={Boolean(confirmClosePoint)}
        title="Encerrar Turno do Ponto de Coleta"
        description={`Tem certeza que deseja fechar o ponto "${confirmClosePoint?.name}"? O local deixará de constar como aberto para acolhimento de pacientes.`}
        confirmText="Sim, Encerrar Turno"
        cancelText="Cancelar"
        kind="danger"
        onConfirm={() => {
          if (confirmClosePoint) void togglePoint(confirmClosePoint, false);
        }}
        onCancel={() => setConfirmClosePoint(null)}
      />
    </Shell>
  );
}
