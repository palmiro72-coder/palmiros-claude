---
name: bug-bounty
description: Workflow de bug bounty pós-Mythos (era de LLMs e agentes autônomos). Stack híbrido humano+IA: ProjectDiscovery, ffuf, Burp, Ghidra, semgrep, codeql, claude-cli para análise de código e geração de exploits. Cobre moat humano (business logic, cross-service invariants, novelty), bypass de WAF/CDN, checklists por vuln, redação de reports para triagem dual (IA+humano), e binary bounty (Pwn2Own/ZDI/Apple). Use sempre que o usuário mencionar bug bounty, HackerOne, Bugcrowd, Intigriti, BugHunt, caça a vulnerabilidades, recon, pentest ofensivo, fuzzing, bypass de WAF, exploit, payload, CVE, CVSS, CWE, AI-assisted pentesting, XBOW, PentestGPT, LLM vuln discovery, memory corruption, ou programas de recompensa por falhas.
---

# Bug Bounty — Era Pós-Mythos

Workflow ofensivo de bug bounty hunter profissional em um mercado onde LLMs e agentes autônomos (XBOW, PentestGPT, Big Sleep, etc.) acham CVEs de 27 anos por menos de $50.

**A tese central:** *spray-and-pray* em vulns comuns morreu. Quem não usa IA como multiplicador vira overhead. Quem só usa IA vira ruído. O edge é no cruzamento: hibridismo disciplinado + foco cirúrgico em onde a IA ainda falha.

## Princípios Operacionais

1. **Scope first, always** — lê programa inteiro antes de scan. Out-of-scope = N/A = tempo perdido.
2. **Recon é 80% do trabalho** — quem acha o ativo primeiro ganha. Automatize tudo.
3. **Qualidade > quantidade de reports** — 1 P1 bem escrito vale 50 low-severity. Noise agora custa reputação.
4. **Cadeia de impacto** — vuln → exploit → dano real ao negócio. Sempre o storytelling.
5. **PoC blindada** — reproduzível, screenshot, curl, vídeo curto de <90s.
6. **Moat humano — específico, não genérico:**
   - **Tribal knowledge** — expectativas não-documentadas ("esse endpoint é só interno porque historicamente…")
   - **Invariantes cross-service** — estado que atravessa microsserviços em repos diferentes (LLM nunca vê junto)
   - **Race conditions distribuídas** e timing assumptions
   - **Trust boundaries a nível de UX** — o que o usuário assume vs o que está enforced
   - **Chaining criativo** — 2+ bugs low/info que viram critical
   - **Contexto regulatório** (LGPD, PCI, HIPAA) que vira multiplicador de impacto

## Era Pós-Mythos — o jogo mudou

### Quem são os adversários agora

| Player | Força | Fraqueza |
|--------|-------|----------|
| LLM puro (claude-cli, codex) | Leitura de código em escala | Contexto cross-repo, state distribuído |
| Agente autônomo (XBOW, PentestGPT) | Chain recon→exploit→report automatizado | Novelty, business logic profunda |
| Triage AI (H1 Hai, BC auto-triage) | Filtra reports mal escritos | Enganada por storytelling de impacto fraco |
| Caçador humano experiente | Contexto, chain, novelty | Velocidade, cobertura de breadth |

### Onde concentrar esforço (upside)
- **Business logic chains** em apps grandes (fintech, marketplaces)
- **Binary bounties** (Pwn2Own, ZDI, Apple Security Bounty) — memory corruption em targets hardened; LLMs ainda péssimos aqui
- **Novelty classes** — programas maduros pagam 2–5× para classes novas ou chains não-automatizáveis
- **Context-dependent** — IDOR semântico, race conditions, auth bypass multi-step

### Onde desinvestir (corrida perdida)
- XSS refletido comum, SQLi básico, open redirect, SSRF trivial → já automatizado em massa
- Nuclei scan puro de templates públicos → todo mundo faz, P5/dup

