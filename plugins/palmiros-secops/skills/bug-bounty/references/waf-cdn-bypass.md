# WAF & CDN Bypass

Quando o alvo está atrás de CloudFlare/CloudFront/Imperva/Akamai, você está atacando o proxy, não a origem. Achar a origem ou contornar regras do proxy é muitas vezes a diferença entre P1 e N/A.

## Filosofia

1. **Identifique primeiro** o que está na frente. Tech stack errada → técnica errada.
2. **Origem exposta** vale mais que bypass fancy — vá buscar.
3. **Sempre** respeite scope. Muitos programas excluem atacar CDN diretamente.

## Detecção do WAF/CDN

```bash
# httpx já detecta
httpx -u target.com -cdn -tech-detect

# wafw00f
wafw00f https://target.com

# Por header
curl -I https://target.com | grep -iE 'server|x-cache|cf-ray|x-cdn|x-served-by'
```

| Sinal | CDN/WAF |
|-------|---------|
| `cf-ray`, `cf-cache-status` | Cloudflare |
| `x-amz-cf-id`, `via: 1.1 ... cloudfront` | CloudFront |
| `x-iinfo`, `x-cdn: Incapsula` | Imperva/Incapsula |
| `akamai-*`, `x-akamai-*` | Akamai |
| `x-sucuri-*` | Sucuri |
| `x-served-by: cache-*` | Fastly |
| `x-powered-by-plesk` + WAF | Atomicorp |

## Origin IP Discovery

### 1. DNS history
Passive DNS mostra IPs antigos antes do alvo ir pro CDN.
```bash
# SecurityTrails
curl -H "APIKEY: $ST_KEY" "https://api.securitytrails.com/v1/history/target.com/dns/a" | jq

# ViewDNS
curl "https://viewdns.info/iphistory/?domain=target.com" | grep -oE '[0-9.]{7,15}'
```

### 2. Certificate Transparency
CT logs costumam expor IPs em SANs ou em sister domains que não usam CDN.
```bash
# crt.sh queries expandidas
curl -s "https://crt.sh/?q=%25.target.com&output=json" | jq -r '.[].common_name' | sort -u
```

### 3. Favicon hash (Shodan)
```bash
# Hash do favicon do alvo
python3 -c "import mmh3, requests, base64; r=requests.get('https://target.com/favicon.ico'); print(mmh3.hash(base64.encodebytes(r.content)))"

# Search no Shodan
shodan search "http.favicon.hash:HASH_AQUI"
# → IPs expondo mesmo favicon = origem provável
```

### 4. SPF / MX / TXT records
```bash
dig TXT target.com +short
# SPF pode listar IPs de mailers que às vezes batem com origem web
```

### 5. Subdomínios sem CDN
```bash
# Vários subdomínios NÃO estão atrás do CDN
for s in recon/subdomains-all.txt; do
    echo "$s -> $(dig +short "$s")"
done | grep -vE 'cloudflare|fastly|akamai|cloudfront|104\.16\.' > recon/non-cdn.txt
```
Qualquer subdomínio que resolve para IP próprio = possível origem compartilhada.

### 6. Shodan / Censys queries
```
# Shodan
ssl.cert.subject.CN:"target.com"
http.html:"target.com"
http.title:"Target - Login"

# Censys
services.tls.certificates.leaf_data.subject.common_name: "*.target.com"
```

### 7. Leaks em GitHub
Config files de deploy (terraform, k8s, ansible) frequentemente têm IPs hardcoded.
```
"target.com" filename:terraform.tfvars
"target.com" extension:yaml kind:Ingress
```

### 8. Validação
Depois de achar IP suspeito:
```bash
# Request com Host header forçado
curl -k -H "Host: target.com" https://IP_SUSPEITO/
# Se retornar mesma app → origem confirmada
```

## WAF Bypass — Técnicas

### Header injection
WAF às vezes confia em headers do "proxy interno". Se CDN/WAF não limpa esses:
```
X-Forwarded-For: 127.0.0.1
X-Forwarded-Host: internal.target.com
X-Original-URL: /admin
X-Rewrite-URL: /admin
X-Real-IP: 127.0.0.1
X-Client-IP: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Host: admin.target.com
X-Originating-IP: 127.0.0.1
```

### HTTP verb tampering
```
GET /admin → 403
POST /admin → 200
PUT /admin → 200
OPTIONS /admin → revela methods
PATCH, DELETE, TRACE, HEAD
```

