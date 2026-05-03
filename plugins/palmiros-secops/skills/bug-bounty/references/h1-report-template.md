# H1 / Bugcrowd Report Template — Dual-Reader

Reports em 2026+ são lidos por **IA triage primeiro** (H1 Hai, Bugcrowd auto-triage) e humano depois. Estrutura precisa servir os dois leitores. Objetivo do template: maximizar chance de reach humano + severidade correta.

## Regra de ouro

- **Primeiros 3 parágrafos**: escaneáveis por IA — título claro, CWE, CVSS, 1 linha de impacto.
- **Meio**: narrativa de impacto para humano — storytelling de negócio.
- **Fim**: reprodução, PoC e remediation.
- **Zero hype**. Adjetivos ("catastrophic", "devastating") viram red flag em auto-triage.

---

## Template Genérico

```markdown
**Título:** [Ação concreta] via [Vetor] em [Endpoint/Componente]

Exemplos bons:
- "Unauthenticated account takeover via OAuth state parameter fixation in /auth/callback"
- "IDOR in GET /api/invoices/:id allows cross-tenant invoice disclosure"
- "Stored XSS in admin panel via profile bio field leads to admin session hijack"

Exemplos ruins (evitar):
- "Critical vulnerability found" (sem info)
- "Report Intent #4821" (default ruim)
- "XSS" (muito genérico)

---

## Summary

One-paragraph summary escaneável por IA.

- **CWE**: CWE-XXX: [Nome específico] (link: https://cwe.mitre.org/data/definitions/XXX.html)
- **CVSS 3.1**: X.X (Severity) — `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N`
- **Affected endpoint(s)**: `GET /api/v2/foo/:id`
- **Authentication required**: None / Low-priv user / High-priv user
- **Impact one-liner**: Unauthenticated attacker can [read/modify/delete] [data/function] belonging to any user.

## Impact

Business impact bullets — esta seção é onde humano calibra severidade.

- **Data exposure**: X records of PII (name, email, phone, CPF) of all ~N users are accessible without authentication.
- **Financial**: Attacker can trigger unlimited refunds via [path], capped only by [thing].
- **Regulatory**: Exposure of CPF + financial data falls under LGPD Art. 46 → mandatory ANPD notification within 72h, potential fine up to 2% of revenue (max R$50M).
- **Reputational**: Breach is externally verifiable from public internet → any researcher can confirm independently.
- **Pivot potential**: This access permits further attacks on [X], escalating to [Y].

## Steps to Reproduce

Numbered, reproducible, copy-pasteable.

1. Create a test account at https://target.com/signup (or use provided creds: `user1@test.com / Pass123`).
2. Capture the session cookie after login:
   ```bash
   export COOKIE="sessionid=abc123..."
   ```
3. Send the following request:
   ```bash
   curl -s 'https://target.com/api/v2/invoices/99999' \
     -H "Cookie: $COOKIE" \
     -H 'Accept: application/json'
   ```
4. Observe the response:
   ```json
   {
     "id": 99999,
     "owner_id": 42,
     "amount": "1250.00",
     "cpf": "123.456.789-00"
   }
   ```
5. Note that `owner_id: 42` does not match the authenticated user (`owner_id: 1`), confirming IDOR.

## Proof of Concept

- **Screenshot**: [attach screenshot of response in UI or Burp]
- **Video** (<90s): [link to unlisted YouTube / Loom / asciinema]
- **Raw request/response**:
  ```
  GET /api/v2/invoices/99999 HTTP/1.1
  Host: target.com
  Cookie: sessionid=abc123
  ...

  HTTP/1.1 200 OK
  Content-Type: application/json
  ...
  ```

## Technical Root Cause

Opcional, mas ajuda triager a escalar pro dev certo.

The handler in `/app/api/v2/invoices_controller.py:42` queries the database by `invoice_id` alone:
\```python
invoice = Invoice.query.get(invoice_id)
return jsonify(invoice.to_dict())
\```
It does not verify that `invoice.owner_id == current_user.id`.

## Remediation

Concrete code fix. "Sanitize input" NUNCA basta.

Add ownership check in the handler:
\```python
invoice = Invoice.query.get(invoice_id)
if invoice.owner_id != current_user.id:
    abort(404)  # 404 preferred over 403 to avoid leaking existence
return jsonify(invoice.to_dict())
\```
Or use a scoped query:
\```python
invoice = Invoice.query.filter_by(id=invoice_id, owner_id=current_user.id).first_or_404()
\```

Consider adding automated tests that assert cross-tenant access returns 404.

## References

- CWE-639: Authorization Bypass Through User-Controlled Key
- OWASP API Security Top 10 (2023) — API1: Broken Object Level Authorization
- Similar disclosed reports:
  - https://hackerone.com/reports/XXXXXX (Shopify, 2024)
  - https://hackerone.com/reports/YYYYYY

## AI Disclosure

*Include this only if programa has `ai_policy: disclosure_required`. See ai-disclosure-snippet.md.*

Initial code review was assisted by `claude-cli` (Claude 4.7) and `semgrep 1.x` with custom authorization rules. Vulnerability validation, reproduction, PoC construction, and impact assessment were performed manually.
```

