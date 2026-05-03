# Vuln Checklists

Checklist operacional por classe. Use como trilha de teste manual depois que a recon identificou a superfície. **Ordem**: começar por auth/autz (maior impacto), depois lógica de negócio, depois injection.

## Autenticação

### Login
- [ ] User enumeration via response/timing difference (`"user not found"` vs `"wrong password"`)
- [ ] Rate limit em /login (brute force possível?)
- [ ] Account lockout DoS (posso bloquear conta de outro user enviando senhas erradas?)
- [ ] Weak password policy (aceita "123456"?)
- [ ] Password reset token previsível, reutilizável, vida longa, ou não invalidado após uso
- [ ] Password reset via email header injection (X-Forwarded-Host)
- [ ] OAuth: `state` param missing → CSRF em login
- [ ] OAuth: `redirect_uri` open → account takeover
- [ ] OAuth: implicit flow aceitando access_token de outro client_id
- [ ] SSO: SAML response assinada corretamente? XML Signature Wrapping
- [ ] JWT: alg=none aceito? HS256/RS256 confusion? kid injection? weak secret?
- [ ] 2FA: bypass via race condition, response manipulation, fallback method
- [ ] 2FA: TOTP window muito largo (30s vs 5min)
- [ ] 2FA: recovery codes sem rate limit
- [ ] Session fixation (cookie não roda após login)
- [ ] Logout não invalida token server-side

### Registro
- [ ] Email já cadastrado → oracle de enumeration
- [ ] Verification bypass (signup sem confirmar email, depois muda email)
- [ ] Race condition em signup (dois registros com mesmo email quase simultâneos)

## Autorização / IDOR

- [ ] Endpoint aceita `id` no path/query/body → testar outro user
- [ ] UUIDs previsíveis? (v1 tem timestamp, v4 ok; GUID enumerar de sessions próximas)
- [ ] Numeric ID ordenado → enumeração trivial
- [ ] Role escalation: user→admin via `role=admin` em request
- [ ] Mass assignment: `{ "email": "x", "is_admin": true }`
- [ ] IDOR via HTTP verb change (GET ok, PUT/DELETE sem check)
- [ ] IDOR em export/download (`?format=pdf&id=X`)
- [ ] IDOR em websocket (após handshake, role check some)
- [ ] Endpoint público leaking data que devia ser autz (profile público com email/phone)
- [ ] Indirect object reference em filename (`/uploads/user_123/foo.pdf` → mudar `123`)
- [ ] GraphQL: alias para batchear requests e escapar rate limit
- [ ] GraphQL: introspection ativa em prod → mapa da autz

## SSRF (Server-Side Request Forgery)

- [ ] Campo URL/webhook/image-fetch/PDF-render → cloud metadata:
  - AWS: `http://169.254.169.254/latest/meta-data/iam/security-credentials/`
  - GCP: `http://metadata.google.internal/computeMetadata/v1/` (header `Metadata-Flavor: Google`)
  - Azure: `http://169.254.169.254/metadata/instance?api-version=2021-02-01` (header `Metadata: true`)
  - DigitalOcean: `http://169.254.169.254/metadata/v1.json`
- [ ] Blind SSRF: usar burp collaborator / interact.sh para confirmar
- [ ] SSRF com schema alternativo: `file://`, `gopher://`, `dict://`, `ftp://`, `ldap://`
- [ ] DNS rebinding: TTL 0, rebind para 169.254.169.254 após bypass de check
- [ ] IPv6 bypass: `[::1]`, `[::ffff:127.0.0.1]`
- [ ] Redirect-based SSRF (app segue redirect para interno)
- [ ] Parser differential: `http://attacker.com@internal/`, `http://internal#@attacker.com/`
- [ ] Port scan interno via SSRF (diferença em timing/response)

## XSS (Cross-Site Scripting)

