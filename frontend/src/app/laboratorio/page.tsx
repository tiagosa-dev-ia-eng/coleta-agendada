/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useCallback, useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { CalendarView } from "@/components/CalendarView";
import { Button, Card, ConfirmModal, Empty, Notice, StatusBadge, fmtDate, money } from "@/components/ui";
import WhatsAppContactsCard from "@/components/WhatsAppContactsCard";
import { authedFetch } from "@/lib/auth";

type RequestRow = {
  id: number;
  protocol: string;
  status: string;
  created_at: string;
  patient?: { name?: string; email?: string };
};

type Quote = {
  id: number;
  request_id?: number;
  version: number;
  quotation_type: string;
  total: string;
  is_final: boolean;
  is_validated: boolean;
  is_sent: boolean;
  items: { description: string; quantity: number; unit_price: string | null }[];
};

type Exam = {
  id: number;
  code: string;
  name: string;
  price: { id: number; price: string } | null;
};

type Appt = {
  id: number;
  code: string;
  status: string;
  scheduled_at: string;
  patient?: { name?: string; email?: string };
  pharmacy_name?: string | null;
  technician_name?: string | null;
  location?: string;
};

type Commission = {
  id: number;
  request_protocol: string;
  beneficiary_type: string;
  beneficiary_name?: string | null;
  amount: string;
  status: string;
};

type WindowItem = {
  id: number;
  weekday: number;
  open_time: string;
  close_time: string;
};

type AssignedTechnician = {
  id: number;
  email: string;
  active: boolean;
  assigned_at: string;
};

type ResellerItem = {
  id: number;
  email_read?: string;
  name?: string;
  status: string;
  created_at?: string;
};

type AuditLogItem = {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string | number;
  user?: { id: number; email: string } | null;
  laboratory?: { id: number; name: string } | null;
  ip?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
};

type CollectionPoint = {
  id: number;
  kind: "pharmacy" | "laboratory";
  kind_display: string;
  laboratory: number;
  pharmacy?: number | null;
  pharmacy_name?: string | null;
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  latitude: number | null;
  longitude: number | null;
  is_open: boolean;
  status: string;
  windows: WindowItem[];
  technicians: AssignedTechnician[];
};

type TechnicianOption = {
  id: number;
  user: { id: number; email: string; name?: string };
  coren: string;
  active: boolean;
};

type PharmacyOption = {
  id: number;
  name: string;
  city: string;
  state: string;
};

type PaymentItem = {
  id: number;
  request: number;
  amount: string;
  status: "PENDING" | "CONFIRMED" | "CANCELLED" | "REFUNDED" | string;
  payment_method: string;
  payment_url?: string | null;
  pix_code?: string | null;
  created_at: string;
};

const WEEKDAY_NAMES = [
  "Segunda-feira",
  "Terça-feira",
  "Quarta-feira",
  "Quinta-feira",
  "Sexta-feira",
  "Sábado",
  "Domingo",
];

