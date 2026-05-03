---
name: endo-derm-sales
description: "Jornada consultiva Mary Kay para Clínica Palmiros e Bella Derm. Pipeline de pacientes, cross-sell endo-derm, protocolos integrados, indicações e KPIs."
---

# Endo-Derm Sales — Jornada Consultiva Mary Kay

Skill de vendas consultivas integradas para Clínica Palmiros (endocrinologia) e Bella Derm (dermatologia/estética). Implementa o modelo Mary Kay de venda relacional aplicado à medicina premium, com protocolos clínicos de endo-dermatologia como diferencial competitivo.

## Quando usar
- Gestão de pipeline de pacientes (novos leads, follow-up, retenção)
- Cross-sell bilateral entre Clínica Palmiros e Bella Derm
- Ativação de protocolos endo-dermatológicos integrados
- Programa de indicações e embaixadores
- Geração de propostas comerciais para pacientes
- Análise de métricas de vendas e LTV
- Cadências de follow-up e nutrição de relacionamento
- Criação de conteúdo para captação (Instagram, WhatsApp)

## Contexto do Negócio

### Clínica Palmiros
- **Especialidade**: Endocrinologia e Metabologia
- **Médico**: Dr. Lucas do Prado Palmiro (CRM-SP 139089, RQE 75065)
- **Posicionamento**: Premium (R$3.500/consulta, espera 90-120 dias)
- **Foco**: Tireoide, diabetes, obesidade, doenças raras, metabolismo
- **Hospital**: Israelita Albert Einstein

### Bella Derm
- **Especialidade**: Dermatologia e Estética
- **Médica**: Dra. Michelle de Lima Ourives Palmiro
- **Posicionamento**: Premium, hospital-equivalente
- **Foco**: Procedimentos estéticos, skincare, dermatologia clínica
- **Localização**: Vila Clementino, São Paulo

### Diferencial Competitivo: Endo-Dermatologia Integrada
As duas clínicas operam como ecossistema integrado. O diferencial é CLÍNICO (não apenas comercial): protocolos médicos que conectam causas endócrinas a manifestações dermatológicas, gerando resultados superiores ao tratamento isolado.

## Jornada do Paciente — 7 Fases

### Fase 1: Descoberta
**Objetivo**: Atração e primeiro contato qualificado
- Conteúdo educativo: "Sua pele reflete seus hormônios"
- Canais: Instagram, Google Ads, indicações, parcerias médicas
- Classificação de leads: endo / derm / integrado
- **Automação**: Lead → Zapier → monday.com (pipeline) → n8n (WhatsApp boas-vindas)

### Fase 2: Análise Consultiva
**Objetivo**: Diagnóstico profundo com checklist cruzado
- Palmiros: anamnese 90-120min, exames completos, bioimpedância, EndoAI
- Bella Derm: dermatoscopia digital, IA dermatológica, skincare assessment
- **Checklist cruzado**: Endo examina pele (acanthosis, hirsutismo). Derm questiona hormônios
- **Automação**: Exames → EndoAI pré-analisa → flags endo-derm → monday.com pipeline integrado

### Fase 3: Recomendação Premium
**Objetivo**: Proposta de protocolo integrado personalizado
- Documento único mostrando plano endo + derm com timeline sincronizada
- Ticket 3-5x maior que consulta isolada
- Simulação financeira de pacotes
- **Automação**: Protocolo definido → gerar proposta PDF/PPTX → simulação xlsx → envio WhatsApp

### Fase 4: Execução Sincronizada
**Objetivo**: Entrega de valor excepcional com sincronia clínica
- Endo libera procedimento estético somente quando parâmetros metabólicos permitem
- Documentação fotográfica padronizada (antes/durante/depois)
- Celebração de marcos
- **Automação**: Dashboard atualiza → verifica marcos endo → libera próximo passo derm

### Fase 5: Follow-up Inteligente
**Objetivo**: Nutrição do relacionamento e retenção
- Cadências por patologia/procedimento
- Follow-up cruzado: resultado endo → recomendação derm e vice-versa
- Conteúdo sazonal relevante
- **Automação**: n8n cadências → IA classifica respostas → escala ou nutre

### Fase 6: Indicação & Embaixadores
**Objetivo**: Multiplicação orgânica via referral
- NPS 9-10 → programa automático de indicação
- Benefício duplo se indicado agenda nas duas clínicas
- História clínica como marketing: "resolveu acne tratando hormônio"
- **Automação**: NPS alto → link único → tracking → benefício creditado

### Fase 7: Fidelização & LTV
**Objetivo**: Ecossistema de saúde premium com recorrência
- Assinatura "Saúde & Beleza Integrada": check-up endo + manutenção estética + skincare
- Relatório anual de evolução auto-gerado
- Acesso VIP a ambas clínicas
- **Automação**: Scoring → segmentação VIP → renovação proativa

## Protocolos Clínicos Endo-Dermatologia

### 1. Acne Hormonal & SOP
- **Trigger automático**: HOMA-IR > 2.71 + acne grau III
- **Endo**: Testosterona, SDHEA, 17-OH progesterona, SHBG, Insulina/HOMA-IR
- **Derm**: Classificação IGA, mapeamento lesões, avaliação cicatrizes
- **Protocolo**: Endo trata causa (metformina ± antiandrogênico) + Derm trata manifestação (tópico + procedimentos)
- **Revenue**: Ticket 3.2x maior que isolado

