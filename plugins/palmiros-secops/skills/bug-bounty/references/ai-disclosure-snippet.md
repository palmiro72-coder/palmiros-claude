# AI Disclosure Snippet

Copy-paste templates para seção "AI Disclosure" em reports. Usar quando `ai_policy: disclosure_required` está setado no `scope.txt` do alvo.

## Por que isto importa

- Programas maduros (Google, Apple, grandes fintech) exigem declaração.
- Omitir quando exigido = ban + possível escalada legal (especialmente em jurisdições com regras anti-spam automatizado).
- Disclosure bem redigido **não diminui** severidade — reforça rigor.

## Regras de redação

1. **Seja específico**: nomeie ferramenta + versão, não "AI tools".
2. **Separe descoberta de validação**: "IA ajudou a identificar candidatos; validação foi manual."
3. **Nunca afirme que a IA "encontrou o bug"** sozinha — você validou, construiu chain, testou em prod.
4. **Curto**: 2-4 linhas. Não é redação, é disclosure.

---

## Template MÍNIMO (para bugs achados majoritariamente manualmente)

```markdown
## AI Disclosure

No AI-based code analysis, vuln scanner, or exploit generator was used in this finding.
```

Ou:

```markdown
## AI Disclosure

AI tools were not used in the discovery or exploitation of this vulnerability.
```

---

## Template PADRÃO (IA para descoberta, humano para validação)

```markdown
## AI Disclosure

Initial code review was assisted by claude-cli (Claude 4.7) reading the public repository
at https://github.com/target/repo. Static analysis with semgrep 1.x (custom rule set) was
run in parallel to cross-check findings.

Vulnerability validation, exploitation path construction, PoC development, impact
assessment, and this report were authored manually.
```

---

## Template DETALHADO (para programas estritos — Google, Apple, grandes fintechs)

```markdown
## AI Disclosure

**Tools used:**
- claude-cli (Claude 4.7) — prompted to identify authorization flaws in Python/Django
  controllers at ~/bounty/<target>/source-code/<repo>. Prompt template available on
  request.
- semgrep 1.x with custom rule set (ruleset at https://github.com/my/rules if public)
- Manual code review in Burp and local IDE

**AI-assisted activities:**
- Identifying candidate locations (14 flagged, 3 validated as real issues)
- Drafting CVSS vector (validated against CVSS 3.1 spec manually)

**Manual activities:**
- False-positive filtering on AI output
- Constructing and validating exploit chain on the live target
- Authoring PoC, reproduction steps, and impact analysis
- Writing this report

**Output verification:** All AI-suggested findings were independently verified against
the live target before submission. No AI-suggested finding was submitted without manual
validation.
```

---

## Template para BINARY / REVERSING

```markdown
## AI Disclosure

Decompiled pseudocode from Ghidra 11.x was reviewed with AI assistance (claude-cli 4.7)
to identify candidate memory safety issues. All exploit primitives (heap grooming,
info leak, ROP chain construction) and reliability engineering were developed manually
without AI assistance. The final PoC exploit, tested against [target] version [X.Y.Z]
with stock mitigations enabled (ASLR, CET/IBT, stack canaries), achieves ≥85%
reliability over 100 runs.
```

---

## Template para programa com `ai_policy: banned`

Se está banned, **não submita** usando IA. Se submitar manualmente e seu processo não
tocou em IA, o template mínimo acima é apropriado. Se você *tentou* usar IA mesmo com
ban, não submita esse finding — reescreva ou descarte.

---

## Checklist antes de colar

- [ ] Li `ai_policy` no `scope.txt` do alvo
- [ ] Se `banned`: não usei IA e declarei explicitamente
- [ ] Se `disclosure_required`: nomeei ferramentas e versões
- [ ] Separei claramente descoberta (IA ajudou) de validação (manual)
- [ ] Não afirmei que a IA "encontrou o bug" — fui eu
- [ ] Snippet tem <10 linhas

## Casos especiais

### Programa não menciona política de IA
Default conservador: **incluir disclosure padrão**. Custa 4 linhas, ganha confiança.

### IA foi usada só para redigir o report (não descoberta)
Ainda vale disclosure, uma linha:
```markdown
## AI Disclosure

Discovery and validation were fully manual. This report was drafted with writing
assistance from Claude 4.7; technical content reflects my own analysis.
```

### Múltiplas IAs no pipeline
Listar todas:
```markdown
## AI Disclosure

- Code review: claude-cli 4.7
- Secondary static analysis: semgrep 1.x (custom rules), CodeQL
- Prompt for exploit draft: Claude 4.7 (draft refined and validated manually)
- Report draft: none (written manually)

All findings validated against live target before submission.
```

## Referências

- **H1 Hacker Directive** — terms evolving, check current policy
- **Bugcrowd** — AI guidelines page
- **Google VRP** — specific AI disclosure language
- **HackerOne blog**: posts sobre política de AI-assisted submissions
