/**
 * Cliente base da API do backend (base /api/v1 — doc 07).
 * NEXT_PUBLIC_API_URL aponta para o backend (default dev local).
 */
import { handleMockFallback } from "./mockInterceptor";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = (await res.json()) as { error?: { message?: string } };
        detail = body.error?.message ?? res.statusText;
      } catch {
        // corpo não-JSON: mantém statusText
      }
      throw new ApiError(res.status, detail);
    }
    return (await res.json()) as T;
  } catch (err) {
    // Se for erro de rede (backend offline ou preview isolado), utiliza o fallback de mock
    if (err instanceof ApiError) {
      throw err;
    }
    return handleMockFallback<T>(path, init);
  }
}
