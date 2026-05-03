#!/usr/bin/env python3
"""
HARMONIA — Motor de Análise Harmônica Sexagesimal
Patente: PI 2026-03-01 (SHA-256: 9d3a6a8bfb0b32c6...)
Inventor: Dr. Lucas do Prado Palmiro

Métodos implementados:
  CHS — Codificação Harmônica Sexagesimal
  SIE — Superfícies Isoharmônicas Estelares
  APD — Afinação por Paralaxe Diferencial
"""

import math
import json
import sys
import argparse
from typing import List, Dict, Tuple, Optional

# ============================================================
# CONSTANTES
# ============================================================

MUSICAL_INTERVALS = {
    'uníssono':      (1, 1,   1200 * math.log2(1),   1),
    'oitava':        (2, 1,   1200,                   10),
    'quinta':        (3, 2,   702,                     9),
    'quarta':        (4, 3,   498,                     8),
    'terça maior':   (5, 4,   386,                     7),
    'terça menor':   (6, 5,   316,                     6),
    'sexta maior':   (5, 3,   884,                     6),
    'sexta menor':   (8, 5,   814,                     5),
    'tom maior':     (9, 8,   204,                     5),
    'tom menor':     (10, 9,  182,                     4),
    'sétima menor':  (9, 5,   1018,                    4),
    'sétima maior':  (15, 8,  1088,                    3),
    'dupla oitava':  (4, 1,   2400,                    3),
    'trítono':       (7, 5,   583,                     2),
    'semitom':       (16, 15, 112,                     2),
}

HARMONIC_DIVISORS_360 = [
    1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 18,
    20, 24, 30, 36, 40, 45, 60, 72, 90, 120, 180, 360
]

HARMONIC_NAMES = {
    360: "círculo (6×60)",
    180: "diâmetro (3×60)",
    120: "trígono (2×60)",
    90:  "quadratura (1½×60)",
    72:  "pentágono",
    60:  "hexágono (1×60)",
    45:  "octógono",
    40:  "nonágono",
    36:  "decágono",
    30:  "zodiacal (½×60)",
    24:  "pentadecágono",
    20:  "⅓×60",
    15:  "¼×60",
    12:  "⅕×60",
    10:  "⅙×60",
    9:   "40-gono",
    8:   "45-gono",
    6:   "1 shusi",
    5:   "72-gono",
    4:   "90-gono",
    3:   "120-gono",
    2:   "180-gono",
    1:   "360-gono",
}

TOLERANCE = 0.05  # 5% default

# ============================================================
# CHS — Codificação Harmônica Sexagesimal
# ============================================================

def sexagesimal_decompose(deg: float) -> Dict:
    """Decompõe ângulo em notação sexagesimal posicional [A;BB,CC,DD]₆₀"""
    a = int(deg / 60)
    rem = deg - a * 60
    b = int(rem)
    rem2 = (rem - b) * 60
    c = int(rem2)
    d = (rem2 - c) * 60
    
    notation = f"[{a};{b:02d},{c:02d},{d:04.1f}]₆₀"
    shusi = deg / 6.0
    fraction_360 = deg / 360.0
    
    return {
        "angle_deg": round(deg, 4),
        "notation": notation,
        "components": {"A": a, "B": b, "C": c, "D": round(d, 1)},
        "shusi": round(shusi, 4),
        "fraction_360": round(fraction_360, 6),
        "nearest_integer_shusi": round(shusi),
        "shusi_deviation": round(shusi - round(shusi), 4)
    }


def find_nearest_harmonic(deg: float) -> Dict:
    """Encontra o divisor harmônico de 360° mais próximo"""
    best = min(HARMONIC_DIVISORS_360, key=lambda x: abs(x - deg))
    delta = deg - best
    return {
        "angle_deg": round(deg, 4),
        "nearest_harmonic": best,
        "harmonic_name": HARMONIC_NAMES.get(best, f"{best}°"),
        "delta_deg": round(delta, 4),
        "delta_arcmin": round(delta * 60, 2),
        "relative_error_pct": round(abs(delta) / best * 100, 3) if best > 0 else 0
    }