---

## Checklist pré-envio

- [ ] Título nomeia ação + vetor + componente (não só classe de vuln)
- [ ] CWE específico (nunca CWE-20, CWE-200 genéricos)
- [ ] CVSS vector com justificativa em cada métrica
- [ ] Impact em termos de negócio, não só técnico
- [ ] Steps copy-pasteáveis e reproduzíveis do zero
- [ ] Bug validado em produção (não staging)
- [ ] Screenshot + vídeo <90s
- [ ] Remediation com código concreto
- [ ] Disclosed similares buscados (combate dup)
- [ ] Nenhum hype-word ("catastrophic", "insane", "game-over")
- [ ] AI disclosure se ai_policy exige

## Dicas de redação

### O que ganha com IA triage
- Tags claras: "CWE-XXX", "CVSS 3.1: AV:N/..."
- Cabeçalhos estruturados (Summary, Impact, Steps, PoC, Remediation)
- Oneliner de impacto logo no Summary
- Endpoint e método HTTP no Summary
- Link para CWE oficial

### O que ganha com humano
- Contexto regulatório (LGPD, PCI, HIPAA) se aplicável
- Pivot potential — o que esse bug habilita
- Comparação com disclosed similares (calibra severidade)
- Remediation code diff (mostra que você entende o fix)
- Video ≤ 90s (humano tem 5min por report)

### O que perde com os dois
- Paredão de texto sem estrutura
- Linguagem emotiva ("This is the worst bug I've ever seen!")
- PoC não reproduzível ("just tried a few times and it worked")
- Impact vago ("this could be bad")
- Pedir severity P1 explicitamente ("please rate this critical") — deixa o report falar

## Anti-patterns que quebram reports

- ❌ Enviar logs crus sem curadoria (triager não vai ler)
- ❌ Incluir stack trace inteiro no corpo (anexar em vez)
- ❌ Afirmar impact que não conseguiu provar ("this probably leads to RCE")
- ❌ Submitar sem test account quando programa fornece
- ❌ Screenshot borrada, vídeo com som de fundo, ou cortado no meio
- ❌ Steps que dependem de estado não-reproduzível ("após usar a app por alguns dias...")

## Variações por plataforma

### HackerOne (Hai)
- Hai classifica primeiro por matching de padrões → estrutura Markdown ajuda.
- Títulos específicos (ação+vetor+componente) sobem no ranking interno.
- `Attach`s renderizam inline — use para screenshots, não para logs.

### Bugcrowd
- Usar VRT (Vulnerability Rating Taxonomy) na classificação.
- Auto-triage agressiva — evitar palavras que disparam "duplicate likely".
- Severidade é do programa, você sugere.

### Intigriti
- Mais humano em triagem, pouca IA.
- Program-specific rewards variam muito — checar antes.

### ZDI (binary)
- Formato próprio, foco técnico extremo.
- Proof of reliability importa (exploit funciona em X% das vezes).

## Referências

- **HackerOne's "Writing a Great Report"** — guia oficial
- **PortSwigger blog** — writeups exemplares de Orange Tsai, James Kettle
- **pentesterland.com** — writeups disclosed categorizados
