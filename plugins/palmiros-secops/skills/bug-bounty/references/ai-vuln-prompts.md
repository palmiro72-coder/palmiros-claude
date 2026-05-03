# AI Vuln Prompts — Library por Linguagem e Framework

Prompts testados para usar com `claude-cli`, Codex ou análise manual via API. Estratégia: **sempre priorizar top-N candidatos** com evidência, nunca lista exaustiva (LLM alucina severidade).

## Princípios de Prompt

1. **Contexto primeiro** — cole o trecho relevante, não o repo inteiro. LLM foca melhor com <8k tokens de código.
2. **Peça evidência, não veredito** — "cite linha, arquivo, função" > "é vulnerável? sim/não".
3. **Force ranking** — "top 5 candidatos por plausibilidade, não top 50".
4. **Separe descoberta de exploit** — prompts diferentes para (a) achar vuln e (b) gerar PoC.
5. **Cross-check com semgrep/codeql** — se LLM aponta e ferramenta estática concorda, confiança sobe.

---

## Java / Spring

### Achado de vulns
```
Você é um security researcher revisando código Java/Spring. Analise os arquivos abaixo
buscando ESPECIFICAMENTE:

- Endpoints com @RequestMapping / @GetMapping / @PostMapping sem @PreAuthorize ou
  filtro de segurança explícito
- Uso de ObjectInputStream, XMLDecoder, SnakeYAML < 2.0 (deserialização insegura)
- Concatenação de string em JPQL/native queries (SQLi)
- SpEL evaluation com input do usuário (RCE via #{...})
- RestTemplate/WebClient com URL controlada pelo user (SSRF)
- @CrossOrigin com "*" em endpoints sensíveis
- Autowired services expostos via actuator sem auth

Formato de saída:
| # | Arquivo:linha | Classe | Evidência (trecho) | Como explorar |

Retorne NO MÁXIMO 5 candidatos, ordenados por plausibilidade de exploit real.
Se não achar nada crítico, retorne "nenhum candidato de alta confiança".
```

### Geração de PoC
```
Dado o controller abaixo e a vuln descrita, gere:
1. curl reproduzível com headers realistas
2. Payload de exploit comentado (cada linha)
3. Output esperado quando vulnerável vs quando patched
4. Lista de mitigations (Spring Security config, validação, etc.)

[COLE CONTROLLER]
[DESCREVA VULN]
```

---

## Python / Django

### Achado
```
Revise este código Django buscando:

- Views sem @login_required / permission_required (autz broken)
- QuerySet.extra() ou .raw() com input não sanitizado (SQLi)
- Pickle.loads / yaml.load(sem Loader) / shelve (deserialização)
- HttpResponseRedirect(request.GET[...]) (open redirect)
- render() com template_name dinâmico do user (SSTI)
- subprocess / os.system com input do user (command injection)
- get_object_or_404(Model, pk=request.GET.get('id')) sem checar ownership (IDOR)
- DEBUG=True em settings ou SECRET_KEY hardcoded
- middleware custom que remove CSRF

Formato de saída idêntico ao prompt Spring. Max 5 candidatos.
```

### Django REST Framework-específico
```
Analise este ViewSet/APIView do DRF buscando:
- Missing permission_classes
- get_queryset() que não filtra por request.user
- Serializer.save() com validated_data do user direto em fields sensíveis
  (e.g. is_staff, user_id)
- SerializerMethodField que expõe dados privados
- @action custom sem @permission_classes próprio
```

---

## Python / Flask / FastAPI

```
Revise buscando:

FLASK:
- @app.route sem @login_required (flask-login) ou verificação
- render_template_string(user_input) → SSTI Jinja2
- send_file(path) com path controlado (path traversal / LFI)
- session['is_admin'] = ... sem verificação server-side
- SECRET_KEY fraco ou hardcoded

FASTAPI:
- Endpoints sem Depends(get_current_user)
- Pydantic model com extra="allow" em contexto sensível
- BackgroundTasks com função que aceita input user-controlled
- OAuth2PasswordBearer sem scopes checados
- SQLAlchemy raw com f-string (SQLi)

Max 5 candidatos, formato tabela.
```

---

## Node.js / Express

### Achado
```
Revise este código Express buscando:

- Middleware de auth missing em rotas sensíveis (/admin, /api/*)
- req.body destructuring direto em Mongoose.update (prototype pollution → NoSQLi)
- eval() / Function() / vm.runInNewContext com user input (RCE)
- res.sendFile(req.params.file) sem path.resolve + whitelist (LFI)
- child_process.exec/spawn com input user (command injection)
- jwt.verify(token) sem verificar alg, ou aceitando alg: "none"
- CORS com origin: true ou reflect-request em endpoints com credenciais
- Object.assign(target, req.body) sem filtro (mass assignment)
- req.query[param] usado em Mongo .find() diretamente (NoSQLi operator injection)

Formato tabela. Max 5.
```

