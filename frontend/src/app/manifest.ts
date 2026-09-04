import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Coleta Agendada",
    short_name: "Coleta",
    description: "Plataforma de solicitação, orçamento, agendamento e realização de coletas laboratoriais.",
    start_url: "/login",
    display: "standalone",
    background_color: "#fafafa",
    theme_color: "#059669",
    lang: "pt-BR",
    icons: [
      {
        src: "/favicon.ico",
        sizes: "any",
        type: "image/x-icon",
      },
    ],
  };
}