def identify_musical_interval(ratio: float, tolerance: float = TOLERANCE) -> Optional[Dict]:
    """Identifica o intervalo musical mais próximo de uma razão"""
    best_name = None
    best_err = 999
    best_n, best_d = 0, 0
    best_weight = 0
    
    for name, (n, d, cents, weight) in MUSICAL_INTERVALS.items():
        target = n / d
        err = abs(ratio - target) / target
        if err < best_err:
            best_err = err
            best_name = name
            best_n, best_d = n, d
            best_weight = weight
    
    if best_err > tolerance:
        return None
    
    rank = "★★★" if best_err < 0.01 else "★★" if best_err < 0.03 else "★"
    
    return {
        "ratio": round(ratio, 6),
        "fraction": f"{best_n}/{best_d}",
        "interval": best_name,
        "error_pct": round(best_err * 100, 4),
        "rank": rank,
        "weight": best_weight,
        "cents_nominal": MUSICAL_INTERVALS[best_name][2],
        "cents_actual": round(1200 * math.log2(ratio), 1) if ratio > 0 else 0
    }


def compute_harmonicity_index(intervals: List[Dict], k: int = None) -> float:
    """Índice de harmonicidade global H"""
    if not intervals:
        return 0.0
    
    if k is None:
        k = len(intervals)
    
    # Ordenar por erro (menores primeiro)
    sorted_ivs = sorted(intervals, key=lambda x: x['error_pct'])[:k]
    
    if not sorted_ivs:
        return 0.0
    
    total = sum(iv['weight'] / (1 + iv['error_pct'] / 100) for iv in sorted_ivs)
    max_possible = sum(iv['weight'] for iv in sorted_ivs)
    
    return round(total / max_possible, 4) if max_possible > 0 else 0.0


def classify_verdict(index_h: float, n_precise: int) -> str:
    """Classifica o veredito baseado no índice H"""
    if index_h > 0.9 and n_precise >= 2:
        return "FORTEMENTE HARMÔNICO"
    elif index_h > 0.7:
        return "HARMÔNICO"
    elif index_h > 0.4:
        return "PARCIALMENTE HARMÔNICO"
    else:
        return "NÃO-HARMÔNICO"


def analyze_angles(angles: List[float], labels: List[str] = None, tolerance: float = TOLERANCE) -> Dict:
    """Análise CHS completa de uma lista de ângulos"""
    n = len(angles)
    if labels is None:
        labels = [f"C{i+1}" for i in range(n)]
    
    # 1. Decomposição sexagesimal
    sexagesimal = []
    for i, deg in enumerate(angles):
        s = sexagesimal_decompose(deg)
        s["label"] = labels[i]
        sexagesimal.append(s)
    
    # 2. Harmônicos mais próximos
    harmonics = []
    for i, deg in enumerate(angles):
        h = find_nearest_harmonic(deg)
        h["label"] = labels[i]
        harmonics.append(h)
    
    # 3. Razões e intervalos musicais
    intervals = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            ratio = angles[i] / angles[j]
            if ratio < 1:
                continue
            iv = identify_musical_interval(ratio, tolerance)
            if iv is not None:
                iv["pair"] = f"{labels[i]}/{labels[j]}"
                iv["numerator_deg"] = angles[i]
                iv["denominator_deg"] = angles[j]
                intervals.append(iv)
    
    # Ordenar por precisão
    intervals.sort(key=lambda x: x['error_pct'])
    
    # 4. Índice de harmonicidade
    index_h = compute_harmonicity_index(intervals)
    n_precise = sum(1 for iv in intervals if iv['error_pct'] < 1.0)
    verdict = classify_verdict(index_h, n_precise)
    
    # 5. Somas significativas
    sums = []
    for i in range(n):
        for j in range(i + 1, n):
            s = angles[i] + angles[j]
            nearest = min(HARMONIC_DIVISORS_360, key=lambda x: abs(x - s))
            if abs(s - nearest) < 10:
                sums.append({
                    "pair": f"{labels[i]}+{labels[j]}",
                    "sum_deg": round(s, 2),
                    "nearest_harmonic": nearest,
                    "delta": round(s - nearest, 2)
                })
    
    return {
        "input": {
            "n_angles": n,
            "angles_deg": [round(a, 4) for a in angles],
            "labels": labels
        },
        "sexagesimal": sexagesimal,
        "harmonics": harmonics,
        "intervals": intervals,
        "sums": sums,
        "index_H": index_h,
        "n_intervals_found": len(intervals),
        "n_precise_lt1pct": n_precise,
        "verdict": verdict
    }


# ============================================================
# GEOMETRIA ESFÉRICA
# ============================================================

