#!/usr/bin/env bash
# recon.sh — pipeline de recon passiva + ativa
# Uso: ./recon.sh <target-name>
# Lê scope.txt para domínios in-scope e roda subfinder → httpx → nuclei → katana.

set -euo pipefail

BOUNTY_ROOT="${BOUNTY_ROOT:-$HOME/bounty}"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
    echo "Uso: $0 <target-name>" >&2
    exit 1
fi

TARGET_DIR="$BOUNTY_ROOT/$TARGET"
[[ -d "$TARGET_DIR" ]] || { echo "Target não existe: $TARGET_DIR" >&2; exit 1; }
cd "$TARGET_DIR"

# Checar dependências mínimas
for cmd in subfinder httpx nuclei katana; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "Faltando: $cmd — ver SKILL.md Stack Técnico" >&2; exit 1; }
done

# Extrair domínios in-scope (linhas indentadas após "in_scope:", sem comentários)
SCOPE_FILE="scope.txt"
[[ -f "$SCOPE_FILE" ]] || { echo "scope.txt não encontrado" >&2; exit 1; }

# Parse simples: pega linhas indentadas após "in_scope:" até próxima chave
DOMAINS=$(awk '
    /^in_scope:/ { in_scope=1; next }
    /^[a-z_]+:/ && in_scope { in_scope=0 }
    in_scope && /^[[:space:]]+[^#[:space:]]/ {
        gsub(/^[[:space:]]+/, "")
        gsub(/^\*\./, "")
        print
    }
' "$SCOPE_FILE")

if [[ -z "$DOMAINS" ]]; then
    echo "Nenhum domínio in-scope encontrado em $SCOPE_FILE" >&2
    exit 1
fi

echo "=== Domínios in-scope ==="
echo "$DOMAINS"
echo ""

TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="recon/recon-$TIMESTAMP.log"
mkdir -p recon
echo "[$(date -u +%FT%TZ)] recon start for $TARGET" | tee -a "$LOG"

# 1. Subdomain enumeration
echo "[1/5] Subdomain enum (subfinder)..." | tee -a "$LOG"
echo "$DOMAINS" | while read -r d; do
    [[ -z "$d" ]] && continue
    subfinder -d "$d" -silent 2>>"$LOG"
done | sort -u > recon/subdomains.txt
echo "  → $(wc -l < recon/subdomains.txt) subdomínios" | tee -a "$LOG"

# 2. Resolução DNS + alive check (httpx)
echo "[2/5] httpx (alive + tech detect)..." | tee -a "$LOG"
httpx -l recon/subdomains.txt \
      -silent -title -tech-detect -status-code \
      -o recon/alive.txt -json > recon/alive.json 2>>"$LOG" || true
echo "  → $(wc -l < recon/alive.txt) hosts vivos" | tee -a "$LOG"

# 3. URL crawl (katana)
echo "[3/5] katana crawl..." | tee -a "$LOG"
katana -list recon/alive.txt -silent -depth 2 -jc -o recon/urls.txt 2>>"$LOG" || true
echo "  → $(wc -l < recon/urls.txt 2>/dev/null || echo 0) URLs" | tee -a "$LOG"

# 4. Nuclei (apenas inventário — achados reais vêm da análise humana)
echo "[4/5] nuclei scan (medium+, inventário)..." | tee -a "$LOG"
nuclei -l recon/alive.txt \
       -severity medium,high,critical \
       -silent -o "nuclei/scan-$TIMESTAMP.txt" 2>>"$LOG" || true
echo "  → $(wc -l < nuclei/scan-$TIMESTAMP.txt 2>/dev/null || echo 0) achados preliminares" | tee -a "$LOG"

# 5. JS analysis (extrair endpoints/secrets de JS files)
echo "[5/5] JS analysis..." | tee -a "$LOG"
grep -iE '\.js(\?|$)' recon/urls.txt 2>/dev/null | sort -u > recon/js-urls.txt || true
echo "  → $(wc -l < recon/js-urls.txt 2>/dev/null || echo 0) JS files" | tee -a "$LOG"

echo ""
echo "=== recon concluído ==="
echo "Output em: $TARGET_DIR/recon/"
echo "Log completo: $LOG"
echo ""
echo "Próximos passos:"
echo "  - Inspecionar recon/alive.txt (títulos/tech)"
echo "  - LinkFinder/SecretFinder em recon/js-urls.txt"
echo "  - ffuf em endpoints interessantes"
echo "  - Triar nuclei/scan-$TIMESTAMP.txt"
