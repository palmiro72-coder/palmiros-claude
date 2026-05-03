# Recon Pipeline

Recon é 80% do trabalho. Quem acha o ativo primeiro ganha. Objetivo: inventário completo de superfície de ataque antes de qualquer exploit.

## Filosofia

- **Passiva primeiro** — sem tocar no alvo. Usa OSINT, logs públicos, CT.
- **Ativa depois** — só em hosts confirmados in-scope.
- **Contínua, não one-shot** — alvos mudam. Reexecute recon semanalmente.
- **Diff-driven** — foco em o que é *novo* desde último scan (novelty premium).

## Etapa 1 — Seed (ponto de partida)

### Inventário inicial
- Domínios do scope (+ wildcards)
- ASN do alvo → `whois` + Hurricane Electric BGP
- Blocos de IP públicos
- Organização no GitHub/GitLab/Bitbucket
- Apps mobile nas stores (Android APK, iOS IPA)

### Ferramentas
```bash
# ASN discovery
amass intel -org "Acme Corp"
whois -h whois.radb.net -- '-i origin AS12345' | grep -Eo "([0-9.]+){4}/[0-9]+"

# GitHub orgs
curl -s "https://api.github.com/users/acme/repos?per_page=100" | jq -r '.[].clone_url'
```

## Etapa 2 — Subdomain Enumeration

### Fontes passivas
- **Certificate Transparency**: crt.sh, censys, Google CT logs
- **Passive DNS**: SecurityTrails, DNSdumpster, VirusTotal, Shodan
- **Archive**: wayback machine, commoncrawl
- **Search engines**: Google, Bing dorking
- **Chaos** (ProjectDiscovery): recon curado contínuo

### Pipeline padrão
```bash
# Multi-fonte merge
(
    subfinder -d target.com -silent -all
    amass enum -passive -d target.com
    curl -s "https://crt.sh/?q=%25.target.com&output=json" | jq -r '.[].name_value' | tr ',' '\n'
    curl -s "https://api.certspotter.com/v1/issuances?domain=target.com&include_subdomains=true&expand=dns_names" \
        | jq -r '.[].dns_names[]'
    chaos -d target.com -silent
) | sort -u > recon/subdomains-all.txt

# DNS brute (só se scope permite)
puredns bruteforce ~/SecLists/Discovery/DNS/subdomains-top1million-110000.txt target.com \
    -r resolvers.txt >> recon/subdomains-all.txt

sort -u -o recon/subdomains-all.txt recon/subdomains-all.txt
```

### Truque: subdomain takeover
- Procurar CNAME para serviços abandonados: `dnsx -cname -resp -l recon/subdomains-all.txt`
- Dead providers clássicos: heroku, AWS S3, GitHub Pages, Azure, Fastly, Shopify
- `nuclei -t takeovers/` pega a maioria, mas manual em CNAMEs suspeitos vale ouro.

## Etapa 3 — Resolução e Alive Check

```bash
# DNS resolution
dnsx -l recon/subdomains-all.txt -resp -silent -o recon/resolved.txt

# HTTP probe
httpx -l recon/resolved.txt \
      -title -tech-detect -status-code -web-server -tls-probe \
      -cdn -favicon -hash sha256 \
      -silent -json -o recon/alive.json

# Text summary
jq -r '[.url, .status_code, .title, (.tech // [] | join(","))] | @tsv' recon/alive.json > recon/alive.tsv
```

### Tecnologias interessantes para priorizar
- **Admin panels**: Grafana, Kibana, Jenkins, Adminer, phpMyAdmin
- **Old frameworks**: Struts, Spring Boot antigo, Rails < 6, Drupal 7
- **Dev tools leaked**: Swagger, GraphQL playground exposto, actuator sem auth
- **Cloud misconfig**: S3 buckets, Azure storage, GCS com listing

## Etapa 4 — Port & Service Discovery

```bash
# Top 1000 ports (rápido)
naabu -l recon/resolved.txt -top-ports 1000 -silent -o recon/ports.txt

# All ports em hosts interessantes
naabu -host api.target.com -p - -silent -rate 1000 -o recon/ports-api.txt

# Service detection
nmap -sV -iL recon/ports.txt -oA recon/nmap/services
```

### Ports além de 80/443
- 8080, 8443, 8888, 9000, 9090 — admin panels
- 3000, 3001, 4000, 5000 — dev backends
- 27017 (Mongo), 6379 (Redis), 9200 (Elasticsearch), 5984 (CouchDB) — DBs expostos
- 22 (SSH), 3389 (RDP) — acesso que pode ter auth fraca

## Etapa 5 — Content Discovery

### URL crawling (passivo)
```bash
# Waybackurls — URLs históricas
echo target.com | waybackurls > recon/wayback.txt

# gau — URLs de múltiplas fontes (Wayback, AlienVault, CommonCrawl)
echo target.com | gau --threads 10 > recon/gau.txt

# Katana — crawl ativo
katana -u https://target.com -depth 3 -jc -o recon/crawl.txt
```

