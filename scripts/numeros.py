"""Texto con cifras → texto para la voz, en español natural.
«0,12» → «cero coma doce», «1.260» → «mil doscientos sesenta», «−0,62» → «menos cero coma sesenta y dos»,
«28 %» → «veintiocho por ciento», «515 $» → «quinientos quince dólares», «A3» → «A tres», «ρ» → «ro»,
«Nasdaq» y «S&P 500» con pronunciación inglesa, género femenino delante de «estrategias», «sesiones», etc."""
import re

U = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince",
     "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco",
     "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
D = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
C = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}
FEM = r"(estrategias?|sesiones?|familias?|apuestas?|ventanas?|veces|operaciones?|semanas?|horas?|pruebas?|carteras?|parejas?|casillas?|frases?|lecciones?|filas?|columnas?|clases?|muestras?|simulaciones?|unidades?|personas?|décimas?|centésimas?|milésimas?|series?)"

def _menor1000(n, fem=False, apoc=False):
    if n < 30:
        w = U[n]
        if fem and n in (1, 21): w = "una" if n == 1 else "veintiuna"
        elif apoc and n in (1, 21): w = "un" if n == 1 else "veintiún"
        return w
    if n < 100:
        d, u = divmod(n, 10)
        if not u: return D[d]
        return D[d] + " y " + (("una" if fem else "un" if apoc else "uno") if u == 1 else U[u])
    if n == 100: return "cien"
    c, r = divmod(n, 100)
    w = C[c] if not fem or c == 1 else C[c][:-2] + "as"
    return w + ((" " + _menor1000(r, fem, apoc)) if r else "")

def entero(n, fem=False, apoc=False):
    if n < 0: return "menos " + entero(-n, fem, apoc)
    if n < 1000: return _menor1000(n, fem, apoc)
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        w = "mil" if m == 1 else _menor1000(m, fem, True) + " mil"
        return w + ((" " + _menor1000(r, fem, apoc)) if r else "")
    mm, r = divmod(n, 1_000_000)
    w = "un millón" if mm == 1 else entero(mm, False, True) + " millones"
    return w + ((" " + entero(r, fem, apoc)) if r else "")

def decimal(s, fem=False, apoc=False):
    """«12,05» → «doce coma cero cinco»: la parte decimal se lee como número, con sus ceros a la izquierda."""
    neg = s.startswith(("-", "−"))
    s = s.lstrip("-−")
    e, _, d = s.partition(",")
    e = int(e.replace(".", "")) if e else 0
    w = entero(e, fem and not d, apoc and not d)
    if d:
        ceros = len(d) - len(d.lstrip("0"))
        w += " coma " + " ".join(["cero"] * ceros) + ((" " if ceros and d.lstrip("0") else "") + entero(int(d.lstrip("0"))) if d.lstrip("0") else "")
    return ("menos " if neg else "") + w

MASC = {"días", "día", "sistemas", "problemas", "programas", "temas", "mapas", "planetas", "idiomas", "clima", "mapa", "dilemas", "esquemas", "ya", "para", "hasta", "contra", "entre", "sobre", "a", "la", "las", "una", "esa", "esta", "cada"}

NOMBRES = [(r"S&P\s?500", "{S&P} quinientos"), (r"(?<!\{)\bS&P\b", "{S&P}"), (r"\bNasdaq\b|\bNASDAQ\b", "{Nasdaq}"), (r"\bEURUSD\b", "euro dólar"),
           (r"\bNumPy\b|\bnumpy\b", "{NumPy}"), (r"\bcorrcoef\b", "{corr coef}"), (r"\bcvxpy\b", "{CVX pie}")]

def para_voz(t):
    for a, b in NOMBRES: t = re.sub(a, b, t)
    t = re.sub(r"\b([A-E])(\d{1,2})\b", lambda m: f"{m.group(1)} {entero(int(m.group(2)))}", t)          # A3 → A tres
    t = re.sub(r"(\d)\s?/\s?(√?\d)", r"\1 entre \2", t)
    t = re.sub(r"√\s?(\d[\d.,]*)", lambda m: "raíz de " + decimal(m.group(1)), t)
    t = t.replace("ρ", "ro").replace("σ", "sigma").replace("×", " por ").replace("≈", " aproximadamente ")
    t = re.sub(r"\s=\s", " igual a ", t); t = t.replace(" · ", ", ")
    t = re.sub(r"1\.ª", "primera", t); t = re.sub(r"2\.ª", "segunda", t); t = re.sub(r"3\.ª", "tercera", t)
    num = r"[-−]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|[-−]?\d+(?:,\d+)?"
    def rep(m):
        s, despues = m.group(1), m.group(2) or ""
        sig = re.match(r"\s+(\w+)", t[m.end(1):]); w = sig.group(1).lower() if sig else ""
        fem = bool(re.fullmatch(FEM, w)) or (bool(re.search(r"(as|a|ión|iones)$", w)) and w not in MASC)
        if despues.strip() == "%": return decimal(s) + " por ciento"
        if despues.strip() == "$": return decimal(s, apoc=True) + (" dólar" if s in ("1", "−1", "-1") else " dólares")
        if despues.strip() == "€": return decimal(s, apoc=True) + (" euro" if s in ("1",) else " euros")
        return decimal(s, fem=fem) + despues
    t = re.sub(rf"(?<![\w{{])({num})(\s?[%$€])?", rep, t)
    return re.sub(r"\s{2,}", " ", t).strip()

if __name__ == "__main__":
    for x in ["La volatilidad baja de 560 $ a 223 $: un 28 % menos.", "El Sharpe pasa de 0,72 a 1,82, y el techo de 2,07 a 2,94.",
              "Con 30 estrategias hay 870 covarianzas; 21 estrategias y 1.260 sesiones.", "A3 y B6, de tendencia en el Nasdaq y de reversión en el S&P 500.",
              "Correlación media 0,12; en la crisis, 0,37. E2 tiene −0,62.", "0,635 / √0,2 = 1,42 · 0,05 · 1.000.000 · 1 $ · 101 sesiones"]:
        print(para_voz(x))