### Geração de PoC Express
```
Dada a vuln: [DESCRIÇÃO]
Gere:
1. curl com body/query maliciosos
2. Se for prototype pollution, pollui __proto__ e mostra side-effect
3. Se for NoSQLi, use operadores $ne, $gt, $where
4. Expected response pre/post patch
```

---

## C / C++ (binary bounty companion)

```
Analise este código C/C++ buscando:

- strcpy/strcat/gets/sprintf sem bounds (buffer overflow)
- memcpy/memmove com tamanho user-controlled
- printf(user_input) sem format string (format string bug)
- malloc(user_size) sem check de overflow de multiplicação (integer overflow)
- Use-after-free: ponteiro usado após free() ou destructor
- Double-free, return of stack address
- Race condition em signal handler (non async-signal-safe functions)
- TOCTOU em filesystem ops (access() + open())
- Integer underflow em size_t arithmetic

Para cada candidato, cite:
- Arquivo:linha
- Assinatura da função e caller chain
- Condições para trigger (input, estado)
- Mitigations que podem bloquear exploit (ASLR, CET, stack canary, PAC, MTE)

Max 5. Priorize funções reachable de input externo (network, file parsing).
```

---

## Go

```
Revise este código Go buscando:

- net/http handler sem middleware de auth
- exec.Command com input user (command injection)
- sql.DB.Query com fmt.Sprintf (SQLi) — deve ser parametrizado
- filepath.Join sem filepath.Clean + check de "../" (path traversal)
- template/html: texttemplate em vez de htmltemplate (XSS)
- json.Unmarshal em struct com campos sensíveis exposed (mass assignment)
- crypto/rand não usado (ou math/rand em contexto crypto)
- goroutine leak (sem context.WithCancel, channel não drenado)
- TLS config com InsecureSkipVerify: true em produção
- gRPC sem TLS / sem auth interceptor

Max 5 candidatos.
```

---

## Prompts Genéricos (qualquer stack)

### Triagem de false positives
```
Para cada candidato abaixo, responda:
1. É exploitable no ambiente real de produção? (considere sanitização upstream,
   WAF, validação em layer anterior)
2. Qual input/estado é necessário?
3. Qual CWE mais preciso (nunca CWE-20 genérico)?
4. CVSS 3.1 vector estimado (justificar AV, AC, PR, UI, C, I, A)
5. Probabilidade de ser duplicate (já reportado em disclosed H1)? baixa/média/alta

Candidatos:
[COLE LISTA]
```

### Geração de exploit a partir de achado validado
```
Vuln confirmada: [DESCRIÇÃO + LINHA DE CÓDIGO]
Ambiente: [TECH STACK, WAF se houver]

Gere:
1. PoC mínimo (curl ou script em Python requests)
2. Payload blindado contra WAF comum (Cloudflare, Imperva) — 2-3 variações
3. Chain possível: como isso vira P1/P2 (escalation path)
4. Screenshot/output esperado para incluir no report
5. Remediation code diff (o que o dev deveria fazer)
```

### Redação de report dual-reader
```
Vuln: [DESCRIÇÃO]
Target: [PROGRAMA]
Impact: [O QUE EU CONSEGUI FAZER]

Escreva um report H1/Bugcrowd com esta estrutura OBRIGATÓRIA:

## Summary (1 parágrafo, escaneável por IA — CWE-XXX, CVSS vector)
## Impact (3 bullets de negócio — dinheiro, dados, trust)
## Steps to Reproduce (numerados, com curl copiável)
## Proof of Concept (screenshot/video placeholder + output)
## Remediation (código concreto, não "sanitize input")
## References (CWE, OWASP, disclosed similares)

Tom: técnico, direto, sem hype. Assuma que primeiros 3 parágrafos serão
lidos por Hai/auto-triage AI; narrativa de impacto é para humano.
```

---

## Pitfalls comuns de prompt

- **Não** peça "encontre todas as vulns" → LLM vira ruído. Peça top-N.
- **Não** cole repo inteiro → perde precisão. Foque em um módulo por vez.
- **Não** aceite severidade do LLM sem questionar → costuma inflar P4 para P2.
- **Não** use output sem validar no target real → false positives caros em reputação.
- **Sempre** cruze com semgrep/codeql → concordância = maior confiança.
- **Sempre** documente o prompt usado (prompt + versão do modelo) em `ai-analysis/`.