def angular_separation(ra1, dec1, ra2, dec2):
    """Separação angular entre dois pontos na esfera (tudo em radianos)"""
    cs = (math.sin(dec1) * math.sin(dec2) +
          math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2))
    return math.acos(max(-1, min(1, cs)))


def vertex_angle(v_ra, v_dec, a_ra, a_dec, b_ra, b_dec):
    """Ângulo no vértice V entre A e B na esfera (lei do cosseno esférico)"""
    va = angular_separation(v_ra, v_dec, a_ra, a_dec)
    vb = angular_separation(v_ra, v_dec, b_ra, b_dec)
    ab = angular_separation(a_ra, a_dec, b_ra, b_dec)
    
    sin_va = math.sin(va)
    sin_vb = math.sin(vb)
    
    if sin_va < 1e-12 or sin_vb < 1e-12:
        return 0
    
    cos_c = (math.cos(ab) - math.cos(va) * math.cos(vb)) / (sin_va * sin_vb)
    return math.degrees(math.acos(max(-1, min(1, cos_c))))


def hms_to_rad(h, m, s):
    return math.radians((h + m / 60 + s / 3600) * 15)


def dms_to_rad(d, m, s):
    sign = 1 if d >= 0 else -1
    return math.radians(abs(d) + m / 60 + s / 3600) * sign


def star_to_xyz(ra_rad, dec_rad, dist):
    return [
        dist * math.cos(dec_rad) * math.cos(ra_rad),
        dist * math.cos(dec_rad) * math.sin(ra_rad),
        dist * math.sin(dec_rad)
    ]


# ============================================================
# SIE — Superfícies Isoharmônicas
# ============================================================

def apparent_radec(observer, star_xyz):
    """RA/Dec aparente de uma estrela vista de um observador"""
    dx = star_xyz[0] - observer[0]
    dy = star_xyz[1] - observer[1]
    dz = star_xyz[2] - observer[2]
    r = math.sqrt(dx*dx + dy*dy + dz*dz)
    if r < 1e-10:
        return 0, 0
    dec = math.asin(max(-1, min(1, dz / r)))
    ra = math.atan2(dy, dx)
    return ra, dec


def compute_angle_from_observer(observer, stars_xyz, vertex_id, a_id, b_id):
    """Computa ângulo no vértice visto de um observador arbitrário"""
    rv, dv = apparent_radec(observer, stars_xyz[vertex_id])
    ra_, da = apparent_radec(observer, stars_xyz[a_id])
    rb, db = apparent_radec(observer, stars_xyz[b_id])
    return vertex_angle(rv, dv, ra_, da, rb, db)


