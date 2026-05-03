---
name: clinical-data-analysis
description: "Analisa dados clínicos, laboratoriais e de pesquisa para endocrinologia. Processa CSV, Excel, bioimpedância. Gera sumários estatísticos e visualizações."
---

# Clinical Data Analysis — Skill de Análise de Dados Clínicos

Análise estatística e visualização de dados para prática clínica endocrinológica
e pesquisa acadêmica.

## Capacidades

### 1. Análise de Dados de Pacientes
- Evolução temporal de parâmetros (peso, IMC, circunferências, labs)
- Análise de composição corporal (bioimpedância seriada)
- Correlações entre variáveis clínicas e laboratoriais
- Estratificação de risco metabólico
- Curvas de resposta terapêutica

### 2. Estatística para Pesquisa
- Teste t, Mann-Whitney, Wilcoxon
- ANOVA / Kruskal-Wallis
- Regressão linear e logística
- Curvas ROC e AUC
- Análise de sobrevida (Kaplan-Meier)
- Tamanho amostral e poder estatístico
- Meta-análise (forest plots, funnel plots)

### 3. Validação de IA Médica
- Sensibilidade, especificidade, VPP, VPN
- Matrizes de confusão
- Curvas ROC para modelos de classificação
- Validação cruzada k-fold
- Concordância inter-observador (Kappa de Cohen)
- Bland-Altman plots
- Calibração de modelos (Hosmer-Lemeshow)

### 4. Dashboards Clínicos
- Perfil de pacientes por diagnóstico
- Distribuição de comorbidades
- Tempo médio de espera / follow-up
- Indicadores de qualidade assistencial
- Análise financeira da clínica

## Parâmetros Endocrinológicos Comuns

### Perfil Tireoidiano
| Exame | Unidade | Referência | Notas |
|-------|---------|------------|-------|
| TSH | mUI/L | 0.4 - 4.0 | Ultrassensível |
| T4 Livre | ng/dL | 0.7 - 1.8 | |
| T3 Total | ng/dL | 80 - 200 | |
| Anti-TPO | UI/mL | < 35 | Autoimunidade |
| Anti-Tg | UI/mL | < 115 | |
| Tireoglobulina | ng/mL | < 77 | Seguimento ca tireoide |

### Perfil Metabólico
| Exame | Unidade | Referência |
|-------|---------|------------|
| Glicemia jejum | mg/dL | 70 - 99 |
| HbA1c | % | < 5.7 (normal), < 7.0 (DM controlado) |
| Insulina basal | µUI/mL | 2.6 - 24.9 |
| HOMA-IR | - | < 2.71 |
| Colesterol total | mg/dL | < 190 |
| LDL | mg/dL | Conforme risco CV |
| HDL | mg/dL | > 40 (H), > 50 (M) |
| Triglicérides | mg/dL | < 150 |

### Perfil Hormonal
| Exame | Unidade | Notas |
|-------|---------|-------|
| Cortisol 8h | µg/dL | 6.2 - 19.4 |
| ACTH | pg/mL | 7.2 - 63.3 |
| IGF-1 | ng/mL | Ajustar por idade |
| GH basal | ng/mL | < 3.0 |
| Testosterona total | ng/dL | 249-836 (H) |
| Estradiol | pg/mL | Conforme fase do ciclo |
| PTH | pg/mL | 15 - 65 |
| 25-OH Vitamina D | ng/mL | 30 - 60 (suficiente) |
| Cálcio iônico | mmol/L | 1.12 - 1.32 |

## Ferramentas Estatísticas

### Python (preferido)
```python
# Bibliotecas core
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, confusion_matrix
import statsmodels.api as sm
```

### Visualizações Padrão
- **Evolução temporal**: Line plot com IC 95%
- **Distribuição**: Histogramas com KDE overlay
- **Correlação**: Scatter plots com regressão + r²
- **Comparação de grupos**: Box plots / Violin plots
- **ROC**: Curva com AUC e IC bootstrap
- **Forest plot**: Para meta-análises
- **Waterfall plot**: Para variação individual

### Formatação de Gráficos Clínicos
```python
# Paleta médica padrão
COLORS = {
    'normal': '#2ecc71',
    'borderline': '#f39c12',
    'alterado': '#e74c3c',
    'referencia': '#95a5a6',
    'primary': '#3498db',
    'secondary': '#9b59b6'
}

# Estilo padrão
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 150
```

## Validação de IA Dermatológica (Pesquisa Doutoral)

### Métricas Obrigatórias
1. **Acurácia global** e por classe
2. **Sensibilidade/Especificidade** por lesão
3. **Curva ROC multiclasse** (one-vs-rest)
4. **Matriz de confusão** normalizada
5. **Concordância** IA vs dermatologista (Kappa ponderado)
6. **Calibração** (reliability diagram)

### Framework de Validação
```
DATASET
├── Treino (70%)
├── Validação (15%)
└── Teste (15%) — nunca tocado até avaliação final

AVALIAÇÃO
├── Validação cruzada 5-fold no treino
├── Métricas no conjunto de teste
├── Comparação com dermatologistas (ground truth)
└── Análise de subgrupos (fototipo, localização, tamanho)
```

## Fluxo de Análise

1. **Receber dados** (CSV, XLSX, ou entrada manual)
2. **Validar** integridade e qualidade dos dados
3. **Explorar** estatística descritiva e distribuições
4. **Analisar** conforme objetivo (comparação, correlação, predição)
5. **Visualizar** com gráficos publicação-ready
6. **Gerar** relatório com interpretação clínica
7. **Exportar** em formato solicitado (xlsx, pdf, png)

## Exemplos de Uso

- "Analise a evolução de TSH destes 50 pacientes ao longo de 12 meses"
- "Calcule o HOMA-IR e estratifique o risco metabólico desta coorte"
- "Gere uma curva ROC para o modelo de classificação de lesões dermatológicas"
- "Compare os resultados de perda de peso entre semaglutida e tirzepatida neste dataset"
- "Monte um dashboard dos KPIs da clínica no último trimestre"
- "Faça a análise estatística para o artigo sobre validação de IA dermatológica"
