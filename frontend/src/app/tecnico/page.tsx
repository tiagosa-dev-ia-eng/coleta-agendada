/* eslint-disable react-hooks/set-state-in-effect */
"use client";
import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { Button, Card, Empty, Notice, StatusBadge, fmtDate, money } from "@/components/ui";
import { authedFetch } from "@/lib/auth";
type Appt = { id: number; code: string; status: string; scheduled_at: string; patient?: { name?: string }; location?: string; completed_at?: string | null };
type Commission = { id: number; request_protocol: string; amount: string; status: string };
export default function Tecnico() {
  const [appts, setAppts] = useState<Appt[]>([]);
  const [comms, setComms] = useState<Commission[]>([]);
  const [notice, setNotice] = useState("");
  const [err, setErr] = useState("");
  const load = useCallback(async () => {
    try {
      const [a, c] = await Promise.all([authedFetch<Appt[]>("/api/v1/appointments"), authedFetch<Commission[]>("/api/v1/commissions")]);
      setAppts(a);
      setComms(c);
    } catch (e) { setErr(e instanceof Error ? e.message : "erro"); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  async function act(a: Appt, action: "check-in" | "complete") {
    try {
      await authedFetch("/api/v1/appointments/" + a.id + "/" + action, { method: "POST", body: "{}" });
      setNotice(action === "check-in" ? "Check-in registrado." : "Coleta concluída.");
      await load();
    } catch (e) { setNotice("Erro: " + (e instanceof Error ? e.message : "")); }
  }
  return (
    <Shell title="Painel do Técnico">
      {notice && <Notice kind="ok">{notice}</Notice>}
      {err && <Notice kind="err">{err}</Notice>}
      <Card title="Minha agenda de coletas">
        {appts.length === 0 && <Empty text="Nenhuma coleta atribuída." />}
        <div className="space-y-2">
          {appts.map((a) => (
            <div key={a.id} className="flex flex-wrap items-center gap-2 rounded-xl border border-zinc-200 p-3 text-sm">
              <b>{a.code}</b><StatusBadge status={a.status} />
              <span className="text-xs text-zinc-600">{fmtDate(a.scheduled_at)}</span>
              <span className="text-xs text-zinc-500">{a.patient?.name ?? ""} · {a.location || "coleta"}</span>
              <div className="ml-auto flex gap-2">
                {a.status === "SCHEDULED" && <Button onClick={() => act(a, "check-in")}>Check-in</Button>}
                {(a.status === "IN_PROGRESS" || a.status === "SCHEDULED") && <Button kind="primary" onClick={() => act(a, "complete")}>Concluir coleta</Button>}
                {a.status === "COMPLETED" && <span className="text-xs text-emerald-600">✓ concluída</span>}
              </div>
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