def find_isosurface(stars_xyz, vertex_defs, angle1_def, angle2_def,
                    target_ratio=2.0, n_trials=500, seed=42):
    """
    Encontra pontos na superfície isoharmônica onde angle1/angle2 = target_ratio.
    
    angle1_def, angle2_def: tuplas (vertex_id, a_id, b_id)
    """
    import random
    random.seed(seed)
    
    solutions = []
    earth = [0.0, 0.0, 0.0]
    
    def cost(obs):
        try:
            a1 = compute_angle_from_observer(obs, stars_xyz, *angle1_def)
            a2 = compute_angle_from_observer(obs, stars_xyz, *angle2_def)
            if a2 < 0.1:
                return 1e6
            return (a1 / a2 - target_ratio) ** 2
        except:
            return 1e6
    
    # Nelder-Mead simples (sem scipy para portabilidade)
    def nelder_mead(f, x0, tol=1e-12, max_iter=5000):
        n = len(x0)
        alpha, gamma, rho, sigma = 1.0, 2.0, 0.5, 0.5
        
        # Simplex inicial
        simplex = [list(x0)]
        for i in range(n):
            p = list(x0)
            p[i] += 1.0
            simplex.append(p)
        
        fvals = [f(s) for s in simplex]
        
        for _ in range(max_iter):
            # Ordenar
            order = sorted(range(n + 1), key=lambda i: fvals[i])
            simplex = [simplex[i] for i in order]
            fvals = [fvals[i] for i in order]
            
            if fvals[0] < tol:
                break
            
            # Centróide (sem o pior)
            centroid = [sum(simplex[i][j] for i in range(n)) / n for j in range(n)]
            
            # Reflexão
            xr = [centroid[j] + alpha * (centroid[j] - simplex[-1][j]) for j in range(n)]
            fr = f(xr)
            
            if fvals[0] <= fr < fvals[-2]:
                simplex[-1] = xr
                fvals[-1] = fr
            elif fr < fvals[0]:
                # Expansão
                xe = [centroid[j] + gamma * (xr[j] - centroid[j]) for j in range(n)]
                fe = f(xe)
                if fe < fr:
                    simplex[-1] = xe
                    fvals[-1] = fe
                else:
                    simplex[-1] = xr
                    fvals[-1] = fr
            else:
                # Contração
                xc = [centroid[j] + rho * (simplex[-1][j] - centroid[j]) for j in range(n)]
                fc = f(xc)
                if fc < fvals[-1]:
                    simplex[-1] = xc
                    fvals[-1] = fc
                else:
                    # Encolhimento
                    for i in range(1, n + 1):
                        simplex[i] = [simplex[0][j] + sigma * (simplex[i][j] - simplex[0][j]) for j in range(n)]
                        fvals[i] = f(simplex[i])
        
        return simplex[0], fvals[0]
    
    for trial in range(n_trials):
        random.seed(seed + trial)
        if trial < n_trials // 3:
            x0 = [random.gauss(0, 5) for _ in range(3)]
        elif trial < 2 * n_trials // 3:
            x0 = [random.gauss(0, 15) for _ in range(3)]
        else:
            x0 = [random.gauss(0, 30) for _ in range(3)]
        
        try:
            sol, fval = nelder_mead(cost, x0)
            if fval < 1e-10:
                # Deduplicar
                is_dup = False
                for prev in solutions:
                    dist = math.sqrt(sum((sol[i] - prev[0][i])**2 for i in range(3)))
                    if dist < 0.1:
                        is_dup = True
                        break
                if not is_dup:
                    a1 = compute_angle_from_observer(sol, stars_xyz, *angle1_def)
                    a2 = compute_angle_from_observer(sol, stars_xyz, *angle2_def)
                    d = math.sqrt(sum(s**2 for s in sol))
                    solutions.append((sol, a1, a2, d, fval))
        except:
            pass
    
    # Ordenar por distância da Terra
    solutions.sort(key=lambda x: x[3])
    
    return solutions


# ============================================================
# APD — Afinação por Paralaxe Diferencial
# ============================================================

def compute_jacobian(stars_xyz, vertex_defs, observer=None, h=1.0):
    """Computa a matriz Jacobiana de sensibilidade"""
    if observer is None:
        observer = [0.0, 0.0, 0.0]
    
    jacobian = {}
    
    for label, (v, a, b) in vertex_defs.items():
        row = []
        for axis in range(3):
            obs_plus = list(observer)
            obs_minus = list(observer)
            obs_plus[axis] += h
            obs_minus[axis] -= h
            
            a_plus = compute_angle_from_observer(obs_plus, stars_xyz, v, a, b)
            a_minus = compute_angle_from_observer(obs_minus, stars_xyz, v, a, b)
            
            deriv = (a_plus - a_minus) / (2 * h)
            row.append(round(deriv, 6))
        
        jacobian[label] = {
            "d_dx": row[0],
            "d_dy": row[1],
            "d_dz": row[2],
            "magnitude": round(math.sqrt(sum(r**2 for r in row)), 6)
        }
    
    return jacobian


# ============================================================
# CLI & OUTPUT
# ============================================================

