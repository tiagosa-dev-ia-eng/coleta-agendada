import type { ReactNode } from "react";

export const STATUS_LABEL: Record<string, string> = {
  REQUESTED: "Solicitado",
  QUOTE_DRAFT: "Rascunho de orçamento",
  WAITING_HUMAN_VALIDATION: "Validação humana",
  QUOTE_SENT: "Orçamento enviado",
  APPROVED: "Aprovado",
  SCHEDULED: "Agendado",
  IN_PROGRESS: "Em realização",
  COMPLETED: "Realizado",
  PAYMENT_PENDING: "Pagamento pendente",
  PAYMENT_CONFIRMED: "Pagamento confirmado",
  CANCELED: "Cancelado",
};

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    CANCELED: "bg-rose-100 text-rose-700",
    COMPLETED: "bg-emerald-100 text-emerald-700",
    APPROVED: "bg-sky-100 text-sky-700",
    SCHEDULED: "bg-indigo-100 text-indigo-700",
    IN_PROGRESS: "bg-amber-100 text-amber-700",
    QUOTE_SENT: "bg-violet-100 text-violet-700",
    WAITING_HUMAN_VALIDATION: "bg-orange-100 text-orange-700",
    QUOTE_DRAFT: "bg-zinc-200 text-zinc-600",
  };
  const cls = map[status] ?? "bg-zinc-100 text-zinc-600";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

export function Button({
  children,
  onClick,
  kind = "primary",
  disabled,
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  kind?: "primary" | "ghost" | "danger";
  disabled?: boolean;
  className?: string;
}) {
  const styles = {
    primary: "bg-emerald-600 text-white hover:bg-emerald-500",
    ghost: "border border-zinc-300 text-zinc-700 hover:bg-zinc-100",
    danger: "bg-rose-600 text-white hover:bg-rose-500",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-40 ${styles[kind]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Card({ title, children, actions }: { title?: string; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      {(title || actions) && (
        <header className="mb-3 flex items-center justify-between gap-2">
          {title && <h2 className="text-sm font-semibold text-zinc-800">{title}</h2>}
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

export function Notice({ kind, children }: { kind: "ok" | "err"; children: ReactNode }) {
  return (
    <p
      className={`rounded-lg px-3 py-2 text-sm ${
        kind === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
      }`}
    >
      {children}
    </p>
  );
}

export function Empty({ text }: { text: string }) {
  return <p className="py-6 text-center text-sm text-zinc-400">{text}</p>;
}

export function money(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}
