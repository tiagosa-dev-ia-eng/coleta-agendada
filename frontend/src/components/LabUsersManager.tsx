"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Button, Card, Empty, Notice, StatusBadge, fmtDate } from "@/components/ui";
import { authedFetch } from "@/lib/auth";

export interface LabUser {
  id: number;
  email: string;
  name: string;
  role: { code: string; name: string };
  is_active: boolean;
  date_joined?: string;
  created_at?: string;
}

interface LabUsersManagerProps {
  onBackToHome: () => void;
  isAdmin: boolean;
}

export default function LabUsersManager({ onBackToHome, isAdmin }: LabUsersManagerProps) {
  const [users, setUsers] = useState<LabUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [err, setErr] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  // Modal de novo usuário
  const [showModal, setShowModal] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [roleCode, setRoleCode] = useState("laboratory_attendant");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadUsers = async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await authedFetch<LabUser[]>("/api/v1/users");
      setUsers(data || []);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Erro ao carregar usuários.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadUsers();
  }, []);

  const handleCreateUser = async (e: FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || !email.trim()) {
      setErr("Preencha nome completo e e-mail.");
      return;
    }

    setSubmitting(true);
    setErr("");
    try {
      await authedFetch<LabUser>("/api/v1/users", {
        method: "POST",
        body: JSON.stringify({
          name: fullName.trim(),
          full_name: fullName.trim(),
          email: email.trim().toLowerCase(),
          role: roleCode,
          role_code: roleCode,
          password: password.trim() || "Mudar@123456",
          is_active: true,
        }),
      });

      setNotice(`Usuário ${fullName} criado com sucesso no laboratório!`);
      setShowModal(false);
      setFullName("");
      setEmail("");
      setPassword("");
      setRoleCode("laboratory_attendant");
      await loadUsers();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Erro ao cadastrar usuário.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (user: LabUser) => {
    setErr("");
    try {
      await authedFetch<LabUser>(`/api/v1/users/${user.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      setNotice(
        `Usuário ${user.name || user.email} ${
          !user.is_active ? "ativado" : "desativado"
        } com sucesso.`
      );
      await loadUsers();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Erro ao atualizar status do usuário.");
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchSearch =
      (u.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchRole =
      roleFilter === "all" ||
      u.role?.code === roleFilter ||
      (roleFilter === "admin" && (u.role?.code === "laboratory_admin" || u.role?.code === "admin")) ||
      (roleFilter === "attendant" && (u.role?.code === "laboratory_attendant" || u.role?.code === "attendant"));
    return matchSearch && matchRole;
  });

  if (!isAdmin) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 border-b border-zinc-200 pb-3">
          <Button kind="ghost" onClick={onBackToHome} className="gap-1.5 text-xs font-bold">
            ← Voltar ao Hub do Laboratório
          </Button>
        </div>
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center text-amber-900">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-2xl">
            🔒
          </div>
          <h3 className="mt-3 text-lg font-bold">Acesso Restrito ao Administrador</h3>
          <p className="mt-1 text-sm text-amber-700 max-w-md mx-auto">
            O módulo de Cadastro e Gestão de Usuários é restrito ao perfil de Administrador / Gestor do
            Laboratório (permissão RBAC <code>user.manage</code>).
          </p>
          <div className="mt-4">
            <Button kind="primary" onClick={onBackToHome}>
              Voltar à Tela Inicial
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {notice && <Notice kind="ok">{notice}</Notice>}
      {err && <Notice kind="err">{err}</Notice>}

      {/* Topo com navegação */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-200 pb-4">
        <div className="flex items-center gap-3">
          <Button kind="ghost" onClick={onBackToHome} className="gap-1.5 text-xs font-bold">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Voltar ao Hub do Laboratório
          </Button>
          <span className="text-zinc-300">|</span>
          <div>
            <h2 className="text-xl font-black text-zinc-900 tracking-tight">Cadastro de Usuários</h2>
            <p className="text-xs text-zinc-500">Gestão de acessos, administradores e atendentes do laboratório</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button kind="ghost" onClick={() => void loadUsers()} disabled={loading}>
            {loading ? "Carregando…" : "Atualizar"}
          </Button>
          <Button kind="primary" onClick={() => setShowModal(true)}>
            + Novo Usuário
          </Button>
        </div>
      </div>

      {/* Barra de Filtros e Busca */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-zinc-200 bg-white p-3 shadow-xs">
        <div className="flex-1 max-w-md">
          <input
            type="text"
            placeholder="Buscar por nome ou e-mail…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-1.5 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto">
          <span className="text-xs text-zinc-500 font-semibold whitespace-nowrap">Filtrar cargo:</span>
          {[
            { id: "all", label: "Todos" },
            { id: "admin", label: "Administradores" },
            { id: "attendant", label: "Atendentes" },
            { id: "technician", label: "Técnicos" },
          ].map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => setRoleFilter(r.id)}
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition cursor-pointer whitespace-nowrap ${
                roleFilter === r.id
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tabela de Usuários */}
      <Card title={`Usuários Cadastrados (${filteredUsers.length})`}>
        {loading ? (
          <div className="py-8 text-center text-xs text-zinc-500">Carregando lista de usuários…</div>
        ) : filteredUsers.length === 0 ? (
          <Empty text="Nenhum usuário encontrado com os filtros selecionados." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-[11px] font-bold text-zinc-600 uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Nome / Operador</th>
                  <th className="px-4 py-2.5">E-mail de Acesso</th>
                  <th className="px-4 py-2.5">Perfil de Acesso</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Cadastrado em</th>
                  <th className="px-4 py-2.5 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {filteredUsers.map((u) => {
                  const isAdminRole = u.role?.code === "laboratory_admin" || u.role?.code === "admin";
                  const isAttendantRole = u.role?.code === "laboratory_attendant" || u.role?.code === "attendant";

                  return (
                    <tr key={u.id} className="hover:bg-zinc-50/80 transition">
                      <td className="px-4 py-3 font-semibold text-zinc-900">
                        <div className="flex items-center gap-2">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                            {(u.name || u.email || "U").slice(0, 2).toUpperCase()}
                          </div>
                          <span>{u.name || "Sem nome cadastrado"}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-zinc-600 font-mono text-[11px]">{u.email}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold ${
                            isAdminRole
                              ? "bg-purple-100 text-purple-800"
                              : isAttendantRole
                              ? "bg-blue-100 text-blue-800"
                              : "bg-zinc-100 text-zinc-700"
                          }`}
                        >
                          {u.role?.name || (isAdminRole ? "Administrador / Gestor" : "Atendente")}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                            u.is_active
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              u.is_active ? "bg-emerald-600" : "bg-rose-600"
                            }`}
                          />
                          {u.is_active ? "Ativo" : "Inativo"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-500 text-[11px]">
                        {u.date_joined || u.created_at ? fmtDate(u.date_joined || u.created_at || "") : "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => void handleToggleActive(u)}
                          className={`rounded-lg px-2.5 py-1 text-[11px] font-bold transition cursor-pointer ${
                            u.is_active
                              ? "border border-zinc-200 text-zinc-600 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200"
                              : "border border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
                          }`}
                        >
                          {u.is_active ? "Desativar" : "Ativar"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal de Criação de Novo Usuário */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <h3 className="text-base font-bold text-zinc-900">Novo Usuário do Laboratório</h3>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="text-zinc-400 hover:text-zinc-600 text-lg font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-zinc-700 mb-1">Nome Completo *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex.: Dra. Fernanda Vasconcelos"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-xl border border-zinc-300 p-2.5 text-xs text-zinc-900 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                />
              </div>

              <div>
                <label className="block font-semibold text-zinc-700 mb-1">E-mail de Acesso *</label>
                <input
                  type="email"
                  required
                  placeholder="Ex.: fernanda.triagem@laboratorio.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-zinc-300 p-2.5 text-xs text-zinc-900 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                />
              </div>

              <div>
                <label className="block font-semibold text-zinc-700 mb-1">Perfil / Cargo *</label>
                <select
                  value={roleCode}
                  onChange={(e) => setRoleCode(e.target.value)}
                  className="w-full rounded-xl border border-zinc-300 p-2.5 text-xs text-zinc-900 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                >
                  <option value="laboratory_attendant">Atendente / Triagem de Orçamentos</option>
                  <option value="laboratory_admin">Administrador / Gestor do Laboratório</option>
                  <option value="technician">Técnico de Coleta e Enfermagem</option>
                </select>
                <p className="mt-1 text-[11px] text-zinc-500">
                  {roleCode === "laboratory_admin"
                    ? "Acesso irrestrito a todos os formulários e configurações administrativas."
                    : "Acesso focado na validação de orçamentos, agendamentos e catálogo de exames."}
                </p>
              </div>

              <div>
                <label className="block font-semibold text-zinc-700 mb-1">Senha Provisória</label>
                <input
                  type="password"
                  placeholder="Deixe em branco para senha padrão: Mudar@123456"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-zinc-300 p-2.5 text-xs text-zinc-900 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                />
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-zinc-100 pt-3">
                <Button kind="ghost" type="button" onClick={() => setShowModal(false)}>
                  Cancelar
                </Button>
                <Button kind="primary" type="submit" disabled={submitting}>
                  {submitting ? "Cadastrando…" : "Cadastrar Usuário"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
