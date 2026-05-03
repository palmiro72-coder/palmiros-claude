---
name: mining
description: "Engenharia de minas open-source — estimativa de recursos minerais, modelagem geológica 3D e otimização de lavra. Implementa kriging ordinário (OK), variograma experimental e modelado, compositing de furos de sondagem, visualização 3D de depósitos e otimização de pit final por programação linear. Use sempre que o usuário mencionar: estimativa de recursos, kriging, variograma, geoestatística, furo de sondagem, collar, assay, composite, teor, g/t, ppm, modelagem de depósito, block model, bloco de lavra, pit final, cava, ultimate pit, Lerchs-Grossmann, otimização de lavra, scheduling de produção, NI 43-101, JORC, OMF, Open Mining Format, GemPy, GeostatsPy, PyVista, CMOC, Leapfrog, Micromine, Seequent, Vulcan, Datamine, ouro, cobre, nióbio, ferro, ore body, orebody, ore reserve, mineral resource, prospectividade mineral, mineral prospectivity, ou qualquer análise quantitativa de depósito mineral."
---

# Mining — Engenharia de Minas Open-Source

## Visão Geral

Stack computacional para os três pilares da engenharia de minas quantitativa:

1. **Estimativa de recursos** — kriging ordinário, variograma, compositing (GeostatsPy)
2. **Modelagem geológica 3D** — envelopes implícitos de minério, superfícies (GemPy)
3. **Otimização de lavra** — pit final por programação linear (PuLP)

Formato de intercâmbio com a indústria via **OMF** (Open Mining Format) — aceito por Leapfrog, Seequent, Micromine.

## Quando Usar

- Usuário fornece CSV de furos de sondagem (collar + survey + assays) e quer estimativa
- Análise de variograma experimental e ajuste de modelo teórico
- Compositing de furos em intervalos regulares (tipicamente 2 m ou 10 m)
- Kriging ordinário 2D (slabs) ou extensão 3D por bancos
- Visualização 3D de depósito colorido por teor
- Otimização de pit final ou sequenciamento de blocos
- Export para formato OMF para entrega ao time técnico com Leapfrog/Seequent
- Análise de prospectividade mineral (etapa exploratória)

## Fluxo de Uso

### 1. Identificar o tipo de entrada

| Entrada                                     | Comando                                                                          |
|---------------------------------------------|----------------------------------------------------------------------------------|
| CSV de assays (X,Y,Z,teor)                  | `python scripts/mining.py summary --csv assays.csv --grade-col Au_gpt`           |
| CSV + parâmetros de variograma              | `python scripts/mining.py variogram --csv assays.csv --grade-col Au_gpt`         |
| Kriging 2D num slab horizontal              | `python scripts/mining.py krige2d --csv assays.csv --grade-col Au_gpt --z -75 --z-tol 15` |
| Exportar para OMF                           | `python scripts/mining.py export-omf --csv assays.csv --grade-col Au_gpt --out deposito.omf` |
| Gerar depósito sintético para teste         | `python scripts/mining.py synthetic --n-holes 50 --out assays_sim.csv`           |
| Otimização de pit final (LP, Lerchs-Gross.) | `python scripts/mining.py pit --blocks blocks.csv`                               |

### 2. Executar a análise

```bash
# Copiar o engine para o workspace
cp /mnt/skills/user/mining/scripts/mining.py /home/claude/mining.py

# Sumário estatístico de uma base de assays
python /home/claude/mining.py summary --csv assays.csv --grade-col Au_gpt

# Compositing por furo para uma janela Z
python /home/claude/mining.py composite --csv assays.csv --grade-col Au_gpt --z -75 --z-tol 15 --out composites.csv

# Kriging ordinário 2D num slab
python /home/claude/mining.py krige2d --csv assays.csv --grade-col Au_gpt \
    --z -75 --z-tol 15 \
    --nx 50 --ny 50 --xsiz 10 --ysiz 10 \
    --nugget 0.10 --sill 0.90 --range 80 \
    --out kriging.npz

# Exportar assays para OMF
python /home/claude/mining.py export-omf --csv assays.csv --grade-col Au_gpt --out deposito.omf
```

### 3. Interpretar a saída

Saída sempre em **JSON estruturado** (stdout) ou arquivo NPZ/OMF (disco).

```json
{
  "input": { "file": "assays.csv", "n_samples": 750, "grade_col": "Au_gpt" },
  "stats": {
    "n": 750, "min": 0.02, "max": 18.4,
    "mean": 1.23, "median": 0.68, "std": 1.87,
    "cv": 1.52, "skew": 3.41
  },
  "distribution": "lognormal-like",
  "recommendations": [
    "CV > 1.5 — considerar capping no percentil 97.5",
    "Skew > 3 — transformar para log antes do variograma"
  ]
}
```

### 4. Classificação do Veredito