### Dois leitores, não um
Reports agora passam por **triagem IA** antes do humano (H1 Hai, Bugcrowd auto-triage). Estrutura:
- **Primeiros 3 parágrafos**: escaneáveis por IA (título claro, CWE no topo, CVSS vector, impact bullet).
- **Meio**: narrativa de impacto para humano (storytelling de negócio).
- **Fim**: reprodução passo-a-passo + remediation.

## Plataformas

| Plataforma | Foco | Nota |
|-----------|------|------|
| HackerOne | Global, maior pool | Hai (IA triagem) revisa antes do humano |
| Bugcrowd | Global, VRT próprio | Auto-triage agressiva; PayPal/Payoneer |
| Intigriti | EU forte | Bom pagamento, menos saturado |
| YesWeHack | EU/França | Programas únicos |
| Synack | Private red team | Precisa passar em exame |
| BugHunt | 🇧🇷 Sorocaba | OLX, UOL, BTG, Enjoei, Warren |
| Hackaflag | 🇧🇷 SP | BMG, PAN, Stark Bank, EBANX, Elo |
| ZDI | Binary, N-day/0-day | Pagamentos altos, requer Ghidra/IDA |
| Apple Security Bounty | iOS/macOS | Tiers até $2M, humano-dominado |

**IMPORTANTE — política de IA:** cada programa tem sua regra. Alguns proíbem submissions AI-assisted, outros exigem disclosure. Sempre registrar em `scope.txt` o campo `ai_policy`.

## Fluxo de Trabalho

```
0. ESCOLHA DE ALVO
   ├── Filtrar scope em bounty-targets-data (arkadiyt)
   ├── Priorizar: escopo amplo (*.target.com), bounty médio-alto
   ├── Evitar programas saturados (Shopify, Uber)
   ├── Verificar última atividade + política de IA (allowed/disclosure/banned)
   └── Se tiver código público (GitHub, npm, PyPI) → pula pra passo 1b

1a. RECON PASSIVA         ┃  1b. ANÁLISE DE CÓDIGO (paralelo)
    → references/             → references/ai-vuln-prompts.md
      recon-pipeline.md       ├── Clone de repos públicos
    ├── Subdomain enum        ├── semgrep + regras custom
    ├── Ports/services        ├── codeql (GitHub)
    ├── JS analysis           ├── claude-cli com prompts por
    ├── GitHub dorking        │   linguagem/framework
    └── Wayback/archive       └── Trufflehog em commits antigos

2. RECON ATIVA
   ├── Directory/file fuzzing (ffuf, feroxbuster)
   ├── Parameter mining (arjun, paramspider)
   ├── Vuln scan (nuclei) — só p/ inventariar, não é achado
   └── Manual browse com Burp proxy

3. TRIAGEM DE ACHADOS (human-in-the-loop)
   ├── IA gerou N candidatos → humano filtra false positives
   ├── Priorizar: business logic > chains > novelty
   └── Descartar: vulns comuns em asset saturado

4. EXPLORAÇÃO + VALIDAÇÃO
   → references/vuln-checklists.md
   ├── Validar no target real (não só no código)
   ├── Construir chain se possível (low+low → high)
   ├── Bypass de proteções → references/waf-cdn-bypass.md
   └── PoC final: curl + screenshot + vídeo

5. REPORT DUAL-READER
   → references/h1-report-template.md
   ├── Título descritivo (NUNCA "Report Intent #xxx")
   ├── CWE + CVSS no topo (p/ IA triage)
   ├── Impact bullets (p/ humano)
   ├── Steps numerados reproduzíveis
   ├── Business storytelling (moat humano)
   ├── Remediation concreta
   └── AI disclosure se programa exige
```

## Stack Técnico

### Sistema
- **Kali Linux** ou **Parrot OS** (VM ou bare metal)
- **Burp Suite Professional** (essencial — Community não tem Intruder sério)
- **Proxychains4** + pool SOCKS (rotação anti-ratelimit)
- **tmux/zellij** (sessions longas de recon)

### ProjectDiscovery Toolchain
```bash
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest

# Pipeline clássico
subfinder -d target.com -silent | httpx -silent -title -tech-detect | tee alive.txt
cat alive.txt | nuclei -t ~/nuclei-templates/ -severity medium,high,critical
```

