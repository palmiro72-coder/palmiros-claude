# Mythos Competition Strategy

Como operar em um mercado onde agentes autônomos inundam programas com achados. Não é sobre competir com a IA — é sobre escolher o terreno onde ela perde.

## Contexto: o que mudou

- **Big Sleep** (Google Project Zero) achou 0-day em SQLite com LLM puro.
- **XBOW** ficou #1 no leaderboard do HackerOne US em 2025, disputando com humanos.
- LLMs com agentes acham CVEs de 27 anos por <$50 em libs C clássicas.
- Triagem também virou IA: **H1 Hai**, **Bugcrowd auto-triage** filtram reports antes do humano ler.

Consequência: **vulns comuns em assets public-facing são commodity**. O valor concentrou em áreas onde IA falha ou onde IA dá noise — programa paga quem filtra o noise.

## Modelo de ameaça competitiva

| Competidor | O que faz melhor que você | O que você faz melhor |
|------------|---------------------------|-----------------------|
| LLM puro | Escaneia 1000 repos em 1h | Entende negócio, chain |
| Agente autônomo (XBOW-like) | Recon + exploit + report auto | Novelty, trust boundaries |
| Hunter humano júnior + LLM | Velocidade em low-severity | Profundidade, relacionamento |
| Hunter humano sênior sem IA | Experiência, instinto | Cobertura de breadth |
| Time de security interna do alvo | Contexto total | Olhar externo, criatividade adversarial |

**Seu posicionamento ideal:** hunter sênior + IA como multiplicador, focado em classes onde agentes falham.

## Onde concentrar (alto upside)

### 1. Business logic profunda
- Fluxos de negócio multi-step (checkout, refund, escrow, KYC).
- Invariantes que atravessam serviços (carrinho ≠ pagamento ≠ estoque em repos diferentes).
- Auth/autz context-dependent (role-based com regras implícitas).
- **Por que IA falha:** precisa entender o que o negócio considera válido, não só o que o código permite.

### 2. Chains de low+low → critical
- SSRF low → metadata endpoint → IAM credential → full AWS.
- Open redirect → OAuth flow hijack → account takeover.
- IDOR em endpoint não-crítico → enumeração → doxing em massa (LGPD multiplier).
- **Por que IA falha:** agente otimiza por "achou um bug", não por "chain é P1".

### 3. Binary bounties (foso real)
- Pwn2Own, ZDI, Apple Security Bounty, Samsung Mobile Security.
- Memory corruption em targets hardened (ASLR, CET, PAC, MTE, shadow stack).
- Kernel, hypervisor, firmware, secure enclave.
- **Por que IA falha:** exploitation requer heap grooming, gadget finding, ROP/JOP chains sob mitigations ativas. LLM não "sente" o heap.
- **$/hora**: 6 dígitos por chain funcional vs centenas por web P2.

### 4. Novelty premium
- Programas maduros (Google, Meta, Microsoft) pagam **2–5× bounty base** para:
  - Classes novas de vuln
  - Chains que a equipe interna não tinha mapeado
  - Bugs em features recém-lançadas (grace period quando scanners ainda não têm template)
- **Estratégia:** monitorar changelogs, release notes, PRs grandes em repos públicos → janela de 24-72h de vantagem.

### 5. Context regulatório como multiplier
- LGPD: vuln que expõe PII de brasileiros = fine risk real → impact inflado.
- PCI-DSS: acesso a dados de cartão → obrigação de notificação, multa.
- HIPAA: PHI em US → $50k-$1.5M por incidente.
- **Redação de report:** traduzir vuln técnica em risco regulatório concreto move severidade.

## Onde recuar (corrida perdida)

- XSS refletido em param comum (dalfox automatizado acha)
- SQLi em formulário público (sqlmap + nuclei destroem)
- Open redirect em param `?next=` (grep de um liner)
- Subdomain takeover em DNS abandonado (nuclei template público)
- CVE N-day em versão antiga de software comum (Shodan + nuclei)

Tempo gasto nessas classes em 2026+ = tempo morto. A não ser que seja em asset **recém-adicionado ao scope** (janela de grace).

## Redação para dual-reader (IA triage + humano)

