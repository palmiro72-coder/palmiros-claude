---
name: harmonia
description: "Análise harmônica sexagesimal de geometria esférica e euclidiana. Verifica se ângulos, proporções ou coordenadas obedecem padrões geométricos harmônicos (intervalos musicais pitagóricos/ptolemaicos, divisores de 360°, ressonâncias em base 60). Use sempre que o usuário mencionar: harmonia geométrica, análise sexagesimal, shusi, intervalos musicais em geometria, verificação de padrões angulares, razões harmônicas, oitava/quinta/quarta/terça em ângulos, superfícies isoharmônicas, paralaxe diferencial, ou qualquer verificação de se um conjunto de ângulos/medidas obedece proporções harmônicas. Também use quando o usuário pedir para analisar ângulos de constelações, sítios arqueológicos, cristalografia, arquitetura sagrada, ou qualquer geometria que possa conter razões de inteiros simples."
---

# Harmonia — Análise Harmônica Sexagesimal

## Visão Geral

Sistema computacional para verificar se conjuntos de ângulos, proporções ou coordenadas obedecem padrões geométricos harmônicos. Implementa os três métodos patenteados:

1. **CHS** — Codificação Harmônica Sexagesimal
2. **SIE** — Superfícies Isoharmônicas Estelares
3. **APD** — Afinação por Paralaxe Diferencial

## Quando Usar

- Usuário fornece ângulos e quer saber se formam padrões harmônicos
- Análise de constelações, sítios megalíticos, geometria molecular
- Verificação de proporções arquitetônicas ou artísticas
- Qualquer conjunto de medidas angulares para análise em base 60
- Coordenadas estelares (RA/Dec) para análise 3D com paralaxe
- Comparação de razões geométricas com intervalos musicais

## Fluxo de Uso

### 1. Identificar o tipo de entrada

| Entrada | Método | Comando |
|---------|--------|---------|
| Lista de ângulos (graus) | CHS | `python scripts/harmonia.py chs --angles "121.4 115.2 129.7 66.9 33.4 52.8"` |
| Coordenadas RA/Dec + distâncias | CHS + SIE + APD | `python scripts/harmonia.py full --coords coords.json` |
| Pares de medidas para razão | CHS (razões) | `python scripts/harmonia.py ratio --a 66.9 --b 33.4` |
| Polígono (lados em graus) | CHS completo | `python scripts/harmonia.py polygon --sides "2.31 8.86 3.27 7.86 1.90 0.21"` |

### 2. Executar a análise

```bash
# Copiar o engine para o workspace
cp /mnt/skills/user/harmonia/scripts/harmonia.py /home/claude/harmonia.py

# Análise CHS de ângulos
python /home/claude/harmonia.py chs --angles "121.4 115.2 129.7 66.9 33.4 52.8"

# Razão específica
python /home/claude/harmonia.py ratio --a 66.9 --b 33.4

# Análise completa com coordenadas estelares
python /home/claude/harmonia.py full --coords coords.json

# Análise de superfície isoharmônica
python /home/claude/harmonia.py isosurface --coords coords.json --target-ratio 2.0 --angle1 "era" --angle2 "ear"
```

### 3. Interpretar a saída

O sistema produz saída JSON estruturada com:

```json
{
  "input": { "angles": [...], "source": "..." },
  "sexagesimal": [
    { "angle_deg": 121.4, "notation": "[2;01,24,00]₆₀", "shusi": 20.233 }
  ],
  "harmonics": [
    { "angle": 121.4, "nearest": 120, "name": "trígono (2×60)", "delta": 1.4 }
  ],
  "intervals": [
    { "pair": "C1/C2", "ratio": 2.003, "fraction": "2/1", "interval": "oitava", "error_pct": 0.15, "rank": "★★★" }
  ],
  "index_H": 0.847,
  "verdict": "HARMÔNICO — 3 intervalos com erro < 1%"
}
```

### 4. Classificação do Veredito

| Index H | Veredito | Significado |
|---------|----------|-------------|
| > 0.9 | FORTEMENTE HARMÔNICO | Múltiplos intervalos com < 0.5% erro |
| 0.7–0.9 | HARMÔNICO | Intervalos significativos presentes |
| 0.4–0.7 | PARCIALMENTE HARMÔNICO | Alguns intervalos, mas com erro > 3% |
| < 0.4 | NÃO-HARMÔNICO | Sem ressonâncias significativas |

### 5. Formato de entrada para coordenadas (coords.json)

```json
{
  "stars": [
    { "id": "alpha", "name": "Arcturus", "ra": [14,15,39.7], "dec": [19,10,56.8], "dist_ly": 36.7 },
    { "id": "beta", "name": "Nekkar", "ra": [15,7,18.9], "dec": [40,21,5.3], "dist_ly": 219.0 }
  ],
  "topology": [["beta","gamma"], ["gamma","rho"], ["rho","epsilon"], ["epsilon","alpha"]],
  "vertices": [
    { "label": "gBr", "vertex": "beta", "a": "gamma", "b": "rho" },
    { "label": "ear", "vertex": "alpha", "a": "epsilon", "b": "rho" }
  ]
}
```

## Conceitos Fundamentais

Referência completa em `references/teoria.md`. Resumo:

- **Shusi**: 1/60 do círculo = 6°. Unidade natural base-60.
- **Notação [A;BB,CC,DD]₆₀**: A×60° + BB° + CC' + DD"
- **Intervalos musicais**: Razões p/q com p,q ≤ 10. Erro < 5% = ressonância.
- **Índice H**: Média ponderada dos inversos dos erros dos k melhores intervalos.
- **Superfície isoharmônica**: Locus 2D em ℝ³ onde uma razão angular = p/q exato.
- **Paralaxe diferencial**: Assimetria de sensibilidade quando estrelas têm distâncias heterogêneas.

## Tabelas de Referência Rápida

### Intervalos Musicais (tolerância padrão: 5%)

| Razão | Nome | Cents | Peso w |
|-------|------|-------|--------|
| 2:1 | Oitava | 1200 | 10 |
| 3:2 | Quinta | 702 | 9 |
| 4:3 | Quarta | 498 | 8 |
| 5:4 | Terça maior | 386 | 7 |
| 6:5 | Terça menor | 316 | 6 |
| 5:3 | Sexta maior | 884 | 6 |
| 8:5 | Sexta menor | 814 | 5 |
| 9:8 | Tom maior | 204 | 5 |
| 10:9 | Tom menor | 182 | 4 |
| 9:5 | Sétima menor | 1018 | 4 |
| 15:8 | Sétima maior | 1088 | 3 |
| 4:1 | Dupla oitava | 2400 | 3 |
| 7:5 | Trítono | 583 | 2 |
| 16:15 | Semitom | 112 | 2 |

### Harmônicos de 360°

Os 24 divisores de 360 = 2³ × 3² × 5:
1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45, 60, 72, 90, 120, 180, 360

### Polígonos Regulares

| Ângulo | n-gono | Shusi | Fração |
|--------|--------|-------|--------|
| 360° | — | 60 | 1/1 |
| 180° | — | 30 | 1/2 |
| 120° | Trígono | 20 | 1/3 |
| 90° | Quadratura | 15 | 1/4 |
| 72° | Pentágono | 12 | 1/5 |
| 60° | Hexágono | 10 | 1/6 |
| 45° | Octógono | 7.5 | 1/8 |
| 40° | Nonágono | 6.667 | 1/9 |
| 36° | Decágono | 6 | 1/10 |
| 30° | Zodiacal | 5 | 1/12 |