### Stored
- [ ] Campos salvos: name, bio, comment, post → render sem escape
- [ ] Upload de SVG/HTML com JS inline
- [ ] CSV injection (`=HYPERLINK(...)`, `=cmd|...`) em export
- [ ] Admin panel interpreta conteúdo de user (second-order XSS → account takeover da sessão admin)

### Reflected
- [ ] Query param refletido no HTML → testar contexto (attribute, script block, URL, CSS)
- [ ] POST redirect to GET (mensagem de erro com input)
- [ ] Error pages refletindo path/header

### DOM
- [ ] `location.hash` / `location.search` usado em `innerHTML`, `document.write`, `eval`, `setTimeout`
- [ ] `postMessage` sem origin check

### Bypass contexts
```
Attribute: ?q=" onmouseover=alert(1) x="
Script: ?q='-alert(1)-'
URL: ?redirect=javascript:alert(1)
JS Template: ?q=${alert(1)}
JSON context: ?q=</script><script>alert(1)</script>
```

## SSTI (Server-Side Template Injection)

- [ ] Payloads de detecção: `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`, `#{7*7}`
- [ ] Identificar engine: Jinja2, Twig, Freemarker, Velocity, ERB, Smarty, Handlebars
- [ ] Escalar para RCE (varia por engine — ver PayloadsAllTheThings)

## XXE (XML External Entity)

- [ ] Endpoint aceita XML (SOAP, .docx, .xlsx, SVG upload, RSS feed)
- [ ] Testar: `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>`
- [ ] Blind XXE via OOB (DTD externo, FTP, HTTP)
- [ ] Billion laughs / DoS
- [ ] SSRF via XXE: `<!ENTITY xxe SYSTEM "http://169.254.169.254/...">`

## Deserialization

- [ ] Procurar: cookies com base64 de objeto, parâmetros com estrutura binária, APIs que recebem serialized
- [ ] Java: `ObjectInputStream`, gadgets via ysoserial
- [ ] Python: `pickle.loads` → RCE trivial
- [ ] PHP: `unserialize` → POP chain (phpggc)
- [ ] .NET: BinaryFormatter, ObjectStateFormatter (ysoserial.net)
- [ ] Node: node-serialize (CVE-2017-5941) → RCE
- [ ] Ruby: `Marshal.load` em input user

## SQL Injection

- [ ] `'`, `"`, `\` em campos → erro?
- [ ] Payload clássico: `' OR '1'='1'--`
- [ ] UNION-based → extrair dados
- [ ] Boolean blind: `AND 1=1` vs `AND 1=2`
- [ ] Time-based blind: `SLEEP(5)`, `pg_sleep(5)`, `WAITFOR DELAY '0:0:5'`
- [ ] Second-order: payload salvo, triggered em outra query
- [ ] NoSQL (Mongo): operators `$ne`, `$gt`, `$where`, `$regex`
  - `{"user":{"$ne":null},"pass":{"$ne":null}}` → login bypass
- [ ] ORMs com raw escape: `.raw()`, `.extra()`, `f"SELECT {user}..."`

## Race Conditions

- [ ] Operações de saldo: transferir/sacar com múltiplas requests simultâneas
- [ ] Cupom de desconto: usar N vezes antes do check de "already used"
- [ ] Signup: criar N contas com mesmo email quase simultâneo
- [ ] Approval flows: aprovar e cancelar simultâneo
- [ ] **Ferramenta**: Burp Repeater → Send group in parallel (last-byte sync)
- [ ] Turbo Intruder para timing preciso

## Cache Poisoning

- [ ] Header não-chaveado que reflete no body (X-Forwarded-Host, X-Host, X-Original-URL)
- [ ] Request sem cookie tem response cacheado contendo dados de outro user
- [ ] CDN cache key normalization mismatch
- [ ] Param cloaking: `?param1=x` vs `?param1=x&` diferença de cache
- [ ] **Fat GET** / **hidden params** via paramspider

