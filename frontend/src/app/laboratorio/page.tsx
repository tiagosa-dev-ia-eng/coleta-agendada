/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useCallback, useEffect, useState } from "react";

import Shell from "@/components/Shell";
import { Button, Card, Empty, Notice, StatusBadge, fmtDate, money } from "@/components/ui";
import { authedFetch } from "@/lib/auth";

type RequestRow = { id: number; protocol: string; status: string; created_at: string; patient?: { name?: string; email?: string } };
type Quote = { id: number; request_id?: number; version: number; quotation_type: string; total: string; is_final: boolean; is_validated: boolean; is_sent: boolean; items: { description: string; quantity: number; unit_price: string | null }[] };
type Exam = { id: number; code: string; name: string; price: { id: number; price: string } | null };
type Appt = { id: number; code: string; status: string; scheduled_at: string; patient?: { name?: string; email?: string }; pharmacy_name?: string | null; technician_name?: string | null; location?: string };
type Commission = { id: number; request_protocol: string; beneficiary_type: string; beneficiary_name?: string | null; amount: string; status: string };

export default function Laboratorio() {
  const [reqs, setReqs] = useState<RequestRow[]>([]);
  const [quotes, setQuotes] = useState<Record<number, Quote[]>>({});
  const [exams, setExams] = useState<Exam[]>([]);
  const [appts, setAppts] = useState<Appt[]>([]);
  const [comms, setComms] = useState<Commission[]>([]);
  const [prices, setPrices] = useState<Record<number, string>>({});
  const [notice, setNotice] = useState("");
  const [err, setErr] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [r, e, a, c] = await Promise.all([
        authedFetch<RequestRow[]>("/api/v1/requests"),
        authedFetch<Exam[]>("/api/v1/exams"),
        authedFetch<Appt[]>("/api/v1/appointments"),
        authedFetch<Commission[]>("/api/v1/commissions"),
      ]);
      setReqs(r);
      setExams(e);
      setAppts(a);
      setComms(c);
      setErr("");
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "erro");
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  async function loadQuotes(id: number) {
    try {
      const list = await authedFetch<Quote[]>("/api/v1/requests/" + id + "/quotations");
      setQuotes((q) => ({ ...q, [id]: list }));
    } catch {
      setQuotes((q) => ({ ...q, [id]: [] }));
    }
  }

  async function actQuote(q: Quote, action: "validate" | "send" | "approve") {
    setBusyId(q.id);
    setNotice("");
    try {
      await authedFetch("/api/v1/quotations/" + q.id + "/" + action, { method: "POST", body: "{}" });
      setNotice(action === "validate" ? "Orçamento validado (final criado)." : action === "send" ? "Orçamento enviado ao paciente." : "Aprovado.");
      if (q.request_id) await loadQuotes(q.request_id);
      await loadAll();
    } catch (ex) {
      setNotice("Erro: " + (ex instanceof Error ? ex.message : ""));
    } finally {
      setBusyId(null);
    }
  }

  async function savePrice(examId: number) {
    setBusyId(examId);
    try {
      const price = prices[examId];
      if (!price || Number.isNaN(Number(price))) {
        setNotice("Informe um preço válido.");
        return;
      }
      await authedFetch("/api/v1/exams/" + examId + "/price", { method: "POST", body: JSON.stringify({ price }) });
      setNotice("Preço salvo.");
      await loadAll();
    } catch (ex) {
      setNotice("Erro: " + (ex instanceof Error ? ex.message : ""));
    } finally {
      setBusyId(null);
    }
  }

  const queue = reqs.filter((r) => r.status === "QUOTE_DRAFT" || r.status === "WAITING_HUMAN_VALIDATION");
  const sent = reqs.filter((r) => ["QUOTE_SENT", "APPROVED", "SCHEDULED", "IN_PROGRESS", "COMPLETED"].includes(r.status));

  const counts: Record<string, number> = {};
  reqs.forEach((r) => { counts[r.status] = (counts[r.status] ?? 0) + 1; });

  return (
    <Shell title="Painel do Laboratório">
      {notice && <Notice kind="ok">{notice}</Notice>}
      {err && <Notice kind="err">{err}</Notice>}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          ["Solicitadas", reqs.length, "text-zinc-700"],
          ["Rascunho/Validação", queue.length, "text-orange-600"],
          ["Enviadas/Fluxo", sent.length, "text-emerald-600"],
          ["Aprovadas", counts.APPROVED ?? 0, "text-sky-600"],
        ].map(([label, value, cls]) => (
          <div key={String(label)} className="rounded-xl border border-zinc-200 bg-white p-3 text-center">
            <p className={`text-2xl font-bold ${cls}`}>{value}</p>
            <p className="text-xs text-zinc-500">{label}</p>
          </div>
        ))}
      </div>

      <Card title="Validação humana (rascunhos aguardando revisão)" actions={<Button kind="ghost" onClick={() => void loadAll()}>Atualizar</Button>}>
        {queue.length === 0 && <Empty text="Nenhum rascunho aguardando validação." />}
        <div className="space-y-3">
          {queue.map((r) => {
            const qs = quotes[r.id] ?? [];
            const draft = [...qs].reverse().find((q) => q.quotation_type === "draft");
            const final = qs.find((q) => q.quotation_type === "final");
            return (
              <div key={r.id} className="rounded-xl border border-zinc-200 p-3">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <b>{r.protocol}</b>
                  <StatusBadge status={r.status} />
                  <span className="text-xs text-zinc-500">{r.patient?.name || r.patient?.email}</span>
                  <button onClick={() => void loadQuotes(r.id)} className="ml-auto text-xs text-emerald-600 hover:underline">ver itens</button>
                </div>
                {qs.length > 0 && (
                  <div className="mt-2 space-y-2 border-t border-zinc-100 pt-2">
                    {qs.map((q) => (
                      <div key={q.id} className="rounded bg-zinc-50 p-2 text-xs text-zinc-700">
                        <p className="mb-1 font-medium">
                          v{q.version} · {q.quotation_type === "final" ? "orçamento final" : "rascunho"} · total {money(q.total)}
                        </p>
                        <ul className="space-y-0.5">
                          {q.items.map((i, ix) => (
                            <li key={ix} className="flex justify-between">
                              <span>{i.description} x{i.quantity}</span>
                              <span>{i.unit_price ? money(i.unit_price) : "SEM PREÇO"}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                    <div className="flex flex-wrap gap-2">
                      {draft && !draft.is_final && (
                        <Button onClick={() => actQuote(draft, "validate")} disabled={busyId === draft.id}>Validar (gerar orçamento final)</Button>
                      )}
                      {final && final.is_validated && !final.is_sent && (
                        <Button kind="primary" onClick={() => actQuote(final, "send")} disabled={busyId === final.id}>Enviar orçamento ao paciente</Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Catálogo de exames e preços (por laboratório)">
          {exams.length === 0 && <Empty text="Nenhum exame no catálogo." />}
          <div className="space-y-2">
            {exams.map((e) => (
              <div key={e.id} className="flex items-center gap-2 text-sm">
                <b className="w-14 text-xs">{e.code}</b>
                <span className="flex-1 text-xs text-zinc-600">{e.name}</span>
                <input
                  type="number"
                  step="0.01"
                  value={prices[e.id] ?? e.price?.price ?? ""}
                  onChange={(ev) => setPrices({ ...prices, [e.id]: ev.target.value })}
                  placeholder="R$"
                  className="w-24 rounded border border-zinc-300 px-2 py-1 text-right text-xs outline-none focus:border-emerald-500"
                />
                <Button kind="ghost" onClick={() => savePrice(e.id)} disabled={busyId === e.id}>Salvar</Button>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Agenda de coletas">
          {appts.length === 0 && <Empty text="Nenhum agendamento." />}
          <div className="space-y-2">
            {appts.map((a) => (
              <div key={a.id} className="flex items-center gap-2 rounded-lg bg-zinc-50 p-2 text-xs">
                <span>{a.code}</span>
                <StatusBadge status={a.status} />
                <span className="text-zinc-600">{fmtDate(a.scheduled_at)}</span>
                <span className="text-zinc-500">{a.pharmacy_name || a.technician_name || a.location || ""}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="Lançamentos de comissão">
        {comms.length === 0 && <Empty text="Nenhum lançamento." />}
        <div className="space-y-1 text-xs text-zinc-600">
          {comms.map((c) => (
            <div key={c.id} className="flex flex-wrap gap-2 rounded bg-zinc-50 p-2">
              <span className="font-medium">{c.request_protocol}</span>
              <span>{c.beneficiary_name || c.beneficiary_type}</span>
              <span>{money(c.amount)}</span>
              <span>{c.status}</span>
            </div>
          ))}
        </div>
      </Card>
    </Shell>
  );
}