export default function Laboratorio() {
  const [reqs, setReqs] = useState<RequestRow[]>([]);
  const [quotes, setQuotes] = useState<Record<number, Quote[]>>({});
  const [exams, setExams] = useState<Exam[]>([]);
  const [appts, setAppts] = useState<Appt[]>([]);
  const [comms, setComms] = useState<Commission[]>([]);
  const [prices, setPrices] = useState<Record<number, string>>({});

  // F-02: Collection Points & Technicians
  const [points, setPoints] = useState<CollectionPoint[]>([]);
  const [techList, setTechList] = useState<TechnicianOption[]>([]);
  const [pharmacies, setPharmacies] = useState<PharmacyOption[]>([]);
  const [selectedPointId, setSelectedPointId] = useState<number | null>(null);

  // New point form
  const [showNewPointModal, setShowNewPointModal] = useState(false);

  // F-05: Gestão de Revendedores
  const [resellers, setResellers] = useState<ResellerItem[]>([]);
  const [showResellerModal, setShowResellerModal] = useState(false);
  const [resellerEmail, setResellerEmail] = useState("");
  const [resellerPassword, setResellerPassword] = useState("");
  const [resellerFirstName, setResellerFirstName] = useState("");
  const [confirmToggleReseller, setConfirmToggleReseller] = useState<ResellerItem | null>(null);

  // F-06: Trilha de Auditoria e Eventos
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditFilterAction, setAuditFilterAction] = useState("");
  const [auditFilterEntity, setAuditFilterEntity] = useState("");
  const [auditLoading, setAuditLoading] = useState(false);

  // F-04: CRUD de Exames (Criar / Editar / Desativar)
  const [showExamModal, setShowExamModal] = useState(false);
  const [examModalMode, setExamModalMode] = useState<"create" | "edit">("create");
  const [editingExamId, setEditingExamId] = useState<number | null>(null);
  const [examCode, setExamCode] = useState("");
  const [examName, setExamName] = useState("");
  const [examSearch, setExamSearch] = useState("");
  const [confirmDeactivateExam, setConfirmDeactivateExam] = useState<Exam | null>(null);
  const [newKind, setNewKind] = useState<"laboratory" | "pharmacy">("laboratory");
  const [newPharmacyId, setNewPharmacyId] = useState<string>("");
  const [newName, setNewName] = useState("");
  const [newAddress, setNewAddress] = useState("");
  const [newCity, setNewCity] = useState("");
  const [newState, setNewState] = useState("SP");
  const [newZip, setNewZip] = useState("");
  const [newLat, setNewLat] = useState("");
  const [newLng, setNewLng] = useState("");

  // Window form
  const [newWeekday, setNewWeekday] = useState<number>(0);
  const [newOpenTime, setNewOpenTime] = useState("07:00");
  const [newCloseTime, setNewCloseTime] = useState("17:00");

  // Assign technician form
  const [selectedTechToAssign, setSelectedTechToAssign] = useState<string>("");

  // F-03: Payments per request
  const [reqPayments, setReqPayments] = useState<Record<number, PaymentItem[]>>({});
  const [paymentModalData, setPaymentModalData] = useState<{
    paymentId: number;
    action: "cancel" | "refund";
    protocol: string;
    amount: string;
  } | null>(null);

  const [notice, setNotice] = useState("");
  const [err, setErr] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [r, e, a, c, pts, tchs, pharms, resList, auditResp] = await Promise.all([
        authedFetch<RequestRow[]>("/api/v1/requests"),
        authedFetch<Exam[]>("/api/v1/exams"),
        authedFetch<Appt[]>("/api/v1/appointments"),
        authedFetch<Commission[]>("/api/v1/commissions"),
        authedFetch<CollectionPoint[]>("/api/v1/collection-points").catch(() => []),
        authedFetch<TechnicianOption[]>("/api/v1/technicians").catch(() => []),
        authedFetch<PharmacyOption[]>("/api/v1/pharmacies").catch(() => []),
        authedFetch<ResellerItem[]>("/api/v1/resellers").catch(() => []),
        authedFetch<{ items: AuditLogItem[]; count: number }>("/api/v1/audit").catch(() => ({ items: [], count: 0 })),
      ]);
      setReqs(r);
      setExams(e);
      setAppts(a);
      setComms(c);
      setPoints(pts);
      setTechList(tchs);
      setPharmacies(pharms);
      setResellers(resList);
      setAuditLogs(auditResp.items || []);
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

  async function loadPayments(reqId: number) {
    try {
      const list = await authedFetch<PaymentItem[]>("/api/v1/requests/" + reqId + "/payments");
      setReqPayments((prev) => ({ ...prev, [reqId]: list }));
    } catch (ex) {
      setNotice("Erro ao carregar pagamentos: " + (ex instanceof Error ? ex.message : ""));
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

  // F-05: Revendedores Handlers
  async function handleCreateReseller() {
    if (!resellerEmail.trim() || !resellerPassword.trim()) {
      setNotice("E-mail e senha inicial são obrigatórios para cadastrar o revendedor.");
      return;
    }
    if (resellerPassword.length < 8) {
      setNotice("A senha inicial deve ter pelo menos 8 caracteres.");
      return;
    }

    setBusyId(888888);
    try {
      await authedFetch("/api/v1/resellers", {
        method: "POST",
        body: JSON.stringify({
          email: resellerEmail.trim().toLowerCase(),
          password: resellerPassword,
          first_name: resellerFirstName.trim(),
        }),
      });
      setNotice(`Revendedor ${resellerEmail} cadastrado com sucesso!`);
      setShowResellerModal(false);
      setResellerEmail("");
      setResellerPassword("");
      setResellerFirstName("");
      await loadAll();
    } catch (err) {
      setNotice("Erro ao cadastrar revendedor: " + (err instanceof Error ? err.message : ""));
    } finally {
      setBusyId(null);
    }
  }

  async function handleToggleResellerStatus() {
    if (!confirmToggleReseller) return;
    const nextStatus = confirmToggleReseller.status === "active" ? "inactive" : "active";
    setBusyId(confirmToggleReseller.id);
    try {
      await authedFetch(`/api/v1/resellers/${confirmToggleReseller.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      });
      setNotice(`Status do revendedor ${confirmToggleReseller.email_read} alterado para ${nextStatus === "active" ? "Ativo" : "Inativo"}.`);
      setConfirmToggleReseller(null);
      await loadAll();
    } catch (err) {
      setNotice("Erro ao alterar status do revendedor: " + (err instanceof Error ? err.message : ""));
    } finally {
      setBusyId(null);
    }
  }

  // F-06: Filtro e Atualização da Auditoria
  async function reloadAuditLogs() {
    setAuditLoading(true);
    try {
      const params = new URLSearchParams();
      if (auditFilterAction.trim()) params.set("action", auditFilterAction.trim());
      if (auditFilterEntity.trim()) params.set("entity_type", auditFilterEntity.trim());
      params.set("limit", "150");
      const url = `/api/v1/audit?${params.toString()}`;
      const data = await authedFetch<{ items: AuditLogItem[]; count: number }>(url);
      setAuditLogs(data.items || []);
    } catch (err) {
      setNotice("Erro ao carregar logs de auditoria: " + (err instanceof Error ? err.message : ""));
    } finally {
      setAuditLoading(false);
    }
  }

  // F-04: Exames Handlers
  async function handleSaveExam() {
    if (!examName.trim()) {
      setNotice("O nome do exame é obrigatório.");
      return;
    }
    if (examModalMode === "create" && !examCode.trim()) {
      setNotice("O código do exame é obrigatório.");
      return;
    }

    setBusyId(editingExamId ?? 999999);
    try {
      if (examModalMode === "create") {
        await authedFetch("/api/v1/exams", {
          method: "POST",
          body: JSON.stringify({ code: examCode.trim().toUpperCase(), name: examName.trim() }),
        });
        setNotice("Novo exame cadastrado no catálogo com sucesso!");
      } else if (editingExamId) {
        await authedFetch(`/api/v1/exams/${editingExamId}`, {
          method: "PATCH",
          body: JSON.stringify({ name: examName.trim() }),
        });
        setNotice("Nome do exame atualizado com sucesso!");
      }
      setShowExamModal(false);
      setExamCode("");
      setExamName("");
      setEditingExamId(null);
      await loadAll();
    } catch (ex) {
      setNotice("Erro no exame: " + (ex instanceof Error ? ex.message : ""));
    } finally {
      setBusyId(null);
    }
  }

  async function handleDeactivateExam() {
    if (!confirmDeactivateExam) return;
    setBusyId(confirmDeactivateExam.id);
    try {
      await authedFetch(`/api/v1/exams/${confirmDeactivateExam.id}`, {
        method: "DELETE",
      });
      setNotice(`Exame ${confirmDeactivateExam.code} desativado com sucesso (histórico preservado).`);
      setConfirmDeactivateExam(null);
      await loadAll();
    } catch (ex) {
      setNotice("Erro ao desativar exame: " + (ex instanceof Error ? ex.message : ""));
    } finally {
      setBusyId(null);
    }
  }

  function openEditExam(e: Exam) {
    setExamModalMode("edit");
    setEditingExamId(e.id);
    setExamCode(e.code);
    setExamName(e.name);
    setShowExamModal(true);
  }

  function openCreateExam() {
    setExamModalMode("create");
    setEditingExamId(null);
    setExamCode("");
    setExamName("");
    setShowExamModal(true);
  }

  // F-02 Actions
  async function handleCreatePoint() {
    if (!newName.trim() || !newAddress.trim() || !newCity.trim()) {
      setNotice("Preencha nome, endereço e cidade.");
      return;
    }
    if (newKind === "pharmacy" && !newPharmacyId) {
      setNotice("Selecione a farmácia parceira.");
      return;
    }

    try {
      const payload: Record<string, unknown> = {
        kind: newKind,
        name: newName,
        address: newAddress,
        city: newCity,
        state: newState,
        zip_code: newZip,
        status: "active",
      };
      if (newKind === "pharmacy") {
        payload.pharmacy = Number(newPharmacyId);
      }
      if (newLat && newLng) {
        payload.latitude = parseFloat(newLat);
        payload.longitude = parseFloat(newLng);
      }

      await authedFetch("/api/v1/collection-points", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setNotice("Ponto de coleta cadastrado com sucesso!");
      setShowNewPointModal(false);
      setNewName("");
      setNewAddress("");
      setNewCity("");
      setNewZip("");
      setNewLat("");
      setNewLng("");
      setNewPharmacyId("");
      await loadAll();
    } catch (ex) {
      setNotice("Erro ao cadastrar ponto: " + (ex instanceof Error ? ex.message : ""));
    }
  }

  async function handleAddWindow(pointId: number) {
    try {
      await authedFetch(`/api/v1/collection-points/${pointId}/windows`, {
        method: "POST",
        body: JSON.stringify({
          weekday: newWeekday,
          open_time: newOpenTime,
          close_time: newCloseTime,
        }),
      });
      setNotice("Janela de funcionamento adicionada.");
      await loadAll();
    } catch (ex) {
      setNotice("Erro ao adicionar janela: " + (ex instanceof Error ? ex.message : ""));
    }
  }

  async function handleRemoveWindow(pointId: number, windowId: number) {
    try {
      await authedFetch(`/api/v1/collection-points/${pointId}/windows/${windowId}`, {
        method: "DELETE",
      });
      setNotice("Janela removida.");
      await loadAll();
    } catch (ex) {
      setNotice("Erro ao remover janela: " + (ex instanceof Error ? ex.message : ""));
    }
  }

  async function handleAssignTechnician(pointId: number) {
    if (!selectedTechToAssign) {
      setNotice("Selecione um técnico.");
      return;
    }
    try {
      await authedFetch(`/api/v1/collection-points/${pointId}/technicians`, {
        method: "POST",
        body: JSON.stringify({ technician_id: Number(selectedTechToAssign) }),
      });
      setNotice("Técnico designado com sucesso.");
      setSelectedTechToAssign("");
      await loadAll();
    } catch (ex) {
      setNotice("Erro ao designar técnico: " + (ex instanceof Error ? ex.message : ""));
    }
  }

  async function handleUnassignTechnician(pointId: number, techId: number) {
    try {
      await authedFetch(`/api/v1/collection-points/${pointId}/technicians/${techId}`, {
        method: "DELETE",
      });
      setNotice("Técnico desvinculado.");
      await loadAll();
    } catch (ex) {
      setNotice("Erro ao desvincular técnico: " + (ex instanceof Error ? ex.message : ""));
    }
  }

  // F-03 Payment Actions (Cancel link & Refund)
  async function confirmPaymentAction() {
    if (!paymentModalData) return;
    const { paymentId, action } = paymentModalData;
    setBusyId(paymentId);
    setNotice("");
    try {
      await authedFetch(`/api/v1/payments/${paymentId}/${action}`, {
        method: "POST",
        body: "{}",
      });
      setNotice(action === "cancel" ? "Link de pagamento cancelado com sucesso." : "Pagamento estornado com sucesso (comissões retidas).");
      setPaymentModalData(null);
      await loadAll();
    } catch (ex) {
      setNotice("Erro no pagamento: " + (ex instanceof Error ? ex.message : ""));
    } finally {
      setBusyId(null);
    }
  }

  const queue = reqs.filter((r) => r.status === "QUOTE_DRAFT" || r.status === "WAITING_HUMAN_VALIDATION");
  const counts: Record<string, number> = {};
  reqs.forEach((r) => { counts[r.status] = (counts[r.status] ?? 0) + 1; });

  const activePoint = points.find((p) => p.id === selectedPointId) ?? points[0];

  return (
    <Shell title="Painel do Laboratório">
      {notice && <Notice kind="ok">{notice}</Notice>}
      {err && <Notice kind="err">{err}</Notice>}

      {/* Métricas do Laboratório */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          ["Solicitações", reqs.length, "text-zinc-700"],
          ["Rascunhos / Revisão", queue.length, "text-orange-600"],
          ["Pontos de Coleta", points.length, "text-indigo-600"],
          ["Aprovadas", counts.APPROVED ?? 0, "text-sky-600"],
        ].map(([label, value, cls]) => (
          <div key={String(label)} className="rounded-xl border border-zinc-200 bg-white p-3 text-center shadow-xs">
            <p className={`text-2xl font-bold ${cls}`}>{value}</p>
            <p className="text-xs text-zinc-500">{label}</p>
          </div>
        ))}
      </div>

      {/* F-02: Gestão de Pontos de Coleta e Janelas de Funcionamento */}
      <Card
        title="Pontos de Coleta e Unidades Parceiras (D-03 / F-02)"
        actions={
          <div className="flex gap-2">
            <Button kind="ghost" onClick={() => void loadAll()}>Atualizar</Button>
            <Button kind="primary" onClick={() => setShowNewPointModal(true)}>+ Novo Ponto</Button>
          </div>
        }
      >
        {points.length === 0 ? (
          <Empty text="Nenhum ponto de coleta cadastrado no laboratório." />
        ) : (
          <div className="space-y-4">
            {/* Lista de pontos */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {points.map((p) => {
                const isSelected = activePoint?.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedPointId(p.id)}
                    className={`cursor-pointer rounded-xl border p-4 transition-all ${
                      isSelected
                        ? "border-emerald-600 bg-emerald-50/40 shadow-xs ring-1 ring-emerald-600"
                        : "border-zinc-200 bg-white hover:border-zinc-300"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-semibold text-zinc-900 text-sm">{p.name}</h4>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                        p.is_open ? "bg-emerald-100 text-emerald-800" : "bg-zinc-100 text-zinc-600"
                      }`}>
                        {p.is_open ? "● ABERTO" : "○ FECHADO"}
                      </span>
                    </div>

                    <p className="mt-1 text-xs text-zinc-500">
                      {p.kind === "pharmacy" ? `Farmácia: ${p.pharmacy_name || "Vinculada"}` : "Unidade Própria do Laboratório"}
                    </p>
                    <p className="mt-1 text-xs text-zinc-600 truncate">{p.address}, {p.city} - {p.state}</p>

                    <div className="mt-3 flex items-center justify-between border-t border-zinc-100 pt-2 text-[11px] text-zinc-500">
                      <span>{p.windows.length} janela(s)</span>
                      <span>{p.technicians.filter((t) => t.active).length} técnico(s) ativo(s)</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Painel de detalhes do ponto selecionado */}
            {activePoint && (
              <div className="mt-4 rounded-xl border border-zinc-200 bg-zinc-50 p-4 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-200 pb-3">
                  <div>
                    <h3 className="text-base font-bold text-zinc-900">{activePoint.name}</h3>
                    <p className="text-xs text-zinc-500">{activePoint.address} · {activePoint.city}/{activePoint.state} · CEP: {activePoint.zip_code || "—"}</p>
                  </div>
                  <span className="rounded-lg bg-white border border-zinc-200 px-3 py-1 text-xs font-semibold text-zinc-700">
                    Status: {activePoint.status}
                  </span>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  {/* Janelas de Atendimento */}
                  <div className="rounded-lg bg-white p-3 border border-zinc-200">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-2">
                      Janelas de Funcionamento
                    </h4>
                    {activePoint.windows.length === 0 ? (
                      <p className="text-xs text-zinc-400">Nenhuma janela cadastrada.</p>
                    ) : (
                      <div className="space-y-1.5 mb-3">
                        {activePoint.windows.map((w) => (
                          <div key={w.id} className="flex items-center justify-between rounded bg-zinc-50 px-2 py-1 text-xs text-zinc-700">
                            <span className="font-medium">{WEEKDAY_NAMES[w.weekday] ?? `Dia ${w.weekday}`}</span>
                            <span className="font-mono text-zinc-600">{w.open_time} às {w.close_time}</span>
                            <button
                              onClick={() => handleRemoveWindow(activePoint.id, w.id)}
                              className="text-[11px] text-red-600 hover:underline ml-2"
                            >
                              remover
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Adicionar nova janela */}
                    <div className="border-t border-zinc-100 pt-2 flex flex-wrap gap-2 items-center text-xs">
                      <select
                        value={newWeekday}
                        onChange={(e) => setNewWeekday(Number(e.target.value))}
                        className="rounded border border-zinc-300 p-1 text-xs bg-white"
                      >
                        {WEEKDAY_NAMES.map((name, idx) => (
                          <option key={idx} value={idx}>{name}</option>
                        ))}
                      </select>
                      <input
                        type="time"
                        value={newOpenTime}
                        onChange={(e) => setNewOpenTime(e.target.value)}
                        className="rounded border border-zinc-300 p-1 text-xs w-20 bg-white"
                      />
                      <span>às</span>
                      <input
                        type="time"
                        value={newCloseTime}
                        onChange={(e) => setNewCloseTime(e.target.value)}
                        className="rounded border border-zinc-300 p-1 text-xs w-20 bg-white"
                      />
                      <Button kind="ghost" onClick={() => handleAddWindow(activePoint.id)}>+ Adicionar</Button>
                    </div>
                  </div>

                  {/* Técnicos Designados */}
                  <div className="rounded-lg bg-white p-3 border border-zinc-200">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-2">
                      Técnicos Designados (Abertura / Turno)
                    </h4>
                    {activePoint.technicians.filter((t) => t.active).length === 0 ? (
                      <p className="text-xs text-zinc-400">Nenhum técnico ativo designado.</p>
                    ) : (
                      <div className="space-y-1.5 mb-3">
                        {activePoint.technicians.filter((t) => t.active).map((t) => (
                          <div key={t.id} className="flex items-center justify-between rounded bg-zinc-50 px-2 py-1 text-xs text-zinc-700">
                            <span className="font-medium truncate">{t.email}</span>
                            <span className="text-[10px] text-zinc-400">{fmtDate(t.assigned_at)}</span>
                            <button
                              onClick={() => handleUnassignTechnician(activePoint.id, t.id)}
                              className="text-[11px] text-red-600 hover:underline ml-2"
                            >
                              desvincular
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Designar técnico */}
                    <div className="border-t border-zinc-100 pt-2 flex gap-2 items-center text-xs">
                      <select
                        value={selectedTechToAssign}
                        onChange={(e) => setSelectedTechToAssign(e.target.value)}
                        className="flex-1 rounded border border-zinc-300 p-1 text-xs bg-white"
                      >
                        <option value="">Selecione um técnico da rede...</option>
                        {techList.map((tech) => (
                          <option key={tech.id} value={tech.id}>
                            {tech.user?.email} (COREN: {tech.coren || "S/N"})
                          </option>
                        ))}
                      </select>
                      <Button kind="ghost" onClick={() => handleAssignTechnician(activePoint.id)}>Designar</Button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Modal de Criação de Ponto de Coleta */}
      {showNewPointModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-zinc-900">Novo Ponto de Coleta</h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-zinc-700 block mb-1">Tipo de Ponto</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="pointKind"
                      value="laboratory"
                      checked={newKind === "laboratory"}
                      onChange={() => setNewKind("laboratory")}
                    />
                    Próprio (Laboratório)
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="pointKind"
                      value="pharmacy"
                      checked={newKind === "pharmacy"}
                      onChange={() => setNewKind("pharmacy")}
                    />
                    Farmácia Parceira
                  </label>
                </div>
              </div>

              {newKind === "pharmacy" && (
                <div>
                  <label className="font-semibold text-zinc-700 block mb-1">Farmácia Anfitriã</label>
                  <select
                    value={newPharmacyId}
                    onChange={(e) => setNewPharmacyId(e.target.value)}
                    className="w-full rounded-lg border border-zinc-300 p-2 text-xs bg-white"
                  >
                    <option value="">Selecione a farmácia parceira...</option>
                    {pharmacies.map((pharm) => (
                      <option key={pharm.id} value={pharm.id}>
                        {pharm.name} ({pharm.city}/{pharm.state})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="font-semibold text-zinc-700 block mb-1">Nome do Ponto</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Ex: Unidade Centro ou Farmácia São Paulo"
                  className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-zinc-700 block mb-1">Endereço Completo</label>
                <input
                  type="text"
                  value={newAddress}
                  onChange={(e) => setNewAddress(e.target.value)}
                  placeholder="Ex: Av. Paulista, 1000"
                  className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <label className="font-semibold text-zinc-700 block mb-1">Cidade</label>
                  <input
                    type="text"
                    value={newCity}
                    onChange={(e) => setNewCity(e.target.value)}
                    placeholder="São Paulo"
                    className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-zinc-700 block mb-1">UF</label>
                  <input
                    type="text"
                    value={newState}
                    maxLength={2}
                    onChange={(e) => setNewState(e.target.value.toUpperCase())}
                    className="w-full rounded-lg border border-zinc-300 p-2 text-xs uppercase"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="font-semibold text-zinc-700 block mb-1">CEP</label>
                  <input
                    type="text"
                    value={newZip}
                    onChange={(e) => setNewZip(e.target.value)}
                    placeholder="01310-100"
                    className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-zinc-700 block mb-1">Latitude</label>
                  <input
                    type="text"
                    value={newLat}
                    onChange={(e) => setNewLat(e.target.value)}
                    placeholder="-23.561"
                    className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                  />
                </div>
                <div>
                  <label className="font-semibold text-zinc-700 block mb-1">Longitude</label>
                  <input
                    type="text"
                    value={newLng}
                    onChange={(e) => setNewLng(e.target.value)}
                    placeholder="-46.656"
                    className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-zinc-100">
              <Button kind="ghost" onClick={() => setShowNewPointModal(false)}>Cancelar</Button>
              <Button kind="primary" onClick={handleCreatePoint}>Criar Ponto de Coleta</Button>
            </div>
          </div>
        </div>
      )}

      {/* F-03: Validação de Orçamentos & Gestão de Pagamentos */}
      <Card title="Validação de orçamentos e Pagamentos (F-03)" actions={<Button kind="ghost" onClick={() => void loadAll()}>Atualizar</Button>}>
        {queue.length === 0 && <Empty text="Nenhum rascunho aguardando validação." />}
        <div className="space-y-4">
          {queue.map((r) => {
            const qs = quotes[r.id] ?? [];
            const draft = [...qs].reverse().find((q) => q.quotation_type === "draft");
            const final = qs.find((q) => q.quotation_type === "final");
            const pmts = reqPayments[r.id] ?? [];

            return (
              <div key={r.id} className="rounded-xl border border-zinc-200 p-4 space-y-3 bg-white shadow-xs">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <b>{r.protocol}</b>
                  <StatusBadge status={r.status} />
                  <span className="text-xs text-zinc-500">{r.patient?.name || r.patient?.email}</span>
                  <div className="ml-auto flex gap-3 text-xs">
                    <button onClick={() => void loadQuotes(r.id)} className="text-emerald-600 hover:underline">
                      {qs.length > 0 ? "recarregar itens" : "ver itens do orçamento"}
                    </button>
                    <button onClick={() => void loadPayments(r.id)} className="text-indigo-600 hover:underline">
                      {pmts.length > 0 ? "recarregar pagamentos" : "ver pagamentos"}
                    </button>
                  </div>
                </div>

                {/* Itens de Orçamento */}
                {qs.length > 0 && (
                  <div className="space-y-2 border-t border-zinc-100 pt-3">
                    {qs.map((q) => (
                      <div key={q.id} className="rounded-lg bg-zinc-50 p-3 text-xs text-zinc-700">
                        <p className="mb-1 font-medium">
                          v{q.version} · {q.quotation_type === "final" ? "orçamento final" : "rascunho"} · total {money(q.total)}
                        </p>
                        <ul className="space-y-1">
                          {q.items.map((i, ix) => (
                            <li key={ix} className="flex justify-between border-b border-zinc-100 pb-0.5 last:border-none">
                              <span>{i.description} x{i.quantity}</span>
                              <span>{i.unit_price ? money(i.unit_price) : "SEM PREÇO"}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                    <div className="flex flex-wrap gap-2 pt-1">
                      {draft && !draft.is_final && (
                        <Button onClick={() => actQuote(draft, "validate")} disabled={busyId === draft.id}>
                          Validar (gerar orçamento final)
                        </Button>
                      )}
                      {final && final.is_validated && !final.is_sent && (
                        <Button kind="primary" onClick={() => actQuote(final, "send")} disabled={busyId === final.id}>
                          Enviar orçamento ao paciente
                        </Button>
                      )}
                    </div>
                  </div>
                )}

                {/* F-03: Pagamentos e Ações de Cancelamento / Estorno */}
                {pmts.length > 0 && (
                  <div className="border-t border-zinc-100 pt-3 space-y-2">
                    <h5 className="text-xs font-bold text-zinc-600 uppercase tracking-wider">Histórico de Pagamentos</h5>
                    {pmts.map((pmt) => (
                      <div key={pmt.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-zinc-50 p-2.5 text-xs">
                        <div className="space-x-2">
                          <span className="font-bold text-zinc-800">{money(pmt.amount)}</span>
                          <span className="text-zinc-500 font-mono">({pmt.payment_method})</span>
                          <StatusBadge status={pmt.status} />
                          <span className="text-zinc-400 text-[10px]">{fmtDate(pmt.created_at)}</span>
                        </div>

                        <div className="flex gap-2">
                          {pmt.status === "PENDING" && (
                            <Button
                              kind="danger"
                              onClick={() => setPaymentModalData({
                                paymentId: pmt.id,
                                action: "cancel",
                                protocol: r.protocol,
                                amount: pmt.amount,
                              })}
                              disabled={busyId === pmt.id}
                            >
                              Cancelar Link
                            </Button>
                          )}
                          {pmt.status === "CONFIRMED" && (
                            <Button
                              kind="danger"
                              onClick={() => setPaymentModalData({
                                paymentId: pmt.id,
                                action: "refund",
                                protocol: r.protocol,
                                amount: pmt.amount,
                              })}
                              disabled={busyId === pmt.id}
                            >
                              Estornar Pagamento
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>

      {/* Modal de Confirmação para Cancelar / Estornar Pagamento */}
      <ConfirmModal
        isOpen={Boolean(paymentModalData)}
        title={paymentModalData?.action === "cancel" ? "Cancelar Link de Pagamento" : "Estornar Pagamento Confirmado"}
        description={
          paymentModalData?.action === "cancel"
            ? `Tem certeza que deseja cancelar o link de pagamento de ${money(paymentModalData.amount)} para a solicitação ${paymentModalData.protocol}? O link expirará imediatamente.`
            : `Atenção: Você está prestes a estornar ${money(paymentModalData?.amount ?? "0")} da solicitação ${paymentModalData?.protocol ?? ""}. O status passará para REFUNDED e as comissões registradas serão mantidas para auditoria.`
        }
        confirmText={paymentModalData?.action === "cancel" ? "Sim, Cancelar Link" : "Sim, Confirmar Estorno"}
        kind="danger"
        onConfirm={() => void confirmPaymentAction()}
        onCancel={() => setPaymentModalData(null)}
      />

      {/* Demanda Evolutiva: Calendário Interativo Multi-formato (Semanal, Diário e Mensagem WhatsApp) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-zinc-900">
            📅 Calendário Integrado de Coletas (Multi-formato)
          </h2>
          <span className="text-xs text-zinc-500">{appts.length} coleta(s) registradas</span>
        </div>
        <CalendarView
          appointments={appts.map((a) => ({
            id: a.id,
            code: a.code,
            status: a.status,
            scheduled_at: a.scheduled_at,
            patient_name: a.patient?.name ?? a.patient?.email,
            location: a.location,
            pharmacy_name: a.pharmacy_name,
            technician_name: a.technician_name,
          }))}
        />
      </div>

      {/* F-04: Gestão do Catálogo de Exames (CRUD + Preços por Laboratório) */}
      <Card
        title="Catálogo Geral de Exames e Tabela de Preços (F-04)"
        actions={
          <div className="flex gap-2">
            <Button kind="ghost" onClick={() => void loadAll()}>Atualizar</Button>
            <Button kind="primary" onClick={openCreateExam}>+ Novo Exame</Button>
          </div>
        }
      >
        <div className="mb-3">
          <input
            type="text"
            placeholder="🔍 Buscar exame por código ou nome..."
            value={examSearch}
            onChange={(e) => setExamSearch(e.target.value)}
            className="w-full rounded-xl border border-zinc-200 px-3 py-2 text-xs outline-none focus:border-emerald-500"
          />
        </div>

        {exams.length === 0 ? (
          <Empty text="Nenhum exame cadastrado no catálogo." />
        ) : (
          <div className="space-y-2">
            {exams
              .filter(
                (e) =>
                  e.code.toLowerCase().includes(examSearch.toLowerCase()) ||
                  e.name.toLowerCase().includes(examSearch.toLowerCase())
              )
              .map((e) => (
                <div
                  key={e.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-xl border border-zinc-200 bg-white p-3 hover:border-zinc-300 transition-all text-sm"
                >
                  <div className="flex items-center gap-3">
                    <span className="rounded-lg bg-zinc-100 px-2 py-1 font-mono text-xs font-bold text-zinc-800">
                      {e.code}
                    </span>
                    <div>
                      <h4 className="font-semibold text-zinc-900 text-xs sm:text-sm">{e.name}</h4>
                      <p className="text-[11px] text-zinc-500">
                        Preço base definido: {e.price ? money(e.price.price) : "Ainda não precificado"}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <div className="flex items-center gap-1">
                      <span className="text-xs text-zinc-500">R$</span>
                      <input
                        type="number"
                        step="0.01"
                        value={prices[e.id] ?? e.price?.price ?? ""}
                        onChange={(ev) => setPrices({ ...prices, [e.id]: ev.target.value })}
                        placeholder="0,00"
                        className="w-20 rounded-lg border border-zinc-300 px-2 py-1 text-right text-xs outline-none focus:border-emerald-500"
                      />
                      <Button kind="ghost" onClick={() => savePrice(e.id)} disabled={busyId === e.id}>
                        Salvar
                      </Button>
                    </div>

                    <button
                      onClick={() => openEditExam(e)}
                      className="rounded-lg border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100"
                    >
                      ✏️ Editar
                    </button>

                    <button
                      onClick={() => setConfirmDeactivateExam(e)}
                      className="rounded-lg border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-100"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </Card>

      {/* F-05: Gestão de Revendedores Parceiros */}
      <Card
        title="Gestão de Revendedores Parceiros (F-05)"
        actions={
          <div className="flex gap-2">
            <Button kind="ghost" onClick={() => void loadAll()}>Atualizar</Button>
            <Button kind="primary" onClick={() => setShowResellerModal(true)}>+ Novo Revendedor</Button>
          </div>
        }
      >
        <p className="text-xs text-zinc-500 mb-3">
          Revendedores expandem a rede do laboratório, cadastrando farmácias e técnicos parceiros para coleta externa.
        </p>

        {resellers.length === 0 ? (
          <Empty text="Nenhum revendedor cadastrado neste laboratório." />
        ) : (
          <div className="space-y-2">
            {resellers.map((res) => (
              <div
                key={res.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-white p-3.5 shadow-2xs hover:border-zinc-300 transition-all text-sm"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-zinc-900">{res.name || res.email_read}</span>
                    <StatusBadge status={res.status === "active" ? "ACTIVE" : "INACTIVE"} />
                  </div>
                  <p className="text-xs text-zinc-500">
                    📧 {res.email_read} {res.created_at ? `· Cadastrado em: ${fmtDate(res.created_at)}` : ""}
                  </p>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <button
                    onClick={() => setConfirmToggleReseller(res)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                      res.status === "active"
                        ? "border border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100"
                        : "border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
                    }`}
                  >
                    {res.status === "active" ? "Desativar Revendedor" : "Ativar Revendedor"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* F-06: Trilha de Auditoria e Conformidade */}
      <Card
        title="Trilha de Auditoria e Eventos de Conformidade (F-06)"
        actions={
          <Button kind="ghost" onClick={() => void reloadAuditLogs()} disabled={auditLoading}>
            {auditLoading ? "Carregando..." : "Atualizar Logs"}
          </Button>
        }
      >
        <p className="text-xs text-zinc-500 mb-3">
          Histórico imutável de eventos sensíveis (criação de exames, pontos de coleta, aprovações, orçamentos e logins).
        </p>

        {/* Filtros de Auditoria */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4 bg-zinc-50 p-3 rounded-xl border border-zinc-200">
          <div>
            <label className="block text-[11px] font-semibold text-zinc-600 mb-1">Filtrar por Ação</label>
            <input
              type="text"
              placeholder="Ex: pharmacy.created, appointment.completed"
              value={auditFilterAction}
              onChange={(e) => setAuditFilterAction(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-2.5 py-1.5 text-xs outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-zinc-600 mb-1">Filtrar por Entidade</label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Ex: pharmacy, exam, quotation"
                value={auditFilterEntity}
                onChange={(e) => setAuditFilterEntity(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 bg-white px-2.5 py-1.5 text-xs outline-none focus:border-emerald-500"
              />
              <Button kind="primary" onClick={() => void reloadAuditLogs()} disabled={auditLoading} className="text-xs">
                Filtrar
              </Button>
            </div>
          </div>
        </div>

        {auditLogs.length === 0 ? (
          <Empty text="Nenhum registro de auditoria encontrado para os filtros selecionados." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-200 bg-zinc-100 text-zinc-700 font-bold uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Data / Hora</th>
                  <th className="py-2.5 px-3">Ação</th>
                  <th className="py-2.5 px-3">Entidade</th>
                  <th className="py-2.5 px-3">Usuário</th>
                  <th className="py-2.5 px-3">IP / Detalhes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 font-mono">
                {auditLogs.slice(0, 50).map((log) => (
                  <tr key={log.id} className="hover:bg-zinc-50 transition-colors">
                    <td className="py-2 px-3 whitespace-nowrap text-zinc-600">
                      {fmtDate(log.created_at)}
                    </td>
                    <td className="py-2 px-3 font-semibold text-zinc-900">
                      <span className="rounded bg-zinc-100 px-1.5 py-0.5 border border-zinc-200">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-zinc-700">
                      {log.entity_type} #{log.entity_id}
                    </td>
                    <td className="py-2 px-3 text-zinc-600 truncate max-w-[140px]" title={log.user?.email || "Sistema"}>
                      {log.user?.email || "Sistema"}
                    </td>
                    <td className="py-2 px-3 text-zinc-500 text-[11px] truncate max-w-[200px]" title={JSON.stringify(log.metadata || {})}>
                      {log.ip ? `${log.ip} · ` : ""}{log.metadata ? JSON.stringify(log.metadata) : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {auditLogs.length > 50 && (
              <p className="text-center text-[11px] text-zinc-400 py-2 border-t border-zinc-100">
                Exibindo os 50 registros mais recentes de {auditLogs.length}.
              </p>
            )}
          </div>
        )}
      </Card>

      {/* Lançamentos de Comissão */}
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
      {/* Modal de Criação / Edição de Exame (F-04) */}
      {showExamModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-zinc-900">
              {examModalMode === "create" ? "Cadastrar Novo Exame" : `Editar Exame: ${examCode}`}
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-zinc-700 block mb-1">Código do Exame (Ex: HEMO, GLIC)</label>
                <input
                  type="text"
                  value={examCode}
                  disabled={examModalMode === "edit"}
                  onChange={(e) => setExamCode(e.target.value.toUpperCase())}
                  placeholder="HEMO"
                  className="w-full rounded-lg border border-zinc-300 p-2 text-xs font-mono uppercase disabled:bg-zinc-100"
                />
                {examModalMode === "edit" && (
                  <p className="mt-1 text-[11px] text-zinc-400">O código do exame é imutável após a criação.</p>
                )}
              </div>

              <div>
                <label className="font-semibold text-zinc-700 block mb-1">Nome do Exame</label>
                <input
                  type="text"
                  value={examName}
                  onChange={(e) => setExamName(e.target.value)}
                  placeholder="Hemograma Completo com Plaquetas"
                  className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-zinc-100">
              <Button kind="ghost" onClick={() => setShowExamModal(false)}>Cancelar</Button>
              <Button kind="primary" onClick={handleSaveExam} disabled={busyId !== null}>
                {examModalMode === "create" ? "Cadastrar Exame" : "Salvar Alterações"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmação de Desativação de Exame (Soft Delete) */}
      <ConfirmModal
        isOpen={Boolean(confirmDeactivateExam)}
        title={`Desativar Exame ${confirmDeactivateExam?.code}`}
        description={`Tem certeza que deseja desativar o exame "${confirmDeactivateExam?.name}"? O exame não aparecerá mais para novos orçamentos, mas todo o histórico e orçamentos anteriores serão preservados integralmente.`}
        confirmText="Sim, Desativar Exame"
        kind="danger"
        onConfirm={() => void handleDeactivateExam()}
        onCancel={() => setConfirmDeactivateExam(null)}
      />
      {/* Modal de Criação de Revendedor (F-05) */}
      {showResellerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-zinc-900">Cadastrar Novo Revendedor Parceiro</h3>
            <p className="text-xs text-zinc-500">
              O revendedor terá acesso ao painel do revendedor (/revendedor) para cadastrar suas próprias farmácias e técnicos vinculados ao seu laboratório.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-zinc-700 block mb-1">Nome do Responsável / Razão Social</label>
                <input
                  type="text"
                  value={resellerFirstName}
                  onChange={(e) => setResellerFirstName(e.target.value)}
                  placeholder="Distribuidora Saúde Total Ltda"
                  className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-zinc-700 block mb-1">E-mail Corporativo de Acesso</label>
                <input
                  type="email"
                  value={resellerEmail}
                  onChange={(e) => setResellerEmail(e.target.value)}
                  placeholder="contato@distribuidorasaude.com.br"
                  className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-zinc-700 block mb-1">Senha Inicial de Acesso</label>
                <input
                  type="password"
                  value={resellerPassword}
                  onChange={(e) => setResellerPassword(e.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  className="w-full rounded-lg border border-zinc-300 p-2 text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-zinc-100">
              <Button kind="ghost" onClick={() => setShowResellerModal(false)}>Cancelar</Button>
              <Button kind="primary" onClick={handleCreateReseller} disabled={busyId !== null}>
                Cadastrar Revendedor
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmação de Alteração de Status de Revendedor */}
      <ConfirmModal
        isOpen={Boolean(confirmToggleReseller)}
        title={confirmToggleReseller?.status === "active" ? "Desativar Revendedor" : "Ativar Revendedor"}
        description={`Deseja realmente ${confirmToggleReseller?.status === "active" ? "desativar" : "ativar"} o revendedor "${confirmToggleReseller?.name || confirmToggleReseller?.email_read}"? ${
          confirmToggleReseller?.status === "active"
            ? "Ele não conseguirá gerenciar novas farmácias nem emitir orçamentos enquanto estiver inativo."
            : "Ele voltará a ter acesso total à gestão da sua rede vinculada."
        }`}
        confirmText={confirmToggleReseller?.status === "active" ? "Sim, Desativar" : "Sim, Ativar"}
        kind={confirmToggleReseller?.status === "active" ? "danger" : "primary"}
        onConfirm={() => void handleToggleResellerStatus()}
        onCancel={() => setConfirmToggleReseller(null)}
      />

      {/* F-07: Contatos WhatsApp por Perfil (Laboratório Central) */}
      <WhatsAppContactsCard ownerKind="laboratory" title="Canais Oficiais de WhatsApp do Laboratório (F-07)" />

    </Shell>
  );
}
