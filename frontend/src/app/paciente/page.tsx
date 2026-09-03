/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useCallback, useEffect, useState } from "react";

import Shell from "@/components/Shell";
import { Button, Card, Empty, Notice, StatusBadge, fmtDate, money } from "@/components/ui";
import { API_URL } from "@/lib/api";
import { authedFetch, getToken } from "@/lib/auth";

type Quote = {
  id: number;
  request_id?: number;
  version: number;
  quotation_type: string;
  total: string;
  is_final: boolean;
  is_sent: boolean;
  is_approved: boolean;
  items: { description: string; quantity: number; unit_price: string | null }[];
};

type RequestRow = {
  id: number;
  protocol: string;
  status: string;
  collection_mode: string;
  preferred_location: string;
  desired_date: string | null;
  desired_period: string;
  medical_orders_count: number;
  created_at: string;
};

export default function Paciente() {
  const [rows, setRows] = useState<RequestRow[] | null>(null);
  const [notice, setNotice] = useState("");
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    desired_date: "",
    desired_period: "morning",
    collection_mode: "pharmacy",
    preferred_location: "",
  });
  const [busy, setBusy] = useState(false);
  const [uploadFor, setUploadFor] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [quotes, setQuotes] = useState<Record<number, Quote[]>>({});

  const load = useCallback(async () => {
    try {
      setRows(await authedFetch<RequestRow[]>("/api/v1/requests"));
      setErr("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "erro");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function loadQuotes(id: number) {
    try {
      const url = "/api/v1/requests/" + id + "/quotations";
      const list = await authedFetch<Quote[]>(url);
      setQuotes((q) => ({ ...q, [id]: list }));
    } catch {
      setQuotes((q) => ({ ...q, [id]: [] }));
    }
  }

  async function createRequest() {
    setBusy(true);
    setNotice("");
    try {
      await authedFetch("/api/v1/requests", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setNotice("Solicitação criada! Envie o pedido médico e acompanhe o orçamento.");
      setForm({ desired_date: "", desired_period: "morning", collection_mode: "pharmacy", preferred_location: "" });
      await load();
    } catch (e) {
      setNotice("Erro: " + (e instanceof Error ? e.message : ""));
    } finally {
      setBusy(false);
    }
  }

  async function uploadPedido(reqId: number) {
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const url = API_URL + "/api/v1/requests/" + reqId + "/medical-orders";
      const res = await fetch(url, {
        method: "POST",
        headers: { Authorization: "Bearer " + getToken() },
        body: fd,
      });
      if (!res.ok) throw new Error("Falha no upload");
      setNotice("Pedido médico anexado com sucesso.");
      setUploadFor(null);
      setFile(null);
      await load();
    } catch (e) {
      setNotice("Erro no upload: " + (e instanceof Error ? e.message : ""));
    } finally {
      setBusy(false);
    }
  }

  async function approve(q: Quote) {
    setBusy(true);
    try {
      const url = "/api/v1/quotations/" + q.id + "/approve";
      await authedFetch(url, { method: "POST", body: "{}" });
      setNotice("Orçamento aprovado! A coleta será agendada pelo laboratório.");
      if (q.request_id) await loadQuotes(q.request_id);
      await load();
    } catch (e) {
      setNotice("Erro: " + (e instanceof Error ? e.message : ""));
    } finally {
      setBusy(false);
    }
  }

  const periodLabel: Record<string, string> = { morning: "Manhã", afternoon: "Tarde", evening: "Noite" };
  const modeLabel: Record<string, string> = { pharmacy: "Farmácia/ponto", domiciliary: "Domiciliar", laboratory: "Laboratório" };

  return (
    <Shell title="Portal do Paciente">
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Nova solicitação de coleta">
          <div className="space-y-2 text-sm">
            <input type="date" value={form.desired_date} onChange={(e) => setForm({ ...form, desired_date: e.target.value })}
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 outline-none focus:border-emerald-500" />
            <div className="grid grid-cols-2 gap-2">
              <select value={form.desired_period} onChange={(e) => setForm({ ...form, desired_period: e.target.value })}
                className="rounded-lg border border-zinc-300 px-2 py-2 outline-none">
                {Object.entries(periodLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <select value={form.collection_mode} onChange={(e) => setForm({ ...form, collection_mode: e.target.value })}
                className="rounded-lg border border-zinc-300 px-2 py-2 outline-none">
                {Object.entries(modeLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <input value={form.preferred_location}
              onChange={(e) => setForm({ ...form, preferred_location: e.target.value })}
              placeholder="Local preferido (opcional)"
              className="w-full rounded-lg border border-zinc-300 px-3 py-2 outline-none focus:border-emerald-500" />
            <Button onClick={createRequest} disabled={busy} className="w-full">{busy ? "Enviando…" : "Solicitar coleta"}</Button>
          </div>
          <p className="mt-3 text-xs text-zinc-400">
            Os exames serão identificados a partir do pedido médico e o orçamento passará por validação humana.
          </p>
        </Card>

        <div className="lg:col-span-2">
          <Card title="Minhas solicitações" actions={<Button kind="ghost" onClick={() => void load()}>Atualizar</Button>}>
            {notice && <div className="mb-3"><Notice kind="ok">{notice}</Notice></div>}
            {rows === null && <p className="py-6 text-center text-sm text-zinc-400">Carregando…</p>}
            {rows !== null && rows.length === 0 && <Empty text="Nenhuma solicitação ainda." />}
            <div className="space-y-3">
              {rows?.map((r) => {
                const qs = quotes[r.id] ?? [];
                const toApprove = qs.find((q) => q.is_final && q.is_sent && !q.is_approved);
                return (
                  <div key={r.id} className="rounded-xl border border-zinc-200 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <b className="text-sm">{r.protocol}</b>
                      <StatusBadge status={r.status} />
                      <span className="text-xs text-zinc-500">{modeLabel[r.collection_mode]} · {periodLabel[r.desired_period]}</span>
                      <button onClick={() => void loadQuotes(r.id)} className="ml-auto text-xs text-emerald-600 hover:underline">ver orçamentos</button>
                    </div>
                    {qs.length > 0 && (
                      <div className="mt-2 space-y-1 border-t border-zinc-100 pt-2 text-xs text-zinc-600">
                        {qs.map((q) => (
                          <div key={q.id} className="flex flex-wrap items-center gap-2">
                            <span>v{q.version} · {q.quotation_type === "final" ? "orçamento final" : "rascunho"} · total {money(q.total)}</span>
                            {q.items.map((i, ix) => (
                              <span key={ix} className="rounded bg-zinc-100 px-1.5 py-0.5">
                                {i.description} x{i.quantity}{i.unit_price ? " (" + money(i.unit_price) + ")" : " (sem preço)"}
                              </span>
                            ))}
                            {q.is_approved && <span className="font-medium text-emerald-600">✓ aprovado</span>}
                          </div>
                        ))}
                        {toApprove && (
                          <Button onClick={() => approve(toApprove)} disabled={busy}>
                            Aprovar orçamento (R$ {money(toApprove.total)})
                          </Button>
                        )}
                      </div>
                    )}
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-zinc-400">
                      {r.medical_orders_count > 0 ? (
                        <span>Pedido médico anexado ✓</span>
                      ) : (
                        <button onClick={() => { setUploadFor(r.id); setFile(null); }} className="text-emerald-600 hover:underline">
                          Anexar pedido médico
                        </button>
                      )}
                      <span className="ml-auto">Criada em {fmtDate(r.created_at)}</span>
                    </div>
                    {uploadFor === r.id && (
                      <div className="mt-2 flex items-center gap-2">
                        <input type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                          className="text-xs text-zinc-500" />
                        <Button onClick={() => uploadPedido(r.id)} disabled={!file || busy}>Enviar</Button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            {err && <div className="mt-2"><Notice kind="err">{err}</Notice></div>}
          </Card>
        </div>
      </div>
    </Shell>
  );
}