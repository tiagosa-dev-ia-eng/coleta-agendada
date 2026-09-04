"use client";

import { useEffect, useState } from "react";
import { authedFetch } from "@/lib/auth";

export interface WhatsAppContact {
  id: number;
  owner_kind: "laboratory" | "pharmacy" | "technician" | "reseller";
  number: string;
  name: string;
  meta_bsuid?: string;
  is_main: boolean;
  created_at?: string;
  updated_at?: string;
}

interface Props {
  ownerKind: "laboratory" | "pharmacy" | "technician" | "reseller";
  ownerId?: number;
  title?: string;
}

export default function WhatsAppContactsCard({ ownerKind, title }: Props) {
  const [contacts, setContacts] = useState<WhatsAppContact[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Form states
  const [number, setNumber] = useState("");
  const [name, setName] = useState("");
  const [metaBsuid, setMetaBsuid] = useState("");
  const [isMain, setIsMain] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const loadContacts = async () => {
    setLoading(true);
    try {
      const data = await authedFetch<WhatsAppContact[]>("/api/v1/whatsapp/contacts");
      // Filtra os contatos pertinentes ao perfil se vier lista agregada
      const filtered = Array.isArray(data)
        ? data.filter((c) => c.owner_kind === ownerKind)
        : [];
      setContacts(filtered);
    } catch {
      // Ignora ou mantém lista
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContacts();
  }, [ownerKind]);

  const resetForm = () => {
    setNumber("");
    setName("");
    setMetaBsuid("");
    setIsMain(false);
    setEditingId(null);
    setShowAddForm(false);
    setErrorMsg("");
  };

  const handleStartEdit = (contact: WhatsAppContact) => {
    setEditingId(contact.id);
    setNumber(contact.number);
    setName(contact.name);
    setMetaBsuid(contact.meta_bsuid || "");
    setIsMain(contact.is_main);
    setShowAddForm(true);
    setErrorMsg("");
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!number.trim()) {
      setErrorMsg("Informe o número de telefone com DDD.");
      return;
    }

    setSaving(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const payload: Record<string, unknown> = {
        number: number.replace(/\D/g, ""),
        name: name.trim() || "Canal de Atendimento",
        meta_bsuid: metaBsuid.trim(),
        is_main: isMain,
      };

      if (editingId) {
        // Edição parcial
        await authedFetch<WhatsAppContact>(`/api/v1/whatsapp/contacts/${editingId}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
        setSuccessMsg("Contato WhatsApp atualizado com sucesso!");
      } else {
        // Novo cadastro
        payload.owner_kind = ownerKind;
        if (ownerKind === "laboratory") payload.laboratory = 1;
        if (ownerKind === "pharmacy") payload.pharmacy = 1;
        if (ownerKind === "technician") payload.technician = 1;
        if (ownerKind === "reseller") payload.reseller = 1;

        await authedFetch<WhatsAppContact>("/api/v1/whatsapp/contacts", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setSuccessMsg("Novo canal de WhatsApp cadastrado com sucesso!");
      }

      resetForm();
      await loadContacts();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao salvar contato";
      setErrorMsg(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Deseja realmente remover este canal de WhatsApp?")) return;
    try {
      await authedFetch(`/api/v1/whatsapp/contacts/${id}`, { method: "DELETE" });
      setSuccessMsg("Contato removido com sucesso.");
      await loadContacts();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao excluir contato";
      setErrorMsg(msg);
    }
  };

  const handleMakeMain = async (id: number) => {
    try {
      await authedFetch(`/api/v1/whatsapp/contacts/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_main: true }),
      });
      setSuccessMsg("Definido como canal principal.");
      await loadContacts();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro ao atualizar";
      setErrorMsg(msg);
    }
  };

  const formatPhone = (phone: string) => {
    const digits = phone.replace(/\D/g, "");
    if (digits.length === 13) {
      return `+${digits.slice(0, 2)} (${digits.slice(2, 4)}) ${digits.slice(4, 9)}-${digits.slice(9)}`;
    }
    if (digits.length === 11) {
      return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
    }
    return phone;
  };

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700 text-sm font-bold">
              📱
            </span>
            <h2 className="text-base font-bold text-zinc-900">
              {title || "Canais de WhatsApp (F-07 / D-04)"}
            </h2>
            <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
              Meta Cloud API
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            Gerenciamento de números oficiais e BSUID para atendimento inteligente de coletas.
          </p>
        </div>

        {!showAddForm && (
          <button
            onClick={() => {
              resetForm();
              setShowAddForm(true);
            }}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-emerald-700"
          >
            <span>+</span>
            <span>Novo Canal WhatsApp</span>
          </button>
        )}
      </div>

      {successMsg && (
        <div className="mt-3 flex items-center justify-between rounded-xl bg-emerald-50 px-3 py-2 text-xs text-emerald-800 border border-emerald-200">
          <span>✓ {successMsg}</span>
          <button onClick={() => setSuccessMsg("")} className="font-bold text-emerald-600 hover:text-emerald-900">
            ✕
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="mt-3 flex items-center justify-between rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-800 border border-rose-200">
          <span>⚠ {errorMsg}</span>
          <button onClick={() => setErrorMsg("")} className="font-bold text-rose-600 hover:text-rose-900">
            ✕
          </button>
        </div>
      )}

      {/* Formulário de Criação / Edição */}
      {showAddForm && (
        <form onSubmit={handleSave} className="mt-4 rounded-xl border border-zinc-200 bg-zinc-50/70 p-4">
          <div className="flex items-center justify-between border-b border-zinc-200 pb-2 mb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-700">
              {editingId ? "Editar Canal WhatsApp" : "Novo Canal WhatsApp"}
            </h3>
            <button
              type="button"
              onClick={resetForm}
              className="text-xs text-zinc-500 hover:text-zinc-800 font-medium"
            >
              Cancelar
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Número com DDD (ex.: 5511999998888) *
              </label>
              <input
                type="text"
                required
                value={number}
                onChange={(e) => setNumber(e.target.value)}
                placeholder="5511999998888"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Nome de Identificação do Canal
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex.: Central de Agendamento SP"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:outline-hidden"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-700 mb-1">
                Meta BSUID (Opcional - Cloud API)
              </label>
              <input
                type="text"
                value={metaBsuid}
                onChange={(e) => setMetaBsuid(e.target.value)}
                placeholder="Ex.: @coletacentral.atendimento"
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-500 focus:outline-hidden"
              />
            </div>

            <div className="flex items-center sm:pt-5">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-zinc-800">
                <input
                  type="checkbox"
                  checked={isMain}
                  onChange={(e) => setIsMain(e.target.checked)}
                  className="h-4 w-4 rounded border-zinc-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span>Definir como contato principal deste perfil</span>
              </label>
            </div>
          </div>

          <div className="mt-4 flex justify-end gap-2">
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 hover:bg-zinc-100"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50"
            >
              {saving ? "Salvando..." : editingId ? "Salvar Alterações" : "Cadastrar Canal"}
            </button>
          </div>
        </form>
      )}

      {/* Lista de Contatos */}
      <div className="mt-4 space-y-2">
        {loading ? (
          <p className="py-4 text-center text-xs text-zinc-400">Carregando canais de WhatsApp...</p>
        ) : contacts.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-200 py-6 text-center text-xs text-zinc-500">
            <p>Nenhum canal de WhatsApp cadastrado para este perfil.</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-2 text-xs font-semibold text-emerald-600 hover:underline"
            >
              + Adicionar primeiro canal de WhatsApp
            </button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-zinc-200">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-semibold text-zinc-600">
                <tr>
                  <th className="py-2.5 px-3">Canal / Nome</th>
                  <th className="py-2.5 px-3">Número Formatado</th>
                  <th className="py-2.5 px-3">Meta BSUID</th>
                  <th className="py-2.5 px-3 text-center">Status</th>
                  <th className="py-2.5 px-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {contacts.map((c) => (
                  <tr key={c.id} className="hover:bg-zinc-50/60 transition">
                    <td className="py-2.5 px-3 font-semibold text-zinc-900">
                      <div className="flex items-center gap-2">
                        <span>{c.name || "Canal de WhatsApp"}</span>
                        {c.is_main && (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 border border-emerald-300">
                            Principal
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-zinc-700">
                      {formatPhone(c.number)}
                    </td>
                    <td className="py-2.5 px-3">
                      {c.meta_bsuid ? (
                        <span className="rounded bg-zinc-100 px-2 py-0.5 font-mono text-[11px] text-zinc-700">
                          {c.meta_bsuid}
                        </span>
                      ) : (
                        <span className="text-zinc-400">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        Conectado
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <div className="inline-flex items-center gap-1.5">
                        {!c.is_main && (
                          <button
                            onClick={() => handleMakeMain(c.id)}
                            title="Definir como contato principal"
                            className="rounded px-2 py-1 text-[11px] font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
                          >
                            Tornar Principal
                          </button>
                        )}
                        <button
                          onClick={() => handleStartEdit(c)}
                          className="rounded px-2 py-1 text-[11px] font-medium text-emerald-600 hover:bg-emerald-50 hover:text-emerald-800"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(c.id)}
                          className="rounded px-2 py-1 text-[11px] font-medium text-rose-600 hover:bg-rose-50 hover:text-rose-800"
                        >
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
