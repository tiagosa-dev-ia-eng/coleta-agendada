/**
 * Mock Backend Data & Storage para o Preview do Google AI Studio.
 * Permite navegação completa e interativa mesmo quando o backend Django (porta 8000)
 * não estiver ativo ou em conexões isoladas no iframe.
 */

export interface MockData {
  version: { name: string; version: string };
  me: {
    id: number;
    email: string;
    name: string;
    role: { code: string; name: string };
  };
  requests: Array<{
    id: number;
    protocol: string;
    status: string;
    created_at: string;
    patient?: { name?: string; email?: string };
  }>;
  quotations: Array<{
    id: number;
    request_id?: number;
    version: number;
    quotation_type: string;
    total: string;
    is_final: boolean;
    is_validated: boolean;
    is_sent: boolean;
    items: Array<{ description: string; quantity: number; unit_price: string | null }>;
  }>;
  exams: Array<{
    id: number;
    code: string;
    name: string;
    price: { id: number; price: string } | null;
  }>;
  appointments: Array<{
    id: number;
    code: string;
    status: string;
    scheduled_at: string;
    patient?: { name?: string; email?: string };
    pharmacy_name?: string | null;
    technician_name?: string | null;
    location?: string;
  }>;
  commissions: Array<{
    id: number;
    request_protocol: string;
    beneficiary_type: string;
    beneficiary_name?: string | null;
    amount: string;
    status: string;
  }>;
  collectionPoints: Array<{
    id: number;
    kind: "pharmacy" | "laboratory";
    kind_display: string;
    laboratory: number;
    pharmacy?: number | null;
    pharmacy_name?: string | null;
    name: string;
    address: string;
    city: string;
    state: string;
    zip_code: string;
    latitude: string | null;
    longitude: string | null;
    status: string;
    is_open: boolean;
    windows: Array<{ id: number; weekday: number; open_time: string; close_time: string }>;
    technicians: Array<{ id: number; email: string; active: boolean; assigned_at: string }>;
  }>;
  resellers: Array<{
    id: number;
    email_read?: string;
    name?: string;
    status: string;
    created_at?: string;
  }>;
  auditLogs: Array<{
    id: number;
    action: string;
    entity_type: string;
    entity_id: string | number;
    user?: { id: number; email: string } | null;
    laboratory?: { id: number; name: string } | null;
    ip?: string | null;
    metadata?: Record<string, unknown> | null;
    created_at: string;
  }>;
  contacts: Array<{
    id: number;
    owner_kind: "laboratory" | "pharmacy" | "technician" | "reseller";
    laboratory?: number | null;
    pharmacy?: number | null;
    technician?: number | null;
    reseller?: number | null;
    number: string;
    name: string;
    meta_bsuid: string;
    is_main: boolean;
    created_at: string;
    updated_at: string;
  }>;
  whatsappMessages: Array<{
    id: number;
    direction: "inbound" | "outbound";
    content: string;
    created_at: string;
    ai_used_mock?: boolean;
    ai_model?: string;
  }>;
}

const STORAGE_KEY = "coleta_agendada_mock_state_v1";