def format_output(result: Dict, fmt: str = "text") -> str:
    """Formata a saída"""
    if fmt == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    lines = []
    lines.append("═" * 65)
    lines.append("  HARMONIA — Análise Harmônica Sexagesimal")
    lines.append("═" * 65)
    
    # Input
    inp = result.get("input", {})
    lines.append(f"\n  Entrada: {inp.get('n_angles', 0)} ângulos")
    if 'angles_deg' in inp:
        labels = inp.get('labels', [])
        for i, a in enumerate(inp['angles_deg']):
            lab = labels[i] if i < len(labels) else f"C{i+1}"
            lines.append(f"    {lab} = {a}°")
    
    # Sexagesimal
    lines.append(f"\n  DECOMPOSIÇÃO SEXAGESIMAL")
    lines.append("  " + "─" * 55)
    for s in result.get('sexagesimal', []):
        lines.append(f"  {s.get('label',''):8s} = {s['notation']:22s} = {s['shusi']:.3f} shusi")
    
    # Harmônicos
    lines.append(f"\n  RESSONÂNCIAS HARMÔNICAS")
    lines.append("  " + "─" * 55)
    for h in result.get('harmonics', []):
        lines.append(f"  {h.get('label',''):8s} = {h['angle_deg']:6.1f}° → {h['nearest_harmonic']:3d}° "
                     f"({h['harmonic_name']}) Δ={h['delta_deg']:+.1f}°")
    
    # Intervalos musicais
    ivs = result.get('intervals', [])
    if ivs:
        lines.append(f"\n  INTERVALOS MUSICAIS ({len(ivs)} encontrados)")
        lines.append("  " + "─" * 55)
        for iv in ivs:
            lines.append(f"  {iv['rank']} {iv['pair']:20s} = {iv['ratio']:.4f} ≈ {iv['fraction']:5s} "
                        f"= {iv['interval']:14s} (err {iv['error_pct']:.2f}%)")
    
    # Somas
    sums = result.get('sums', [])
    if sums:
        lines.append(f"\n  SOMAS SIGNIFICATIVAS")
        lines.append("  " + "─" * 55)
        for s in sums:
            lines.append(f"  {s['pair']:15s} = {s['sum_deg']:6.1f}° → {s['nearest_harmonic']}° "
                        f"(Δ={s['delta']:+.1f}°)")
    
    # Veredito
    lines.append(f"\n  {'═' * 55}")
    lines.append(f"  ÍNDICE DE HARMONICIDADE: H = {result.get('index_H', 0):.4f}")
    lines.append(f"  Intervalos < 1% erro: {result.get('n_precise_lt1pct', 0)}")
    lines.append(f"  VEREDITO: {result.get('verdict', '?')}")
    lines.append(f"  {'═' * 55}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="HARMONIA — Análise Harmônica Sexagesimal")
    subparsers = parser.add_subparsers(dest="command")
    
    # CHS
    p_chs = subparsers.add_parser("chs", help="Codificação Harmônica Sexagesimal")
    p_chs.add_argument("--angles", required=True, help="Ângulos separados por espaço")
    p_chs.add_argument("--labels", help="Labels separados por espaço")
    p_chs.add_argument("--tolerance", type=float, default=0.05, help="Tolerância para intervalos (default 0.05)")
    p_chs.add_argument("--format", choices=["text", "json"], default="text")
    
    # Ratio
    p_ratio = subparsers.add_parser("ratio", help="Análise de uma razão específica")
    p_ratio.add_argument("--a", type=float, required=True, help="Numerador")
    p_ratio.add_argument("--b", type=float, required=True, help="Denominador")
    p_ratio.add_argument("--format", choices=["text", "json"], default="text")
    
    # Full (com coordenadas)
    p_full = subparsers.add_parser("full", help="Análise completa com coordenadas")
    p_full.add_argument("--coords", required=True, help="Arquivo JSON com coordenadas")
    p_full.add_argument("--format", choices=["text", "json"], default="text")
    
    # Isosurface
    p_iso = subparsers.add_parser("isosurface", help="Busca de superfície isoharmônica")
    p_iso.add_argument("--coords", required=True, help="Arquivo JSON com coordenadas")
    p_iso.add_argument("--target-ratio", type=float, default=2.0, help="Razão-alvo (default 2.0)")
    p_iso.add_argument("--angle1", required=True, help="Label do ângulo 1 (numerador)")
    p_iso.add_argument("--angle2", required=True, help="Label do ângulo 2 (denominador)")
    p_iso.add_argument("--n-trials", type=int, default=300, help="Número de tentativas (default 300)")
    p_iso.add_argument("--format", choices=["text", "json"], default="text")
    
    args = parser.parse_args()
    
    if args.command == "chs":
        angles = [float(x) for x in args.angles.split()]
        labels = args.labels.split() if args.labels else None
        result = analyze_angles(angles, labels, args.tolerance)
        print(format_output(result, args.format))
    
    elif args.command == "ratio":
        a, b = args.a, args.b
        ratio = a / b if b != 0 else 0
        iv = identify_musical_interval(ratio)
        sa = sexagesimal_decompose(a)
        sb = sexagesimal_decompose(b)
        
        result = {
            "numerator": {"value": a, **sa},
            "denominator": {"value": b, **sb},
            "ratio": round(ratio, 8),
            "interval": iv,
            "is_harmonic": iv is not None
        }
        
        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n  {a}° / {b}° = {ratio:.6f}")
            print(f"  {a}° = {sa['notation']} = {sa['shusi']:.3f} shusi")
            print(f"  {b}° = {sb['notation']} = {sb['shusi']:.3f} shusi")
            if iv:
                print(f"\n  INTERVALO: {iv['interval']} ({iv['fraction']})")
                print(f"  Erro: {iv['error_pct']:.4f}% — {iv['rank']}")
                print(f"  Cents: {iv['cents_actual']} (nominal: {iv['cents_nominal']})")
            else:
                print(f"\n  Nenhum intervalo musical encontrado (tolerância {TOLERANCE*100}%)")
    
    elif args.command == "full":
        with open(args.coords) as f:
            data = json.load(f)
        
        # Parsear estrelas
        stars_radec = {}
        stars_xyz = {}
        for star in data['stars']:
            ra = hms_to_rad(*star['ra'])
            dec = dms_to_rad(*star['dec'])
            dist = star['dist_ly']
            stars_radec[star['id']] = (ra, dec)
            stars_xyz[star['id']] = star_to_xyz(ra, dec, dist)
        
        # Computar ângulos nos vértices
        angles = []
        labels = []
        for vdef in data['vertices']:
            v_rd = stars_radec[vdef['vertex']]
            a_rd = stars_radec[vdef['a']]
            b_rd = stars_radec[vdef['b']]
            ang = vertex_angle(v_rd[0], v_rd[1], a_rd[0], a_rd[1], b_rd[0], b_rd[1])
            angles.append(ang)
            labels.append(vdef['label'])
        
        result = analyze_angles(angles, labels)
        result["input"]["source"] = args.coords
        result["input"]["stars"] = [s['name'] for s in data['stars']]
        
        # Jacobiana
        vertex_defs_indexed = {}
        star_ids = list(stars_xyz.keys())
        for vdef in data['vertices']:
            vertex_defs_indexed[vdef['label']] = (vdef['vertex'], vdef['a'], vdef['b'])
        
        jac = compute_jacobian(stars_xyz, vertex_defs_indexed)
        result["jacobian"] = jac
        
        print(format_output(result, args.format))
    
    elif args.command == "isosurface":
        with open(args.coords) as f:
            data = json.load(f)
        
        stars_xyz = {}
        for star in data['stars']:
            ra = hms_to_rad(*star['ra'])
            dec = dms_to_rad(*star['dec'])
            stars_xyz[star['id']] = star_to_xyz(ra, dec, star['dist_ly'])
        
        # Encontrar as definições dos ângulos
        a1_def = None
        a2_def = None
        for vdef in data['vertices']:
            if vdef['label'] == args.angle1:
                a1_def = (vdef['vertex'], vdef['a'], vdef['b'])
            if vdef['label'] == args.angle2:
                a2_def = (vdef['vertex'], vdef['a'], vdef['b'])
        
        if a1_def is None or a2_def is None:
            print(f"Erro: ângulos '{args.angle1}' ou '{args.angle2}' não encontrados")
            sys.exit(1)
        
        print(f"Buscando superfície onde {args.angle1}/{args.angle2} = {args.target_ratio}...")
        solutions = find_isosurface(stars_xyz, data['vertices'], a1_def, a2_def,
                                    args.target_ratio, args.n_trials)
        
        result = {
            "target_ratio": args.target_ratio,
            "angle1": args.angle1,
            "angle2": args.angle2,
            "n_solutions": len(solutions),
            "solutions": []
        }
        
        for sol, a1, a2, d, fval in solutions[:20]:
            result["solutions"].append({
                "position_ly": [round(s, 4) for s in sol],
                "distance_ly": round(d, 4),
                "distance_au": round(d * 63241, 0),
                "angle1_deg": round(a1, 6),
                "angle2_deg": round(a2, 6),
                "ratio": round(a1 / a2, 10) if a2 > 0.01 else 0,
                "residual": fval
            })
        
        if args.format == "json":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n  Encontrados {len(solutions)} pontos na superfície")
            if solutions:
                s = solutions[0]
                print(f"\n  PONTO MAIS PRÓXIMO DA TERRA:")
                print(f"  Posição: ({s[0][0]:+.3f}, {s[0][1]:+.3f}, {s[0][2]:+.3f}) ly")
                print(f"  Distância: {s[3]:.4f} ly = {s[3]*63241:.0f} UA")
                print(f"  {args.angle1} = {s[1]:.6f}°")
                print(f"  {args.angle2} = {s[2]:.6f}°")
                print(f"  Razão = {s[1]/s[2]:.10f}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
