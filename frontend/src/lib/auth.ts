"use client";

import { API_URL } from "./api";
import { handleMockFallback } from "./mockInterceptor";
import { getMockData, saveMockData } from "./mockBackend";

export const TOKEN_KEY = "ca_token";
export const DEMO_ROLE_KEY = "ca_demo_role";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  if (window.localStorage.getItem("ca_logged_out") === "true") {
    return null;
  }
  const stored = window.localStorage.getItem(TOKEN_KEY);
  if (stored) return stored;
  // No modo preview do AI Studio, se não houve logout explícito, inicializa com token de demonstração
  const defaultToken = "demo_preview_token_laboratory";
  window.localStorage.setItem(TOKEN_KEY, defaultToken);
  return defaultToken;
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("ca_logged_out");
  window.localStorage.setItem(TOKEN_KEY, token);
  window.dispatchEvent(new CustomEvent("ca:login", { detail: { token } }));
}

export function clearToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(DEMO_ROLE_KEY);
  window.localStorage.setItem("ca_logged_out", "true");
  window.dispatchEvent(new CustomEvent("ca:logout"));
  if (window.location.hash !== undefined && (window.location.pathname === "/" || window.location.pathname === "")) {
    window.location.hash = "login";
  } else {
    window.location.assign("/login");
  }
}

export function isAuthed(): boolean {
  return Boolean(getToken());
}

export function setDemoRole(role: RoleCode) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DEMO_ROLE_KEY, role);
  const data = getMockData();
  const roleNames: Record<RoleCode, string> = {
    laboratory: "Laboratório Central",
    pharmacy: "Farmácia DrogaMais Jardins",
    technician: "Enf. Rodrigo Pires",
    reseller: "Distribuidora FarmaSul SP",
    patient: "Mariana Souza e Silva",
  };
  data.me = {
    id: 1,
    email: `${role}@coletaagendada.com.br`,
    name: roleNames[role],
    role: { code: role, name: ROLE_LABEL[role] || role },
  };
  saveMockData(data);
}

export async function authedFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
    if (res.status === 401) {
      clearToken();
      throw new Error("Sessão expirada — faça login novamente.");
    }
    if (!res.ok) {
      let msg = res.statusText;
      try {
        const body = (await res.json()) as { error?: { message?: string } };
        msg = body.error?.message ?? res.statusText;
      } catch {
        // corpo não-JSON
      }
      throw new Error(msg);
    }
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof Error && err.message.includes("Sessão expirada")) {
      throw err;
    }
    // Em caso de falha de rede/porta 8000 fechada, atende com dados do mock local
    return handleMockFallback<T>(path, init);
  }
}

export type RoleCode = "laboratory" | "reseller" | "pharmacy" | "technician" | "patient";

export const ROLE_HOME: Record<RoleCode, string> = {
  laboratory: "/laboratorio",
  reseller: "/revendedor",
  pharmacy: "/farmacia",
  technician: "/tecnico",
  patient: "/paciente",
};

export const ROLE_LABEL: Record<string, string> = {
  laboratory: "Laboratório",
  reseller: "Revendedor",
  pharmacy: "Farmácia",
  technician: "Técnico de enfermagem",
  patient: "Paciente",
};