### URL crawling (ativo)
```bash
# Dir fuzzing com wordlist específica da stack
ffuf -u https://target.com/FUZZ -w ~/SecLists/Discovery/Web-Content/common.txt \
     -mc 200,301,302,403 -fs 0 -o recon/ffuf-common.json -of json

# Recursive (cuidado com rate)
feroxbuster -u https://target.com -w ~/SecLists/... -x php,asp,aspx,jsp -o recon/feroxbuster.txt

# Parameter mining
arjun -u https://target.com/api -oJ recon/params.json
paramspider -d target.com --quiet -o recon/paramspider.txt
```

### Wordlists recomendadas
- **Assetnote**: https://wordlists.assetnote.io/ (curadas, atualizadas)
- **SecLists**: baseline universal
- **Técnica**: use wordlists específicas da tech detectada
  - Spring: `spring-boot-actuator.txt`, endpoints comuns
  - Laravel: `.env`, `debug=true`, `telescope`
  - Next.js: `/_next/static/`, `/api/`
  - WordPress: `/wp-admin/`, `/wp-json/wp/v2/users`

## Etapa 6 — JavaScript Analysis

```bash
# Extrair JS URLs
grep -iE '\.js(\?|$)' recon/crawl.txt | sort -u > recon/js-urls.txt

# Baixar em paralelo
mkdir -p recon/js
cd recon/js
xargs -a ../js-urls.txt -P 10 -I{} curl -s -O {}

# Endpoints e secrets
linkfinder -i 'recon/js/*.js' -o cli > recon/js-endpoints.txt
secretfinder -i recon/js/*.js -o cli > recon/js-secrets.txt

# Procurar API keys (trufflehog em files, não git)
trufflehog filesystem recon/js/ > recon/js-trufflehog.txt
```

### Padrões manuais em JS
- Chaves AWS: `AKIA[0-9A-Z]{16}`
- Google API: `AIza[0-9A-Za-z\-_]{35}`
- Slack webhook: `https://hooks.slack.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[a-zA-Z0-9]+`
- Stripe: `sk_live_[0-9a-zA-Z]{24}`
- Firebase config: procurar `apiKey`, `authDomain`, `databaseURL`

## Etapa 7 — GitHub Dorking

### Queries úteis (substitua `target` e `target.com`)
```
org:target password
org:target api_key
org:target secret
org:target "BEGIN RSA PRIVATE KEY"
"target.com" filename:.env
"target.com" filename:config.json password
"@target.com" filename:.bash_history
```

### Automação
```bash
# github-dorker / gitdorker
gitdorker -t $GITHUB_TOKEN -q target.com -d dorks/alldorks.txt -o recon/github-dorking.txt
```

## Etapa 8 — Mobile & Backend Analysis

### Android APK
```bash
# Baixar APK (apkpure, apkmirror, extrair do device)
apktool d app.apk -o app-decoded/

# Endpoints e secrets
grep -rEo 'https?://[^"'\'' ]+' app-decoded/ | sort -u > recon/apk-endpoints.txt

# Firebase DB check
grep -r 'firebaseio.com' app-decoded/ → testa .json sem auth
```

### iOS IPA
```bash
# Unzip IPA
unzip app.ipa
cd Payload/App.app

# Binary strings
strings App | grep -iE 'http|api|token|key' > strings.txt
```

## Monitoramento Contínuo

### Novos subdomains/endpoints
```bash
# Diff semanal
sort recon/subdomains-all.txt > /tmp/now.txt
diff /tmp/last.txt /tmp/now.txt | grep '^>' > recon/new-subdomains.txt
cp /tmp/now.txt /tmp/last.txt
```

### GitHub release monitoring
Ver `scripts/release-monitor.sh` — captura janela de 24-72h após release nova (novelty premium).

### Stack mudou?
- `httpx -td` detecta tech atual vs última
- Mudança de framework = nova superfície

## Anti-patterns

- ❌ Rodar recon ativa (nmap -sV, ffuf) em out-of-scope
- ❌ Usar dicionários gigantes sem filtrar → rate limit / ban
- ❌ Não guardar raw outputs — auditoria futura fica impossível
- ❌ Scan sem User-Agent identificável (alguns programas exigem no bug bounty research)
- ❌ Ignorar CDN → muitos achados falsos positivos (mesmo target atrás de CloudFront aparece como N hosts)

## Fontes externas recomendadas

- **Jason Haddix** — *The Bug Hunter's Methodology* (YouTube/Twitter)
- **NahamSec** — recon-specific videos
- **ProjectDiscovery blog** — novas ferramentas e pipelines
- **Assetnote research** — wordlists + advisories
- **TrickestCo** — community-curated recon templates
