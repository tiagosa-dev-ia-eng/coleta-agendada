/**
 * Interceptor para responder requisições da API com dados locais quando o
 * servidor backend Django (porta 8000) não estiver acessível (ex.: modo Preview).
 */

import { getMockData, saveMockData, MockData } from "./mockBackend";

export function handleMockFallback<T>(path: string, init?: RequestInit): T {
  const method = (init?.method ?? "GET").toUpperCase();
  const state = getMockData();
  const body = init?.body ? (typeof init.body === "string" ? JSON.parse(init.body) : init.body) : {};

  // Normaliza caminho (remove query params para matching)
  const [cleanPath, queryStr] = path.split("?");
  const query = new URLSearchParams(queryStr || "");

  // /version
  if (cleanPath.endsWith("/version")) {
    return state.version as T;
  }

  // /auth/me
  if (cleanPath.endsWith("/auth/me")) {
    return state.me as T;
  }

  // /auth/login
  if (cleanPath.endsWith("/auth/login")) {
    const roleCode = (body.email || "").includes("farmacia")
      ? "pharmacy"
      : (body.email || "").includes("tecnico")
      ? "technician"
      : (body.email || "").includes("revendedor")
      ? "reseller"
      : (body.email || "").includes("paciente")
      ? "patient"
      : "laboratory";
    return {
      access: "demo_preview_token_" + roleCode,
      refresh: "demo_refresh_token",
      user: {
        id: 1,
        email: body.email || "demo@coletaagendada.com.br",
        role: { code: roleCode, name: roleCode },
      },
    } as T;
  }

  // /requests
  if (cleanPath.includes("/api/v1/requests")) {
    if (method === "GET") {
      return state.requests as T;
    }
    if (method === "POST") {
      const newReq = {
        id: Date.now(),
        protocol: `REQ-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        status: "WAITING_HUMAN_VALIDATION",
        created_at: new Date().toISOString(),
        patient: { name: body.patient_name || "Paciente Demo", email: body.patient_email || "paciente@demo.com" },
      };
      state.requests.unshift(newReq);
      saveMockData(state);
      return newReq as T;
    }
  }

  // /quotations
  if (cleanPath.includes("/api/v1/quotations")) {
    const matchId = cleanPath.match(/\/quotations\/(\d+)/);
    const quoteId = matchId ? parseInt(matchId[1], 10) : null;

    if (cleanPath.endsWith("/validate") && quoteId) {
      const q = state.quotations.find((item) => item.id === quoteId);
      if (q) {
        q.is_validated = true;
        saveMockData(state);
        return q as T;
      }
    }

    if (cleanPath.endsWith("/send") && quoteId) {
      const q = state.quotations.find((item) => item.id === quoteId);
      if (q) {
        q.is_sent = true;
        q.is_final = true;
        saveMockData(state);
        return q as T;
      }
    }

    if (method === "GET") {
      return state.quotations as T;
    }
  }

  // /exams
  if (cleanPath.includes("/api/v1/exams")) {
    const matchId = cleanPath.match(/\/exams\/(\d+)/);
    const examId = matchId ? parseInt(matchId[1], 10) : null;

    if (cleanPath.endsWith("/price") && examId && method === "POST") {
      const ex = state.exams.find((item) => item.id === examId);
      if (ex) {
        ex.price = { id: Date.now(), price: String(body.price || "0.00") };
        saveMockData(state);
        return ex as T;
      }
    }

    if (method === "DELETE" && examId) {
      state.exams = state.exams.filter((item) => item.id !== examId);
      saveMockData(state);
      return { success: true } as T;
    }

    if (method === "PATCH" && examId) {
      const ex = state.exams.find((item) => item.id === examId);
      if (ex) {
        if (body.name) ex.name = body.name;
        if (body.code) ex.code = body.code;
        saveMockData(state);
        return ex as T;
      }
    }

    if (method === "POST") {
      const newExam = {
        id: Date.now(),
        code: (body.code || "EXM").toUpperCase(),
        name: body.name || "Novo Exame",
        price: body.price ? { id: Date.now(), price: String(body.price) } : null,
      };
      state.exams.push(newExam);
      // Registra na auditoria
      state.auditLogs.unshift({
        id: Date.now(),
        action: "exam.created",
        entity_type: "exam",
        entity_id: newExam.id,
        user: { id: 1, email: state.me.email },
        ip: "127.0.0.1",
        metadata: { code: newExam.code, name: newExam.name },
        created_at: new Date().toISOString(),
      });
      saveMockData(state);
      return newExam as T;
    }

    if (method === "GET") {
      return state.exams as T;
    }
  }

  // /appointments
  if (cleanPath.includes("/api/v1/appointments")) {
    return state.appointments as T;
  }

  // /commissions
  if (cleanPath.includes("/api/v1/commissions")) {
    return state.commissions as T;
  }

  // /collection-points
  if (cleanPath.includes("/api/v1/collection-points")) {
    const matchId = cleanPath.match(/\/collection-points\/(\d+)/);
    const pointId = matchId ? parseInt(matchId[1], 10) : null;

    if (cleanPath.endsWith("/open") && pointId) {
      const p = state.collectionPoints.find((x) => x.id === pointId);
      if (p) p.is_open = true;
      saveMockData(state);
      return { status: "opened", is_open: true } as T;
    }

    if (cleanPath.endsWith("/close") && pointId) {
      const p = state.collectionPoints.find((x) => x.id === pointId);
      if (p) p.is_open = false;
      saveMockData(state);
      return { status: "closed", is_open: false } as T;
    }

    if (cleanPath.endsWith("/technicians") && pointId && method === "POST") {
      const p = state.collectionPoints.find((x) => x.id === pointId);
      if (p) {
        p.technicians.push({
          id: body.technician_id || Date.now(),
          email: "tecnico.novo@coleta.com.br",
          active: true,
          assigned_at: new Date().toISOString(),
        });
        saveMockData(state);
        return p as T;
      }
    }

    if (cleanPath.endsWith("/windows") && pointId && method === "POST") {
      const p = state.collectionPoints.find((x) => x.id === pointId);
      if (p) {
        p.windows.push({
          id: Date.now(),
          weekday: Number(body.weekday ?? 1),
          open_time: body.open_time || "08:00",
          close_time: body.close_time || "17:00",
        });
        saveMockData(state);
        return p as T;
      }
    }

    if (method === "POST") {
      const newPoint = {
        id: Date.now(),
        kind: body.kind || "laboratory",
        kind_display: body.kind === "pharmacy" ? "Farmácia Parceira" : "Laboratório Matriz",
        laboratory: 1,
        pharmacy: body.pharmacy ?? null,
        name: body.name || "Novo Ponto de Coleta",
        address: body.address || "",
        city: body.city || "São Paulo",
        state: body.state || "SP",
        zip_code: body.zip_code || "01000-000",
        latitude: body.latitude || null,
        longitude: body.longitude || null,
        status: "active",
        is_open: true,
        windows: [],
        technicians: [],
      };
      state.collectionPoints.push(newPoint);
      saveMockData(state);
      return newPoint as T;
    }

    if (method === "GET") {
      return state.collectionPoints as T;
    }
  }

  // /resellers (F-05)
  if (cleanPath.includes("/api/v1/resellers")) {
    const matchId = cleanPath.match(/\/resellers\/(\d+)/);
    const resId = matchId ? parseInt(matchId[1], 10) : null;

    if (method === "PATCH" && resId) {
      const r = state.resellers.find((x) => x.id === resId);
      if (r) {
        if (body.status) r.status = body.status;
        saveMockData(state);
        return r as T;
      }
    }

    if (method === "POST") {
      const newRes = {
        id: Date.now(),
        name: body.first_name || body.email.split("@")[0],
        email_read: body.email,
        status: "active",
        created_at: new Date().toISOString(),
      };
      state.resellers.push(newRes);
      state.auditLogs.unshift({
        id: Date.now(),
        action: "reseller.created",
        entity_type: "reseller",
        entity_id: newRes.id,
        user: { id: 1, email: state.me.email },
        ip: "127.0.0.1",
        metadata: { email: newRes.email_read, name: newRes.name },
        created_at: new Date().toISOString(),
      });
      saveMockData(state);
      return newRes as T;
    }

    if (method === "GET") {
      return state.resellers as T;
    }
  }

  // /audit (F-06)
  if (cleanPath.includes("/api/v1/audit")) {
    const actionFilter = query.get("action")?.toLowerCase() || "";
    const entityFilter = query.get("entity_type")?.toLowerCase() || "";
    let logs = state.auditLogs;
    if (actionFilter) logs = logs.filter((l) => l.action.toLowerCase().includes(actionFilter));
    if (entityFilter) logs = logs.filter((l) => l.entity_type.toLowerCase().includes(entityFilter));
    return { items: logs, count: logs.length } as T;
  }

  // /whatsapp/contacts (F-07)
  if (cleanPath.includes("/api/v1/whatsapp/contacts")) {
    const matchId = cleanPath.match(/\/contacts\/(\d+)/);
    const contactId = matchId ? parseInt(matchId[1], 10) : null;

    if (method === "DELETE" && contactId) {
      state.contacts = state.contacts.filter((c) => c.id !== contactId);
      saveMockData(state);
      return { success: true } as T;
    }

    if (method === "PATCH" && contactId) {
      const c = state.contacts.find((x) => x.id === contactId);
      if (c) {
        if (body.name !== undefined) c.name = body.name;
        if (body.number !== undefined) c.number = body.number;
        if (body.meta_bsuid !== undefined) c.meta_bsuid = body.meta_bsuid;
        if (body.is_main !== undefined) {
          if (body.is_main) {
            state.contacts.forEach((other) => {
              if (other.owner_kind === c.owner_kind) other.is_main = false;
            });
          }
          c.is_main = body.is_main;
        }
        c.updated_at = new Date().toISOString();
        saveMockData(state);
        return c as T;
      }
    }

    if (method === "POST") {
      if (body.is_main) {
        state.contacts.forEach((other) => {
          if (other.owner_kind === "laboratory") other.is_main = false;
        });
      }
      const newContact = {
        id: Date.now(),
        owner_kind: (body.owner_kind || "laboratory") as "laboratory" | "pharmacy" | "technician" | "reseller",
        laboratory: 1,
        number: body.number.replace(/\D/g, ""),
        name: body.name || "Canal de Atendimento WhatsApp",
        meta_bsuid: body.meta_bsuid || "",
        is_main: Boolean(body.is_main),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      state.contacts.push(newContact);
      saveMockData(state);
      return newContact as T;
    }

    if (method === "GET") {
      return state.contacts as T;
    }
  }

  // /whatsapp/conversations
  if (cleanPath.includes("/whatsapp/conversations")) {
    if (method === "DELETE") {
      state.whatsappMessages = [];
      saveMockData(state);
      return { success: true } as T;
    }
    if (cleanPath.endsWith("/messages")) {
      return state.whatsappMessages as T;
    }
  }

  // /webhooks/whatsapp (F-09)
  if (cleanPath.includes("/webhooks/whatsapp")) {
    if (body.location) {
      const lat = parseFloat(body.location.latitude);
      const lon = parseFloat(body.location.longitude);
      const userInMsg = {
        id: Date.now(),
        direction: "inbound" as const,
        content: `📍 [Localização Compartilhada]: Lat ${lat.toFixed(4)}, Lon ${lon.toFixed(4)}`,
        created_at: new Date().toISOString(),
      };
      state.whatsappMessages.push(userInMsg);

      // Resposta inteligente do ponto mais próximo (F-09)
      const point = state.collectionPoints[0];
      const botReply = {
        id: Date.now() + 1,
        direction: "outbound" as const,
        content: `O local de coleta mais próximo da sua localização é o laboratório ${point.name} — ${point.address}, ${point.city}, ${point.state} (a cerca de 1.4 km).\n\n⏰ Horário de Funcionamento: Seg-Sex das 07:00 às 17:00, Sáb das 07:00 às 12:00.\n🟢 No momento: Aberto hoje para atendimento.\n\nPosso agendar a coleta nesse ponto para você? É só me dizer qual exame e em qual período prefere!`,
        created_at: new Date(Date.now() + 1000).toISOString(),
        ai_used_mock: false,
        ai_model: "gemini-flash",
      };
      state.whatsappMessages.push(botReply);
      saveMockData(state);
      return { status: "received", nearest_point: point } as T;
    }

    if (body.text || body.content) {
      const text = body.text || body.content;
      const userMsg = {
        id: Date.now(),
        direction: "inbound" as const,
        content: text,
        created_at: new Date().toISOString(),
      };
      state.whatsappMessages.push(userMsg);

      let reply = "Entendido! Como posso ajudar você no agendamento da sua coleta ou orçamento?";
      const lower = text.toLowerCase();
      if (lower.includes("hemograma") || lower.includes("exame") || lower.includes("orçamento") || lower.includes("valor")) {
        reply = "Temos o exame solicitado em nossa rede! Hemograma Completo por R$ 45,00 e Glicemia por R$ 25,00. Deseja realizar em uma farmácia parceira ou com coleta domiciliar do técnico de enfermagem?";
      } else if (lower.includes("local") || lower.includes("onde") || lower.includes("endereço") || lower.includes("perto")) {
        reply = "Para encontrar o ponto de coleta mais próximo com os horários de atendimento em tempo real, clique no botão '📍 Usar GPS / Minha Localização Atual' logo abaixo!";
      }

      const botReply = {
        id: Date.now() + 1,
        direction: "outbound" as const,
        content: reply,
        created_at: new Date(Date.now() + 800).toISOString(),
        ai_used_mock: false,
        ai_model: "gemini-flash",
      };
      state.whatsappMessages.push(botReply);
      saveMockData(state);
      return { status: "received" } as T;
    }
  }

  // Fallback genérico para listas vazias ou objetos
  return ([] as unknown) as T;
}