const INITIAL_MOCK_DATA: MockData = {
  version: { name: "Coleta Agendada", version: "1.1.20" },
  me: {
    id: 1,
    email: "gestor@laboratoriocentral.com.br",
    name: "Dr. Carlos Eduardo (Laboratório Central)",
    role: { code: "laboratory", name: "Laboratório" },
  },
  requests: [
    {
      id: 101,
      protocol: "REQ-2026-0891",
      status: "WAITING_HUMAN_VALIDATION",
      created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
      patient: { name: "Mariana Souza e Silva", email: "mariana.silva@email.com" },
    },
    {
      id: 102,
      protocol: "REQ-2026-0892",
      status: "APPROVED",
      created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
      patient: { name: "Roberto Dias de Toledo", email: "roberto.toledo@email.com" },
    },
    {
      id: 103,
      protocol: "REQ-2026-0893",
      status: "COMPLETED",
      created_at: new Date(Date.now() - 86400000).toISOString(),
      patient: { name: "Camila Fernandes Braga", email: "camila.braga@email.com" },
    },
  ],
  quotations: [
    {
      id: 501,
      request_id: 101,
      version: 1,
      quotation_type: "human_review",
      total: "185.00",
      is_final: false,
      is_validated: false,
      is_sent: false,
      items: [
        { description: "Hemograma Completo c/ Plaquetas", quantity: 1, unit_price: "45.00" },
        { description: "Glicemia de Jejum", quantity: 1, unit_price: "25.00" },
        { description: "Perfil Lipídico (Lipidograma)", quantity: 1, unit_price: "65.00" },
        { description: "Taxa de Coleta Domiciliar", quantity: 1, unit_price: "50.00" },
      ],
    },
    {
      id: 502,
      request_id: 102,
      version: 2,
      quotation_type: "auto_approved",
      total: "120.00",
      is_final: true,
      is_validated: true,
      is_sent: true,
      items: [
        { description: "Creatinina e Ureia", quantity: 1, unit_price: "40.00" },
        { description: "TSH Ultra Sensível", quantity: 1, unit_price: "45.00" },
        { description: "Taxa de Coleta em Ponto Farmácia", quantity: 1, unit_price: "35.00" },
      ],
    },
  ],
  exams: [
    { id: 1, code: "HEM", name: "Hemograma Completo", price: { id: 1, price: "45.00" } },
    { id: 2, code: "GLI", name: "Glicemia de Jejum", price: { id: 2, price: "25.00" } },
    { id: 3, code: "LIP", name: "Perfil Lipídico Completo", price: { id: 3, price: "65.00" } },
    { id: 4, code: "TSH", name: "Hormônio Tireoestimulante (TSH)", price: { id: 4, price: "45.00" } },
    { id: 5, code: "URI", name: "Urina Tipo I (EAS)", price: { id: 5, price: "28.00" } },
    { id: 6, code: "VITD", name: "Vitamina D (25-Hidroxi)", price: { id: 6, price: "79.00" } },
  ],
  appointments: [
    {
      id: 301,
      code: "AG-2026-0045",
      status: "SCHEDULED",
      scheduled_at: new Date(Date.now() + 3600000 * 24).toISOString(),
      patient: { name: "Roberto Dias de Toledo", email: "roberto.toledo@email.com" },
      pharmacy_name: "Farmácia DrogaMais - Jardins",
      technician_name: "Enf. Rodrigo Pires (COREN 245.981)",
      location: "Av. Brigadeiro Luís Antônio, 2100 - Bela Vista",
    },
    {
      id: 302,
      code: "AG-2026-0046",
      status: "IN_PROGRESS",
      scheduled_at: new Date().toISOString(),
      patient: { name: "Mariana Souza e Silva", email: "mariana.silva@email.com" },
      pharmacy_name: "Laboratório Central Matriz",
      technician_name: "Enfª. Juliana Mendes (COREN 312.440)",
      location: "Rua Vergueiro, 1500 - Paraíso",
    },
  ],
  commissions: [
    {
      id: 401,
      request_protocol: "REQ-2026-0891",
      beneficiary_type: "pharmacy",
      beneficiary_name: "Farmácia DrogaMais Jardins",
      amount: "15.00",
      status: "pending",
    },
    {
      id: 402,
      request_protocol: "REQ-2026-0892",
      beneficiary_type: "technician",
      beneficiary_name: "Rodrigo Pires (Técnico)",
      amount: "30.00",
      status: "paid",
    },
    {
      id: 403,
      request_protocol: "REQ-2026-0888",
      beneficiary_type: "reseller",
      beneficiary_name: "Rede Farma SP Revenda",
      amount: "22.50",
      status: "paid",
    },
  ],
  collectionPoints: [
    {
      id: 1,
      kind: "laboratory",
      kind_display: "Laboratório Matriz",
      laboratory: 1,
      name: "Laboratório Central - Sede Paraíso",
      address: "Rua Vergueiro, 1500",
      city: "São Paulo",
      state: "SP",
      zip_code: "04101-000",
      latitude: "-23.5780",
      longitude: "-46.6432",
      status: "active",
      is_open: true,
      windows: [
        { id: 1, weekday: 1, open_time: "07:00", close_time: "17:00" },
        { id: 2, weekday: 2, open_time: "07:00", close_time: "17:00" },
        { id: 3, weekday: 3, open_time: "07:00", close_time: "17:00" },
        { id: 4, weekday: 4, open_time: "07:00", close_time: "17:00" },
        { id: 5, weekday: 5, open_time: "07:00", close_time: "17:00" },
        { id: 6, weekday: 6, open_time: "07:00", close_time: "12:00" },
      ],
      technicians: [
        { id: 10, email: "juliana.mendes@laboratorio.com", active: true, assigned_at: "2026-09-01T08:00:00Z" },
      ],
    },
    {
      id: 2,
      kind: "pharmacy",
      kind_display: "Farmácia Parceira",
      laboratory: 1,
      pharmacy: 1,
      pharmacy_name: "Farmácia DrogaMais - Unidade Jardins",
      name: "Ponto Coleta Farmácia DrogaMais Jardins",
      address: "Av. Brigadeiro Luís Antônio, 2100",
      city: "São Paulo",
      state: "SP",
      zip_code: "01402-002",
      latitude: "-23.5652",
      longitude: "-46.6515",
      status: "active",
      is_open: true,
      windows: [
        { id: 7, weekday: 1, open_time: "07:30", close_time: "16:30" },
        { id: 8, weekday: 2, open_time: "07:30", close_time: "16:30" },
        { id: 9, weekday: 3, open_time: "07:30", close_time: "16:30" },
        { id: 10, weekday: 4, open_time: "07:30", close_time: "16:30" },
        { id: 11, weekday: 5, open_time: "07:30", close_time: "16:30" },
      ],
      technicians: [
        { id: 11, email: "rodrigo.pires@coletas.com", active: true, assigned_at: "2026-09-02T09:00:00Z" },
      ],
    },
  ],
  resellers: [
    {
      id: 1,
      name: "Distribuidora FarmaSul SP Ltda",
      email_read: "contato@farmasul.com.br",
      status: "active",
      created_at: "2026-08-15T10:00:00Z",
    },
    {
      id: 2,
      name: "Rede Apoio Diagnóstico Brasil",
      email_read: "apoio@diagnostico-br.com.br",
      status: "active",
      created_at: "2026-08-28T14:30:00Z",
    },
  ],
  auditLogs: [
    {
      id: 991,
      action: "exam.created",
      entity_type: "exam",
      entity_id: 6,
      user: { id: 1, email: "gestor@laboratoriocentral.com.br" },
      ip: "189.40.122.10",
      metadata: { code: "VITD", name: "Vitamina D", price: "79.00" },
      created_at: new Date(Date.now() - 3600000 * 3).toISOString(),
    },
    {
      id: 992,
      action: "collection_point.opened",
      entity_type: "collection_point",
      entity_id: 2,
      user: { id: 11, email: "rodrigo.pires@coletas.com" },
      ip: "177.18.90.4",
      metadata: { point: "Ponto Coleta Farmácia DrogaMais Jardins", status: "open" },
      created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    },
    {
      id: 993,
      action: "reseller.created",
      entity_type: "reseller",
      entity_id: 2,
      user: { id: 1, email: "gestor@laboratoriocentral.com.br" },
      ip: "189.40.122.10",
      metadata: { email: "apoio@diagnostico-br.com.br", name: "Rede Apoio Diagnóstico Brasil" },
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: 994,
      action: "quotation.validated",
      entity_type: "quotation",
      entity_id: 502,
      user: { id: 1, email: "gestor@laboratoriocentral.com.br" },
      ip: "189.40.122.10",
      metadata: { request: "REQ-2026-0892", total: "120.00" },
      created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    },
  ],
  contacts: [
    {
      id: 1,
      owner_kind: "laboratory",
      laboratory: 1,
      number: "5511988887777",
      name: "Central de Atendimento e Triagem de Orçamentos",
      meta_bsuid: "@coletacentral.atendimento",
      is_main: true,
      created_at: "2026-09-01T10:00:00Z",
      updated_at: "2026-09-01T10:00:00Z",
    },
    {
      id: 2,
      owner_kind: "laboratory",
      laboratory: 1,
      number: "5511977776666",
      name: "Plantão Emergencial de Validação Técnica",
      meta_bsuid: "@coletacentral.plantao",
      is_main: false,
      created_at: "2026-09-02T12:00:00Z",
      updated_at: "2026-09-02T12:00:00Z",
    },
    {
      id: 3,
      owner_kind: "pharmacy",
      pharmacy: 1,
      number: "5511999991122",
      name: "Farmácia DrogaMais - Recepção Coletas",
      meta_bsuid: "@drogamais.jardins",
      is_main: true,
      created_at: "2026-09-03T09:30:00Z",
      updated_at: "2026-09-03T09:30:00Z",
    },
  ],
  whatsappMessages: [
    {
      id: 1,
      direction: "outbound",
      content: "Olá! Sou a assistente inteligente do Coleta Agendada. 🩺 Como posso te ajudar hoje? Você pode solicitar um orçamento de exames ou encontrar o local de coleta mais próximo da sua casa.",
      created_at: new Date(Date.now() - 600000).toISOString(),
      ai_used_mock: false,
      ai_model: "gemini-flash",
    },
  ],
};

export function getMockData(): MockData {
  if (typeof window === "undefined") return INITIAL_MOCK_DATA;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_MOCK_DATA));
      return INITIAL_MOCK_DATA;
    }
    return JSON.parse(raw) as MockData;
  } catch {
    return INITIAL_MOCK_DATA;
  }
}

export function saveMockData(data: MockData) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // ignorar quota excedida
  }
}

export function updateMockData(updater: (prev: MockData) => void): MockData {
  const current = getMockData();
  updater(current);
  saveMockData(current);
  return current;
}