### 2. Tireoide & Manifestações Cutâneas
- **Trigger**: TSH alterado + queixa capilar/cutânea
- **Endo**: TSH, T4L, T3, Anti-TPO, Anti-Tg, US tireoide
- **Derm**: Tricoscopia, avaliação xerodermia, dermatoscopia
- **Protocolo**: Endo normaliza função → Derm inicia após 3 meses de eutireoidismo
- **Contraindicação**: Tratamento estético antes da estabilização hormonal

### 3. Obesidade & Estética Pós-Emagrecimento
- **Trigger**: Perda > 10% peso corporal
- **Endo**: Bioimpedância seriada, perfil metabólico, vitaminas
- **Derm**: Elasticidade cutânea, grau flacidez, mapeamento estrias
- **Protocolo**: Bella Derm inicia body sculpting ao atingir -10% do peso
- **Revenue**: Maior LTV — 12+ meses endo + 6+ sessões estética

### 4. Diabetes & Complicações Cutâneas
- **Trigger**: Acanthosis nigricans em consulta derm → solicitar HOMA-IR + HbA1c
- **Endo**: HbA1c, glicemia, insulina, função renal/hepática
- **Derm**: Mapeamento acanthosis, dermatoscopia, cultura micológica
- **Protocolo**: Endo controla glicemia → acanthosis melhora 40-60%. Derm complementa após HbA1c < 7%
- **Contraindicação**: Procedimentos invasivos se HbA1c > 8%

### 5. Menopausa & Anti-aging Integrado
- **Trigger**: Mulher > 45 anos com queixa estética ou hormonal
- **Endo**: FSH, LH, Estradiol, Testosterona, DHEA-S, IGF-1, Vit D
- **Derm**: Fotoenvelhecimento (Glogau), elastometria, manchas UV
- **Protocolo**: TRH quando indicada melhora colágeno 30% em 6 meses → potencializa estética
- **Revenue**: Segmento premium — maior poder aquisitivo

### 6. Alopecia & Distúrbios Hormonais
- **Trigger**: Queixa capilar em qualquer clínica
- **Endo**: Painel tireoidiano, ferritina, zinco, Vit D, testosterona, cortisol, prolactina
- **Derm**: Tricoscopia digital, teste tração, biópsia se indicado
- **Protocolo**: Correção hormonal + estímulo local = 60-80% melhora vs 30-40% isolado
- **Regra**: Ferritina < 40 + alopecia → suplementação ANTES de procedimento derm

## Stack Tecnológico

### MCPs Ativos
- **monday.com**: CRM, pipelines, dashboards de vendas
- **n8n**: Automação de fluxos, cadências, webhooks
- **Zapier**: Integração entre plataformas, triggers

### Boards monday.com
1. **🧬 Pipeline Endo-Dermatologia**: Funil de 7 fases com colunas para status endo, status derm, protocolo integrado, flag cross-sell, ticket, NPS
2. **🔬 Protocolos Clínicos Integrados**: Tracking de workups e liberações por condição
3. **🌟 Programa Embaixadores**: Indicações, scoring, benefícios

### Workflows n8n
1. Cadência Pós-Consulta Endo (24h → 7d → 30d)
2. Cadência Pós-Procedimento Derm (6h → 24h → 7d → 30d)
3. Trigger Protocolo Integrado (regras automáticas por exame)
4. Programa Referral Automático (NPS → indicação → benefício)
5. Sincronia Endo-Derm (verificação diária de status cruzado)

## North Star Metrics
- **LTV / CAC**: > 8:1 (integrado) vs 5:1 (isolado)
- **Cross-sell Rate**: > 40% pacientes em ambas clínicas
- **Referral Rate**: > 35% novos via indicação
- **Ticket Integrado**: 3-5x vs consulta isolada

## Regras de Negócio
1. Consulta Palmiros: R$3.500, espera 90-120 dias
2. Ambas clínicas têm equivalência hospitalar
3. Comunicação premium — nunca usar linguagem de "venda"
4. Cross-sell deve ser CLINICAMENTE justificado, não apenas comercial
5. Protocolos seguem evidência médica — timing de procedimentos é inegociável
6. LGPD: dados de pacientes compartilhados entre clínicas requerem consentimento
7. Follow-up via WhatsApp — canal principal de comunicação
8. Nunca prometer resultados específicos em comunicação com paciente

## Instruções para Claude

Ao usar esta skill:
1. **Propostas comerciais**: Use as skills docx/pdf/pptx para gerar documentos premium
2. **Simulações financeiras**: Use xlsx para comparativos de pacotes
3. **Conteúdo de captação**: Linguagem educativa, nunca promocional. Foco em endo-dermatologia como diferencial
4. **Follow-up**: Tom empático, profissional, personalizado por patologia
5. **Cross-sell**: Sempre justificar clinicamente. Usar protocolos acima como base
6. **Métricas**: Calcular LTV considerando ambas clínicas + indicações
7. **Automação**: Referenciar boards monday.com e workflows n8n existentes
