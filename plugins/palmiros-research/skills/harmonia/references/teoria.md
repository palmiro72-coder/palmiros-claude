# Teoria — Referência Completa de Harmonia Sexagesimal

## 1. Por que Base 60?

60 = 2² × 3 × 5 — possui 12 divisores (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60).
Nenhum inteiro menor que 100 tem tantos divisores.

360° = 6 × 60° — o círculo em base 60 tem 24 divisores:
1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45, 60, 72, 90, 120, 180, 360

A base 60 contém NATIVAMENTE os primos 2, 3 e 5 — exatamente os primos
que geram todos os intervalos musicais clássicos:
- Pitagóricos (2,3): oitava 2:1, quinta 3:2, quarta 4:3
- Ptolemaicos (2,3,5): terça maior 5:4, terça menor 6:5, sexta 5:3

## 2. Notação Posicional [A;BB,CC,DD]₆₀

Dado um ângulo C em graus decimais:

    A  = ⌊C / 60⌋           → múltiplos de 60°
    BB = ⌊C mod 60⌋          → graus residuais
    CC = ⌊(frac(C)) × 60⌋   → minutos de arco
    DD = frac do resto × 60  → segundos de arco

Exemplo: 121.4° = [2;01,24,00]₆₀
  → 2 × 60° + 1° + 24' + 0" = 120° + 1° + 0.4° = 121.4°

## 3. O Shusi

1 shusi = 1/60 do círculo = 6°

Origem: termo sumério para 1/60 do côvado.
Em astronomia: 1 shusi = 1/60 × 360° = 6°

Conversão: S = C / 6

Valores harmônicos em shusi:
  60 shusi = 360° (círculo)
  30 shusi = 180° (diâmetro)
  20 shusi = 120° (trígono/equilátero)
  15 shusi = 90°  (quadratura)
  12 shusi = 72°  (pentágono)
  10 shusi = 60°  (hexágono)
  6  shusi = 36°  (decágono)
  5  shusi = 30°  (signo zodiacal)

## 4. Intervalos Musicais

### Tabela Completa

| Razão  | Nome            | Cents  | Peso | Primos  |
|--------|-----------------|--------|------|---------|
| 1:1    | Uníssono        | 0      | 1    | —       |
| 2:1    | Oitava          | 1200   | 10   | 2       |
| 3:2    | Quinta          | 702    | 9    | 2,3     |
| 4:3    | Quarta          | 498    | 8    | 2,3     |
| 5:4    | Terça maior     | 386    | 7    | 2,5     |
| 6:5    | Terça menor     | 316    | 6    | 2,3,5   |
| 5:3    | Sexta maior     | 884    | 6    | 3,5     |
| 8:5    | Sexta menor     | 814    | 5    | 2,5     |
| 9:8    | Tom maior       | 204    | 5    | 2,3     |
| 10:9   | Tom menor       | 182    | 4    | 2,3,5   |
| 9:5    | Sétima menor    | 1018   | 4    | 3,5     |
| 15:8   | Sétima maior    | 1088   | 3    | 2,3,5   |
| 4:1    | Dupla oitava    | 2400   | 3    | 2       |
| 7:5    | Trítono         | 583    | 2    | 5,7     |
| 16:15  | Semitom         | 112    | 2    | 2,3,5   |

### Cents
cents = 1200 × log₂(f₂/f₁)

### Hierarquia de Consonância
Intervalos envolvendo apenas 2 e 3 (pitagóricos) são mais consonantes.
Intervalos adicionando 5 (ptolemaicos) são secundários.
Intervalos com 7 (trítono) são dissonantes.

Essa mesma hierarquia aparece na geometria de Boötes:
- 9:8 (primos 2,3) → erro 0.08% ★★★
- 2:1 (primo 2) → erro 0.15% ★★★
- 9:5 (primos 3,5) → erro 0.81% ★★★
- 5:4 (primos 2,5) → erro 1.36% ★★

## 5. Índice de Harmonicidade H

H = (1/k) × Σᵢ wᵢ / (1 + εᵢ)

Onde:
  k = número de intervalos significativos
  wᵢ = peso do i-ésimo intervalo (da tabela acima)
  εᵢ = erro relativo do i-ésimo intervalo

Normalizado pelo máximo teórico: H ∈ [0, 1]

Classificação:
  H > 0.9  → FORTEMENTE HARMÔNICO
  H > 0.7  → HARMÔNICO
  H > 0.4  → PARCIALMENTE HARMÔNICO
  H ≤ 0.4  → NÃO-HARMÔNICO

## 6. Geometria Esférica

### Separação Angular
cos(Δσ) = sin(δ₁)sin(δ₂) + cos(δ₁)cos(δ₂)cos(α₁ − α₂)

### Ângulo no Vértice (Lei do Cosseno Esférico)
cos(C) = [cos(c) − cos(a)cos(b)] / [sin(a)sin(b)]

Onde a = VB, b = VA, c = AB são os lados opostos.

### Coordenadas 3D
x = d × cos(δ) × cos(α)
y = d × cos(δ) × sin(α)  
z = d × sin(δ)

## 7. Superfícies Isoharmônicas (SIE)

Definição: S = {O ∈ ℝ³ | ∠₁(O)/∠₂(O) = r*}

Onde ∠ₖ(O) é o ângulo k da figura estelar observada do ponto O,
e r* = p/q é um intervalo musical.

A superfície é 2D no espaço 3D (pelo teorema da função implícita).

### Mecanismo: Paralaxe Diferencial
Quando estrelas estão a distâncias heterogêneas, o deslocamento do
observador altera os ângulos aparentes assimetricamente:
- Estrelas próximas: pouca mudança angular
- Estrelas distantes: muita mudança angular

Essa assimetria permite "afinar" razões angulares.

## 8. Paralelo Endócrino

As mesmas razões harmônicas governam osciladores biológicos:

| Razão | Geométrico (Boötes)      | Endócrino                    |
|-------|--------------------------|------------------------------|
| 2:1   | εrα/εαρ = 2.003         | GnRH/LH, Cortisol 120/60min |
| 9:8   | γρε/βγρ = 1.126         | TSH ultradiano               |
| 5:4   | ερα/ραη = 1.267         | Insulina fases               |
| 3:2   | —                        | GHRH/GH burst                |

Princípio: razões de inteiros simples são ATRATORES UNIVERSAIS
de sistemas oscilatórios acoplados (Arnold tongues).

Hormônio é frequência, não molécula. Doença endócrina é desarmonia.