## Prototype Pollution

### Client-side
- [ ] Sinks: `jQuery.extend(true, ...)`, merge libs antigas, `Object.assign` recursivo
- [ ] Testar: `?__proto__[foo]=bar`, depois checar `window.foo === 'bar'`
- [ ] Escalar para XSS via gadget DOM (htmltag, script src manipulation)

### Server-side (Node.js)
- [ ] `lodash.merge` < 4.17.11, `mixin`, `defaultsDeep` em versões antigas
- [ ] Body JSON com `__proto__`, `constructor.prototype`
- [ ] Escalar para RCE via child_process argument pollution

## Business Logic (moat humano — alto valor)

- [ ] **Workflow skip**: pular passo de aprovação manipulando `state` / URL direta
- [ ] **Negative amount**: valor negativo em transferência → credit oneself
- [ ] **Integer overflow/underflow** em saldo, quantidade, limite
- [ ] **Currency confusion**: comprar em BRL 1 algo de USD 1000
- [ ] **Coupon stacking**: aplicar múltiplos cupons não-stackable
- [ ] **Refund loop**: comprar → refund → manter produto
- [ ] **Partial payment abuse**: pagar R$0.01 de um pedido marca como paid
- [ ] **Import/export reversal**: exportar dados, importar alterado, app confia
- [ ] **Tier bypass**: feature premium acessível via endpoint direto
- [ ] **Inconsistent state across services**: carrinho aprova mas estoque não debita
- [ ] **Multi-step race**: iniciar fluxo, timing, finalizar em estado inconsistente

## CORS / CSRF

- [ ] CORS: `Origin: evil.com` → `Access-Control-Allow-Origin: evil.com` + credentials?
- [ ] CORS wildcard com credentials (browser rejeita, mas servidor não deveria retornar)
- [ ] CORS: `null` origin aceito
- [ ] CSRF: endpoints state-changing sem token
- [ ] CSRF token fraco (previsível, não vinculado a session, reutilizável)
- [ ] SameSite cookie: Lax permite POST navegacional em certos contextos
- [ ] CORS subdomain reflection: `*.target.com` → sub.evil-target.com

## File Upload

- [ ] Extensão validada só no nome (.php.jpg, .pHP, `.pht`, `.phar`)
- [ ] Magic bytes vs extensão mismatch
- [ ] SVG com JS → stored XSS
- [ ] HTML upload renderizado mesmo domain → XSS + CSRF
- [ ] ZIP bomb / path traversal em unzip (`../../evil.php`)
- [ ] Imagem com payload ghidra'd (EXIF comment com PHP)

## GraphQL específico

- [ ] Introspection habilitada em prod
- [ ] Query depth/complexity sem limite → DoS
- [ ] Batching (`[{query:...},{query:...}]`) escapa rate limit
- [ ] Aliases permitem múltiplas chamadas de mesma mutation (ex: tentar 1000 senhas em 1 request)
- [ ] Field suggestion exposto revela schema mesmo com introspection off
- [ ] Mutations sem autz check (ex: `updateUser(id: X)` sem verificar ownership)

## Checklist de meta-qualidade (antes de reportar)

- [ ] Bug validado em produção (não só staging)
- [ ] PoC reproduzível com curl limpo
- [ ] Impact articulado em termos de negócio (não só técnico)
- [ ] CWE específico (checar https://cwe.mitre.org/data/definitions/)
- [ ] CVSS vector justificado
- [ ] Disclosed similares buscados (evitar dup)
- [ ] Screenshot/video <90s
- [ ] Remediation concreta sugerida

## Referências

- **PayloadsAllTheThings** — repo de payloads por categoria
- **HackTricks** — book.hacktricks.xyz — técnicas detalhadas
- **PortSwigger Web Security Academy** — teoria + lab para cada classe
- **OWASP Testing Guide v4.2** — baseline metodológica
