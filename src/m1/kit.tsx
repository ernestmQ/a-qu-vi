import React from "react";
import { C, SANS, MONO, fmt } from "../l11/lib";
import TEX from "../gen/tex.json";
import DAT from "../gen/datos.json";

// Piezas comunes.

export const RET: number[] = (DAT as { r: number[] }).r; // 1.500 rentabilidades diarias, en %
export const TRADES: number[] = (DAT as { t: number[] }).t; // 250 operaciones, en $
export const OPS = [450, -200, -150, 800, -300, 250, -2100, 600];
export const ORD = [...OPS].sort((a, b) => a - b);

export const cuantil = (a: number[], p: number) => {
  const s = [...a].sort((x, y) => x - y), h = (s.length - 1) * p, f = Math.floor(h);
  return f + 1 < s.length ? s[f] + (h - f) * (s[f + 1] - s[f]) : s[f];
};
export const npdf = (x: number, m = 0, s = 1) => Math.exp(-0.5 * ((x - m) / s) ** 2) / (s * Math.sqrt(2 * Math.PI));
export const mediaDe = (a: number[]) => a.reduce((x, y) => x + y, 0) / a.length;
export const sdDe = (a: number[]) => { const m = mediaDe(a); return Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / (a.length - 1)); };
export const escala = (d0: number, d1: number, r0: number, r1: number) => (v: number) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

