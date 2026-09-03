"use client";

import { API_URL } from "./api";

export const TOKEN_KEY = "ca_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination
  window.location.assign("/login");
}

export function isAuthed(): boolean {
  return Boolean(getToken());
}

export async function authedFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
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