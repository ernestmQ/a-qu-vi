// Academia Quant · servidor de vídeo (Cloudflare Worker delante del almacén R2 «academia-quant-videos»).
// Sirve /v/<nombre>.mp4 con rangos (para avanzar y retroceder) y solo a la web de la academia:
// se rechazan las peticiones que vienen de otra web y las que se abren directamente en el navegador.
const PERMITIDOS = [/^https:\/\/academiaquant\.netlify\.app$/, /^https:\/\/[a-z0-9-]+--academiaquant\.netlify\.app$/];
const origen = (u) => { try { return new URL(u).origin; } catch { return ""; } };

function permitido(req) {
  const ref = req.headers.get("Origin") || origen(req.headers.get("Referer") || "");
  if (ref) return PERMITIDOS.some((r) => r.test(ref));
  // Sin Origin ni Referer (algunos navegadores los quitan): solo si lo pide un reproductor de vídeo, no una pestaña.
  const dest = req.headers.get("Sec-Fetch-Dest");
  return dest === "video" || dest === "audio" || dest === "track";
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname === "/salud") return new Response("ok");
    if (req.method !== "GET" && req.method !== "HEAD") return new Response("Método no permitido", { status: 405 });
    const m = url.pathname.match(/^\/v\/([a-z0-9][a-z0-9._-]*\.(mp4|vtt|jpg))$/);
    if (!m) return new Response("No encontrado", { status: 404 });
    if (!permitido(req)) return new Response("Este vídeo solo se puede ver desde Academia Quant.", { status: 403 });

    const obj = await env.VIDEOS.get(m[1], { range: req.headers, onlyIf: req.headers });
    if (obj === null) return new Response("No encontrado", { status: 404 });
    const h = new Headers();
    obj.writeHttpMetadata(h);
    h.set("ETag", obj.httpEtag);
    h.set("Accept-Ranges", "bytes");
    h.set("Cache-Control", "private, max-age=3600");
    h.set("Content-Disposition", "inline");
    const ref = req.headers.get("Origin");
    if (ref && PERMITIDOS.some((r) => r.test(ref))) { h.set("Access-Control-Allow-Origin", ref); h.set("Vary", "Origin"); }
    if (!("body" in obj)) return new Response(null, { status: 304, headers: h });
    if (obj.range && req.headers.has("Range")) {
      const ini = obj.range.offset ?? (obj.range.suffix !== undefined ? obj.size - obj.range.suffix : 0);
      const lon = obj.range.length ?? (obj.size - ini);
      h.set("Content-Range", `bytes ${ini}-${ini + lon - 1}/${obj.size}`);
      h.set("Content-Length", String(lon));
      return new Response(req.method === "HEAD" ? null : obj.body, { status: 206, headers: h });
    }
    h.set("Content-Length", String(obj.size));
    return new Response(req.method === "HEAD" ? null : obj.body, { status: 200, headers: h });
  },
};
