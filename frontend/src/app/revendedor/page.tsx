/* eslint-disable react-hooks/set-state-in-effect */
"use client";
import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { Card, Empty, Notice, money } from "@/components/ui";
import { authedFetch } from "@/lib/auth";
type Farm = { id: number; name: string; email_read: string; city?: string };
type Tech = { id: number; email_read: string; professional_registration?: string };
type Commission = { id: number; request_protocol: string; amount: string; status: string };
export default function Revendedor() {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [techs, setTechs] = useState<Tech[]>([]);
  const [comms, setComms] = useState<Commission[]>([]);
  const [err, setErr] = useState("");
  const load = useCallback(async () => {
    try {
      const [f, t, c] = await Promise.all([
        authedFetch<Farm[]>("/api/v1/pharmacies"),
        authedFetch<Tech[]>("/api/v1/technicians"),
        authedFetch<Commission[]>("/api/v1/commissions"),
      ]);
      setFarms(f); setTechs(t); setComms(c);
    } catch (e) { setErr(e instanceof Error ? e.message : "erro"); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return (
    <Shell title="Painel do Revendedor">
      {err && <Notice kind="err">{err}</Notice>}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Farmácias da minha rede">
          {farms.length === 0 && <Empty text="Nenhuma farmácia." />}
          {farms.map((f) => (<div key={f.id} className="text-sm text-zinc-700">{f.name} · {f.city || "—"}</div>))}
        </Card>
        <Card title="Técnicos da minha rede">
          {techs.length === 0 && <Empty text="Nenhum técnico." />}
          {techs.map((t) => (<div key={t.id} className="text-sm text-zinc-700">{t.email_read} · {t.professional_registration || "—"}</div>))}
        </Card>
      </div>
      <Card title="Minhas comissões (indicações)">
        {comms.length === 0 && <Empty text="Nenhuma comissão ainda." />}
        {comms.map((c) => (<div key={c.id} className="text-xs text-zinc-600">{c.request_protocol} — {money(c.amount)} · {c.status}</div>))}
      </Card>
    </Shell>
  );
}