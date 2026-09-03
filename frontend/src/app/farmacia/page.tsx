/* eslint-disable react-hooks/set-state-in-effect */
"use client";
import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { Card, Empty, Notice, StatusBadge, fmtDate, money } from "@/components/ui";
import { authedFetch } from "@/lib/auth";
type Appt = { id: number; code: string; status: string; scheduled_at: string; patient?: { name?: string } };
type Commission = { id: number; request_protocol: string; amount: string; status: string };
export default function Farmacia() {
  const [appts, setAppts] = useState<Appt[]>([]);
  const [comms, setComms] = useState<Commission[]>([]);
  const [err, setErr] = useState("");
  const load = useCallback(async () => {
    try {
      const [a, c] = await Promise.all([authedFetch<Appt[]>("/api/v1/appointments"), authedFetch<Commission[]>("/api/v1/commissions")]);
      setAppts(a); setComms(c);
    } catch (e) { setErr(e instanceof Error ? e.message : "erro"); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return (
    <Shell title="Painel da Farmácia / Ponto de Coleta">
      {err && <Notice kind="err">{err}</Notice>}
      <Card title="Agenda de coletas no meu ponto">
        {appts.length === 0 && <Empty text="Nenhuma coleta agendada para este ponto." />}
        <div className="space-y-2">
          {appts.map((a) => (
            <div key={a.id} className="flex flex-wrap items-center gap-2 rounded-xl border border-zinc-200 p-3 text-sm">
              <b>{a.code}</b><StatusBadge status={a.status} />
              <span className="text-xs text-zinc-600">{fmtDate(a.scheduled_at)}</span>
              <span className="text-xs text-zinc-500">{a.patient?.name ?? ""}</span>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Minhas comissões">
        {comms.length === 0 && <Empty text="Nenhuma comissão ainda." />}
        {comms.map((c) => (<div key={c.id} className="text-xs text-zinc-600">{c.request_protocol} — {money(c.amount)} · {c.status}</div>))}
      </Card>
    </Shell>
  );
}