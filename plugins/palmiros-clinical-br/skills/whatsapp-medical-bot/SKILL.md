---
name: whatsapp-medical-bot
description: "Chatbot médico para WhatsApp via Evolution API/Baileys. Agenda consultas, triagem, lembretes, fluxos de atendimento. Integra com prontuários."
---

# WhatsApp Medical Bot — Skill de Automação de Atendimento

Desenvolvimento de sistemas inteligentes de atendimento via WhatsApp para
clínicas médicas premium.

## Arquitetura do Sistema

```
PACIENTE (WhatsApp)
    ↓
EVOLUTION API / WA Business API
    ↓
WEBHOOK HANDLER (Node.js / Python)
    ↓
├── NLU Engine (LLM / Regex / Intent Classification)
├── State Machine (fluxo conversacional)
├── Database (PostgreSQL / MongoDB)
├── Integrations
│   ├── Agenda (Google Calendar / sistema próprio)
│   ├── Prontuário (PEP)
│   ├── Financeiro (gateway pagamento)
│   └── Notificações (lembretes, confirmações)
└── Admin Dashboard
```

## Fluxos de Atendimento

### 1. Primeiro Contato
```
BOT: Olá! Bem-vindo(a) à [Clínica]. Sou a assistente virtual.
     Como posso ajudar?

     1️⃣ Agendar consulta
     2️⃣ Remarcar/cancelar consulta
     3️⃣ Informações sobre a clínica
     4️⃣ Falar com a recepção
     5️⃣ Enviar exames/documentos

PACIENTE: [escolhe opção]
```

### 2. Agendamento
```
COLETA DE DADOS:
├── Nome completo
├── CPF (validação)
├── Convênio ou particular
├── Especialidade desejada
├── Preferência de horário
└── É primeira consulta?

CONFIRMAÇÃO:
├── Resumo do agendamento
├── Valor (se particular) + link de pagamento
├── Orientações pré-consulta
└── Lembrete automático (24h e 2h antes)
```

### 3. Triagem Inteligente
```
QUESTIONÁRIO INICIAL:
├── Motivo principal da consulta (texto livre)
├── Há quanto tempo tem os sintomas?
├── Já consultou outro médico sobre isso?
├── Está em uso de medicamentos?
└── Tem exames recentes?

OUTPUT → Classificação de prioridade
├── 🔴 Urgente → Transferir para médico
├── 🟡 Prioritário → Agenda preferencial
└── 🟢 Rotina → Agenda normal
```

### 4. Pós-Consulta
```
FOLLOW-UP AUTOMÁTICO:
├── D+1: "Como está se sentindo após a consulta?"
├── D+7: Lembrete de início de medicação
├── D+30: Lembrete de exames de controle
├── D+60-90: Lembrete de retorno
└── Pesquisa NPS (0-10)
```

## Templates de Mensagens

### Confirmação de Agendamento
```
✅ *Consulta Confirmada*

📋 *Paciente:* {{nome}}
👨‍⚕️ *Médico:* Dr(a). {{medico}}
📅 *Data:* {{data}} às {{hora}}
📍 *Local:* {{endereco}}

📎 *Orientações:*
• Trazer documento com foto e carteirinha do convênio
• Chegar 15 minutos antes
• Trazer exames anteriores

_Para remarcar ou cancelar, responda "REMARCAR" ou "CANCELAR"_
```

### Lembrete 24h
```
⏰ *Lembrete de Consulta*

Olá, {{nome}}! Sua consulta é *amanhã*, {{data}} às {{hora}}.

📍 {{endereco}}

Confirma presença? Responda:
✅ SIM - Confirmo
❌ NÃO - Preciso remarcar
```

### Envio de Resultados
```
📋 *Resultados Disponíveis*

{{nome}}, seus resultados de exames estão prontos.

📎 Acesse pelo link seguro (válido por 48h):
{{link_seguro}}

🔒 Senha de acesso: {{senha}}

_Em caso de dúvidas, agende um retorno._
```

## Integrações

### Evolution API (self-hosted)
```javascript
// Enviar mensagem
const sendMessage = async (number, text) => {
  await fetch(`${EVOLUTION_URL}/message/sendText/${INSTANCE}`, {
    method: 'POST',
    headers: {
      'apikey': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      number: `55${number}@s.whatsapp.net`,
      text: text
    })
  });
};

// Webhook handler
app.post('/webhook', async (req, res) => {
  const { data } = req.body;
  const message = data.message?.conversation || 
                  data.message?.extendedTextMessage?.text;
  const from = data.key.remoteJid;
  
  // Process message through state machine
  await processMessage(from, message);
  res.sendStatus(200);
});
```

### N8N / Zapier (no-code)
- Webhook trigger → Process → Send response
- Integração com Google Sheets para log
- Integração com Google Calendar para agendamento
- Integração com Stripe/PagSeguro para pagamento

## Estado Conversacional

### State Machine
```javascript
const STATES = {
  IDLE: 'idle',
  MENU: 'menu_principal',
  AGENDAMENTO_NOME: 'agendamento_nome',
  AGENDAMENTO_CPF: 'agendamento_cpf',
  AGENDAMENTO_CONVENIO: 'agendamento_convenio',
  AGENDAMENTO_ESPECIALIDADE: 'agendamento_especialidade',
  AGENDAMENTO_HORARIO: 'agendamento_horario',
  AGENDAMENTO_CONFIRMA: 'agendamento_confirma',
  TRIAGEM: 'triagem',
  AGUARDANDO_HUMANO: 'aguardando_humano',
  ENVIO_DOCUMENTOS: 'envio_documentos'
};
```

### Timeout e Fallback
- **Timeout**: 30 min sem resposta → salvar estado, retomar depois
- **Fallback**: 3 mensagens não compreendidas → transferir para humano
- **Horário**: Fora do expediente → mensagem automática + coleta de dados
- **Rate limit**: Máximo 20 mensagens/minuto por conversa

## LGPD e Compliance

### Consentimento
- Solicitar opt-in explícito antes de enviar mensagens
- Permitir opt-out a qualquer momento ("SAIR")
- Informar sobre coleta e uso de dados
- Link para política de privacidade

### Dados Sensíveis (LGPD Art. 11)
- Dados de saúde requerem consentimento específico
- Nunca enviar resultados de exames em texto plano
- Usar links temporários com senha para documentos
- Log de todas as interações com timestamp
- Retenção conforme CFM (mínimo 20 anos para prontuário)

### Segurança
- Criptografia end-to-end (nativa WhatsApp)
- Validação de identidade por CPF + data de nascimento
- 2FA para acesso ao painel administrativo
- Audit trail de todas as operações

## Métricas de Performance

| KPI | Meta | Medição |
|-----|------|---------|
| Tempo de resposta | < 30s | Média por interação |
| Taxa de resolução | > 70% | Sem transferência para humano |
| NPS | > 8.5 | Pesquisa pós-atendimento |
| Taxa de agendamento | > 40% | Conversas → agendamento |
| No-show rate | < 15% | Com lembretes automáticos |
| Satisfação | > 90% | Pesquisa de satisfação |

## Exemplos de Uso

- "Crie o fluxo de agendamento via WhatsApp com validação de convênio"
- "Implemente triagem inteligente com classificação de prioridade"
- "Monte o sistema de lembretes automáticos 24h e 2h antes da consulta"
- "Configure webhook da Evolution API com state machine em Node.js"
- "Crie templates de mensagens para pós-consulta e follow-up"
- "Implemente pesquisa NPS automatizada após cada atendimento"