### AI-Assisted Toolchain (o diferencial)
```bash
# claude-cli para análise de código em escala
npm install -g @anthropic-ai/claude-code

# semgrep — engine de regras estáticas (custom rules > regras públicas)
pip install semgrep
semgrep --config=auto ./source-code/

# CodeQL (GitHub) — queries profundas em AST
gh codeql database create db --language=javascript
gh codeql database analyze db --format=sarif-latest -o results.sarif

# Trufflehog — secrets em git history
docker run --rm trufflesecurity/trufflehog:latest git https://github.com/target/repo.git

# Ghidra + AI (binary bounty)
# Plugins: Ghidrathon, GhidraMCP (interface LLM ↔ Ghidra)
```

Prompts específicos por stack em `references/ai-vuln-prompts.md`.

### Fuzzing e Enumeration
- `ffuf`, `feroxbuster`, `arjun`, `paramspider`, `gau`, `waybackurls`
- `gf` (tomnomnom), `unfurl`, `dalfox`, `sqlmap` (com cuidado)

### Análise
- `jq`, `httpie`, `curl`, `mitmproxy`
- `trufflehog`, `gitleaks`, `LinkFinder`, `SecretFinder`

### Wordlists
```bash
git clone https://github.com/danielmiessler/SecLists ~/SecLists
# Assetnote wordlists — https://wordlists.assetnote.io/ (mais novas)
```

## Organização do Alvo

```
~/bounty/
└── target-name/
    ├── scope.txt              # in-scope + ai_policy + out-of-scope
    ├── recon/
    │   ├── subdomains.txt
    │   ├── alive.txt
    │   ├── ports.txt
    │   ├── js-urls.txt
    │   └── endpoints.txt
    ├── source-code/           # repos clonados (se público)
    │   ├── repo-a/
    │   └── repo-b/
    ├── ai-analysis/           # output de LLM/semgrep/codeql
    │   ├── claude-findings.md
    │   ├── semgrep-results.json
    │   ├── codeql-results.sarif
    │   └── triaged.md         # após filtro humano
    ├── fuzz/
    │   └── ffuf-results.json
    ├── nuclei/
    │   └── scan.log
    ├── burp/
    │   └── target.burp
    ├── findings/
    │   └── vuln-001-idor.md   # um por bug validado
    └── reports/
        └── submitted/
```

Formato do `scope.txt`:
```
# Target: acme.com
# Platform: HackerOne
# Last updated: 2026-04-24
# ai_policy: disclosure_required   # allowed | disclosure_required | banned

in_scope:
  *.acme.com
  api.acme.com
  mobile app (iOS, Android)

out_of_scope:
  marketing.acme.com
  third-party SSO providers
```

## Arquivos de Referência

- **`references/recon-pipeline.md`** — Pipeline completo de recon (passiva + ativa), scripts, fontes de dados.
- **`references/ai-vuln-prompts.md`** — Library de prompts para claude-cli/codex por linguagem e framework (Java Spring, Python Django/Flask/FastAPI, Node.js Express, C/C++, Go). Prompts de triagem e exploit-gen.
- **`references/mythos-competition-strategy.md`** — Estratégia competitiva contra agentes autônomos: onde atacar, onde recuar, redação dual-reader, novelty premium, relacionamento com security teams.
- **`references/waf-cdn-bypass.md`** — CloudFront, Cloudflare, Imperva, Akamai. Origin IP discovery, header spoofing, request smuggling.
- **`references/vuln-checklists.md`** — OWASP + além: IDOR, SSRF, XSS, SSTI, XXE, deserialização, auth, race conditions, cache poisoning, prototype pollution.
- **`references/h1-report-template.md`** — Template dual-reader (IA triage + humano) com CWE mapping, CVSS 3.1, storytelling de impacto.
- **`references/binary-bounty.md`** — Apple Security Bounty, Samsung, ZDI, Pwn2Own. Workflow Ghidra + AI assistants, memory corruption, logic bugs, privilege escalation em targets hardened.
- **`references/ai-disclosure-snippet.md`** — Templates copy-paste para seção "AI Disclosure" em reports quando `ai_policy: disclosure_required`.

