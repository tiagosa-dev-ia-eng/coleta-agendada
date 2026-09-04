"use client";

import { useState } from "react";
import { StatusBadge } from "@/components/ui";

export type CalendarAppointment = {
  id: number;
  code: string;
  status: string;
  scheduled_at: string;
  patient_name?: string | null;
  patient_phone?: string | null;
  location?: string | null;
  pharmacy_name?: string | null;
  technician_name?: string | null;
};

type CalendarMode = "day" | "week" | "message";

interface CalendarViewProps {
  appointments: CalendarAppointment[];
  onSelectAppt?: (appt: CalendarAppointment) => void;
}

export function CalendarView({ appointments, onSelectAppt }: CalendarViewProps) {
  const [mode, setMode] = useState<CalendarMode>("week");
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    return new Date().toISOString().split("T")[0];
  });

  // Helpers de data
  const curr = new Date(selectedDate + "T12:00:00");
  
  // Semana atual (Segunda a Domingo)
  const dayOfWeek = curr.getDay(); // 0 = Domingo
  const diffToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  const monday = new Date(curr);
  monday.setDate(curr.getDate() + diffToMonday);

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d.toISOString().split("T")[0];
  });

  const weekDayLabels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

  // Agrupamento de coletas por dia YYYY-MM-DD
  const apptsByDay: Record<string, CalendarAppointment[]> = {};
  appointments.forEach((a) => {
    const d = a.scheduled_at.split("T")[0];
    if (!apptsByDay[d]) apptsByDay[d] = [];
    apptsByDay[d].push(a);
  });

  // Navegação de datas
  function shiftDate(days: number) {
    const next = new Date(curr);
    next.setDate(curr.getDate() + days);
    setSelectedDate(next.toISOString().split("T")[0]);
  }

  // Geração de mensagem formatada para WhatsApp / Envio ao paciente ou equipe
  function generateScheduleMessage(): string {
    const dayAppts = apptsByDay[selectedDate] ?? [];
    const formattedDate = curr.toLocaleDateString("pt-BR", {
      weekday: "long",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });

    if (dayAppts.length === 0) {
      return `📅 *Agenda de Coletas - ${formattedDate}*\n\nNenhuma coleta agendada para esta data.`;
    }

    let msg = `📅 *Agenda de Coletas - ${formattedDate}*\n`;
    msg += `Total de coletas agendadas: ${dayAppts.length}\n\n`;

    dayAppts.forEach((a, idx) => {
      const time = new Date(a.scheduled_at).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      });
      msg += `*${idx + 1}. [${time}] Coleta ${a.code}*\n`;
      msg += `👤 *Paciente:* ${a.patient_name || "Não informado"}\n`;
      if (a.patient_phone) msg += `📞 *Tel:* ${a.patient_phone}\n`;
      msg += `📍 *Local:* ${a.location || a.pharmacy_name || "A combinar"}\n`;
      if (a.technician_name) msg += `🩺 *Técnico:* ${a.technician_name}\n`;
      msg += `Status: ${a.status}\n\n`;
    });

    msg += `Equipe de Coleta Agendada`;
    return msg;
  }

  const [copied, setCopied] = useState(false);
  function copyMessage() {
    const text = generateScheduleMessage();
    if (navigator.clipboard) {
      void navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  }

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-4 sm:p-5 shadow-xs">
      {/* Barra Superior com Modos e Filtros de Data */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-100 pb-4 mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => shiftDate(mode === "week" ? -7 : -1)}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-zinc-200 bg-zinc-50 text-zinc-700 hover:bg-zinc-100 font-bold"
            title="Anterior"
          >
            ‹
          </button>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-xl border border-zinc-300 bg-white px-3 py-1.5 text-xs sm:text-sm font-medium text-zinc-800 outline-none focus:border-emerald-500"
          />
          <button
            onClick={() => shiftDate(mode === "week" ? 7 : 1)}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-zinc-200 bg-zinc-50 text-zinc-700 hover:bg-zinc-100 font-bold"
            title="Próximo"
          >
            ›
          </button>
          <button
            onClick={() => setSelectedDate(new Date().toISOString().split("T")[0])}
            className="rounded-xl border border-zinc-200 bg-zinc-50 px-2.5 py-1.5 text-xs font-semibold text-zinc-600 hover:bg-zinc-100"
          >
            Hoje
          </button>
        </div>

        {/* Abas de Modo: Semana, Diário, Mensagem WhatsApp */}
        <div className="flex items-center rounded-xl bg-zinc-100 p-1 text-xs font-semibold">
          <button
            onClick={() => setMode("week")}
            className={`rounded-lg px-3 py-1.5 transition-all ${
              mode === "week"
                ? "bg-white text-zinc-900 shadow-xs"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            📅 Semanal
          </button>
          <button
            onClick={() => setMode("day")}
            className={`rounded-lg px-3 py-1.5 transition-all ${
              mode === "day"
                ? "bg-white text-zinc-900 shadow-xs"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            ☀️ Diário
          </button>
          <button
            onClick={() => setMode("message")}
            className={`rounded-lg px-3 py-1.5 transition-all ${
              mode === "message"
                ? "bg-white text-emerald-700 shadow-xs"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            💬 Msg WhatsApp
          </button>
        </div>
      </div>

      {/* Visualização 1: Modo Semanal (Grid de 7 Dias) */}
      {mode === "week" && (
        <div className="grid grid-cols-1 sm:grid-cols-7 gap-2">
          {weekDays.map((dStr, idx) => {
            const isToday = dStr === new Date().toISOString().split("T")[0];
            const isSelected = dStr === selectedDate;
            const dayList = apptsByDay[dStr] ?? [];
            const dObj = new Date(dStr + "T12:00:00");

            return (
              <div
                key={dStr}
                onClick={() => setSelectedDate(dStr)}
                className={`min-h-[140px] rounded-xl border p-2 cursor-pointer transition-all ${
                  isSelected
                    ? "border-emerald-600 bg-emerald-50/30 ring-1 ring-emerald-600"
                    : isToday
                    ? "border-zinc-300 bg-zinc-50/50"
                    : "border-zinc-200 bg-white hover:border-zinc-300"
                }`}
              >
                <div className="flex items-center justify-between border-b border-zinc-100 pb-1 mb-1.5">
                  <span className="text-[11px] font-bold uppercase text-zinc-500">
                    {weekDayLabels[idx]}
                  </span>
                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
                      isToday
                        ? "bg-emerald-600 text-white"
                        : "text-zinc-700"
                    }`}
                  >
                    {dObj.getDate()}
                  </span>
                </div>

                {dayList.length === 0 ? (
                  <p className="text-[10px] text-zinc-400 italic pt-1">Sem coletas</p>
                ) : (
                  <div className="space-y-1">
                    {dayList.map((a) => (
                      <div
                        key={a.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectAppt?.(a);
                        }}
                        className="rounded bg-white p-1.5 border border-zinc-200 shadow-2xs hover:border-emerald-400 text-[11px]"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-zinc-800 truncate">{a.code}</span>
                          <span className="text-[9px] text-zinc-500">
                            {new Date(a.scheduled_at).toLocaleTimeString("pt-BR", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>
                        <p className="text-[10px] text-zinc-600 truncate">
                          {a.patient_name || a.location || "Coleta"}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Visualização 2: Modo Diário Detalhado */}
      {mode === "day" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-xl bg-zinc-50 p-3">
            <div>
              <h4 className="font-bold text-zinc-900 text-sm">
                {curr.toLocaleDateString("pt-BR", {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </h4>
              <p className="text-xs text-zinc-500">
                {(apptsByDay[selectedDate] ?? []).length} coleta(s) agendada(s)
              </p>
            </div>
            <button
              onClick={() => setMode("message")}
              className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100"
            >
              Exportar para WhatsApp
            </button>
          </div>

          {(apptsByDay[selectedDate] ?? []).length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-200 p-8 text-center text-xs text-zinc-500">
              Nenhuma coleta marcada para o dia selecionado.
            </div>
          ) : (
            <div className="space-y-2">
              {(apptsByDay[selectedDate] ?? []).map((a) => (
                <div
                  key={a.id}
                  onClick={() => onSelectAppt?.(a)}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-white p-3.5 shadow-2xs hover:border-zinc-300 transition-all cursor-pointer"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-zinc-900">{a.code}</span>
                      <StatusBadge status={a.status} />
                      <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                        🕒 {new Date(a.scheduled_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-700 font-medium">
                      👤 {a.patient_name || "Paciente sem nome"} {a.patient_phone ? `(${a.patient_phone})` : ""}
                    </p>
                    <p className="text-xs text-zinc-500">
                      📍 {a.location || a.pharmacy_name || "Endereço a confirmar"}
                      {a.technician_name ? ` · 🩺 Técnico: ${a.technician_name}` : ""}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Visualização 3: Modo Mensagem WhatsApp (Pronto para Copiar/Enviar) */}
      {mode === "message" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-xs text-zinc-600">
              Mensagem formatada para envio rápido no WhatsApp (equipe ou pacientes do dia):
            </p>
            <button
              onClick={copyMessage}
              className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-emerald-500 active:scale-98 transition-all"
            >
              {copied ? "✓ Mensagem Copiada!" : "📋 Copiar Texto do WhatsApp"}
            </button>
          </div>

          <textarea
            readOnly
            rows={10}
            value={generateScheduleMessage()}
            className="w-full rounded-xl border border-zinc-300 bg-zinc-50 p-3 font-mono text-xs text-zinc-800 outline-none leading-relaxed"
          />

          <div className="flex justify-end gap-2">
            <a
              href={`https://wa.me/?text=${encodeURIComponent(generateScheduleMessage())}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-2 text-xs font-bold text-emerald-800 hover:bg-emerald-100"
            >
              💬 Abrir Direto no WhatsApp Web
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
