import ApiStatus from "@/components/ApiStatus";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center bg-zinc-50 px-6 py-20">
      <div className="w-full max-w-3xl rounded-2xl border border-zinc-200 bg-white p-10 shadow-sm">
        <p className="text-sm font-medium tracking-wide text-sky-600 uppercase">Coleta Agendada · MVP (M0)</p>
        <h1 className="mt-3 text-3xl font-semibold text-zinc-900">
          Plataforma de agendamento e realização de coletas de exames
        </h1>
        <p className="mt-4 max-w-xl leading-7 text-zinc-600">
          Solicitação, rascunho e orçamento com validação humana, aprovação do paciente,
          agendamento, realização da coleta, pagamento e comissões — conectando laboratórios,
          revendedores, farmácias, técnicos de enfermagem e pacientes via Web e WhatsApp + IA.
        </p>

        <h2 className="mt-8 text-sm font-semibold text-zinc-900">Perfis (RBAC — chega no M1)</h2>
        <ul className="mt-2 flex flex-wrap gap-2 text-sm text-zinc-700">
          {["Laboratório", "Revendedor", "Farmácia", "Técnico de enfermagem", "Paciente"].map((p) => (
            <li key={p} className="rounded-full bg-zinc-100 px-3 py-1">
              {p}
            </li>
          ))}
        </ul>

        <div className="mt-8 border-t border-zinc-200 pt-6">
          <ApiStatus />
        </div>
      </div>
    </main>
  );
}