## Scripts de Automação

- **`scripts/bootstrap-target.sh <target> [platform] [ai-policy]`** — cria estrutura de diretórios + `scope.txt` + `README.md` em `~/bounty/<target>/`.
- **`scripts/recon.sh <target>`** — pipeline subfinder → httpx → katana → nuclei → JS extraction. Lê `scope.txt` para domínios in-scope.
- **`scripts/ai-scan.sh <target> <language>`** — roda semgrep + claude-cli + trufflehog em `source-code/`. Respeita `ai_policy` (aborta se `banned`). Linguagens: java, python, node, go, c, generic.
- **`scripts/release-monitor.sh <target>`** — monitora GitHub releases de `repos-to-monitor.txt` para capturar janela de novelty premium. Ideal em cron 4x/dia. Suporta webhook de notificação via `NOTIFY_WEBHOOK`.

Variável de ambiente `BOUNTY_ROOT` (default `$HOME/bounty`) define onde ficam os workspaces.

## Binary Bounty como Foso

Enquanto web vira commodity AI, binary fica *mais* defensável:
- LLMs péssimos em exploitation de memory corruption sob mitigations modernas (ASLR, CET, PAC, MTE, shadow stack).
- Reversing com Ghidra ainda requer intuição humana para identificar gadgets, heap grooming, race windows.
- Pwn2Own/ZDI pagam 6 dígitos por chain funcional.
- **Posicionamento estratégico**: investir horas em Ghidra + um target hardened específico (kernel iOS, hypervisor, firmware de smart lock) rende mais $/hora que 100 reports web em 2026+.

Ver `references/binary-bounty.md`.

## Comunidade e Aprendizado

### Writeups e Disclosed Reports
- **HackerOne Hacktivity** (ordenado por bounty) — estude 50 P1/P2 recentes
- **pentesterland.com/list-of-bug-bounty-writeups.html** — agregador
- `ngalongc/bug-bounty-reference` — por tipo de bug

### Referências Humanas
- NahamSec, LiveOverflow, STÖK, InsiderPhD, Zseano, Jhaddix
- Critical Thinking Podcast (Justin Gardner + Joel)
- Frans Rosén, Orange Tsai (Twitter)

### Labs de Prática
- **PortSwigger Web Security Academy** — padrão-ouro até BSCP
- **HackTheBox** / **TryHackMe** — boxes e rooms
- **Hacker101** (HackerOne) — CTFs com convites privados

## Exemplos de Uso

- "Faça recon completa em acme.com dentro de escopo *.acme.com"
- "Clone o repo X, roda semgrep + claude-cli com prompt de Spring, traga top 10 candidatos"
- "Analise este JS file e encontre endpoints não documentados"
- "Monte report H1 dual-reader para este IDOR, com CWE, CVSS e business storytelling"
- "Como bypass do CloudFront na frente desse backend?"
- "Gere templates nuclei custom para essa CVE"
- "Revise este report antes de submeter — CWE tá certo? Passa na triagem da Hai?"
- "Sugere programas BR no HackerOne com escopo amplo"
- "Analise esse binário com Ghidra buscando memory corruption para ZDI"
- "Prompt para claude-cli achar race condition em código Django"

## Ética e Legalidade

- **SEMPRE** dentro do escopo autorizado do programa
- **NUNCA** exfiltrar dados além do mínimo para PoC
- **NUNCA** testar sem programa ativo (Lei 14.155/2021 — invasão de dispositivo)
- **AI disclosure** — respeitar `ai_policy` do programa. Se exige disclosure, declarar ferramentas usadas (claude-cli, semgrep, codeql) no report.
- **Responsible disclosure** — avisar empresa antes de publicar writeup
- **Conflito de interesse** — não testar programas do próprio empregador
- **Preservar logs** de interação para auditoria se necessário
