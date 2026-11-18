import React from "react";
import { AbsoluteFill, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { loadFont } from "@remotion/fonts";
import FORM from "../formulas.json";

// Piezas comunes: colores, tipografía, tiempos sincronizados con la voz,
// subtítulos, cabecera de sección, fórmulas y recta numérica.

for (const [w, f] of [[400, "inter-latin-400-normal"], [600, "inter-latin-600-normal"], [700, "inter-latin-700-normal"], [800, "inter-latin-800-normal"]] as const) {
  loadFont({ family: "Inter", url: staticFile(`fonts/${f}.woff2`), weight: String(w) });
}
for (const [w, f] of [[400, "jetbrains-mono-latin-400-normal"], [600, "jetbrains-mono-latin-600-normal"]] as const) {
  loadFont({ family: "JBM", url: staticFile(`fonts/${f}.woff2`), weight: String(w) });
}

export type Segmento = { id: string; text: string; sub?: string; start: number; duration: number; end: number };
export type Manifiesto = { provider: string; duration: number; segments: Segmento[] };
export type Props = { manifest: Manifiesto; audio: string | null; etiqueta: string };

export const C = { bg: "#0F1420", ink: "#EEF1F6", mut: "#93A0B5", dim: "#5D6B82", line: "#3A4659", card: "#161D2C", cardLine: "#2A3447", media: "#5B9DFF", mediana: "#F5B94A", good: "#3FCF8E", bad: "#F2706B", violeta: "#B79CFF" };
export const SANS = "Inter, sans-serif", MONO = "JBM, monospace";
export const ease = Easing.bezier(0.4, 0, 0.2, 1);

export const fmt = (x: number, d = 0) => {
  const s = Math.abs(x).toFixed(d).split(".");
  s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return (x < 0 ? "−" : "") + s.join(",");
};
export const sg = (x: number, d = 0) => (x > 0 ? "+" : "") + fmt(x, d);
export const media = (a: number[]) => a.reduce((x, y) => x + y, 0) / a.length;
export const mediana = (a: number[]) => { const s = [...a].sort((x, y) => x - y), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };

/** Reloj de la composición: instante actual y momentos de cada frase o palabra según el manifiesto de la voz. */
export const useTiempo = (manifest: Manifiesto) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const S = Object.fromEntries(manifest.segments.map((s) => [s.id, s]));
  const at = (id: string, palabra?: string, n = 1) => {
    const s = S[id];
    if (!s) throw new Error("Falta la frase " + id);
    if (!palabra) return s.start;
    let i = -1;
    for (let k = 0; k < n; k++) i = s.text.indexOf(palabra, i + 1);
    if (i < 0) throw new Error(`«${palabra}» no está en ${id}`);
    return s.start + (s.duration * i) / s.text.length;
  };
  const fin = (id: string) => S[id].end;
  const p = (a: number, dur = 0.5) => interpolate(t, [a, a + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  /** visible entre a y b, con entrada y salida suaves */
  const vis = (a: number, b: number, d = 0.45) => p(a - 0.15, d) * (1 - p(b - d, d));
  return { t, at, fin, p, vis };
};

export const Lienzo: React.FC<{ manifest: Manifiesto; audio: string | null; children?: React.ReactNode; svg?: React.ReactNode; etiqueta?: string }> = ({ manifest, audio, children, svg, etiqueta }) => {
  const { t } = useTiempo(manifest);
  const sub = manifest.segments.find((s) => t >= s.start - 0.05 && t <= s.end + 0.35);
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>{svg}</svg>
      {children}
      {sub && etiqueta !== "portada" ? (
        <div style={{ position: "absolute", left: 180, right: 180, bottom: 38, textAlign: "center", fontFamily: SANS, fontWeight: 600, fontSize: 40, lineHeight: 1.3, color: "#fff", textShadow: "0 0 10px #000, 0 2px 4px #000" }}>{sub.sub || sub.text}</div>
      ) : null}
    </AbsoluteFill>
  );
};

/** Rótulo fijo arriba a la izquierda con la sección del vídeo. */
export const Rotulo: React.FC<{ texto: string; o?: number }> = ({ texto, o = 1 }) => (
  <text x={90} y={86} fontFamily={SANS} fontWeight={600} fontSize={26} letterSpacing={3} fill={C.dim} opacity={o}>{texto}</text>
);

/** Portada: etiqueta + título grande. */
export const Portada: React.FC<{ etiqueta: string; titulo: string; o: number }> = ({ etiqueta, titulo, o }) => (
  <g opacity={o} transform={`translate(0 ${20 * (1 - o)})`}>
    <text x={960} y={430} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={38} letterSpacing={4} fill={C.mediana}>{etiqueta}</text>
    <text x={960} y={560} textAnchor="middle" fontFamily={SANS} fontWeight={800} fontSize={120} fill={C.ink}>{titulo}</text>
  </g>
);

/** Fórmula de MathJax (prerenderizada) como imagen, a una altura en píxeles por «ex». */
export const Formula: React.FC<{ k: keyof typeof FORM; x: number; y: number; ex?: number; o?: number; centro?: boolean; color?: string }> = ({ k, x, y, ex = 20, o = 1, centro = true, color }) => {
  const f = FORM[k] as { w: number; h: number; svg: string };
  const svg = color ? f.svg.replace(/#EEF1F6/g, color) : f.svg;
  const w = f.w * ex, h = f.h * ex;
  return (
    <img src={`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`} style={{ position: "absolute", left: centro ? x - w / 2 : x, top: y - h / 2, width: w, height: h, opacity: o }} />
  );
};

/** Recta numérica horizontal. */
export const Recta: React.FC<{ x0: number; x1: number; y: number; marcas: number[]; X: (v: number) => number; unidad?: string; o?: number }> = ({ x0, x1, y, marcas, X, unidad = "", o = 1 }) => (
  <g opacity={o}>
    <line x1={x0} x2={x1} y1={y} y2={y} stroke={C.line} strokeWidth={4} />
    {marcas.map((k) => (
      <g key={k}>
        <line x1={X(k)} x2={X(k)} y1={y - 12} y2={y + 12} stroke={C.line} strokeWidth={3} />
        <text x={X(k)} y={y + 52} textAnchor="middle" fontFamily={MONO} fontSize={30} fill={C.mut}>{fmt(k)}{unidad}</text>
      </g>
    ))}
  </g>
);

/** Marcador de la media (triángulo) y de la mediana (línea discontinua) sobre una recta. */
export const MarcaMedia: React.FC<{ x: number; y: number; o: number; texto: string; abajo?: number }> = ({ x, y, o, texto, abajo = 156 }) => (
  <g opacity={o}>
    <path d={`M${x},${y + 70} l-22,42 h44 z`} fill={C.media} />
    <text x={x} y={y + abajo} textAnchor="middle" fontFamily={SANS} fontWeight={700} fontSize={38} fill={C.media}>{texto}</text>
  </g>
);
export const MarcaMediana: React.FC<{ x: number; y: number; o: number; texto: string; alto?: number }> = ({ x, y, o, texto, alto = 110 }) => (
  <g opacity={o}>
    <line x1={x} x2={x} y1={y - alto} y2={y - 30} stroke={C.mediana} strokeWidth={5} strokeDasharray="14 9" />
    <text x={x} y={y - alto - 20} textAnchor="middle" fontFamily={SANS} fontWeight={700} fontSize={38} fill={C.mediana}>{texto}</text>
  </g>
);

export const Tarjeta: React.FC<{ x: number; y: number; w: number; h: number; o?: number; borde?: string; grosor?: number; children?: React.ReactNode }> = ({ x, y, w, h, o = 1, borde = C.cardLine, grosor = 2, children }) => (
  <g opacity={o} transform={`translate(${x} ${y})`}>
    <rect width={w} height={h} rx={18} fill={C.card} stroke={borde} strokeWidth={grosor} />
    {children}
  </g>
);