/** Recuentos de un histograma con k clases entre lo y hi (los extremos se acumulan en las clases de los bordes). */
export const histo = (a: number[], lo: number, hi: number, k: number) => {
  const c = new Array(k).fill(0), h = (hi - lo) / k;
  for (const v of a) c[Math.min(k - 1, Math.max(0, Math.floor((v - lo) / h)))]++;
  return { c, h };
};
export const camino = (xs: number[], ys: number[]) => xs.map((x, i) => `${i ? "L" : "M"}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");

/** Fórmula LaTeX prerenderizada (src/gen/tex.json). */
export const Tex: React.FC<{ k: keyof typeof TEX; x: number; y: number; ex?: number; o?: number; color?: string; centro?: boolean }> = ({ k, x, y, ex = 20, o = 1, color, centro = true }) => {
  const f = TEX[k] as { w: number; h: number; svg: string };
  const svg = color ? f.svg.replace(/#EEF1F6/g, color) : f.svg;
  const w = f.w * ex, h = f.h * ex;
  return <img src={`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`} style={{ position: "absolute", left: centro ? x - w / 2 : x, top: y - h / 2, width: w, height: h, opacity: o }} />;
};

export const Titulo: React.FC<{ texto: string; o?: number; color?: string; y?: number }> = ({ texto, o = 1, color = C.ink, y = 200 }) => (
  <text x={960} y={y} textAnchor="middle" fontFamily={SANS} fontWeight={700} fontSize={50} fill={color} opacity={o}>{texto}</text>
);

/** Portada con el título ajustado al ancho. */
export const Portada2: React.FC<{ etiqueta: string; titulo: string; o: number }> = ({ etiqueta, titulo, o }) => {
  const fs = Math.min(116, 1700 / (titulo.length * 0.55));
  return (
    <g opacity={o} transform={`translate(0 ${20 * (1 - o)})`}>
      <text x={960} y={430} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={38} letterSpacing={4} fill={C.mediana}>{etiqueta}</text>
      <text x={960} y={560} textAnchor="middle" fontFamily={SANS} fontWeight={800} fontSize={fs} fill={C.ink}>{titulo}</text>
    </g>
  );
};

export const Cierre: React.FC<{ o: number; texto: string }> = ({ o, texto }) => (
  <g opacity={o}>
    <text x={960} y={440} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={36} letterSpacing={4} fill={C.mut}>SIGUIENTE</text>
    <text x={960} y={550} textAnchor="middle" fontFamily={SANS} fontWeight={800} fontSize={84} fill={C.ink}>{texto}</text>
  </g>
);

/** Tarjeta con una cifra: etiqueta pequeña arriba y valor grande. */
export const Cifra: React.FC<{ x: number; y: number; w?: number; h?: number; etq: string; valor: string; color?: string; o?: number; nota?: string; notaColor?: string; borde?: string }> = ({ x, y, w = 360, h = 170, etq, valor, color = C.ink, o = 1, nota, notaColor = C.mut, borde = C.cardLine }) => (
  <g opacity={o} transform={`translate(${x} ${y + 16 * (1 - o)})`}>
    <rect width={w} height={h} rx={18} fill={C.card} stroke={borde} strokeWidth={borde === C.cardLine ? 2 : 5} />
    <text x={w / 2} y={50} textAnchor="middle" fontFamily={SANS} fontWeight={600} fontSize={28} fill={C.mut}>{etq}</text>
    <text x={w / 2} y={nota ? 112 : 122} textAnchor="middle" fontFamily={MONO} fontWeight={600} fontSize={52} fill={color}>{valor}</text>
    {nota ? <text x={w / 2} y={152} textAnchor="middle" fontFamily={MONO} fontSize={26} fill={notaColor}>{nota}</text> : null}
  </g>
);

/** Casilla con un número (datos ordenados, posiciones…). */
export const Casilla: React.FC<{ x: number; y: number; w?: number; h?: number; v: string; color?: string; borde?: string; o?: number; fs?: number }> = ({ x, y, w = 180, h = 100, v, color = C.ink, borde = C.cardLine, o = 1, fs = 40 }) => (
  <g opacity={o} transform={`translate(${x} ${y})`}>
    <rect width={w} height={h} rx={16} fill={C.card} stroke={borde} strokeWidth={borde === C.cardLine ? 2 : 6} />
    <text x={w / 2} y={h / 2 + fs * 0.36} textAnchor="middle" fontFamily={MONO} fontWeight={600} fontSize={fs} fill={color}>{v}</text>
  </g>
);

/** Eje horizontal con marcas. */
export const EjeX: React.FC<{ x0: number; x1: number; y: number; marcas: number[]; X: (v: number) => number; f?: (v: number) => string; o?: number; titulo?: string }> = ({ x0, x1, y, marcas, X, f = (v) => fmt(v), o = 1, titulo }) => (
  <g opacity={o}>
    <line x1={x0} x2={x1} y1={y} y2={y} stroke={C.line} strokeWidth={3} />
    {marcas.map((k) => (
      <g key={k}>
        <line x1={X(k)} x2={X(k)} y1={y} y2={y + 12} stroke={C.line} strokeWidth={3} />
        <text x={X(k)} y={y + 46} textAnchor="middle" fontFamily={MONO} fontSize={28} fill={C.mut}>{f(k)}</text>
      </g>
    ))}
    {titulo ? <text x={(x0 + x1) / 2} y={y + 90} textAnchor="middle" fontFamily={SANS} fontSize={28} fill={C.dim}>{titulo}</text> : null}
  </g>
);

/** Líneas horizontales de referencia con etiquetas a la izquierda. */
export const RejillaY: React.FC<{ x0: number; x1: number; marcas: number[]; Y: (v: number) => number; f?: (v: number) => string; o?: number }> = ({ x0, x1, marcas, Y, f = (v) => fmt(v), o = 1 }) => (
  <g opacity={o}>
    {marcas.map((k) => (
      <g key={k}>
        <line x1={x0} x2={x1} y1={Y(k)} y2={Y(k)} stroke={C.cardLine} strokeWidth={2} />
        <text x={x0 - 16} y={Y(k) + 10} textAnchor="end" fontFamily={MONO} fontSize={26} fill={C.mut}>{f(k)}</text>
      </g>
    ))}
  </g>
);

/** Barras de un histograma ya calculado. */
export const Barras: React.FC<{ c: number[]; lo: number; h: number; X: (v: number) => number; Y: (v: number) => number; y0: number; color?: string; o?: number; crece?: number; gap?: number; colorDe?: (i: number) => string }> = ({ c, lo, h, X, Y, y0, color = C.media, o = 1, crece = 1, gap = 2, colorDe }) => (
  <g opacity={o}>
    {c.map((v, i) => {
      const x0 = X(lo + i * h), x1 = X(lo + (i + 1) * h), yy = y0 + (Y(v) - y0) * crece;
      const g = Math.min(gap, (x1 - x0) * 0.2);
      return v > 0 ? <rect key={i} x={x0 + g / 2} y={yy} width={Math.max(0.6, x1 - x0 - g)} height={y0 - yy} fill={colorDe ? colorDe(i) : color} /> : null;
    })}
  </g>
);

export { C, SANS, MONO, fmt };