| Métrica         | Faixa       | Interpretação                                              |
|-----------------|-------------|------------------------------------------------------------|
| CV (coef. var.) | < 0.5       | Baixa variabilidade — ouro disseminado uniforme            |
| CV              | 0.5 – 1.5   | Média — tipico de depósitos sulfetados                     |
| CV              | > 1.5       | Alta — nugget effect alto, considerar capping              |
| CV              | > 3.0       | Extrema — provavelmente veios/nuggets, tratar com cautela  |
| Skew            | < 1         | Quase-normal                                               |
| Skew            | 1 – 3       | Lognormal típico                                           |
| Skew            | > 3         | Forte assimetria — obrigatório capping/transformação       |

### 5. Formato de entrada para assays (assays.csv)

```csv
HoleID,X,Y,Z,Au_gpt,Cu_pct
DDH-001,412500.0,7845230.0,-15.0,0.12,0.04
DDH-001,412500.0,7845230.0,-25.0,0.87,0.08
DDH-001,412500.0,7845230.0,-35.0,3.45,0.21
DDH-002,412480.0,7845245.0,-15.0,0.08,0.03
...
```

Mínimo exigido: `X, Y, Z, <grade_col>`. Coluna `HoleID` recomendada para compositing correto.

### 6. Formato de entrada para block model (blocks.csv)

```csv
i,j,k,x,y,z,grade,density,cost,revenue
0,0,0,5.0,5.0,-5.0,0.12,2.7,3.2,0.0
0,0,1,5.0,5.0,-15.0,0.87,2.7,3.2,2.1
...
```

`grade` em g/t, `cost` em USD/t (lavra+proc.), `revenue` em USD por bloco. Precedência vertical (slope angle padrão 45°) aplicada automaticamente.

## Conceitos Fundamentais

Referência completa em `references/teoria.md`. Resumo:

- **Variograma γ(h)**: semi-variância em função da separação h. Modela continuidade espacial.
- **Nugget, sill, range**: parâmetros do modelo teórico. Nugget = descontinuidade à origem; sill = patamar; range = alcance.
- **Kriging ordinário (OK)**: estimador BLUE (Best Linear Unbiased Estimator) com peso local ótimo.
- **Composite**: regularização de amostras em intervalos uniformes (obrigatório antes de kriging).
- **Capping**: truncamento de outliers para evitar influência desproporcional (tipicamente P97.5 ou P99).
- **Block model**: discretização do depósito em prismas retos com teor estimado.
- **Pit final (Lerchs-Grossmann)**: otimização do contorno de cava maximizando valor econômico descontado, sujeito a ângulo de talude.

## Tabelas de Referência Rápida

### Modelos de variograma (it no GSLIB)

| Código | Modelo        | Uso típico                                      |
|--------|---------------|-------------------------------------------------|
| 1      | Esférico      | Padrão para depósitos minerais (range definido) |
| 2      | Exponencial   | Variáveis contínuas sem range estrito           |
| 3      | Gaussiano     | Variáveis muito contínuas (topografia)          |
| 4      | Potência      | Fenômenos fractais                              |

### Teor de corte típico (cut-off grade)

| Commodity | Cut-off típico | Unidade |
|-----------|----------------|---------|
| Au        | 0.3 – 0.5      | g/t     |
| Cu        | 0.25 – 0.5     | %       |
| Fe        | 25 – 45        | %       |
| Ni        | 0.5 – 1.0      | %       |
| Nb        | 0.3 – 0.5      | %       |

### Stack instalada

| Pacote       | Versão pinned | Função                             |
|--------------|---------------|------------------------------------|
| GeostatsPy   | 0.0.79        | Kriging, variograma (GSLIB Python) |
| GemPy        | 2025.2.0      | Modelagem geológica 3D implícita   |
| PyVista      | 0.47.3        | Visualização 3D VTK                |
| OMF          | 1.0.1         | Open Mining Format                 |
| PuLP         | 3.3.0         | Programação linear (pit final)     |
| Numba        | 0.65.0        | JIT para aceleração do kriging     |

Instalação via `/opt/mining-stack/venv` (LXC Proxmox). Ver bundle `mining-stack.tar.gz` para detalhes.

## Armadilhas Conhecidas

1. **Matriz singular no kb2d** — pontos co-localizados em XY (múltiplos Zs do mesmo furo). Sempre compositar por `HoleID` antes.
2. **make_variogram** — fica em `geostatspy.GSLIB`, não em `geostatspy.geostats`. Erro comum.
3. **PyVista headless** — definir `pv.OFF_SCREEN = True` em LXC sem X server.
4. **Outliers em Au** — sempre fazer EDA antes do kriging. Skew > 3 obriga capping.
5. **Range do variograma** — se o `--range` for menor que o espaçamento médio dos furos, kriging degenera para média global.
