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
  OPEN: "Ponto Aberto",
  CLOSED: "Ponto Fechado",
};

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    CANCELED: "bg-rose-100 text-rose-700 border-rose-200",
    COMPLETED: "bg-emerald-100 text-emerald-700 border-emerald-200",
    APPROVED: "bg-sky-100 text-sky-700 border-sky-200",
    SCHEDULED: "bg-indigo-100 text-indigo-700 border-indigo-200",
    IN_PROGRESS: "bg-amber-100 text-amber-700 border-amber-200",
    QUOTE_SENT: "bg-violet-100 text-violet-700 border-violet-200",
    WAITING_HUMAN_VALIDATION: "bg-orange-100 text-orange-700 border-orange-200",
    QUOTE_DRAFT: "bg-zinc-200 text-zinc-600 border-zinc-300",
    OPEN: "bg-emerald-100 text-emerald-800 border-emerald-300",
    CLOSED: "bg-zinc-200 text-zinc-700 border-zinc-300",
  };
  const cls = map[status] ?? "bg-zinc-100 text-zinc-600 border-zinc-200";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      {status === "OPEN" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 animate-pulse" />}
      {status === "CLOSED" && <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />}
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
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  kind?: "primary" | "ghost" | "danger" | "success" | "warning";
  disabled?: boolean;
  className?: string;
  type?: "button" | "submit" | "reset";
}) {
  const styles = {
    primary: "bg-emerald-600 text-white hover:bg-emerald-500 shadow-sm active:bg-emerald-700",
    ghost: "border border-zinc-300 text-zinc-700 hover:bg-zinc-100 active:bg-zinc-200",
    danger: "bg-rose-600 text-white hover:bg-rose-500 shadow-sm active:bg-rose-700",
    success: "bg-emerald-700 text-white hover:bg-emerald-600 shadow-sm active:bg-emerald-800",
    warning: "bg-amber-600 text-white hover:bg-amber-500 shadow-sm active:bg-amber-700",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex min-h-[44px] items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-150 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-40 ${styles[kind]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Card({
  title,
  children,
  actions,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-2xl border border-zinc-200/80 bg-white p-4 shadow-sm sm:p-5 ${className}`}>
      {(title || actions) && (
        <header className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 pb-3">
          {title && <h2 className="text-base font-bold text-zinc-900">{title}</h2>}
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

export function Notice({ kind, children }: { kind: "ok" | "err"; children: ReactNode }) {
  return (
    <div
      role="alert"
      className={`rounded-xl border p-3.5 text-sm font-medium flex items-center gap-2.5 ${
        kind === "ok"
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : "border-rose-200 bg-rose-50 text-rose-800"
      }`}
    >
      <span className="text-base">{kind === "ok" ? "✓" : "⚠"}</span>
      <div className="flex-1">{children}</div>
    </div>
  );
}

export function ConfirmModal({
  isOpen,
  title,
  description,
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  kind = "primary",
  onConfirm,
  onCancel,
}: {
  isOpen: boolean;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  kind?: "primary" | "danger";
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-zinc-200">
        <h3 className="text-lg font-bold text-zinc-900">{title}</h3>
        <p className="mt-2 text-sm text-zinc-600 leading-relaxed">{description}</p>
        <div className="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end gap-2.5">
          <Button kind="ghost" onClick={onCancel}>
            {cancelText}
          </Button>
          <Button kind={kind === "danger" ? "danger" : "primary"} onClick={onConfirm}>
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function Empty({ text }: { text: string }) {
  return <p className="py-8 text-center text-sm font-medium text-zinc-400">{text}</p>;
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

const WEEKDAY_NAMES = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"];
export function weekdayLabel(day: number): string {
  return WEEKDAY_NAMES[day] ?? `Dia ${day}`;
}
