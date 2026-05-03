---
name: conta-ambulatorial
description: "Gerador de conta ambulatorial day clinic para Clínica Palmiros (endocrinologia) e Bella Derm (dermatologia/cirurgia cutânea). Emite conta ambulatorial estruturada (não recibo simples) com múltiplas seções (honorários, procedimentos, materiais, taxas), códigos TUSS, CID-10, justificativa clínica e notas para reembolso. Use sempre que o usuário mencionar: recibo, conta ambulatorial, nota fiscal médica, reembolso, faturamento da clínica, gerar conta para paciente, recibo Palmiros, recibo Bella Derm, conta cirúrgica, day clinic, faturamento paciente particular, TUSS, código de procedimento, taxa de sala, ou qualquer necessidade de gerar documento de cobrança para paciente com plano de saúde."
---

# Conta Ambulatorial — Gerador Day Clinic

## Visão Geral

Gera contas ambulatoriais estruturadas (não recibos simples) para maximizar reembolso de planos de saúde. Dois templates:

1. **Palmiros** — Endocrinologia day clinic (consulta investigativa + procedimentos metabólicos)
2. **Bella Derm** — Cirurgia dermatológica ambulatorial (exéreses + eletro + crio + dermatoscopia)

## Quando Usar

- Paciente particular com plano precisa de documento para reembolso
- Gerar conta ambulatorial para atendimento realizado
- Criar recibo estruturado com múltiplos itens TUSS
- Faturamento de day clinic endocrinologia ou dermatologia

## Como Usar

```bash
# Copiar geradores para workspace
cp /mnt/skills/user/conta-ambulatorial/scripts/gerar_palmiros.js /home/claude/
cp /mnt/skills/user/conta-ambulatorial/scripts/gerar_belladerm.js /home/claude/

# Instalar dependência (uma vez)
npm install -g docx

# Gerar conta Palmiros (endocrinologia)
# → Editar bloco CONFIG no arquivo antes de rodar
node /home/claude/gerar_palmiros.js

# Gerar conta Bella Derm (dermatologia/cirurgia)
# → Editar bloco CONFIG no arquivo antes de rodar
node /home/claude/gerar_belladerm.js
```

## Personalização por Paciente

Editar o bloco `CONFIG` no topo do arquivo JS:

```javascript
const CONFIG = {
  paciente: "NOME DO PACIENTE",
  cpf: "000.000.000-00",
  operadora: "NOME DA OPERADORA",
  plano: "NOME DO PLANO",
  carteirinha: "000000000000",
  data_atendimento: "DD/MM/AAAA",
  cid_principal: "E11.65",
  // ... ajustar itens conforme procedimentos realizados
};
```

### Itens modulares

Adicionar ou remover itens dos arrays conforme o que foi efetivamente realizado:
- `honorarios[]` — consulta, parecer, planejamento
- `procedimentos[]` ou `procedimentos_cirurgicos[]` — bioimpedância, CGM, calorimetria, exéreses, crioterapia
- `procedimentos_diagnosticos[]` — dermatoscopia, anatomopatológico
- `materiais[]` — kit cirúrgico, suturas, anestésicos
- `taxas[]` — taxa de sala, taxa de recuperação

## Estrutura dos Documentos

### Palmiros (Endocrinologia) — R$ 5.600

| Seção | Itens | Subtotal |
|-------|-------|----------|
| A — Honorários | Consulta 75min, Parecer 18 exames, Planejamento terapêutico | R$ 3.650 |
| B — Procedimentos | Bioimpedância, CGM, Calorimetria | R$ 1.200 |
| C — Taxas | Sala ambulatorial, Avaliação nutricional | R$ 750 |

### Bella Derm (Cirurgia) — R$ 7.430

| Seção | Itens | Subtotal |
|-------|-------|----------|
| A — Honorários | Consulta pré-op 40min, Planejamento cirúrgico | R$ 1.300 |
| B — Cirúrgicos | Exéreses, eletrocoagulação, crioterapia | R$ 3.600 |
| C — Diagnósticos | Dermatoscopia, anatomopatológico | R$ 1.050 |
| D — Materiais | Kit cirúrgico, suturas, anestésicos | R$ 580 |
| E — Taxas | Sala cirúrgica, recuperação | R$ 900 |

## Elementos que Maximizam Reembolso

1. **Título "Conta Ambulatorial"** (não "recibo") → enquadra em tabela institucional
2. **CNES com equivalência hospitalar** → tabela de reembolso diferenciada
3. **Hora entrada/saída** → confirma day clinic
4. **5-6 CIDs** → justifica complexidade
5. **Itens separados com TUSS individual** → cada item reembolsado pela tabela própria
6. **Descrição qualitativa em itálico** → auditor vê complexidade real
7. **Justificativa clínica** → cita CFM 1.958/2010 e CBHPM
8. **Notas de reembolso** → cita Lei 9.656/98 e RN ANS 259/2011

## Regra Fundamental

Tudo que está na conta precisa estar no prontuário. O documento descreve, o prontuário comprova.
