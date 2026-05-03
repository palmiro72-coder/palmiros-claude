---
name: anti-glosa
description: "Sistema de auditoria preditiva hospitalar anti-glosa. Motor de IA que detecta inconsistências em contas hospitalares ANTES do envio à operadora, identificando erros TUSS/CID, documentação insuficiente, cobranças perdidas e risco de glosa. Use sempre que o usuário mencionar: glosa, auditoria hospitalar, faturamento hospitalar, conta hospitalar, TUSS, OPME, autorização prévia, senha vencida, cobrança perdida, missing charges, revenue cycle, auditoria preditiva, risco de glosa, operadora de saúde, convênio médico, análise de prontuário para faturamento, documentação clínica para cobrança, ou qualquer análise de consistência entre prontuário e conta hospitalar. Também use quando o usuário pedir para verificar compatibilidade CID/procedimento, analisar perfil de operadora, ou otimizar receita hospitalar."
---

# AntiGlosa — Motor de Auditoria Preditiva Hospitalar

## Visão Geral

Sistema com 4 módulos integrados para prevenir glosas hospitalares:

1. **TUSS** — Motor de Regras TUSS/CID (consistência e compatibilidade)
2. **NLP** — Extrator de Justificativas Clínicas (análise de prontuário)
3. **MISS** — Detector de Cobranças Perdidas (receita não faturada)
4. **RISK** — Scoring de Risco de Glosa (priorização de revisão)

## Quando Usar

- Auditar conta hospitalar antes do envio à operadora
- Verificar compatibilidade CID vs procedimento TUSS
- Analisar qualidade de documentação clínica para faturamento
- Detectar procedimentos realizados mas não cobrados
- Calcular risco de glosa por conta
- Consultar perfil de operadora e padrões de glosa
- Analisar texto de prontuário para gaps de justificativa

## Fluxo de Uso

### 1. Preparar entrada

| Entrada | Formato | Comando |
|---------|---------|---------|
| Conta hospitalar (JSON) | ContaHospitalar | `python antiglosa.py audit --input conta.json` |
| Prontuário (texto) | texto livre | `python antiglosa.py nlp --text "..."` |
| Demonstração | built-in | `python antiglosa.py demo` |
| Perfil operadora | nome | `python antiglosa.py operadora --nome amil` |
| Regras ativas | — | `python antiglosa.py regras` |

### 2. Executar análise

```bash
# Copiar engine para workspace
cp /mnt/skills/user/anti-glosa/scripts/antiglosa.py /home/claude/antiglosa.py

# Demo completa (conta simulada com erros propositais)
python /home/claude/antiglosa.py demo

# Auditoria de conta real
python /home/claude/antiglosa.py audit --input conta.json --output relatorio.json

# Apenas NLP do prontuário
python /home/claude/antiglosa.py nlp --text "Paciente com DM2, indicado bariátrica..."

# Apenas perfil de operadora
python /home/claude/antiglosa.py operadora --nome amil

# Listar todas as regras
python /home/claude/antiglosa.py regras
```

### 3. Interpretar saída

A auditoria completa retorna JSON com:

```json
{
  "meta": { "conta_id": "...", "versao_engine": "1.0.0" },
  "risk_score": {
    "risk_score": 0.72,
    "risk_level": "CRÍTICO",
    "action": "REVISÃO OBRIGATÓRIA antes do envio",
    "valor_em_risco": 25400.00
  },
  "resumo": {
    "total_alertas": 8,
    "por_severidade": { "crítica": 1, "alta": 4, "média": 2, "baixa": 1 },
    "por_modulo": { "TUSS": 4, "NLP": 2, "MISS": 2 },
    "valor_total_conta": 35275.00,
    "cobranças_perdidas": 2
  },
  "alertas": { "tuss": [...], "nlp": [...], "missing": [...] },
  "recomendacoes_prioritarias": [...]
}
```

### 4. Classificação de Risco

