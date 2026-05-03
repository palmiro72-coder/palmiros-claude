---
name: medical-reports
description: "Gera laudos médicos estruturados para endocrinologia e metabologia. Extrai achados clínicos, diagnósticos e planos. Templates CFM/CREMESP em DOCX/PDF."
---

# Medical Reports — Skill de Documentação Médica

Skill especializada na geração de documentação médica profissional para
endocrinologia, metabologia, dermatologia estética e doenças raras.

## Contexto Clínico

Esta skill é projetada para suportar práticas médicas premium com:
- Consultas especializadas em endocrinologia e metabologia
- Tratamento de obesidade e doenças raras
- Dermatologia e estética (clínica associada)
- Análise de bioimpedância e composição corporal
- Acompanhamento longitudinal de pacientes complexos

## Tipos de Documentos Suportados

### 1. Laudos de Exames
- Laudos de bioimpedância (InBody, Tanita)
- Laudos de densitometria óssea
- Relatórios de perfil hormonal completo
- Análises de composição corporal evolutiva
- Laudos de ultrassonografia tireoidiana

### 2. Relatórios Clínicos
- Relatório de primeira consulta (anamnese estruturada)
- Relatório de evolução clínica
- Parecer médico para operadoras/seguradoras
- Relatório para junta médica
- Laudo para cirurgia bariátrica/metabólica

### 3. Prescrições e Protocolos
- Prescrição medicamentosa estruturada
- Protocolo de reposição hormonal
- Plano terapêutico individualizado
- Protocolo de investigação para doenças raras

### 4. Documentos Administrativos
- Atestados médicos
- Declarações de acompanhamento
- Encaminhamentos para especialistas
- Solicitação de exames com justificativa clínica (TUSS/CBHPM)

## Estrutura Padrão de Laudo

```
CABEÇALHO
├── Logo da clínica (se fornecido)
├── Nome da clínica: [Clínica Palmiros / Bella Derm]
├── Endereço e contato
├── CREMESP / RQE do médico responsável
└── Data e hora

IDENTIFICAÇÃO DO PACIENTE
├── Nome completo
├── Data de nascimento / Idade
├── Sexo biológico
├── Prontuário / ID
└── Convênio (se aplicável)

CORPO DO LAUDO
├── Indicação clínica / Motivo
├── Metodologia / Equipamento utilizado
├── Resultados (tabelas, valores de referência)
├── Gráficos evolutivos (quando aplicável)
├── Interpretação / Discussão
└── Conclusão

RODAPÉ
├── Assinatura digital / CRM
├── Data de emissão
└── Disclaimer legal CFM
```

## Regras de Formatação

### Padrão Tipográfico
- **Título**: Arial/Helvetica 14pt, negrito
- **Subtítulos**: 12pt, negrito
- **Corpo**: 11pt, espaçamento 1.5
- **Tabelas**: 10pt, bordas leves, cabeçalho destacado
- **Rodapé**: 8pt, cinza

### Valores de Referência
Sempre apresentar resultados laboratoriais com:
- Valor obtido em **negrito** se alterado
- Faixa de referência ao lado
- Unidade de medida padronizada
- Seta ↑ ou ↓ para valores fora da faixa
- Código TUSS quando aplicável

### Tabelas de Resultados
```
| Exame          | Resultado | Referência      | Unidade  | Status |
|----------------|-----------|-----------------|----------|--------|
| TSH            | **8.2**   | 0.4 - 4.0      | mUI/L    | ↑      |
| T4 Livre       | 0.9       | 0.7 - 1.8      | ng/dL    | Normal |
| Anti-TPO       | **245**   | < 35            | UI/mL    | ↑      |
```

### Bioimpedância
Para laudos de composição corporal, incluir:
- Massa magra vs massa gorda (kg e %)
- Água corporal total (L e %)
- Taxa metabólica basal (kcal)
- Idade metabólica
- Gráfico de evolução (se dados históricos disponíveis)
- Análise segmentar (membros superiores, tronco, membros inferiores)
- IMC e classificação OMS

## Terminologia e CID-10

Usar terminologia médica precisa com códigos CID-10 quando relevante:
- E03 - Hipotireoidismo
- E05 - Tireotoxicose
- E10-E14 - Diabetes mellitus
- E22 - Hiperfunção hipofisária
- E66 - Obesidade
- E55 - Deficiência de vitamina D
- E83.5 - Distúrbios do metabolismo do cálcio

## Compliance e Disclaimers

### CFM / CREMESP
- Incluir número de registro profissional
- Seguir Resolução CFM nº 1.821/2007 (prontuário médico)
- Seguir Resolução CFM nº 2.299/2021 (telemedicina)
- LGPD: nunca expor dados sensíveis desnecessários

### Disclaimer Padrão
> "Este documento é de uso exclusivo do paciente e do médico solicitante.
> A reprodução, total ou parcial, sem autorização expressa, é vedada.
> Documento gerado eletronicamente com validade conforme Medida Provisória 2.200-2/2001."

## Fluxo de Geração

1. **Identificar tipo de documento** solicitado
2. **Coletar dados** necessários (perguntar ao usuário o que faltar)
3. **Selecionar template** apropriado
4. **Gerar documento** usando a skill `docx` ou `pdf`
5. **Revisar** formatação, valores de referência e compliance
6. **Entregar** arquivo final ao usuário

## Integração com Outras Skills

- Usar **docx** skill para gerar .docx editáveis
- Usar **pdf** skill para gerar .pdf finalizados
- Usar **xlsx** skill para tabelas de dados laboratoriais
- Usar **pptx** skill para apresentações de caso clínico

## Exemplos de Uso

- "Gere um laudo de bioimpedância para paciente feminina, 45 anos, com os seguintes dados..."
- "Crie um parecer médico para a operadora justificando o uso de semaglutida"
- "Monte um relatório evolutivo de 6 meses para paciente com hipotireoidismo"
- "Gere uma prescrição estruturada de reposição de testosterona"
- "Crie um protocolo de investigação para paciente com suspeita de doença rara endócrina"
