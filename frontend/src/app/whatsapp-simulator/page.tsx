"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { API_URL } from "@/lib/api";

type Msg = {
  id: number;
  direction: "inbound" | "outbound";
  content: string;
  ai_used_mock?: boolean;
  ai_model?: string;
  created_at: string;
};

const SUGGESTIONS = [
  "Quero agendar coleta de hemograma amanhã de manhã",
  "Quero coleta de glicemia e TSH em casa hoje à tarde",
  "Qual o status da minha solicitação?",
  "Qual o local de coleta mais próximo da minha localização?",
  "Oi, tudo bem?",
];

export default function WhatsappSimulator() {
  const [email, setEmail] = useState("paciente@coleta.local");
  const [password, setPassword] = useState("SenhaForte123!");
  const [phone, setPhone] = useState("5511999990001");
  const [token, setToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [notice, setNotice] = useState("");
  const [lat, setLat] = useState("-23.5505"); // demo: centro de São Paulo
  const [lon, setLon] = useState("-46.6333");
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadMessages = useCallback(
    async (authToken: string, fromPhone: string) => {
      try {
        const res = await fetch(
          `${API_URL}/api/v1/whatsapp/conversations/by-phone/${fromPhone}`,
          { headers: { Authorization: `Bearer ${authToken}` }, cache: "no-store" }
        );
        if (res.ok) {
          const data = (await res.json()) as { messages: Msg[] };
          setMessages(data.messages);
        }
      } catch {
        // backend indisponível — mantém histórico local
      }
    },
    []
  );

  async function login() {
    setNotice("");
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        setNotice("Falha no login. Verifique e-mail/senha.");
        return;
      }
      const data = (await res.json()) as { access: string };
      setToken(data.access);
      await loadMessages(data.access, phone);
    } catch {
      setNotice("Não foi possível conectar ao backend (" + API_URL + ").");
    } finally {
      setBusy(false);
    }
  }

  async function send(text: string) {
    if (!token || !text.trim()) return;
    const body = text.trim();
    setInput("");
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/webhooks/whatsapp`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          from: phone,
          body,
          provider: "simulator",
        }),
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => null)) as { error?: { message?: string } } | null;
        setNotice("Erro no envio: " + (err?.error?.message ?? res.statusText));
        return;
      }
      setNotice("");
      await loadMessages(token, phone);
    } catch {
      setNotice("Falha de rede ao enviar a mensagem.");
    } finally {
      setBusy(false);
    }
  }


  async function sendLocation() {
    if (!token) return;
    const latitude = Number(lat.replace(",", "."));
    const longitude = Number(lon.replace(",", "."));
    if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
      setNotice("Localização inválida — use latitude e longitude numéricas.");
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/webhooks/whatsapp`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          from: phone,
          location: { latitude, longitude },
          provider: "simulator",
        }),
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => null)) as { error?: { message?: string } } | null;
        setNotice("Erro no envio da localização: " + (err?.error?.message ?? res.statusText));
        return;
      }
      setNotice("");
      await loadMessages(token, phone);
    } catch {
      setNotice("Falha de rede ao enviar a localização.");
    } finally {
      setBusy(false);
    }
  }

  async function limparMemoria() {
    if (!token) return;
    if (!window.confirm("Limpar a memória da conversa? As mensagens serão apagadas e o chatbot recomeça do zero.")) {
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/v1/whatsapp/conversations/by-phone/${phone}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => null)) as { error?: { message?: string } } | null;
        setNotice("Erro ao limpar: " + (err?.error?.message ?? res.statusText));
        return;
      }
      setMessages([]);
      setNotice("Memória limpa — conversa reiniciada.");
    } catch {
      setNotice("Falha de rede ao limpar a conversa.");
    }
  }

  // polling suave enquanto autenticado (simula o recebimento da resposta)
  useEffect(() => {
    if (!token) return;
    const timer = window.setInterval(() => loadMessages(token, phone), 3000);
    return () => window.clearInterval(timer);
  }, [token, phone, loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!token) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-900 px-4 py-10">
        <div className="w-full max-w-md rounded-2xl border border-zinc-700 bg-zinc-800 p-8">
          <h1 className="text-xl font-semibold text-white">WhatsApp Simulator</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Homologação interna do M8 — conversa com a IA do Coleta Agendada.
          </p>
          <p className="mt-3 rounded bg-amber-500/15 p-2 text-xs text-amber-300">
            Entrar como paciente demo. O simulador envia mensagens ao webhook
            próprio (provider &quot;simulator&quot;) até o provedor real (G-05).
          </p>
          <div className="mt-5 space-y-3">
            <input className="w-full rounded bg-zinc-900 px-3 py-2 text-sm text-white outline-none ring-1 ring-zinc-600 focus:ring-emerald-500" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="e-mail" />
            <input type="password" className="w-full rounded bg-zinc-900 px-3 py-2 text-sm text-white outline-none ring-1 ring-zinc-600 focus:ring-emerald-500" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="senha" />
            <input className="w-full rounded bg-zinc-900 px-3 py-2 text-sm text-white outline-none ring-1 ring-zinc-600 focus:ring-emerald-500" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="telefone (identificador do canal)" />
            <button onClick={login} disabled={busy} className="w-full rounded bg-emerald-600 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50">
              {busy ? "Conectando…" : "Entrar no simulador"}
            </button>
          </div>
          {notice && <p className="mt-3 text-sm text-amber-300">{notice}</p>}
        </div>
      </main>
    );
  }

  return (
    <main className="flex h-screen flex-col bg-zinc-900">
      <header className="flex items-center justify-between border-b border-zinc-700 bg-emerald-700 px-4 py-3">
        <div>
          <p className="text-sm font-semibold text-white">WhatsApp Simulator · Coleta Agendada</p>
          <p className="text-xs text-emerald-100">
            Homologação interna (M8) — canal: {phone} · provider simulator
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={limparMemoria}
            title="Zera a conversa com o chatbot (homologação)"
            className="rounded border border-white/30 px-3 py-1 text-xs text-white hover:bg-white/10"
          >
            🧹 Limpar memória
          </button>
          <button onClick={() => setToken(null)} className="rounded bg-black/20 px-3 py-1 text-xs text-white hover:bg-black/30">
            Sair
          </button>
        </div>
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <p className="mt-8 text-center text-sm text-zinc-500">
            Inicie a conversa (ex.: &quot;Quero agendar coleta de hemograma amanhã de manhã&quot;)
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.direction === "outbound" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${m.direction === "outbound" ? "bg-emerald-600 text-white" : "bg-zinc-800 text-zinc-100"}`}>
              {m.content}
              {m.ai_used_mock && m.direction === "outbound" && (
                <p className="mt-1 text-[10px] opacity-60">IA simulada (sem chave DeepSeek)</p>
              )}
              {m.ai_model && m.direction === "outbound" && !m.ai_used_mock && (
                <p className="mt-1 text-[10px] opacity-60">modelo: {m.ai_model}</p>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="flex flex-wrap gap-2 px-4 pb-2">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => send(s)} disabled={busy} className="rounded-full border border-zinc-600 px-3 py-1 text-xs text-zinc-300 hover:border-emerald-500 hover:text-emerald-300">
            {s}
          </button>
        ))}
      </div>
      <div className="border-t border-zinc-800 px-4 py-2">
        <p className="text-[11px] uppercase tracking-wide text-zinc-500">
          📍 Localização (D-01 — local de coleta mais próximo)
        </p>
        <div className="mt-1 flex items-center gap-2">
          <input
            className="w-28 rounded bg-zinc-800 px-2 py-1 text-xs text-white outline-none ring-1 ring-zinc-600 focus:ring-emerald-500"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            placeholder="latitude"
            title="Latitude (ex.: -23.5505)"
          />
          <input
            className="w-28 rounded bg-zinc-800 px-2 py-1 text-xs text-white outline-none ring-1 ring-zinc-600 focus:ring-emerald-500"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            placeholder="longitude"
            title="Longitude (ex.: -46.6333)"
          />
          <button
            onClick={sendLocation}
            disabled={busy}
            className="rounded bg-emerald-700 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-40"
          >
            Enviar localização
          </button>
        </div>
      </div>
      <div className="border-t border-zinc-700 p-3">
        {notice && <p className="mb-2 text-xs text-amber-300">{notice}</p>}
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-full bg-zinc-800 px-4 py-2 text-sm text-white outline-none ring-1 ring-zinc-600 focus:ring-emerald-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder="Mensagem…"
          />
          <button onClick={() => send(input)} disabled={busy || !input.trim()} className="rounded-full bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-40">
            ➤
          </button>
        </div>
      </div>
    </main>
  );
}