| Score | Nível | Ação |
|-------|-------|------|
| ≥ 0.7 | CRÍTICO | Revisão obrigatória antes do envio |
| 0.5–0.7 | ALTO | Revisão recomendada — prioridade alta |
| 0.3–0.5 | MÉDIO | Revisão seletiva de itens sinalizados |
| < 0.3 | BAIXO | Envio seguro — monitorar resultado |

### 5. Formato de entrada (conta.json)

```json
{
  "id_conta": "CONTA-2026-001",
  "paciente_id": "PAC-001",
  "data_internacao": "2026-02-20",
  "data_alta": "2026-03-01",
  "cid_principal": "E11.9",
  "cids_secundarios": ["E78.5", "I10"],
  "operadora": "amil",
  "tipo_atendimento": "internação",
  "itens": [
    {
      "id": "IT-001",
      "tipo": "procedimento",
      "codigo_tuss": "30901016",
      "descricao": "Cirurgia bariátrica",
      "quantidade": 1,
      "valor_unitario": 15000,
      "data": "2026-02-22",
      "medico_executante": "Dr. Silva",
      "cid_vinculado": "E66.0",
      "senha_autorizacao": "AUTH-12345",
      "data_senha": "2026-01-10",
      "justificativa": "Obesidade grau III refratária a tratamento clínico",
      "registro_anvisa": "",
      "marca": "",
      "lote": ""
    }
  ],
  "prontuario_texto": "Paciente feminina, 45 anos...",
  "prescricoes": ["Enoxaparina 40mg SC 1x/dia"],
  "procedimentos_realizados": ["Cirurgia bariátrica sleeve"]
}
```

## Módulos em Detalhe

### Módulo TUSS — Motor de Regras

Verifica:
- Compatibilidade CID × código TUSS (10 regras de incompatibilidade)
- Documentação obrigatória por tipo (OPME, alto custo, off-label, imunobiológico)
- Cobranças duplicadas (mesmo código + data + médico)
- Autorização prévia (senha válida e dentro do prazo por operadora)

### Módulo NLP — Análise de Prontuário

Detecta no texto:
- Justificativas clínicas presentes (12 padrões)
- Documentação fraca/genérica (4 padrões anti-pattern)
- Itens de alto custo que exigem documentação extra (6 categorias)
- Score de documentação (0–1)

### Módulo MISS — Cobranças Perdidas

Cruza prontuário × conta para encontrar:
- 10 tipos de procedimento frequentemente não faturados
- Medicações prescritas não cobradas
- Padrões: CGM, fisioterapia, nutrição, interconsulta, POCUS, etc.

### Módulo RISK — Scoring de Risco

7 fatores de risco ponderados:
- Valor total da conta (peso 0.20)
- Operadora rigorosa (peso 0.15)
- Número de itens (peso 0.10)
- Internação longa (peso 0.15)
- OPME presente (peso 0.15)
- Itens sem autorização (peso 0.10)
- Documentação fraca (peso 0.15)

## Operadoras Monitoradas

7 operadoras com perfil completo:
- Amil, SulAmérica, Bradesco Saúde, Unimed, Notre Dame Intermédica, CASSI, GEAP

Cada perfil contém: taxa média de glosa, focos de auditoria, exigência de senha,
prazo de validade da senha, e observações específicas.

## Conceitos Fundamentais

Referência completa em `references/regras_tuss.md`:
- Estrutura de códigos TUSS por faixa
- Regras de incompatibilidade CID × TUSS
- Documentação obrigatória por tipo de material
- Top 5 operadoras que mais glosam
- Top 10 procedimentos que mais dão prejuízo
- Causas raiz de glosa (40% documentação, 30% codificação)

## Roadmap (versões futuras)

- **v1.1**: Integração com API do prontuário eletrônico Einstein (FHIR/HL7)
- **v1.2**: LLM local (Llama 3) para NLP avançado do prontuário
- **v2.0**: ML treinado com histórico real de glosas do Einstein
- **v2.1**: Gerador automático de recurso de glosa
- **v3.0**: Dashboard real-time com alertas por convênio
