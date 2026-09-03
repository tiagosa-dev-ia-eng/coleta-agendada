"use client";

import { useState } from "react";

import { API_URL } from "@/lib/api";
import { ROLE_HOME, setToken } from "@/lib/auth";

const DEMO = [
  { label: "Paciente", email: "paciente@coleta.local", role: "patient" },
  { label: "Laboratório", email: "lab@coleta.local", role: "laboratory" },
  { label: "Farmácia", email: "farm-lab@demo.local", role: "pharmacy" },
  { label: "Técnico", email: "tec@demo.local", role: "technician" },
  { label: "Revendedor", email: "rev@demo.local", role: "reseller" },
];

type LoginResp = { access: string; user: { role: { code: string } | null } };

export default function Login() {
  const [email, setEmail] = useState("paciente@coleta.local");
  const [password, setPassword] = useState("SenhaForte123!");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function doLogin(em: string, pw: string) {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: em, password: pw }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as { error?: { message?: string } } | null;
        setError(data?.error?.message ?? "Falha no login.");
        return;
      }
      const data = (await res.json()) as LoginResp;
      setToken(data.access);
      const role = (data.user.role?.code ?? "patient") as keyof typeof ROLE_HOME;
      window.location.assign(ROLE_HOME[role] ?? "/paciente");
    } catch {
      setError("Não foi possível conectar ao backend.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-xl font-bold text-emerald-700">Coleta Agendada</h1>
        <p className="mt-1 text-sm text-zinc-500">Acesso por perfil (homologação M9)</p>
        <div className="mt-5 space-y-3">
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="e-mail"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="senha"
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
          <button onClick={() => doLogin(email, password)} disabled={busy}
            className="w-full rounded-lg bg-emerald-600 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50">
            {busy ? "Entrando…" : "Entrar"}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
        <p className="mt-5 text-xs text-zinc-400">Entrar como demo:</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {DEMO.map((d) => (
            <button key={d.role} onClick={() => doLogin(d.email, "SenhaForte123!")}
              className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs text-emerald-700 hover:bg-emerald-100">
              {d.label}
            </button>
          ))}
        </div>
      </div>
    </main>
  );
}