### Estrutura obrigatória
```
TÍTULO: [Ação] via [Vetor] em [Endpoint/Componente]
  Ex: "Account takeover via OAuth state parameter fixation in /auth/callback"

SUMMARY (1 parágrafo — IA triage escaneia aqui)
  - CWE-XXX (específico, nunca CWE-20 genérico)
  - CVSS 3.1: AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H (com justificativa)
  - Um oneliner de impacto ("unauthenticated attacker can take over any user account")

IMPACT (3 bullets — humano lê aqui)
  - $ ou dados: quantos usuários? que dados? pivot para mais?
  - Regulatório: LGPD/PCI/HIPAA se aplicável
  - Reputacional: breach visible? mídia?

STEPS TO REPRODUCE (numerados, copiáveis)
  1. curl com header X
  2. observe response Y
  3. manipule parâmetro Z
  [video/screenshot links]

PROOF OF CONCEPT
  [request/response completo + screenshot + vídeo <90s]

REMEDIATION
  Código concreto. "Sanitize input" NUNCA. Diff de fix preferencial.

REFERENCES
  - CWE link
  - OWASP page
  - Disclosed similar (H1/Bugcrowd)
  - CVE relacionado se houver

AI DISCLOSURE (se programa exige)
  "Análise inicial assistida por claude-cli 4.7 + semgrep 1.x.
   Validação, chain construction e PoC manual."
```

### Regras de escrita
1. **Primeiros 3 parágrafos escanáveis** — IA triage classifica em segundos.
2. **Zero hype** — "attacker can catastrophically..." vira red flag em auto-triage.
3. **Evidência > adjetivo** — não diga "grave", mostre o PoC.
4. **Link para disclosed similar** — ajuda triager humano a calibrar severidade.

## Relacionamento com security teams (moat social)

- **Reporte bugs educado e limpo** → vira *trusted hacker* → convites a programas privados com bounties maiores.
- **Responda rápido em comments** → sobe em rank, aumenta bounty ceiling.
- **Não brigue por severidade em público** → escale via support. Briga pública mata relacionamento.
- **Community contribution** → talks, writeups (pós-disclosure), nuclei templates → reputação fora de um programa só.
- **Private programs pagam melhor** → foque em construir acesso a eles.

## Workflow competitivo integrado

```
MONITORAR (contínuo)
├── Novos programas / scope expansions (h1 notifications, Twitter)
├── Release notes, changelogs de alvos favoritos
├── GitHub: PRs grandes, dependabot alerts em repos públicos
└── CVE feeds de deps comuns (Snyk, OSV)

CAÇAR (foco por dia)
├── Scan automatizado background (recon diário em scope)
├── Análise manual de 1 feature nova por dia
├── Code review via claude-cli em repo público novo
└── 1 hora de reversing binary (Pwn2Own target)

REPORTAR (qualidade > quantidade)
├── Max 1 report/dia
├── Dual-reader structure
├── Video <90s sempre
└── Follow-up dentro de 24h se triager perguntar
```

## Investimentos de longo prazo (2026+)

1. **Domine 1 stack binary** (iOS kernel, Chrome renderer, hypervisor) — moat defensável.
2. **Construa reputação em 1 programa private** — bounty ceiling sobe 3-5×.
3. **Automatize recon contínuo** (inventário de novos subdomains/endpoints 24/7).
4. **Biblioteca própria de prompts e regras semgrep** — vantagem cumulativa.
5. **Publique writeups pós-disclosure** — gera convites privados.
6. **Networking com triagers** (conferences — DEFCON, h1-events) — acelera resolução de reports borderline.

## Pitfalls a evitar

- Automatizar report submission → ban instantâneo.
- Copiar template de report sem customizar → Hai marca como spam.
- Não ler escopo → report N/A → score cai → pior bounty.
- Brigar por dup → perde tempo, perde relacionamento.
- Testar fora de programa ativo → crime (Lei 14.155/2021 no BR).
- **Não disclosur uso de IA quando programa exige** → ban + possibilmente escalada legal.

## Métrica de sucesso (ajustada para era Mythos)

Não é "quantos reports/mês". É:
- **$/hora de tempo efetivo** (bounties recebidos / horas gastas)
- **% reports P1/P2** (indicador de foco)
- **Bounty ceiling** em programas principais
- **Número de invites privados**
- **Taxa de dup** (baixa = você acha onde outros não olham)
