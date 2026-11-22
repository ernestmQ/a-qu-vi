import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

// Sin ligaduras en el código: JetBrains Mono convierte «/=», «!=», «>=» en ≠ ≥…, y el alumno copiaría otro Python.
if (typeof document !== "undefined" && !document.getElementById("aq-sin-ligaduras")) {
  const st = document.createElement("style"); st.id = "aq-sin-ligaduras";
  st.textContent = '* { font-variant-ligatures: none !important; font-feature-settings: "calt" 0, "liga" 0 !important; }';
  document.head.appendChild(st);
}

registerRoot(RemotionRoot);