### Path normalization
WAF e app podem normalizar diferente:
```
/admin       → blocked
/admin/      → blocked
/admin/.     → 200
/admin/..;/  → 200 (Tomcat)
/%2e/admin   → 200
/admin%20    → 200
//admin      → 200
/./admin     → 200
```

### Case variation
```
/admin → blocked
/ADMIN → 200
/Admin → 200
```

### Content-Type switch
```
Content-Type: application/json → blocked
Content-Type: application/xml → parsed as XML, bypass json WAF
Content-Type: text/plain → payload passa raw
```

### Parameter pollution
```
?id=1&id=2'--
WAF olha primeiro "id", app usa último (ou vice-versa)
```

### Chunked encoding
```
Transfer-Encoding: chunked

4
POST
7
ing /
8
adminHT
...
```

### Request smuggling (TE.CL / CL.TE)
Quando front-end (CDN) e back-end interpretam tamanho da request diferente. Técnica poderosa, geralmente P1.
- **TE.CL**: front-end usa Transfer-Encoding, back-end usa Content-Length
- **CL.TE**: inverso
- **CL.0**: back-end ignora CL
- **Ferramenta**: Burp → HTTP Request Smuggler extension (James Kettle)

### Encoding bypass
```
' → %27 → %25%32%37 → %u0027 (IIS)
< → %3C → \u003c → &#60; → &lt;
SELECT → SeLeCt → SELECT/**/ → %53%45%4c%45%43%54
```

### Long payload
Muitos WAFs têm limite de inspeção (~8KB). Padding com junk antes do payload real passa:
```
?q=AAAA...[8000 chars]...' OR 1=1--
```

## Bypass específico por WAF

### Cloudflare
- **Origem exposta** ainda é o principal vetor — veja seções acima.
- Cloudflare-IUAM (JS challenge) pode ser bypassed com:
  - `cloudscraper` (Python lib)
  - Headless browser (Selenium/Playwright) com user-agent realista
- Enterprise rules costumam ser custom — foque em logic WAF bypasses (path norm, param pollution).
- **Cloudflare Access** (Zero Trust): bugs de autz em apps atrás dele são premium.

### CloudFront (AWS)
- Misconfigurações comuns:
  - `Host` header spoofing → roteia para origin diferente
  - Assinatura de URL vazada em cache público
  - S3 origin listagem exposta
- **CloudFront Functions** / Lambda@Edge podem ter logic bugs próprios.

### Imperva/Incapsula
- HTTP smuggling funcional em muitas configs antigas.
- Verb tampering (POST→GET override).
- Imperva valida tamanho de JSON → enviar payload em string encoded.

### Akamai
- Path normalization clássica (`/..;/`, `/%2e/`).
- Pragma headers revelam cache internals: `Pragma: akamai-x-cache-on, akamai-x-get-true-cache-key`
- Akamai Ghost / edge routing por Host header.

### F5 BIG-IP ASM
- Cookie `BIGipServer` revela backend — as vezes útil para chain.
- `X-F5-Auth-Token` bypass em configs mal setadas.
- CVE-2020-5902 e derivados em appliances não atualizadas.

### ModSecurity (OWASP CRS)
- CRS tem paranoia levels (1-4); muitas instalações em nível 1 passam muito.
- `;` em query breaks regra comum.
- Unicode normalization ataques.

## Anti-patterns

- ❌ Atacar o próprio CDN (Cloudflare etc.) sem escopo explícito — ban.
- ❌ Enviar 10k requests com payloads para descobrir WAF rule — rate limit + burn do alvo.
- ❌ Assumir que bypass no staging funciona em prod. Testar com cuidado.
- ❌ Reportar "WAF bypass" como vuln — não é. Bypass é *meio*; vuln real é o que você explora depois dele.

## Ferramentas

- **wafw00f** — fingerprinting
- **Burp Suite** extensions: HTTP Request Smuggler, Hackvertor, Bypass WAF
- **nuclei** `-t waf-detect/` e `-t cves/` (CVEs de WAF appliances)
- **h2csmuggler** — HTTP/2 downgrade smuggling
- **wafninja** — fuzzing de payloads com variações

## Referências

- **PortSwigger Research** (James Kettle): request smuggling, cache poisoning
- **Assetnote**: write-ups de origin IP discovery
- **HTTP Request Smuggling lab** no PortSwigger Academy (obrigatório)
- **0xInfection/Awesome-WAF** — compilado massivo no GitHub
